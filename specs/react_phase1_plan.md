# React Phase 1: Dashboard Refactoring - Detailed Implementation Plan

**Project**: Pirates Expedition Mini App
**Phase**: 1.1 - Dashboard Refactoring
**Status**: Planning Complete - Ready for Implementation
**Created**: 2025-10-05
**Estimated Duration**: 15 hours (~2-3 days)
**Priority**: HIGH - Pattern Validation Phase

---

## Executive Summary

This document provides a detailed, step-by-step implementation plan for refactoring the Dashboard component from a 359-line monolithic component into 7 focused files following the Container/Presenter pattern with custom hooks.

**Goal**: Validate the container/presenter pattern on the simplest critical component before applying it to CreateExpedition and ExpeditionDetails.

**Impact**:
- Dashboard.tsx: 359 lines → 3 lines (99% reduction)
- 7 new focused files (~70 lines average each)
- Reusable hooks and components
- Pattern proven for Phase 1.2 and 1.3

---

## Current State Analysis

**File**: [Dashboard.tsx](../webapp/src/pages/Dashboard.tsx) (359 lines)

### Identified Responsibilities (7 concerns):

| Concern | Lines | Description |
|---------|-------|-------------|
| 1. State Management | 168-180, 188 | Hook composition, manual refresh state |
| 2. Navigation Logic | 197-210 | Three navigation handlers |
| 3. Statistics Calculation | 243-248 | Fallback stats computation |
| 4. Timeline Transformation | 250-262 | Complex data transformation with defaults |
| 5. Loading/Error Rendering | 212-241 | State-based UI rendering |
| 6. Stats Card Rendering | 268-300 | Statistics presentation |
| 7. Timeline Rendering | 302-355 | Expedition list presentation |

### Key Code Sections:

**State Management**:
```typescript
// Lines 168-180: Hook composition
const {
  expeditions,
  timelineData,
  loading,
  error,
  refreshing,
  refreshExpeditions,
} = useExpeditions({
  autoRefresh: true,
  refreshInterval: 30000,
  realTimeUpdates: true,
});

// Line 188: Manual refresh state
const [refreshing手动, setRefreshing手动] = useState(false);
```

**Navigation Handlers** (Lines 190-210):
```typescript
const handleRefresh = async () => { /* ... */ };
const handleCreateExpedition = () => { /* ... */ };
const handleViewExpedition = (expedition) => { /* ... */ };
const handleManageExpedition = (expedition) => { /* ... */ };
```

**Statistics Calculation** (Lines 243-248):
```typescript
const stats = timelineData?.stats || {
  total_expeditions: expeditions.length,
  active_expeditions: expeditions.filter(e => e.status === 'active').length,
  completed_expeditions: expeditions.filter(e => e.status === 'completed').length,
  overdue_expeditions: 0,
};
```

**Timeline Transformation** (Lines 250-262):
```typescript
const timelineExpeditions = timelineData?.timeline || expeditions.map(exp => ({
  ...exp,
  is_overdue: exp.deadline ? new Date(exp.deadline) < new Date() && exp.status === 'active' : false,
  progress: {
    completion_percentage: 0,
    total_items: 0,
    consumed_items: 0,
    remaining_items: 0,
    total_value: 0,
    consumed_value: 0,
    remaining_value: 0,
  },
})) as ExpeditionTimelineEntry[];
```

---

## Target Architecture

### File Structure (7 new files):

```
webapp/src/
├── hooks/
│   ├── useDashboardStats.ts          (~60 lines)
│   ├── useTimelineExpeditions.ts     (~70 lines)
│   └── useDashboardActions.ts        (~80 lines)
├── components/
│   └── dashboard/
│       ├── DashboardStats.tsx        (~120 lines - includes styled components)
│       └── ExpeditionTimeline.tsx    (~140 lines - includes styled components)
├── containers/
│   └── DashboardContainer.tsx        (~80 lines)
└── components/
    └── dashboard/
        └── DashboardPresenter.tsx    (~100 lines)
```

**Modified File**:
- `webapp/src/pages/Dashboard.tsx` (~3 lines - thin wrapper)

---

## Phase 1: Custom Hooks (6 hours)

### Hook 1: `useDashboardStats.ts` (2 hours)

**Purpose**: Calculate statistics with fallbacks

**Location**: `webapp/src/hooks/useDashboardStats.ts`

**Responsibility**: Statistics calculation only (Single Responsibility Principle)

**Interface**:
```typescript
import { Expedition } from '@/types/expedition';

interface DashboardStats {
  total_expeditions: number;
  active_expeditions: number;
  completed_expeditions: number;
  overdue_expeditions: number;
}

interface TimelineData {
  stats?: DashboardStats;
  timeline?: ExpeditionTimelineEntry[];
}

export function useDashboardStats(
  expeditions: Expedition[],
  timelineData: TimelineData | null
): DashboardStats;
```

**Implementation Plan**:
1. Extract calculation logic from Dashboard.tsx lines 243-248
2. Add memoization with `useMemo` to prevent recalculation on every render
3. Handle edge cases (empty arrays, null values)
4. Return stats object

**Extracted Code**:
```typescript
// Current location: Dashboard.tsx lines 243-248
const stats = timelineData?.stats || {
  total_expeditions: expeditions.length,
  active_expeditions: expeditions.filter(e => e.status === 'active').length,
  completed_expeditions: expeditions.filter(e => e.status === 'completed').length,
  overdue_expeditions: 0,
};
```

**Dependencies**:
- `react` (useMemo)
- `@/types/expedition` (types)

**Testing Strategy**:
- Test with timeline data present
- Test fallback calculation
- Test empty expeditions array
- Test status filtering logic

---

### Hook 2: `useTimelineExpeditions.ts` (2 hours)

