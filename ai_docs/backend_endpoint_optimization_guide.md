# Backend Endpoint Optimization Guide

## Current Issue: Expedition Details Endpoint Timeout

**Endpoint:** `GET /api/expeditions/<int:expedition_id>`
**Status:** ❌ Timing out (>10 seconds)
**Expected Response Time:** < 500ms
**Error:** `'ExpeditionItem' object has no attribute 'product_id'` (Fixed)

---

## 🔍 Root Cause Analysis

### Current Implementation Flow

```python
# app.py:678
expedition_response = expedition_service.get_expedition_response(expedition_id)
    ↓
# expedition_service.py:475-482
def get_expedition_response(self, expedition_id: int):
    expedition = self.get_expedition_by_id(expedition_id)  # Query 1
    items = self.get_expedition_items(expedition_id)       # Query 2 + N queries
    return ExpeditionResponse.create(expedition, items)    # O(n) processing
```

### Identified Performance Bottlenecks

1. **N+1 Query Problem** - `get_expedition_items()` likely makes multiple database queries
2. **Missing Database Joins** - Fetching related data (products, consumptions) separately
3. **No Caching Strategy** - Every request hits the database
4. **Unoptimized Response Model** - `ExpeditionResponse` doesn't match API response structure
5. **Missing Indexes** - Potential missing indexes on foreign keys
6. **Synchronous Processing** - No async/parallel query execution

---

## 🎯 Optimization Strategy

### Phase 1: Quick Wins (30 minutes - 1 hour)

#### 1.1 Fix Response Model Mismatch

**Current Issue:** API expects fields that don't exist in `ExpeditionResponse`

```python
# API expects these fields (app.py:690-721):
{
    "items": [...],           # ✅ Exists
    "consumptions": [...],    # ❌ Missing - requires additional query
    "progress": {             # ❌ Missing - needs calculation
        "total_items": ...,
        "consumed_items": ...,
        "remaining_items": ...,
        "completion_percentage": ...,
        "total_value": ...,
        "consumed_value": ...,
        "remaining_value": ...
    }
}

# But ExpeditionResponse provides (models/expedition.py:334-358):
{
    "expedition": {...},
    "items": [...],
    "total_items_required": ...,
    "total_items_consumed": ...,
    "completion_percentage": ...
}
```

**Solution:** Update `ExpeditionResponse.create()` to fetch consumptions and calculate progress

```python
# models/expedition.py - Enhanced ExpeditionResponse
@dataclass
class ExpeditionResponse:
    expedition: Expedition
    items: List[ExpeditionItemWithProduct]  # Include product details
    consumptions: List[ItemConsumptionResponse]
    total_items: int
    consumed_items: int
    remaining_items: int
    completion_percentage: float
    total_value: Decimal
    consumed_value: Decimal
    remaining_value: Decimal

    @classmethod
    def create(cls, expedition: Expedition, items: List, consumptions: List):
        """Create expedition response with all required data."""
        total_items = sum(item.quantity_needed for item in items)
        consumed_items = sum(item.quantity_consumed for item in items)
        remaining_items = total_items - consumed_items

        completion_pct = (consumed_items / total_items * 100) if total_items > 0 else 0

        total_value = sum(item.quantity_needed * item.unit_price for item in items)
        consumed_value = sum(c.total_price for c in consumptions)
        remaining_value = total_value - consumed_value

        return cls(
            expedition=expedition,
            items=items,
            consumptions=consumptions,
            total_items=total_items,
            consumed_items=consumed_items,
            remaining_items=remaining_items,
            completion_percentage=completion_pct,
            total_value=total_value,
            consumed_value=consumed_value,
            remaining_value=remaining_value
        )
```

#### 1.2 Add Single Optimized Query

**Replace multiple queries with ONE database query using JOINs:**

