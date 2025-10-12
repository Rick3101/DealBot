# Endpoint Performance Diagnostic Checklist

## 🔍 How to Find What's Slow

Use this checklist to diagnose performance issues in any endpoint.

---

## Step 1: Add Timing Logs (2 minutes)

Add timing logs to identify bottlenecks:

```python
# app.py - Expedition details endpoint
import time

@app.route("/api/expeditions/<int:expedition_id>", methods=["GET"])
def api_expedition_by_id(expedition_id: int):
    start_time = time.time()

    # ... existing auth code ...

    logger.debug(f"[PERF] Auth check: {time.time() - start_time:.3f}s")
    step_time = time.time()

    expedition = expedition_service.get_expedition_by_id(expedition_id)
    logger.debug(f"[PERF] Get expedition: {time.time() - step_time:.3f}s")
    step_time = time.time()

    expedition_response = expedition_service.get_expedition_response(expedition_id)
    logger.debug(f"[PERF] Get response: {time.time() - step_time:.3f}s")
    step_time = time.time()

    # Build JSON response
    response_data = {...}
    logger.debug(f"[PERF] Build JSON: {time.time() - step_time:.3f}s")

    logger.info(f"[PERF] TOTAL: {time.time() - start_time:.3f}s")

    return jsonify(response_data)
```

### Check logs:
```bash
# Windows
type logs\app.log | findstr PERF

# Expected output:
# [PERF] Auth check: 0.002s
# [PERF] Get expedition: 0.150s  ← If this is >1s, database is slow
# [PERF] Get response: 8.500s    ← If this is high, service method is slow
# [PERF] Build JSON: 0.001s
# [PERF] TOTAL: 8.653s
```

---

## Step 2: Profile Database Queries (5 minutes)

Add query timing to service methods:

```python
# services/expedition_service.py

def get_expedition_response(self, expedition_id: int):
    import time

    logger.debug(f"[QUERY] Starting expedition response for {expedition_id}")

    start = time.time()
    expedition = self.get_expedition_by_id(expedition_id)
    logger.debug(f"[QUERY] get_expedition_by_id: {time.time() - start:.3f}s")

    start = time.time()
    items = self.get_expedition_items(expedition_id)
    logger.debug(f"[QUERY] get_expedition_items: {time.time() - start:.3f}s")
    logger.debug(f"[QUERY] Items count: {len(items)}")

    # Add more timing for each operation
    ...
```

### Analyze query logs:
```bash
type logs\app.log | findstr QUERY

# Look for:
# [QUERY] get_expedition_items: 5.000s  ← Too slow! N+1 query problem
# [QUERY] Items count: 100              ← Too many individual queries?
```

---

## Step 3: Check Database Performance (10 minutes)

### Enable PostgreSQL slow query logging:

```sql
-- Check current settings
SHOW log_min_duration_statement;

-- Enable slow query logging (log queries >100ms)
ALTER DATABASE your_database SET log_min_duration_statement = 100;

-- OR for current session only:
SET log_min_duration_statement = 100;
```

### Run query with EXPLAIN ANALYZE:

```sql
-- See actual execution time
EXPLAIN ANALYZE
SELECT * FROM expeditions WHERE id = 7;

-- Check for:
-- 1. Seq Scan (bad) vs Index Scan (good)
-- 2. Actual time (milliseconds)
-- 3. Rows returned vs estimated
```

### Example output:
```
Index Scan using expeditions_pkey on expeditions  (cost=0.14..8.16 rows=1 width=100) (actual time=0.015..0.016 rows=1 loops=1)
  Index Cond: (id = 7)
Planning Time: 0.089 ms
Execution Time: 0.042 ms  ← Good! <100ms
```

vs

```
Seq Scan on expedition_items  (cost=0.00..1000.00 rows=1000 width=100) (actual time=0.020..150.500 rows=1000 loops=1)
  Filter: (expedition_id = 7)
Planning Time: 0.100 ms
Execution Time: 150.600 ms  ← Bad! Sequential scan, >100ms
```

---

## Step 4: Check for N+1 Query Problem (5 minutes)

The N+1 problem happens when you:
1. Fetch a list (1 query)
2. Loop through and fetch details for each (N queries)

### How to detect:

```python
# Add query counter
query_count = 0

# In database connection manager
def execute_query(self, query, params=None):
    global query_count
    query_count += 1
    logger.debug(f"[QUERY #{query_count}] {query[:100]}")
    return super().execute_query(query, params)
```

### Check logs:
```bash
# If you see:
# [QUERY #1] SELECT * FROM expeditions WHERE id = 7
# [QUERY #2] SELECT * FROM expedition_items WHERE expedition_id = 7
# [QUERY #3] SELECT * FROM produtos WHERE id = 1  ← RED FLAG!
# [QUERY #4] SELECT * FROM produtos WHERE id = 2  ← N+1 problem!
# [QUERY #5] SELECT * FROM produtos WHERE id = 3
# ...
# [QUERY #52] SELECT * FROM produtos WHERE id = 50
```