**Purpose**: Transform expedition data for timeline display

**Location**: `webapp/src/hooks/useTimelineExpeditions.ts`

**Responsibility**: Data transformation only

**Interface**:
```typescript
import { Expedition, ExpeditionTimelineEntry } from '@/types/expedition';

interface TimelineData {
  stats?: DashboardStats;
  timeline?: ExpeditionTimelineEntry[];
}

export function useTimelineExpeditions(
  expeditions: Expedition[],
  timelineData: TimelineData | null
): ExpeditionTimelineEntry[];
```

**Implementation Plan**:
1. Extract transformation logic from Dashboard.tsx lines 250-262
2. Add memoization to prevent unnecessary transformations
3. Implement overdue detection logic
4. Add default progress object
5. Use Phase 0 utilities if needed (formatters, transforms)

**Extracted Code**:
```typescript
// Current location: Dashboard.tsx lines 250-262
const timelineExpeditions = timelineData?.timeline || expeditions.map(exp => ({
  ...exp,
  is_overdue: exp.deadline ? new Date(exp.deadline) < new Date() && exp.status === 'active' : false,
  progress: {
    completion_percentage: 0,
    total_items: 0,
    consumed_items: 0,
    remaining_items: 0,
    total_value: 0,
    consumed_value: 0,
    remaining_value: 0,
  },
})) as ExpeditionTimelineEntry[];
```

**Dependencies**:
- `react` (useMemo)
- `@/types/expedition` (types)
- Optional: `@/utils/transforms/expeditionTransforms` (Phase 0)

**Testing Strategy**:
- Test with timeline data present
- Test transformation with expeditions array
- Test overdue detection (past deadline + active status)
- Test non-overdue cases (future deadline, no deadline, completed status)
- Test progress object defaults

---

### Hook 3: `useDashboardActions.ts` (2 hours)

**Purpose**: Centralize all action handlers and navigation logic

**Location**: `webapp/src/hooks/useDashboardActions.ts`

**Responsibility**: User interaction handlers only

**Interface**:
```typescript
import { ExpeditionTimelineEntry } from '@/types/expedition';

interface DashboardActions {
  handleRefresh: () => Promise<void>;
  handleCreateExpedition: () => void;
  handleViewExpedition: (expedition: ExpeditionTimelineEntry) => void;
  handleManageExpedition: (expedition: ExpeditionTimelineEntry) => void;
  refreshing: boolean;
}

export function useDashboardActions(
  navigate: NavigateFunction,
  refreshExpeditions: () => Promise<void>
): DashboardActions;
```

**Implementation Plan**:
1. Extract handler functions from Dashboard.tsx lines 190-210
2. Add internal state for manual refresh (`useState`)
3. Add haptic feedback to all actions
4. Memoize callbacks with `useCallback`
5. Return action object

**Extracted Code**:
```typescript
// Current location: Dashboard.tsx lines 188-210
const [refreshing手动, setRefreshing手动] = useState(false);

const handleRefresh = async () => {
  setRefreshing手动(true);
  hapticFeedback('light');
  await refreshExpeditions();
  setRefreshing手动(false);
};

const handleCreateExpedition = () => {
  hapticFeedback('medium');
  navigate('/expedition/create');
};

const handleViewExpedition = (expedition: ExpeditionTimelineEntry) => {
  hapticFeedback('light');
  navigate(`/expedition/${expedition.id}`);
};

const handleManageExpedition = (expedition: ExpeditionTimelineEntry) => {
  hapticFeedback('medium');
  navigate(`/expedition/${expedition.id}`);
};
```

**Dependencies**:
- `react` (useState, useCallback)
- `react-router-dom` (NavigateFunction type)
- `@/utils/telegram` (hapticFeedback)
- `@/types/expedition` (ExpeditionTimelineEntry)

**Testing Strategy**:
- Test navigation to create page
- Test navigation to expedition details
- Test refresh loading state management
- Test haptic feedback calls
- Test async refresh completion

---

## Phase 2: Presentation Components (4 hours)

### Component 1: `DashboardStats.tsx` (2 hours)

**Purpose**: Pure statistics card presentation

**Location**: `webapp/src/components/dashboard/DashboardStats.tsx`

**Responsibility**: Render statistics cards only

**Props Interface**:
```typescript
interface DashboardStatsProps {
  stats: {
    total_expeditions: number;
    active_expeditions: number;
    completed_expeditions: number;
    overdue_expeditions: number;
  };
}
```

**Implementation Plan**:
1. Extract stat cards from Dashboard.tsx lines 268-300
2. Move styled components: `StatsGrid`, `StatCard`, `StatIcon`, `StatValue`, `StatLabel`
3. Keep motion animations from framer-motion
4. Make component pure (no hooks except potentially useMemo)
5. Export both component and styled components for reusability

**Extracted Code**:
```typescript
// Current location: Dashboard.tsx lines 268-300
<StatsGrid>
  <StatCard $color={pirateColors.secondary}>
    <StatIcon $color={pirateColors.secondary}>
      <Package />
    </StatIcon>
    <StatValue>{stats.total_expeditions}</StatValue>
    <StatLabel>Total Expeditions</StatLabel>
  </StatCard>

  <StatCard $color={pirateColors.success}>
    <StatIcon $color={pirateColors.success}>
      <TrendingUp />
    </StatIcon>
    <StatValue>{stats.active_expeditions}</StatValue>
    <StatLabel>Active Expeditions</StatLabel>
  </StatCard>

  <StatCard $color={pirateColors.info}>
    <StatIcon $color={pirateColors.info}>
      <Users />
    </StatIcon>
    <StatValue>{stats.completed_expeditions}</StatValue>
    <StatLabel>Completed</StatLabel>
  </StatCard>

  <StatCard $color={pirateColors.danger}>
    <StatIcon $color={pirateColors.danger}>
      <Calendar />
    </StatIcon>
    <StatValue>{stats.overdue_expeditions}</StatValue>
    <StatLabel>Overdue</StatLabel>
  </StatCard>
</StatsGrid>
```

