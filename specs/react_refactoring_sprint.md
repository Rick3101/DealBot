# React Refactoring Sprint - SRP Optimization

## Sprint Goal
Improve code quality and maintainability by extracting business logic from presentation components, reducing duplication, and following Single Responsibility Principle (SRP).

**Current Grade:** A- (90%)
**Target Grade:** A+ (95%+)
**Estimated Total Time:** 14-16 hours

---

## Sprint Overview

### Phase 1: High Priority - Business Logic Extraction (8 hours)
Critical issues that affect maintainability and testability

### Phase 2: Medium Priority - Code Duplication Removal (6 hours)
Improve reusability and reduce bundle size

### Phase 3: Low Priority - Performance Optimizations (2 hours)
Minor performance wins and validation improvements

---

## Phase 1: High Priority Issues

### Task 1.1: Extract Payment Logic from ConsumptionsTab ⚠️
**Priority:** HIGH
**Estimated Time:** 3-4 hours
**Difficulty:** Medium
**Files:**
- `webapp/src/hooks/useConsumptionPayment.ts` (NEW)
- `webapp/src/components/expedition/tabs/ConsumptionsTab.tsx` (MODIFY)

**Problem:**
ConsumptionsTab mixes presentation with business logic (payment calculations, API calls, validation).

**Acceptance Criteria:**
- [ ] Create `useConsumptionPayment` hook with:
  - [ ] `calculatePaymentDetails()` - Pure calculation function
  - [ ] `validatePaymentAmount()` - Validation logic
  - [ ] `startPayment()` - Initialize payment flow
  - [ ] `processPayment()` - Handle API call
  - [ ] `cancelPayment()` - Reset state
- [ ] Refactor `ConsumptionsTab` to use the hook
- [ ] Remove all business logic from component (should be <150 lines)
- [ ] Add unit tests for hook
- [ ] Verify payment flow works in UI

**Code Structure:**
```typescript
// useConsumptionPayment.ts exports:
interface UseConsumptionPayment {
  // State
  payingConsumptionId: number | null;
  paymentAmount: string;
  processing: boolean;
  error: string | null;

  // Actions
  startPayment: (consumption: ItemConsumption) => void;
  processPayment: (consumptionId: number, amount: number) => Promise<void>;
  cancelPayment: () => void;
  setPaymentAmount: (amount: string) => void;

  // Utilities
  calculatePaymentDetails: (consumption: ItemConsumption) => PaymentCalculations;
  validatePaymentAmount: (amount: string, maxAmount: number) => boolean;
}
```

**Testing:**
```bash
# Test the hook
npm test -- useConsumptionPayment

# Test the component integration
npm test -- ConsumptionsTab
```

---

### Task 1.2: Simplify Modal Management ⚠️
**Priority:** HIGH
**Estimated Time:** 4-5 hours
**Difficulty:** Medium
**Files:**
- `webapp/src/hooks/useModalState.ts` (NEW)
- `webapp/src/hooks/useAddPirateModal.ts` (NEW)
- `webapp/src/hooks/useConsumeItemModal.ts` (NEW)
- `webapp/src/hooks/useAddItemModal.ts` (NEW)
- `webapp/src/containers/ExpeditionDetailsContainer.tsx` (MODIFY)

**Problem:**
ExpeditionDetailsContainer has duplicated modal state management (3 modals with nearly identical patterns).

**Acceptance Criteria:**
- [ ] Create generic `useModalState<T>` hook with:
  - [ ] `isOpen`, `data`, `openModal()`, `closeModal()`, `updateData()`
  - [ ] Haptic feedback integration
  - [ ] TypeScript generics for type safety
- [ ] Create specialized modal hooks:
  - [ ] `useAddPirateModal` - Handles pirate addition flow
  - [ ] `useConsumeItemModal` - Handles item consumption flow
  - [ ] `useAddItemModal` - Handles item creation flow
- [ ] Refactor `ExpeditionDetailsContainer` to use hooks
- [ ] Reduce container from ~220 lines to ~100 lines
- [ ] Verify all modals work correctly