**Solution:** Use JOIN to fetch all at once:
```sql
SELECT ei.*, p.* FROM expedition_items ei
JOIN produtos p ON ei.produto_id = p.id
WHERE ei.expedition_id = 7
```

---

## Step 5: Check Network/Connection Issues (3 minutes)

### Test database connection speed:

```python
import time
from database.connection import get_db_manager

db = get_db_manager()

# Test simple query
start = time.time()
result = db.execute_query("SELECT 1")
print(f"Simple query: {time.time() - start:.3f}s")

# Test with data
start = time.time()
result = db.execute_query("SELECT * FROM expeditions LIMIT 1")
print(f"Table query: {time.time() - start:.3f}s")
```

Expected:
- Simple query: <50ms
- Table query: <100ms

If slower:
- Check database host (remote vs local)
- Check network latency
- Check connection pool size

---

## Step 6: Profile Python Code (Advanced)

Use cProfile to find slow Python code:

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your slow code here
expedition_service.get_expedition_response(7)

profiler.disable()

# Print stats
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest functions
```

Look for:
- High `cumtime` (cumulative time)
- High `ncalls` (number of calls)
- Unexpected slow functions

---

## 🎯 Common Performance Issues & Solutions

### Issue 1: Slow Database Queries
**Symptom:** `[QUERY] get_expedition_items: 5.000s`
**Solution:**
- Add indexes
- Use JOINs instead of multiple queries
- Optimize WHERE clauses

### Issue 2: N+1 Queries
**Symptom:** 50+ queries for a single endpoint
**Solution:**
- Use JOIN to fetch related data
- Use `select_related()` or eager loading
- Batch queries

### Issue 3: Missing Indexes
**Symptom:** `Seq Scan` in EXPLAIN output
**Solution:**
```sql
CREATE INDEX idx_expedition_items_expedition_id ON expedition_items(expedition_id);
```

### Issue 4: Large Data Transfer
**Symptom:** 1000+ consumptions being fetched
**Solution:**
- Add pagination
- Limit results (e.g., last 50 consumptions)
- Add filters

### Issue 5: Slow JSON Serialization
**Symptom:** `[PERF] Build JSON: 2.000s`
**Solution:**
- Use `orjson` instead of `json`
- Pre-format dates/decimals
- Remove unnecessary fields

### Issue 6: No Caching
**Symptom:** Same data fetched repeatedly
**Solution:**
- Add Redis/memory cache
- Use query result caching
- Cache computed values

---

## 📊 Performance Metrics Reference

| Operation | Target | Warning | Critical |
|-----------|--------|---------|----------|
| Simple SELECT | <10ms | <50ms | >100ms |
| JOIN query | <50ms | <200ms | >500ms |
| Full endpoint | <200ms | <500ms | >1000ms |
| With cache hit | <10ms | <50ms | >100ms |
| Database connection | <20ms | <100ms | >500ms |

---

## ✅ Diagnostic Workflow

1. **Add timing logs** → Find which part is slow
2. **Profile database** → Check query performance
3. **Check for N+1** → Look for repeated queries
4. **Test connection** → Rule out network issues
5. **Profile Python** → Find slow code
6. **Apply fix** → Based on findings
7. **Measure again** → Verify improvement

---

## 🔧 Quick Diagnostic Script

Save this as `diagnose_endpoint.py`:

```python
import time
import requests
import json

def diagnose_endpoint(url, headers=None):
    """Diagnose endpoint performance."""
    print(f"\n🔍 Diagnosing: {url}\n")

    # Test 1: Response time
    start = time.time()
    try:
        response = requests.get(url, headers=headers, timeout=30)
        duration = time.time() - start

        print(f"✓ Response Time: {duration:.3f}s")
        print(f"✓ Status Code: {response.status_code}")
        print(f"✓ Response Size: {len(response.content)} bytes")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ JSON Keys: {list(data.keys())}")

            # Check data structure
            if 'items' in data:
                print(f"✓ Items Count: {len(data['items'])}")
            if 'consumptions' in data:
                print(f"✓ Consumptions Count: {len(data['consumptions'])}")

        # Performance rating
        if duration < 0.2:
            print("\n🟢 EXCELLENT (<200ms)")
        elif duration < 0.5:
            print("\n🟡 GOOD (<500ms)")
        elif duration < 1.0:
            print("\n🟠 ACCEPTABLE (<1s)")
        else:
            print("\n🔴 SLOW (>1s) - Needs optimization!")

    except requests.Timeout:
        print("\n❌ TIMEOUT - Endpoint taking >30s")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

# Usage
diagnose_endpoint(
    'http://localhost:5000/api/expeditions/7',
    headers={'X-Chat-ID': '5094426438'}
)
```

Run with:
```bash
python diagnose_endpoint.py
```

---

## 📚 Additional Resources

- **PostgreSQL Performance:** https://wiki.postgresql.org/wiki/Performance_Optimization
- **Flask Profiling:** https://flask.palletsprojects.com/en/2.3.x/logging/
- **Python cProfile:** https://docs.python.org/3/library/profile.html
- **Database Indexing:** https://use-the-index-luke.com/

---

**Remember:** Measure first, then optimize. Don't guess where the slowness is!