**Styled Components to Move**:
```typescript
// Lines 22-80
StatsGrid
StatCard
StatIcon
StatValue
StatLabel
```

**Dependencies**:
- `react`
- `styled-components`
- `framer-motion`
- `lucide-react` (icons)
- `@/utils/pirateTheme`

**Testing Strategy**:
- Render with various stat values
- Verify all 4 cards display
- Check correct colors applied
- Test motion animations
- Snapshot testing for UI consistency

---

### Component 2: `ExpeditionTimeline.tsx` (2 hours)

**Purpose**: Pure timeline list presentation

**Location**: `webapp/src/components/dashboard/ExpeditionTimeline.tsx`

**Responsibility**: Render expedition timeline section only

**Props Interface**:
```typescript
import { ExpeditionTimelineEntry } from '@/types/expedition';

interface ExpeditionTimelineProps {
  expeditions: ExpeditionTimelineEntry[];
  onViewExpedition: (expedition: ExpeditionTimelineEntry) => void;
  onManageExpedition: (expedition: ExpeditionTimelineEntry) => void;
  onRefresh: () => void;
  onCreate: () => void;
  refreshing: boolean;
}
```

**Implementation Plan**:
1. Extract timeline section from Dashboard.tsx lines 302-355
2. Move styled components: `SectionHeader`, `SectionTitle`, `ActionButtons`, `ExpeditionsGrid`, `EmptyState`, etc.
3. Handle empty state rendering
4. Use existing `ExpeditionCard` component
5. Keep AnimatePresence animations
6. Make component pure (props only, no state)

**Extracted Code**:
```typescript
// Current location: Dashboard.tsx lines 302-355
<div>
  <SectionHeader>
    <SectionTitle>
      ⛵ Expedition Timeline
    </SectionTitle>
    <ActionButtons>
      <PirateButton
        variant="outline"
        size="sm"
        onClick={handleRefresh}
        disabled={refreshing || refreshing手动}
        loading={refreshing || refreshing手动}
      >
        🔄 Refresh
      </PirateButton>
      <PirateButton
        variant="primary"
        size="sm"
        onClick={handleCreateExpedition}
        icon="+"
      >
        New Expedition
      </PirateButton>
    </ActionButtons>
  </SectionHeader>

  {timelineExpeditions.length === 0 ? (
    <EmptyState>
      <EmptyIcon>⛵</EmptyIcon>
      <EmptyTitle>No expeditions yet, Captain!</EmptyTitle>
      <EmptyDescription>
        Start your first pirate expedition to begin tracking your adventures.
      </EmptyDescription>
      <PirateButton onClick={handleCreateExpedition} variant="primary" icon="+">
        Create First Expedition
      </PirateButton>
    </EmptyState>
  ) : (
    <ExpeditionsGrid>
      <AnimatePresence>
        {timelineExpeditions.map((expedition) => (
          <ExpeditionCard
            key={expedition.id}
            expedition={expedition}
            onViewDetails={handleViewExpedition}
            onManage={handleManageExpedition}
            compact={false}
          />
        ))}
      </AnimatePresence>
    </ExpeditionsGrid>
  )}
</div>
```

**Styled Components to Move**:
```typescript
// Lines 82-165
SectionHeader
SectionTitle
ActionButtons
ExpeditionsGrid
EmptyState
EmptyIcon
EmptyTitle
EmptyDescription
```

**Dependencies**:
- `react`
- `styled-components`
- `framer-motion` (AnimatePresence)
- `@/components/ui/PirateButton`
- `@/components/expedition/ExpeditionCard`
- `@/utils/pirateTheme`
- `@/types/expedition`

**Testing Strategy**:
- Render with expeditions list
- Render empty state
- Test button callbacks
- Test refresh disabled state
- Verify expedition cards render

---

## Phase 3: Container Component (3 hours)

### Component: `DashboardContainer.tsx`

**Purpose**: Orchestrate hooks, manage state, delegate to presenter

**Location**: `webapp/src/containers/DashboardContainer.tsx`

**Responsibility**: Hook composition and data orchestration ONLY (no UI rendering)

**Structure**:
```typescript
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useExpeditions } from '@/hooks/useExpeditions';
import { useDashboardStats } from '@/hooks/useDashboardStats';
import { useTimelineExpeditions } from '@/hooks/useTimelineExpeditions';
import { useDashboardActions } from '@/hooks/useDashboardActions';
import { DashboardPresenter } from '@/components/dashboard/DashboardPresenter';

export const DashboardContainer: React.FC = () => {
  const navigate = useNavigate();

  // Data fetching
  const {
    expeditions,
    timelineData,
    loading,
    error,
    refreshing,
    refreshExpeditions,
  } = useExpeditions({
    autoRefresh: true,
    refreshInterval: 30000,
    realTimeUpdates: true,
  });

  // Calculation hooks
  const stats = useDashboardStats(expeditions, timelineData);
  const timelineExpeditions = useTimelineExpeditions(expeditions, timelineData);

  // Action hooks
  const actions = useDashboardActions(navigate, refreshExpeditions);

  // Delegate to presenter
  return (
    <DashboardPresenter
      loading={loading}
      error={error}
      stats={stats}
      expeditions={timelineExpeditions}
      actions={actions}
      refreshing={refreshing}
    />
  );
};
```

**Implementation Plan**:
1. Create container component
2. Import all custom hooks
3. Compose hooks (data fetching → calculations → actions)
4. Pass all data to presenter via props
5. No UI logic, no conditional rendering
6. Keep component thin (~80 lines including imports)