**Code Structure:**
```typescript
// useModalState.ts
interface ModalState<T> {
  isOpen: boolean;
  data: T | null;
}

// useAddPirateModal.ts
interface AddPirateModal {
  isOpen: boolean;
  selectedName: string;
  availableBuyers: Buyer[];
  open: () => Promise<void>;
  close: () => void;
  handleAdd: () => Promise<void>;
  setSelectedName: (name: string) => void;
}
```

**Testing:**
```bash
# Test generic modal hook
npm test -- useModalState

# Test specialized hooks
npm test -- useAddPirateModal
npm test -- useConsumeItemModal

# Integration test
npm test -- ExpeditionDetailsContainer
```

---

## Phase 2: Medium Priority Issues

### Task 2.1: Extract Data Transformation Logic 📊
**Priority:** MEDIUM
**Estimated Time:** 2 hours
**Difficulty:** Low
**Files:**
- `webapp/src/utils/transforms/itemTransforms.ts` (NEW)
- `webapp/src/components/expedition/tabs/ItemsTab.tsx` (MODIFY)

**Problem:**
Data transformation is done inline in components, mixing presentation with mapping logic.

**Acceptance Criteria:**
- [ ] Create `itemTransforms.ts` utility with:
  - [ ] `transformExpeditionItems()` - Main transformation function
  - [ ] Handles field name variations (consumed/quantity_consumed)
  - [ ] Calculates available quantity
  - [ ] Provides defaults for missing fields
- [ ] Refactor `ItemsTab` to use transformation
- [ ] Add unit tests for transformations
- [ ] Document field mappings

**Code Structure:**
```typescript
// itemTransforms.ts
export interface TransformedItem {
  id: number;
  product_id: number;
  name: string;
  emoji: string;
  quantity: number;
  price: number;
  quality?: QualityGrade;
  consumed: number;
  available: number;
}

export const transformExpeditionItems = (
  items: ExpeditionItem[]
): TransformedItem[] => {
  // Pure transformation logic
};
```

**Testing:**
```bash
npm test -- itemTransforms
```

---

### Task 2.2: Simplify Hook Orchestration 🎯
**Priority:** MEDIUM
**Estimated Time:** 2 hours
**Difficulty:** Medium
**Files:**
- `webapp/src/hooks/useExpeditionOrchestrator.ts` (NEW)
- `webapp/src/hooks/useExpeditions.ts` (MODIFY)

**Problem:**
`useExpeditions` orchestrates 5+ sub-hooks with complex interdependencies.

**Acceptance Criteria:**
- [ ] Create `useExpeditionOrchestrator` hook for state sync
- [ ] Extract CRUD wrapper logic from `useExpeditions`
- [ ] Simplify `useExpeditions` to be more focused
- [ ] Maintain existing API/contract
- [ ] Add integration tests

**Code Structure:**
```typescript
// useExpeditionOrchestrator.ts
export const useExpeditionOrchestrator = (
  expeditions: Expedition[],
  setExpeditions: Dispatcher,
  crudHook: CRUDHook
) => {
  return {
    createExpedition: async (data) => { /* sync logic */ },
    updateExpeditionStatus: async (id, status) => { /* sync logic */ },
    deleteExpedition: async (id) => { /* sync logic */ },
  };
};
```

**Testing:**
```bash
npm test -- useExpeditionOrchestrator
npm test -- useExpeditions
```

---

### Task 2.3: Create Reusable EmptyState Component 🎨
**Priority:** MEDIUM
**Estimated Time:** 2 hours
**Difficulty:** Low
**Files:**
- `webapp/src/components/ui/EmptyState.tsx` (NEW)
- `webapp/src/components/ui/EmptyState.stories.tsx` (NEW)
- `webapp/src/components/expedition/tabs/PiratesTab.tsx` (MODIFY)
- `webapp/src/components/expedition/tabs/ConsumptionsTab.tsx` (MODIFY)
- `webapp/src/components/expedition/ExpeditionDetailsPresenter.tsx` (MODIFY)

**Problem:**
Empty state UI is duplicated across 4+ components with similar structure.

**Acceptance Criteria:**
- [ ] Create `EmptyState` component with:
  - [ ] Props: `icon`, `title`, `description`, `action`
  - [ ] Consistent styling with pirate theme
  - [ ] Responsive design