```python
# services/expedition_service.py - NEW METHOD
def get_expedition_details_optimized(self, expedition_id: int) -> Optional[dict]:
    """
    Get complete expedition data in a SINGLE optimized query.
    Uses JOINs to fetch expedition, items, products, and consumptions.
    """
    query = """
    WITH expedition_data AS (
        SELECT
            e.id, e.name, e.owner_chat_id, e.status, e.deadline,
            e.created_at, e.completed_at,
            COUNT(DISTINCT ei.id) as item_count
        FROM expeditions e
        LEFT JOIN expedition_items ei ON e.id = ei.expedition_id
        WHERE e.id = %s
        GROUP BY e.id
    ),
    items_data AS (
        SELECT
            ei.id, ei.expedition_id, ei.produto_id,
            p.nome as product_name, p.emoji as product_emoji,
            ei.quantity_required as quantity_needed,
            p.preco as unit_price,
            ei.created_at as added_at,
            COALESCE(SUM(ic.quantity), 0) as quantity_consumed
        FROM expedition_items ei
        JOIN produtos p ON ei.produto_id = p.id
        LEFT JOIN item_consumptions ic ON ei.id = ic.expedition_item_id
        WHERE ei.expedition_id = %s
        GROUP BY ei.id, p.id
    ),
    consumptions_data AS (
        SELECT
            ic.id, ic.consumer_name, ic.quantity,
            ic.unit_price, ic.total_price, ic.payment_status,
            ic.consumed_at, p.nome as product_name
        FROM item_consumptions ic
        JOIN expedition_items ei ON ic.expedition_item_id = ei.id
        JOIN produtos p ON ei.produto_id = p.id
        WHERE ic.expedition_id = %s
        ORDER BY ic.consumed_at DESC
    )
    SELECT * FROM expedition_data, items_data, consumptions_data;
    """

    # Execute single query and transform results
    # This reduces database round-trips from ~10+ to 1
    ...
```

#### 1.3 Add Response Caching

```python
# utils/query_cache.py - Use existing cache system
from utils.query_cache import cached_query

@cached_query(ttl=60)  # Cache for 60 seconds
def get_expedition_response(self, expedition_id: int):
    """Cached expedition response."""
    return self._fetch_expedition_details(expedition_id)
```

---

### Phase 2: Database Optimization (1-2 hours)

#### 2.1 Add Missing Indexes

```sql
-- Check existing indexes
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('expeditions', 'expedition_items', 'item_consumptions')
ORDER BY tablename, indexname;

-- Add recommended indexes
CREATE INDEX IF NOT EXISTS idx_expedition_items_expedition_id
    ON expedition_items(expedition_id);

CREATE INDEX IF NOT EXISTS idx_expedition_items_produto_id
    ON expedition_items(produto_id);

CREATE INDEX IF NOT EXISTS idx_item_consumptions_expedition_id
    ON item_consumptions(expedition_id);

CREATE INDEX IF NOT EXISTS idx_item_consumptions_expedition_item_id
    ON item_consumptions(expedition_item_id);

CREATE INDEX IF NOT EXISTS idx_item_consumptions_payment_status
    ON item_consumptions(payment_status);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_expedition_status_created
    ON expeditions(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_consumptions_expedition_consumed
    ON item_consumptions(expedition_id, consumed_at DESC);
```

#### 2.2 Analyze Query Performance

```sql
-- Enable query timing
\timing on

-- Analyze slow query
EXPLAIN ANALYZE
SELECT * FROM expeditions e
LEFT JOIN expedition_items ei ON e.id = ei.expedition_id
LEFT JOIN item_consumptions ic ON ei.id = ic.expedition_item_id
WHERE e.id = 7;

-- Check for sequential scans (bad)
-- Look for Index Scan (good) or Seq Scan (bad)
```

#### 2.3 Add Database Statistics

```sql
-- Update table statistics for better query planning
ANALYZE expeditions;
ANALYZE expedition_items;
ANALYZE item_consumptions;
ANALYZE produtos;

-- Vacuum tables to reclaim space
VACUUM ANALYZE expeditions;
VACUUM ANALYZE expedition_items;
```

---

### Phase 3: Architecture Improvements (2-4 hours)

#### 3.1 Implement Data Transfer Objects (DTOs)