**Dependencies**:
- `react`
- `react-router-dom` (useNavigate)
- `@/hooks/useExpeditions`
- `@/hooks/useDashboardStats`
- `@/hooks/useTimelineExpeditions`
- `@/hooks/useDashboardActions`
- `@/components/dashboard/DashboardPresenter`

**Testing Strategy**:
- Test hook composition
- Mock all hooks
- Verify props passed to presenter
- Test that container has no rendering logic

---

## Phase 4: Presenter Component (2 hours)

### Component: `DashboardPresenter.tsx`

**Purpose**: Pure UI rendering based on props

**Location**: `webapp/src/components/dashboard/DashboardPresenter.tsx`

**Responsibility**: Conditional rendering and layout ONLY (no business logic)

**Props Interface**:
```typescript
import { ExpeditionTimelineEntry } from '@/types/expedition';

interface DashboardStats {
  total_expeditions: number;
  active_expeditions: number;
  completed_expeditions: number;
  overdue_expeditions: number;
}

interface DashboardActions {
  handleRefresh: () => Promise<void>;
  handleCreateExpedition: () => void;
  handleViewExpedition: (expedition: ExpeditionTimelineEntry) => void;
  handleManageExpedition: (expedition: ExpeditionTimelineEntry) => void;
  refreshing: boolean;
}

interface DashboardPresenterProps {
  loading: boolean;
  error: string | null;
  stats: DashboardStats;
  expeditions: ExpeditionTimelineEntry[];
  actions: DashboardActions;
  refreshing: boolean;
}
```

**Structure**:
```typescript
import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { CaptainLayout } from '@/layouts/CaptainLayout';
import { PirateButton } from '@/components/ui/PirateButton';
import { DashboardStats } from '@/components/dashboard/DashboardStats';
import { ExpeditionTimeline } from '@/components/dashboard/ExpeditionTimeline';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { Loader2 } from 'lucide-react';

// Styled components (from Dashboard.tsx)
const DashboardContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing.xl};
`;

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: ${spacing['3xl']};
  flex-direction: column;
  gap: ${spacing.lg};
`;

const LoadingText = styled.div`
  font-family: ${pirateTypography.headings};
  font-size: 1.25rem;
  color: ${pirateColors.primary};
`;

const EmptyState = styled.div`
  text-align: center;
  padding: ${spacing['3xl']};
  color: ${pirateColors.muted};
`;

const EmptyIcon = styled.div`
  font-size: 4rem;
  margin-bottom: ${spacing.lg};
  opacity: 0.5;
`;

const EmptyTitle = styled.h3`
  font-family: ${pirateTypography.headings};
  font-size: 1.5rem;
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.md};
`;

const EmptyDescription = styled.p`
  font-size: ${pirateTypography.sizes.base};
  margin-bottom: ${spacing.xl};
`;

export const DashboardPresenter: React.FC<DashboardPresenterProps> = ({
  loading,
  error,
  stats,
  expeditions,
  actions,
  refreshing,
}) => {
  // Loading state
  if (loading) {
    return (
      <CaptainLayout>
        <LoadingContainer>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            <Loader2 size={48} color={pirateColors.secondary} />
          </motion.div>
          <LoadingText>Loading your expeditions...</LoadingText>
        </LoadingContainer>
      </CaptainLayout>
    );
  }

  // Error state
  if (error) {
    return (
      <CaptainLayout>
        <EmptyState>
          <EmptyIcon>💀</EmptyIcon>
          <EmptyTitle>Arrr! Something went wrong</EmptyTitle>
          <EmptyDescription>{error}</EmptyDescription>
          <PirateButton onClick={actions.handleRefresh} variant="primary">
            ⚓ Try Again
          </PirateButton>
        </EmptyState>
      </CaptainLayout>
    );
  }

  // Success state
  return (
    <CaptainLayout>
      <DashboardContainer>
        <DashboardStats stats={stats} />
        <ExpeditionTimeline
          expeditions={expeditions}
          onViewExpedition={actions.handleViewExpedition}
          onManageExpedition={actions.handleManageExpedition}
          onRefresh={actions.handleRefresh}
          onCreate={actions.handleCreateExpedition}
          refreshing={actions.refreshing || refreshing}
        />
      </DashboardContainer>
    </CaptainLayout>
  );
};
```

**Implementation Plan**:
1. Extract conditional rendering logic from Dashboard.tsx lines 212-241, 264-358
2. Move remaining styled components (`DashboardContainer`, loading/error states)
3. Create three render paths: loading, error, success
4. Use composition (DashboardStats + ExpeditionTimeline)
5. Keep component pure (no state, only props)

**Styled Components to Move**:
```typescript
// Lines 15-19, 128-165
DashboardContainer
LoadingContainer
LoadingText
EmptyState
EmptyIcon
EmptyTitle
EmptyDescription
```

**Dependencies**:
- `react`
- `styled-components`
- `framer-motion`
- `lucide-react` (Loader2)
- `@/layouts/CaptainLayout`
- `@/components/ui/PirateButton`
- `@/components/dashboard/DashboardStats`
- `@/components/dashboard/ExpeditionTimeline`
- `@/utils/pirateTheme`
- `@/types/expedition`

**Testing Strategy**:
- Render loading state
- Render error state
- Render success state with expeditions
- Test prop delegation to child components
- Snapshot testing for all states

---

## Phase 5: Page Wrapper Update (1 hour)

### Update: `Dashboard.tsx`

**Purpose**: Thin wrapper that exports container

**Location**: `webapp/src/pages/Dashboard.tsx`

