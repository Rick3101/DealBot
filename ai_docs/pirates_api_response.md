# Pirates API Response Structure

## Endpoint
`GET /api/brambler/names/{expedition_id}`

## Headers Required
```
X-Chat-ID: {user_chat_id}
```

## Response Structure

```json
{
  "pirate_names": [
    {
      "id": 13,
      "expedition_id": 7,
      "pirate_name": "Corsário Tsunami o Destemido",
      "original_name": "criss",  // Only visible to owner/admin
      "created_at": "2025-10-10T19:37:51.375238",

      "stats": {
        "total_items": 4,           // Number of consumption records
        "items_consumed": 165,      // ← TOTAL QUANTITY CONSUMED
        "total_spent": 36870.0,     // ← TOTAL AMOUNT SPENT
        "total_paid": 49064.0,      // Total amount paid
        "debt": -12194.0            // Remaining debt (negative = overpaid)
      },

      "recent_items": [             // ← RECENT ITEMS (last 3)
        {
          "name": "Ice",
          "emoji": "🧊",
          "quantity": 12,
          "consumed_at": "2025-10-12T09:37:04.403425"
        },
        {
          "name": "@ - 180",
          "emoji": "🍐",
          "quantity": 30,
          "consumed_at": "2025-10-11T14:14:14.644993"
        },
        {
          "name": "Organicas",
          "emoji": "🦠",
          "quantity": 3,
          "consumed_at": "2025-10-10T20:50:08.440174"
        }
      ]
    }
  ]
}
```

## Frontend Display Mapping

### Pirate Card Fields:

1. **Total Spent**
   - Path: `pirate.stats.total_spent`
   - Type: `number`
   - Example: `36870.0`

2. **Items Consumed**
   - Path: `pirate.stats.items_consumed`
   - Type: `number`
   - Example: `165`

3. **Recent Items**
   - Path: `pirate.recent_items`
   - Type: `array`
   - Each item has:
     - `name`: Product name (string)
     - `emoji`: Product emoji (string)
     - `quantity`: Quantity consumed (number)
     - `consumed_at`: ISO timestamp (string)

### Example TypeScript Interface:

```typescript
interface PirateStats {
  total_items: number;
  items_consumed: number;  // ← Use this for "Items Consumed"
  total_spent: number;      // ← Use this for "Total Spent"
  total_paid: number;
  debt: number;
}

interface RecentItem {
  name: string;
  emoji: string;
  quantity: number;
  consumed_at: string;
}

interface Pirate {
  id: number;
  expedition_id: number;
  pirate_name: string;
  original_name: string | null;
  created_at: string;
  stats: PirateStats;
  recent_items: RecentItem[];  // ← Use this for "Recent Items"
}
```

### React Component Example:

```tsx
const PirateCard = ({ pirate }: { pirate: Pirate }) => {
  return (
    <div className="pirate-card">
      <h3>{pirate.pirate_name}</h3>

      {/* Total Spent */}
      <div>Total Spent: R$ {pirate.stats.total_spent.toFixed(2)}</div>

      {/* Items Consumed */}
      <div>Items Consumed: {pirate.stats.items_consumed}</div>

      {/* Recent Items */}
      <div>
        <h4>Recent Items:</h4>
        {pirate.recent_items.map((item, index) => (
          <div key={index}>
            {item.emoji} {item.name} x{item.quantity}
          </div>
        ))}
      </div>
    </div>
  );
};
```

## Common Issues:

1. **Showing zeros**: Check that you're accessing `stats.items_consumed` and `stats.total_spent`, not other fields
2. **Recent items not showing**: Check that you're accessing `recent_items` array, not a different field
3. **Data not updating**: Make sure the frontend is re-fetching after the API changes

## Test the API:

```bash
curl -H "X-Chat-ID: 5094426438" http://localhost:5000/api/brambler/names/7
```