```python
# models/expedition.py
@dataclass
class ExpeditionDetailsDTO:
    """Optimized DTO for expedition details API response."""
    id: int
    name: str
    owner_chat_id: int
    status: str
    deadline: Optional[str]
    created_at: Optional[str]
    completed_at: Optional[str]
    items: List[dict]
    consumptions: List[dict]
    progress: dict

    def to_json(self) -> dict:
        """Convert to JSON-serializable dict."""
        return asdict(self)
```

#### 3.2 Add Request/Response Validation

```python
# services/expedition_service.py
from functools import lru_cache

class ExpeditionService:
    @lru_cache(maxsize=128)
    def get_expedition_summary(self, expedition_id: int) -> dict:
        """Lightweight endpoint for listings (no consumptions)."""
        # Faster alternative for when full details aren't needed
        ...
```

#### 3.3 Implement Pagination for Consumptions

```python
def get_expedition_details(
    self,
    expedition_id: int,
    include_consumptions: bool = True,
    consumption_limit: int = 50
) -> ExpeditionDetailsDTO:
    """
    Get expedition with optional consumption pagination.
    For expeditions with 100+ consumptions, this prevents timeout.
    """
    ...
```

---

### Phase 4: Advanced Optimizations (Optional)

#### 4.1 Add Database View

```sql
-- Create materialized view for expensive calculations
CREATE MATERIALIZED VIEW expedition_stats AS
SELECT
    e.id as expedition_id,
    COUNT(DISTINCT ei.id) as total_items,
    COALESCE(SUM(ei.quantity_required), 0) as total_quantity_needed,
    COALESCE(SUM(ic.quantity), 0) as total_quantity_consumed,
    COALESCE(SUM(ei.quantity_required * p.preco), 0) as total_value,
    COALESCE(SUM(ic.total_price), 0) as consumed_value
FROM expeditions e
LEFT JOIN expedition_items ei ON e.id = ei.expedition_id
LEFT JOIN produtos p ON ei.produto_id = p.id
LEFT JOIN item_consumptions ic ON ei.id = ic.expedition_item_id
GROUP BY e.id;

-- Refresh periodically (or on data change)
REFRESH MATERIALIZED VIEW expedition_stats;
```

#### 4.2 Add Redis Caching (Production)

```python
# config/redis_cache.py
import redis
import json

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

def cache_expedition(expedition_id: int, data: dict, ttl: int = 300):
    """Cache expedition data in Redis."""
    key = f"expedition:{expedition_id}"
    redis_client.setex(key, ttl, json.dumps(data))

def get_cached_expedition(expedition_id: int) -> Optional[dict]:
    """Get cached expedition data."""
    key = f"expedition:{expedition_id}"
    data = redis_client.get(key)
    return json.loads(data) if data else None
```

#### 4.3 Add Background Jobs for Heavy Calculations

```python
# For analytics/timeline endpoints that timeout
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task
def calculate_expedition_analytics():
    """Calculate analytics in background."""
    # Heavy calculations run async
    ...
```

---

## 📊 Performance Testing

### Benchmark Current Performance

```python
# tests/performance/test_expedition_endpoint.py
import time
import requests

def test_expedition_details_performance():
    """Ensure expedition details load under 500ms."""
    start = time.time()

    response = requests.get(
        'http://localhost:5000/api/expeditions/7',
        headers={'X-Chat-ID': '5094426438'}
    )

    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 0.5, f"Response took {duration}s (> 500ms)"

    data = response.json()
    assert 'items' in data
    assert 'consumptions' in data
    assert 'progress' in data
```

### Load Testing

```bash
# Using Apache Bench
ab -n 100 -c 10 \
   -H "X-Chat-ID: 5094426438" \
   http://localhost:5000/api/expeditions/7

# Expected results:
# - Requests per second: > 20
# - Mean response time: < 500ms
# - 95th percentile: < 1000ms
```

---

## ✅ Implementation Checklist

### Immediate Actions (Do First)
- [ ] Fix `ExpeditionResponse` model to include `consumptions` and `progress`
- [ ] Update `get_expedition_response()` to fetch all required data
- [ ] Add caching with 60-second TTL
- [ ] Test endpoint response time