**Final Code**:
```typescript
/**
 * Dashboard Page
 *
 * Main dashboard view showing expedition statistics and timeline.
 * Refactored to container/presenter pattern for better testability and maintainability.
 *
 * Architecture:
 * - DashboardContainer: Hook composition and state management
 * - DashboardPresenter: Pure UI rendering
 * - Custom hooks: useDashboardStats, useTimelineExpeditions, useDashboardActions
 * - Presentation components: DashboardStats, ExpeditionTimeline
 */

export { DashboardContainer as Dashboard } from '@/containers/DashboardContainer';
```

**Size**: ~14 lines with comments, ~1 line without

**Implementation Plan**:
1. Delete existing Dashboard.tsx content
2. Add documentation comment
3. Re-export DashboardContainer as Dashboard
4. Maintain backward compatibility (routes still work)

**Testing Strategy**:
- Verify route still works
- Test that component renders correctly
- Check no regressions in behavior

---

## Implementation Timeline

### Day 1: Hooks (6 hours)

**Morning (3 hours)**:
1. Create `useDashboardStats.ts` (2h)
   - Extract calculation logic
   - Add memoization
   - Write unit tests
2. Start `useTimelineExpeditions.ts` (1h)
   - Extract transformation logic
   - Add memoization

**Afternoon (3 hours)**:
3. Complete `useTimelineExpeditions.ts` (1h)
   - Write unit tests
4. Create `useDashboardActions.ts` (2h)
   - Extract all handlers
   - Add haptic feedback
   - Write unit tests

**Deliverables**: 3 hooks with tests

---

### Day 2: Components (6 hours)

**Morning (3 hours)**:
1. Create `DashboardStats.tsx` (2h)
   - Extract stat cards
   - Move styled components
   - Write component tests
2. Start `ExpeditionTimeline.tsx` (1h)
   - Extract timeline section
   - Move styled components

**Afternoon (3 hours)**:
3. Complete `ExpeditionTimeline.tsx` (1h)
   - Handle empty state
   - Write component tests
4. Create `DashboardContainer.tsx` (2h)
   - Hook composition
   - Write integration tests

**Deliverables**: 3 components with tests

---

### Day 3: Integration (3 hours)

**Morning (3 hours)**:
1. Create `DashboardPresenter.tsx` (2h)
   - Conditional rendering
   - Layout composition
   - Write component tests
2. Update `Dashboard.tsx` wrapper (0.5h)
   - Re-export container
   - Add documentation
3. Integration testing (0.5h)
   - Test complete flow
   - Verify no regressions
   - Test all interactions

**Deliverables**: Complete refactored Dashboard

---

**Total Time**: 15 hours (matches Phase 1.1 estimate)

---

## Testing Strategy

### Unit Tests (2.5 hours)

#### Hook Tests (1.5 hours)

**Test: `useDashboardStats.test.ts`** (30 min)
```typescript
import { renderHook } from '@testing-library/react';
import { useDashboardStats } from '@/hooks/useDashboardStats';

describe('useDashboardStats', () => {
  it('should use stats from timeline data when available', () => {
    const expeditions = [];
    const timelineData = {
      stats: {
        total_expeditions: 10,
        active_expeditions: 5,
        completed_expeditions: 3,
        overdue_expeditions: 2,
      },
    };

    const { result } = renderHook(() => useDashboardStats(expeditions, timelineData));

    expect(result.current).toEqual(timelineData.stats);
  });

  it('should calculate stats from expeditions when timeline data missing', () => {
    const expeditions = [
      { id: 1, status: 'active', deadline: null },
      { id: 2, status: 'active', deadline: null },
      { id: 3, status: 'completed', deadline: null },
    ];
    const timelineData = null;

    const { result } = renderHook(() => useDashboardStats(expeditions, timelineData));

    expect(result.current).toEqual({
      total_expeditions: 3,
      active_expeditions: 2,
      completed_expeditions: 1,
      overdue_expeditions: 0,
    });
  });

  it('should handle empty expeditions array', () => {
    const expeditions = [];
    const timelineData = null;

    const { result } = renderHook(() => useDashboardStats(expeditions, timelineData));

    expect(result.current.total_expeditions).toBe(0);
  });

  it('should memoize result to prevent recalculation', () => {
    const expeditions = [{ id: 1, status: 'active', deadline: null }];
    const timelineData = null;

    const { result, rerender } = renderHook(() => useDashboardStats(expeditions, timelineData));
    const firstResult = result.current;

    rerender();

    expect(result.current).toBe(firstResult); // Same reference
  });
});
```

**Test: `useTimelineExpeditions.test.ts`** (30 min)
```typescript
import { renderHook } from '@testing-library/react';
import { useTimelineExpeditions } from '@/hooks/useTimelineExpeditions';

describe('useTimelineExpeditions', () => {
  it('should use timeline data when available', () => {
    const expeditions = [];
    const timelineData = {
      timeline: [
        { id: 1, name: 'Test', is_overdue: false, progress: { /* ... */ } },
      ],
    };

    const { result } = renderHook(() => useTimelineExpeditions(expeditions, timelineData));

    expect(result.current).toEqual(timelineData.timeline);
  });

  it('should transform expeditions with overdue flag', () => {
    const pastDate = new Date(Date.now() - 86400000).toISOString(); // Yesterday
    const expeditions = [
      { id: 1, status: 'active', deadline: pastDate },
    ];
    const timelineData = null;

    const { result } = renderHook(() => useTimelineExpeditions(expeditions, timelineData));

    expect(result.current[0].is_overdue).toBe(true);
  });

  it('should not mark completed expeditions as overdue', () => {
    const pastDate = new Date(Date.now() - 86400000).toISOString();
    const expeditions = [
      { id: 1, status: 'completed', deadline: pastDate },
    ];
    const timelineData = null;

    const { result } = renderHook(() => useTimelineExpeditions(expeditions, timelineData));

    expect(result.current[0].is_overdue).toBe(false);
  });

  it('should add default progress object', () => {
    const expeditions = [
      { id: 1, status: 'active', deadline: null },
    ];
    const timelineData = null;

    const { result } = renderHook(() => useTimelineExpeditions(expeditions, timelineData));

    expect(result.current[0].progress).toEqual({
      completion_percentage: 0,
      total_items: 0,
      consumed_items: 0,
      remaining_items: 0,
      total_value: 0,
      consumed_value: 0,
      remaining_value: 0,
    });
  });

  it('should handle expeditions without deadlines', () => {
    const expeditions = [
      { id: 1, status: 'active', deadline: null },
    ];
    const timelineData = null;

    const { result } = renderHook(() => useTimelineExpeditions(expeditions, timelineData));

    expect(result.current[0].is_overdue).toBe(false);
  });
});
```

