# Expedition Endpoint Quick Fix - Action Plan

## 🎯 Goal
Fix `/api/expeditions/<id>` endpoint timeout issue (currently >10s → target <500ms)

---

## ⚡ Immediate Fix (30 minutes)

### Problem Identified
The API response structure doesn't match the data model:

**API Needs (app.py:690-721):**
```json
{
  "items": [...],
  "consumptions": [...],  ❌ Missing - extra query needed
  "progress": {           ❌ Missing - calculations needed
    "total_value": ...,
    "consumed_value": ...,
    ...
  }
}
```

**Model Provides (ExpeditionResponse):**
```json
{
  "expedition": {...},
  "items": [...],
  "total_items_required": ...,  ❌ Different field names
  "total_items_consumed": ...
}
```

### Root Cause
`get_expedition_response()` makes multiple queries:
1. Get expedition
2. Get items (potentially N+1 queries)
3. Missing: Get consumptions
4. Missing: Calculate progress values

---

## 🔧 Step-by-Step Fix

### Step 1: Update the Service Method (5 min)

**File:** `services/expedition_service.py:475`

```python
def get_expedition_response(self, expedition_id: int) -> Optional[dict]:
    """Get complete expedition data with consumptions and progress."""

    # Get basic expedition data
    expedition = self.get_expedition_by_id(expedition_id)
    if not expedition:
        return None

    # Get items with product details
    items = self.get_expedition_items_with_products(expedition_id)

    # Get consumptions ← ADD THIS
    consumptions = self.get_expedition_consumptions(expedition_id)

    # Calculate progress ← ADD THIS
    progress = self._calculate_expedition_progress(items, consumptions)

    # Build response
    return {
        'expedition': expedition,
        'items': items,
        'consumptions': consumptions,
        'progress': progress
    }
```

### Step 2: Add Helper Methods (10 min)

```python
def get_expedition_consumptions(self, expedition_id: int) -> List[dict]:
    """Get all consumptions for an expedition."""
    query = """
        SELECT
            ic.id, ic.consumer_name, ic.quantity,
            ic.unit_price, ic.total_price, ic.payment_status,
            ic.consumed_at, p.nome as product_name
        FROM item_consumptions ic
        JOIN expedition_items ei ON ic.expedition_item_id = ei.id
        JOIN produtos p ON ei.produto_id = p.id
        WHERE ic.expedition_id = %s
        ORDER BY ic.consumed_at DESC
    """

    results = self.db_manager.execute_query(query, (expedition_id,))
    return [dict(row) for row in results]

def _calculate_expedition_progress(
    self,
    items: List[dict],
    consumptions: List[dict]
) -> dict:
    """Calculate expedition progress metrics."""
    total_items = sum(item['quantity_needed'] for item in items)
    consumed_items = sum(item.get('quantity_consumed', 0) for item in items)
    remaining_items = total_items - consumed_items

    total_value = sum(
        item['quantity_needed'] * item['unit_price']
        for item in items
    )
    consumed_value = sum(c['total_price'] for c in consumptions)
    remaining_value = total_value - consumed_value

    completion_pct = (consumed_items / total_items * 100) if total_items > 0 else 0

    return {
        'total_items': total_items,
        'consumed_items': consumed_items,
        'remaining_items': remaining_items,
        'completion_percentage': round(completion_pct, 2),
        'total_value': float(total_value),
        'consumed_value': float(consumed_value),
        'remaining_value': float(remaining_value)
    }
```

### Step 3: Update get_expedition_items (10 min)

Make sure items include product details and consumption count:

```python
def get_expedition_items_with_products(self, expedition_id: int) -> List[dict]:
    """Get expedition items with product details and consumption count."""
    query = """
        SELECT
            ei.id,
            ei.produto_id,
            p.nome as product_name,
            p.emoji as product_emoji,
            ei.quantity_required as quantity_needed,
            p.preco as unit_price,
            ei.created_at as added_at,
            COALESCE(SUM(ic.quantity), 0) as quantity_consumed
        FROM expedition_items ei
        JOIN produtos p ON ei.produto_id = p.id
        LEFT JOIN item_consumptions ic ON ei.id = ic.expedition_item_id
        WHERE ei.expedition_id = %s
        GROUP BY ei.id, p.id
        ORDER BY ei.created_at
    """

    results = self.db_manager.execute_query(query, (expedition_id,))
    return [dict(row) for row in results]
```

### Step 4: Update API Endpoint (5 min)

**File:** `app.py:676-722`

```python
if request.method == "GET":
    # Get detailed expedition response
    data = expedition_service.get_expedition_response(expedition_id)
    if not data:
        return jsonify({"error": "Expedition details not available"}), 500

    # Extract data
    expedition = data['expedition']
    items = data['items']
    consumptions = data['consumptions']
    progress = data['progress']

    return jsonify({
        "id": expedition.id,
        "name": expedition.name,
        "owner_chat_id": expedition.owner_chat_id,
        "status": expedition.status.value,
        "deadline": expedition.deadline.isoformat() if expedition.deadline else None,
        "created_at": expedition.created_at.isoformat() if expedition.created_at else None,
        "completed_at": expedition.completed_at.isoformat() if expedition.completed_at else None,
        "items": items,            # Already formatted
        "consumptions": consumptions,  # Already formatted
        "progress": progress       # Already formatted
    })
```

---

## 🧪 Testing

### Test 1: Basic Functionality
```bash
curl -H "X-Chat-ID: 5094426438" http://localhost:5000/api/expeditions/7 | jq
```

Expected: Response in <1 second with all fields

### Test 2: Performance
```python
import time, requests

start = time.time()
response = requests.get(
    'http://localhost:5000/api/expeditions/7',
    headers={'X-Chat-ID': '5094426438'}
)
print(f"Response time: {time.time() - start:.2f}s")
print(f"Status: {response.status_code}")
```

Expected: <0.5 seconds

### Test 3: Validate Response Structure
```python
data = response.json()
assert 'items' in data
assert 'consumptions' in data
assert 'progress' in data
assert 'total_value' in data['progress']
assert 'consumed_value' in data['progress']
```

---

## 📊 Expected Improvement

| Before | After |
|--------|-------|
| >10s timeout | <500ms |
| 10+ queries | 3 queries |
| Missing data | Complete |

---

## 🚨 If Still Slow

If response time is still >500ms after this fix:

1. **Add indexes:**
```sql
CREATE INDEX idx_item_consumptions_expedition_id ON item_consumptions(expedition_id);
CREATE INDEX idx_expedition_items_expedition_id ON expedition_items(expedition_id);
```

2. **Add caching:**
```python
from utils.query_cache import cached_query

@cached_query(ttl=60)
def get_expedition_response(self, expedition_id: int):
    ...
```

3. **Check for full guide:** See `ai_docs/backend_endpoint_optimization_guide.md`

---

## ✅ Completion Checklist

- [ ] Update `get_expedition_response()` method
- [ ] Add `get_expedition_consumptions()` method
- [ ] Add `_calculate_expedition_progress()` method
- [ ] Update `get_expedition_items_with_products()` method
- [ ] Update API endpoint response building
- [ ] Test with curl/Postman
- [ ] Measure response time
- [ ] Test in webapp ExpeditionDetails page

---

## 📝 Notes

- This fix addresses the immediate timeout issue
- For production, consider the advanced optimizations in the full guide
- Monitor performance after deployment
- Add logging to track slow queries

**Estimated Implementation Time:** 30-45 minutes