- [ ] Create Storybook stories
- [ ] Replace all duplicated empty states
- [ ] Verify consistent appearance across app

**Code Structure:**
```typescript
interface EmptyStateProps {
  icon: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}
```

**Testing:**
```bash
# Visual regression
npm run storybook

# Component test
npm test -- EmptyState
```

---

## Phase 3: Low Priority Optimizations

### Task 3.1: Optimize Pirate Data Fetching 🚀
**Priority:** LOW
**Estimated Time:** 1 hour
**Difficulty:** Low
**Files:**
- `webapp/src/hooks/useExpeditionPirates.ts` (MODIFY)

**Problem:**
`loadAvailableBuyers` fetches pirate names redundantly (already loaded by `loadPirateNames`).

**Acceptance Criteria:**
- [ ] Load all buyers once in `useEffect`
- [ ] Compute `availableBuyers` with `useMemo` from existing data
- [ ] Remove `loadAvailableBuyers` method
- [ ] Update callers to use `availableBuyers` directly
- [ ] Verify no regression in functionality

**Code Structure:**
```typescript
// Before: 2 API calls
loadPirateNames() -> API call
loadAvailableBuyers() -> API call + filter

// After: 1 API call + local computation
loadPirateNames() -> API call
availableBuyers = useMemo(() => filter(allBuyers, pirateNames))
```

**Testing:**
```bash
npm test -- useExpeditionPirates
```

---

### Task 3.2: Extract Validation Hooks 📋
**Priority:** LOW
**Estimated Time:** 1 hour
**Difficulty:** Low
**Files:**
- `webapp/src/hooks/useFormValidation.ts` (NEW)
- Multiple components (MODIFY as needed)

**Problem:**
Input validation is scattered across components.

**Acceptance Criteria:**
- [ ] Create `useNumericValidation` hook
- [ ] Create `useStringValidation` hook (if needed)
- [ ] Refactor components to use validation hooks
- [ ] Add validation error messages
- [ ] Add unit tests

**Code Structure:**
```typescript
export const useNumericValidation = (
  value: string | number,
  min?: number,
  max?: number
) => {
  return {
    isValid: boolean;
    value: number;
    errors: string[];
  };
};
```

**Testing:**
```bash
npm test -- useFormValidation
```

---

## Testing Strategy

### Unit Tests
```bash
# Run all tests
npm test

# Run specific hook tests
npm test -- useConsumptionPayment
npm test -- useModalState
npm test -- itemTransforms

# Run with coverage
npm test -- --coverage
```

### Integration Tests
```bash
# Test full flows
npm test -- ExpeditionDetailsContainer
npm test -- ConsumptionsTab
npm test -- PiratesTab
```

### Manual Testing Checklist
- [ ] Payment flow works correctly
- [ ] All modals open/close properly
- [ ] Empty states display consistently
- [ ] Data transforms correctly
- [ ] No console errors
- [ ] Performance is acceptable
- [ ] Mobile responsiveness maintained

---

## Sprint Checkpoints

### Checkpoint 1: After Task 1.1 (Payment Logic)
**Questions to Answer:**
- [ ] Is the hook fully tested?
- [ ] Is the component easier to understand?
- [ ] Does the payment flow work end-to-end?
- [ ] Is error handling proper?

### Checkpoint 2: After Task 1.2 (Modals)
**Questions to Answer:**
- [ ] Are all three modals working?
- [ ] Is the container significantly simpler?
- [ ] Is the modal pattern reusable?
- [ ] Can we easily add new modals?

### Checkpoint 3: After Phase 2
**Questions to Answer:**
- [ ] Have we reduced code duplication?
- [ ] Is transformation logic centralized?
- [ ] Are components more focused?
- [ ] Is the codebase easier to navigate?

### Checkpoint 4: Sprint Completion
**Questions to Answer:**
- [ ] Have we achieved all acceptance criteria?
- [ ] Are all tests passing?
- [ ] Is documentation updated?
- [ ] Have we improved the grade from A- to A+?

---

## Success Metrics