**Test: `useDashboardActions.test.ts`** (30 min)
```typescript
import { renderHook, act } from '@testing-library/react';
import { useDashboardActions } from '@/hooks/useDashboardActions';
import { hapticFeedback } from '@/utils/telegram';

jest.mock('@/utils/telegram', () => ({
  hapticFeedback: jest.fn(),
}));

describe('useDashboardActions', () => {
  const mockNavigate = jest.fn();
  const mockRefreshExpeditions = jest.fn().mockResolvedValue(undefined);

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should navigate to create expedition on handleCreateExpedition', () => {
    const { result } = renderHook(() =>
      useDashboardActions(mockNavigate, mockRefreshExpeditions)
    );

    act(() => {
      result.current.handleCreateExpedition();
    });

    expect(mockNavigate).toHaveBeenCalledWith('/expedition/create');
    expect(hapticFeedback).toHaveBeenCalledWith('medium');
  });

  it('should navigate to expedition details on handleViewExpedition', () => {
    const { result } = renderHook(() =>
      useDashboardActions(mockNavigate, mockRefreshExpeditions)
    );

    const expedition = { id: 123 };

    act(() => {
      result.current.handleViewExpedition(expedition);
    });

    expect(mockNavigate).toHaveBeenCalledWith('/expedition/123');
    expect(hapticFeedback).toHaveBeenCalledWith('light');
  });

  it('should manage refresh loading state', async () => {
    const { result } = renderHook(() =>
      useDashboardActions(mockNavigate, mockRefreshExpeditions)
    );

    expect(result.current.refreshing).toBe(false);

    const refreshPromise = act(async () => {
      await result.current.handleRefresh();
    });

    await refreshPromise;

    expect(mockRefreshExpeditions).toHaveBeenCalled();
    expect(result.current.refreshing).toBe(false);
  });

  it('should trigger haptic feedback on all actions', () => {
    const { result } = renderHook(() =>
      useDashboardActions(mockNavigate, mockRefreshExpeditions)
    );

    act(() => {
      result.current.handleCreateExpedition();
      result.current.handleViewExpedition({ id: 1 });
      result.current.handleManageExpedition({ id: 2 });
    });

    expect(hapticFeedback).toHaveBeenCalledTimes(3);
  });
});
```

#### Component Tests (1 hour)

**Test: `DashboardStats.test.tsx`** (30 min)
```typescript
import { render, screen } from '@testing-library/react';
import { DashboardStats } from '@/components/dashboard/DashboardStats';

describe('DashboardStats', () => {
  const mockStats = {
    total_expeditions: 10,
    active_expeditions: 5,
    completed_expeditions: 3,
    overdue_expeditions: 2,
  };

  it('should render all stat cards', () => {
    render(<DashboardStats stats={mockStats} />);

    expect(screen.getByText('Total Expeditions')).toBeInTheDocument();
    expect(screen.getByText('Active Expeditions')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Overdue')).toBeInTheDocument();
  });

  it('should display correct values', () => {
    render(<DashboardStats stats={mockStats} />);

    expect(screen.getByText('10')).toBeInTheDocument(); // Total
    expect(screen.getByText('5')).toBeInTheDocument();  // Active
    expect(screen.getByText('3')).toBeInTheDocument();  // Completed
    expect(screen.getByText('2')).toBeInTheDocument();  // Overdue
  });

  it('should handle zero values', () => {
    const emptyStats = {
      total_expeditions: 0,
      active_expeditions: 0,
      completed_expeditions: 0,
      overdue_expeditions: 0,
    };

    render(<DashboardStats stats={emptyStats} />);

    const zeros = screen.getAllByText('0');
    expect(zeros).toHaveLength(4);
  });

  it('should match snapshot', () => {
    const { container } = render(<DashboardStats stats={mockStats} />);

    expect(container).toMatchSnapshot();
  });
});
```

**Test: `ExpeditionTimeline.test.tsx`** (30 min)
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ExpeditionTimeline } from '@/components/dashboard/ExpeditionTimeline';