### Short Term (This Week)
- [ ] Create optimized single-query method with JOINs
- [ ] Add database indexes on foreign keys
- [ ] Run ANALYZE on all expedition tables
- [ ] Add performance tests
- [ ] Monitor query execution times

### Medium Term (Next Sprint)
- [ ] Implement pagination for large consumption lists
- [ ] Add lightweight "summary" endpoint for listings
- [ ] Create database views for expensive calculations
- [ ] Add Redis caching for production

### Long Term (Future)
- [ ] Implement background jobs for analytics
- [ ] Add database connection pooling optimization
- [ ] Consider read replicas for heavy queries
- [ ] Implement GraphQL for flexible data fetching

---

## 🔧 Quick Fix Template

Here's a complete quick fix you can implement right now:

```python
# services/expedition_service.py

def get_expedition_response(self, expedition_id: int) -> Optional[dict]:
    """Get complete expedition data - OPTIMIZED VERSION."""

    # Single optimized query
    query = """
        SELECT
            -- Expedition data
            e.id, e.name, e.owner_chat_id, e.status,
            e.deadline, e.created_at, e.completed_at,

            -- Item data
            json_agg(DISTINCT jsonb_build_object(
                'id', ei.id,
                'product_id', ei.produto_id,
                'product_name', p.nome,
                'product_emoji', p.emoji,
                'quantity_needed', ei.quantity_required,
                'unit_price', p.preco,
                'added_at', ei.created_at
            )) FILTER (WHERE ei.id IS NOT NULL) as items,

            -- Consumption data
            json_agg(DISTINCT jsonb_build_object(
                'id', ic.id,
                'consumer_name', ic.consumer_name,
                'product_name', p2.nome,
                'quantity', ic.quantity,
                'unit_price', ic.unit_price,
                'total_price', ic.total_price,
                'payment_status', ic.payment_status,
                'consumed_at', ic.consumed_at
            )) FILTER (WHERE ic.id IS NOT NULL) as consumptions

        FROM expeditions e
        LEFT JOIN expedition_items ei ON e.id = ei.expedition_id
        LEFT JOIN produtos p ON ei.produto_id = p.id
        LEFT JOIN item_consumptions ic ON ic.expedition_id = e.id
        LEFT JOIN expedition_items ei2 ON ic.expedition_item_id = ei2.id
        LEFT JOIN produtos p2 ON ei2.produto_id = p2.id
        WHERE e.id = %s
        GROUP BY e.id
    """

    result = self._execute_single_query(query, (expedition_id,))

    if not result:
        return None

    # Transform to expected format
    return self._build_response_dict(result)
```

---

## 📈 Expected Results

| Metric | Before | After Optimization | Target |
|--------|--------|-------------------|--------|
| Response Time | >10s | <500ms | <200ms |
| Database Queries | 10-20+ | 1-2 | 1 |
| Cache Hit Rate | 0% | 80%+ | 90%+ |
| Memory Usage | High | Medium | Low |
| Concurrent Users | <5 | 50+ | 100+ |

---

## 🚨 Common Pitfalls to Avoid

1. **Don't** add indexes on every column - only frequently queried ones
2. **Don't** cache forever - use reasonable TTLs (30-300 seconds)
3. **Don't** fetch all consumptions - paginate large datasets
4. **Don't** ignore database connection pooling
5. **Don't** skip testing with realistic data volumes

---

## 📚 Resources

- PostgreSQL EXPLAIN: https://www.postgresql.org/docs/current/sql-explain.html
- Python Query Optimization: https://wiki.postgresql.org/wiki/Performance_Optimization
- Flask Caching: https://flask-caching.readthedocs.io/
- Redis Caching Patterns: https://redis.io/docs/manual/patterns/

---

## 💡 Next Steps

1. Start with Phase 1 (Quick Wins) - Can be done in 1 hour
2. Test performance improvement
3. If still slow, proceed to Phase 2 (Database Optimization)
4. Monitor and iterate based on results

**Target: Get expedition details endpoint to <500ms response time** ⚡
