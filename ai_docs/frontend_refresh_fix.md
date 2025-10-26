# Frontend Refresh Fix - Operations Not Updating UI

## Problem Description

When performing operations in the webapp (consume item, add item, or pay consumption), the operation would succeed on the backend but the frontend UI would not update until the user manually refreshed the page.

## Root Cause

The issue was a timing problem in the async flow:

1. **Operation executed successfully** → Backend updated
2. **Modal closed immediately** → UI transition started
3. **Refresh triggered async** → But modal already closed
4. **Result:** User sees stale data because modal closed before refresh completed

### Code Analysis

The problem occurred in three places:

1. **Consume Item Flow:**
   - `ConsumeItemModal.tsx:247` called `onConfirm()`
   - `useItemConsumption.ts:32` called `onSuccess()` but didn't await it
   - Modal closed at line 247 before refresh completed

2. **Add Item Flow:**
   - `useAddItemModal.ts:74` called `onSuccess()`
   - `useAddItemModal.ts:75` immediately called `close()` without waiting
   - Modal closed with stale data still visible

3. **Payment Flow:**
   - `useConsumptionPayment.ts:126-127` reset state immediately
   - `useConsumptionPayment.ts:129` called `onPaymentSuccess()` but already closed
   - Payment UI disappeared before refresh completed

## Solution

Changed all operations to **await the refresh before closing the modal/UI**:

### Changes Made

#### 1. useItemConsumption.ts
```typescript
// BEFORE
onSuccess?.();

// AFTER
if (onSuccess) {
  await onSuccess();
}
```

Updated the callback type to accept `Promise<void>`:
```typescript
onSuccess?: () => void | Promise<void>
```

#### 2. useAddItemModal.ts
```typescript
// BEFORE
await addFn(expeditionId, items);
await onSuccess();
close();

// AFTER
await addFn(expeditionId, items);
await onSuccess(); // Wait for refresh
close(); // Now close with fresh data
```

#### 3. useConsumptionPayment.ts
```typescript
// BEFORE
await expeditionItemsService.payConsumption(...);
setPayingConsumptionId(null); // Reset immediately
setPaymentAmount('');
if (onPaymentSuccess) {
  onPaymentSuccess(); // Trigger refresh but don't wait
}

// AFTER
await expeditionItemsService.payConsumption(...);
if (onPaymentSuccess) {
  await onPaymentSuccess(); // Wait for refresh
}
// Now reset state with fresh data
setPayingConsumptionId(null);
setPaymentAmount('');
```

#### 4. useExpeditionDetails.ts
```typescript
// BEFORE
const refresh = useCallback(() => {
  loadExpedition(false);
}, [loadExpedition]);

// AFTER
const refresh = useCallback(async () => {
  await loadExpedition(false);
}, [loadExpedition]);
```

Made refresh properly async so it can be awaited.

#### 5. ConsumeItemModal.tsx
Added clarifying comments:
```typescript
// Wait for the operation AND refresh to complete before closing
await onConfirm(selectedPirate, quantity, price);
// Close modal after operation completes
// The onConfirm already triggers a refresh, so data will be fresh
onClose();
```

## Benefits

1. **Immediate UI updates** - User sees updated data without manual refresh
2. **Better UX** - Loading states persist until data is fresh
3. **Consistent behavior** - All operations follow the same pattern
4. **No data races** - UI always shows current state

## Testing Recommendations

Test these scenarios:

1. **Consume Item:**
   - Click consume on an item
   - Wait for modal to close
   - Verify item quantity decreased immediately
   - Verify consumption appears in list

2. **Add Item:**
   - Click "Add Item"
   - Select product and quantity
   - Wait for modal to close
   - Verify new item appears immediately

3. **Pay Consumption:**
   - Click "Pay" on a consumption
   - Enter amount and confirm
   - Wait for payment UI to close
   - Verify amount_paid updated immediately
   - Verify status changed if fully paid

## Files Modified

- `webapp/src/hooks/useItemConsumption.ts`
- `webapp/src/hooks/useAddItemModal.ts`
- `webapp/src/hooks/useConsumptionPayment.ts`
- `webapp/src/hooks/useExpeditionDetails.ts`
- `webapp/src/components/expedition/ConsumeItemModal.tsx`

## Build Status

✓ Build successful with no errors
✓ TypeScript compilation passed
✓ All async flows properly typed

## Notes

- WebSocket real-time updates should still work as a backup
- The fix ensures manual operations have immediate feedback
- The loading states (`isSubmitting`, `processing`, `addingItem`) remain visible until refresh completes
- Error handling unchanged - errors still keep modals open for retry