describe('ExpeditionTimeline', () => {
  const mockExpeditions = [
    { id: 1, name: 'Test Expedition 1', status: 'active' },
    { id: 2, name: 'Test Expedition 2', status: 'completed' },
  ];

  const mockActions = {
    onViewExpedition: jest.fn(),
    onManageExpedition: jest.fn(),
    onRefresh: jest.fn(),
    onCreate: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render expedition cards', () => {
    render(
      <ExpeditionTimeline
        expeditions={mockExpeditions}
        {...mockActions}
        refreshing={false}
      />
    );

    expect(screen.getByText('Test Expedition 1')).toBeInTheDocument();
    expect(screen.getByText('Test Expedition 2')).toBeInTheDocument();
  });

  it('should show empty state when no expeditions', () => {
    render(
      <ExpeditionTimeline
        expeditions={[]}
        {...mockActions}
        refreshing={false}
      />
    );

    expect(screen.getByText(/No expeditions yet/i)).toBeInTheDocument();
    expect(screen.getByText(/Create First Expedition/i)).toBeInTheDocument();
  });

  it('should call onCreate when create button clicked', () => {
    render(
      <ExpeditionTimeline
        expeditions={[]}
        {...mockActions}
        refreshing={false}
      />
    );

    const createButton = screen.getByText(/Create First Expedition/i);
    fireEvent.click(createButton);

    expect(mockActions.onCreate).toHaveBeenCalled();
  });

  it('should call onRefresh when refresh clicked', () => {
    render(
      <ExpeditionTimeline
        expeditions={mockExpeditions}
        {...mockActions}
        refreshing={false}
      />
    );

    const refreshButton = screen.getByText(/Refresh/i);
    fireEvent.click(refreshButton);

    expect(mockActions.onRefresh).toHaveBeenCalled();
  });

  it('should disable refresh button when refreshing', () => {
    render(
      <ExpeditionTimeline
        expeditions={mockExpeditions}
        {...mockActions}
        refreshing={true}
      />
    );

    const refreshButton = screen.getByText(/Refresh/i);
    expect(refreshButton).toBeDisabled();
  });
});
```

---

### Integration Tests (0.5 hours)

**Test: `DashboardContainer.test.tsx`** (30 min)
```typescript
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { DashboardContainer } from '@/containers/DashboardContainer';
import { useExpeditions } from '@/hooks/useExpeditions';

jest.mock('@/hooks/useExpeditions');
jest.mock('@/hooks/useDashboardStats');
jest.mock('@/hooks/useTimelineExpeditions');
jest.mock('@/hooks/useDashboardActions');