### Code Quality Metrics
- **Before:**
  - ConsumptionsTab: ~300 lines
  - ExpeditionDetailsContainer: ~220 lines
  - Duplicated empty state code: ~80 lines × 4 = 320 lines
  - Test coverage: Unknown

- **After (Target):**
  - ConsumptionsTab: <150 lines
  - ExpeditionDetailsContainer: ~100 lines
  - EmptyState component: ~80 lines total (reused)
  - Test coverage: >80%

### Maintainability Metrics
- [ ] Reduced cyclomatic complexity
- [ ] Fewer responsibilities per component
- [ ] More reusable hooks
- [ ] Better test coverage
- [ ] Clearer code organization

---

## Dependencies & Prerequisites

### Before Starting
- [ ] Node.js and npm installed
- [ ] All current tests passing
- [ ] No pending PRs that might conflict
- [ ] Development environment working

### Tools Needed
- VSCode (or preferred IDE)
- TypeScript
- Jest
- React Testing Library
- Storybook (for EmptyState stories)

---

## Risk Mitigation

### Risks
1. **Breaking existing functionality** - High impact, medium probability
2. **Merge conflicts** - Medium impact, low probability
3. **Performance regression** - Low impact, low probability

### Mitigation Strategies
1. **Comprehensive testing at each step**
2. **Work in feature branches**
3. **Regular manual testing**
4. **Code review before merging**
5. **Performance profiling after major changes**

---

## Rollback Plan

If issues arise:
1. **Each task is in its own commit** - Easy to revert
2. **Feature branches** - Can abandon without affecting main
3. **Existing code still works** - Only additions, minimal modifications

---

## Documentation Updates

### Files to Update After Sprint
- [ ] `README.md` - Add new hooks documentation
- [ ] `ARCHITECTURE.md` - Update component patterns
- [ ] `CONTRIBUTING.md` - Add SRP guidelines
- [ ] Storybook - Add new component stories

---

## Next Steps After Sprint

### Future Refactoring Opportunities
1. Extract more specialized hooks from containers
2. Create form builder utilities
3. Implement centralized error boundary
4. Add performance monitoring hooks
5. Create animation utilities

### Code Quality Goals
- [ ] Maintain A+ grade
- [ ] Add ESLint rules for SRP violations
- [ ] Set up automated complexity checks
- [ ] Implement pre-commit hooks for tests

---

## Sprint Tracking

### Progress Dashboard
```
Phase 1: [░░░░░░░░░░] 0/2 tasks
Phase 2: [░░░░░░░░░░] 0/3 tasks
Phase 3: [░░░░░░░░░░] 0/2 tasks

Overall: [░░░░░░░░░░] 0% complete
Estimated time remaining: 14-16 hours
```

### Task Status Legend
- 🔴 Not started
- 🟡 In progress
- 🟢 Complete
- ⚠️ Blocked/Issues

---

## Team Communication

### Daily Standup Questions
1. What refactoring did I complete yesterday?
2. What refactoring will I work on today?
3. Are there any blockers?
4. Do I need code review?

### Code Review Checklist
- [ ] Does the code follow SRP?
- [ ] Are there sufficient tests?
- [ ] Is the API backward compatible?
- [ ] Is documentation updated?
- [ ] Does it pass linting?
- [ ] No console warnings/errors?

---

## Completion Criteria

### Sprint is Complete When:
- [ ] All 7 tasks completed
- [ ] All tests passing (>80% coverage)
- [ ] No TypeScript errors
- [ ] No ESLint warnings
- [ ] Manual testing complete
- [ ] Documentation updated
- [ ] Code reviewed and approved
- [ ] Deployed to staging
- [ ] QA sign-off

---

## Notes & Learnings

### Key Takeaways
_Add notes as you progress through the sprint_

### Challenges Encountered
_Document any unexpected issues_

### Best Practices Discovered
_Share learnings with the team_

### Time Estimates Accuracy
_Track actual vs estimated time for future planning_

---

**Sprint Start Date:** _____________
**Expected Completion:** _____________
**Actual Completion:** _____________

**Sprint Lead:** _____________
**Code Reviewer:** _____________