describe('DashboardContainer', () => {
  it('should compose hooks and pass props to presenter', () => {
    (useExpeditions as jest.Mock).mockReturnValue({
      expeditions: [],
      timelineData: null,
      loading: false,
      error: null,
      refreshing: false,
      refreshExpeditions: jest.fn(),
    });

    render(
      <BrowserRouter>
        <DashboardContainer />
      </BrowserRouter>
    );

    // Verify presenter receives correct props
    expect(screen.getByText(/Expedition Timeline/i)).toBeInTheDocument();
  });

  it('should show loading state', () => {
    (useExpeditions as jest.Mock).mockReturnValue({
      expeditions: [],
      timelineData: null,
      loading: true,
      error: null,
      refreshing: false,
      refreshExpeditions: jest.fn(),
    });

    render(
      <BrowserRouter>
        <DashboardContainer />
      </BrowserRouter>
    );

    expect(screen.getByText(/Loading your expeditions/i)).toBeInTheDocument();
  });

  it('should show error state', () => {
    (useExpeditions as jest.Mock).mockReturnValue({
      expeditions: [],
      timelineData: null,
      loading: false,
      error: 'Network error',
      refreshing: false,
      refreshExpeditions: jest.fn(),
    });

    render(
      <BrowserRouter>
        <DashboardContainer />
      </BrowserRouter>
    );

    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
  });
});
```

---

## Success Criteria

### Code Quality Metrics

✅ **File Size**:
- Dashboard.tsx: 359 lines → 3 lines (99% reduction)
- Largest new file: ~140 lines (ExpeditionTimeline.tsx)
- Average new file size: ~70 lines
- All hooks < 100 lines
- All components < 150 lines

✅ **Separation of Concerns**:
- Hooks: Single responsibility only
- Components: Pure presentation only
- Container: Hook composition only
- Presenter: Conditional rendering only

✅ **Test Coverage**:
- 80%+ coverage for all hooks
- 80%+ coverage for all components
- Integration test for container
- Total: 8 test files

---

### Functional Metrics

✅ **Zero Regressions**:
- Dashboard loads correctly
- All statistics display correctly
- Navigation works identically
- Refresh functionality preserved
- Empty state displays correctly
- Error handling works

✅ **Performance**:
- No performance degradation
- Proper memoization in hooks
- Pure components prevent unnecessary renders
- Same or better render performance

---

### Architecture Validation

✅ **Pattern Proven**:
- Container/Presenter pattern validated
- Custom hooks pattern validated
- Props-based components validated
- Ready to apply to CreateExpedition (Phase 1.2)
- Ready to apply to ExpeditionDetails (Phase 1.3)

✅ **Reusability**:
- `useDashboardStats` can be used in other views
- `DashboardStats` can be embedded elsewhere
- Pattern can be replicated for other features
- Hooks are independently testable

---

## Dependencies

### Phase 0 Utilities (Already Created):
- ✅ `utils/formatters.ts` - Currency, date, percentage formatting
- ✅ `utils/transforms/expeditionTransforms.ts` - Data transformations
- ✅ `utils/validation/expeditionValidation.ts` - Input validation

### Existing Components:
- `CaptainLayout` - Main layout wrapper
- `PirateButton` - Reusable button component
- `ExpeditionCard` - Expedition display card

### Existing Hooks:
- `useExpeditions` - Main data fetching hook

### Types:
- `Expedition` from `@/types/expedition`
- `ExpeditionTimelineEntry` from `@/types/expedition`

### Libraries:
- `react` - Core React library
- `react-router-dom` - Navigation
- `styled-components` - Styling
- `framer-motion` - Animations
- `lucide-react` - Icons
- `@testing-library/react` - Testing

---

## Risk Management

### Technical Risks

**Risk 1: Breaking existing functionality**
- **Probability**: Low
- **Impact**: High
- **Mitigation**:
  - Comprehensive testing before deployment
  - Keep Dashboard.tsx as thin wrapper (easy rollback)
  - Git tag before refactoring starts
  - Feature flag for gradual rollout

**Risk 2: Performance regression**
- **Probability**: Very Low
- **Impact**: Medium
- **Mitigation**:
  - Proper memoization in all hooks
  - Pure components prevent unnecessary renders
  - Before/after performance profiling with React DevTools
  - Load testing with sample data

**Risk 3: Type mismatches during refactor**
- **Probability**: Low
- **Impact**: Low
- **Mitigation**:
  - TypeScript strict mode enabled
  - Comprehensive type definitions for all props
  - Compile-time error catching
  - Type tests in test suite

**Risk 4: Integration issues with existing components**
- **Probability**: Low
- **Impact**: Medium
- **Mitigation**:
  - Integration tests verify container composition
  - Use existing components (CaptainLayout, PirateButton, ExpeditionCard)
  - Minimal changes to component interfaces
  - Test in development environment first

---

### Mitigation Strategies

1. **Git Safety**:
   - Create branch: `feature/dashboard-refactor`
   - Tag before starting: `v1-pre-dashboard-refactor`
   - Commit after each phase
   - PR review before merge

2. **Testing Gates**:
   - All unit tests must pass
   - Integration tests must pass
   - Visual regression testing
   - Manual QA testing

3. **Performance Benchmarks**:
   - Baseline render time: < 100ms
   - Baseline re-render time: < 50ms
   - No degradation allowed
   - React DevTools Profiler comparison

4. **Rollback Plan**:
   - Keep thin wrapper pattern (easy to revert)
   - Git revert to tagged version
   - Feature flag to disable new code
   - Document rollback procedure

---

## Next Steps After Phase 1.1

### Immediate Actions:
1. **Update roadmap**: Mark Phase 1.1 as complete
2. **Document learnings**: Create `ai_docs/react_phase1_1_completion.md`
3. **Review metrics**: Verify success criteria met
4. **Team demo**: Show refactored Dashboard

### Phase 1.2 Preparation (CreateExpedition):
1. **Apply learned patterns**: Use validated container/presenter pattern
2. **Estimate adjustments**: Refine estimates based on Phase 1.1 actuals
3. **Plan wizard extraction**: Design step component structure
4. **Review dependencies**: Ensure Phase 0 utilities are sufficient

### Long-term Tracking:
1. **Performance monitoring**: Track dashboard load times in production
2. **Bug tracking**: Monitor for regressions
3. **Developer feedback**: Survey team on new architecture
4. **Documentation**: Update architecture guide with patterns

---

## Appendix

### A. File Size Comparison

| File | Before | After | Reduction |
|------|--------|-------|-----------|
| Dashboard.tsx | 359 lines | 3 lines | 99% |
| (New) useDashboardStats.ts | - | 60 lines | - |
| (New) useTimelineExpeditions.ts | - | 70 lines | - |
| (New) useDashboardActions.ts | - | 80 lines | - |
| (New) DashboardStats.tsx | - | 120 lines | - |
| (New) ExpeditionTimeline.tsx | - | 140 lines | - |
| (New) DashboardContainer.tsx | - | 80 lines | - |
| (New) DashboardPresenter.tsx | - | 100 lines | - |
| **Total** | **359 lines** | **653 lines** | **+294 lines** |

**Note**: While total lines increase by 82%, we gain:
- 7 independently testable modules
- 3 reusable hooks
- 2 reusable components
- Pattern validation for 87 hours of remaining Phase 1 work
- Significantly improved maintainability

---

### B. Code Standards Applied

#### Container Components:
- ✅ Handle data fetching
- ✅ Manage state
- ✅ Orchestrate hooks
- ❌ NO presentation logic
- ❌ NO styled components
- ✅ Pass props to presenter

#### Presenter Components:
- ✅ Pure functions of props
- ❌ NO data fetching
- ❌ NO state (except UI state if necessary)
- ✅ Styled components allowed
- ✅ Event delegation to props

#### Custom Hooks:
- ✅ Single responsibility
- ✅ Reusable logic
- ✅ Return consistent interface
- ✅ Proper cleanup
- ✅ Memoization where needed

#### Presentation Components:
- ✅ Props-based rendering
- ❌ NO business logic
- ✅ Styled components
- ✅ Can use useMemo for performance
- ❌ NO API calls

---

### C. Glossary

**Container Component**: Responsible for data fetching, state management, and hook orchestration. Delegates to presenter for rendering.

**Presenter Component**: Pure UI component that renders based on props. No data fetching or business logic.

**Custom Hook**: Reusable React hook that encapsulates specific logic (calculations, actions, transformations).

**Presentation Component**: Reusable UI component focused on rendering a specific piece of UI.

**Single Responsibility Principle (SRP)**: Each module should have one reason to change (one responsibility).

**Memoization**: Caching technique to prevent unnecessary recalculation/re-rendering.

---

### D. References

- **[React Rework Roadmap](./react_rework.md)** - Main refactoring roadmap
- **[Phase 0 Completion](../ai_docs/react_phase0_completion.md)** - Foundation utilities
- **[SRP Agent Analysis](../ai_docs/react_srp_toolmaster_analysis.md)** - Architectural review
- **[Testing Guide](../tests/README.md)** - Testing best practices
- [Container/Presenter Pattern](https://medium.com/@dan_abramov/smart-and-dumb-components-7ca2f9a7c7d0) - Dan Abramov
- [Custom Hooks](https://react.dev/learn/reusing-logic-with-custom-hooks) - React docs

---

## Approval & Sign-off

### Stakeholders:
- [ ] Engineering Lead
- [ ] Frontend Developer
- [ ] QA Lead

### Sign-off Criteria:
- [x] Implementation plan reviewed
- [x] Timeline agreed (15 hours)
- [x] Success criteria defined
- [x] Testing strategy approved
- [x] Risk mitigation accepted

---

**Document Owner**: Development Team
**Created**: 2025-10-05
**Status**: Planning Complete - Ready for Implementation
**Next Review**: After Phase 1.1 completion
