# Hook Composition Guide

## Overview

This guide explains the **hook composition pattern** used throughout the Pirates Expedition Mini App. This pattern promotes code reusability, testability, and separation of concerns by composing small, focused hooks into more complex functionality.

## Core Principles

### 1. Single Responsibility Principle
Each hook should have **one clear purpose** and do it well.

**Good Examples**:
- `useExpeditionsList` - Manages expedition list state only
- `useAutoRefresh` - Handles polling logic only
- `useDashboardStats` - Calculates statistics only

**Bad Example** (avoid):
```typescript
// DON'T: This hook does too much
const useEverything = () => {
  const [expeditions, setExpeditions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetching logic
  // Stats calculation
  // Auto-refresh logic
  // WebSocket subscriptions
  // Navigation handlers
  // ...everything in one hook
};
```

### 2. Composability
Hooks should be designed to work together seamlessly.

**Good Example**:
```typescript
const useExpeditions = () => {
  // Compose focused hooks
  const list = useExpeditionsList();
  const crud = useExpeditionCRUD();
  const dashboard = useDashboardData();
  const autoRefresh = useAutoRefresh({ onRefresh: list.fetchExpeditions });
  const realTime = useExpeditionRealTime({ onUpdate: list.fetchExpeditions });

  // Return combined interface
  return {
    ...list,
    ...crud,
    ...dashboard,
  };
};
```

### 3. Dependency Injection
Pass dependencies as parameters instead of hardcoding them.

**Good Example**:
```typescript
const useAutoRefresh = ({
  enabled,
  interval,
  onRefresh,
}: {
  enabled: boolean;
  interval: number;
  onRefresh: () => Promise<void>;
}) => {
  useEffect(() => {
    if (!enabled) return;

    const timer = setInterval(onRefresh, interval);
    return () => clearInterval(timer);
  }, [enabled, interval, onRefresh]);
};
```

**Bad Example** (avoid):
```typescript
const useAutoRefresh = () => {
  // DON'T: Hardcoded dependencies
  const { fetchExpeditions } = useExpeditions(); // Creates circular dependency!

  useEffect(() => {
    const timer = setInterval(fetchExpeditions, 30000);
    return () => clearInterval(timer);
  }, [fetchExpeditions]);
};
```

---

## Hook Categories

### 1. Data Fetching Hooks

**Purpose**: Manage server state (fetching, caching, error handling)

**Pattern**:
```typescript
export const useExpeditionsList = ({ initialLoad = true }: Options = {}) => {
  const [expeditions, setExpeditions] = useState<Expedition[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchExpeditions = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    else setRefreshing(true);

    setError(null);

    try {
      const data = await expeditionApi.getExpeditions();
      setExpeditions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch expeditions');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    if (initialLoad) {
      fetchExpeditions();
    }
  }, [fetchExpeditions, initialLoad]);

  return {
    expeditions,
    loading,
    error,
    refreshing,
    fetchExpeditions,
    setExpeditions, // Allow external updates (optimistic updates)
  };
};
```

**Key Features**:
- Separate `loading` (initial) vs `refreshing` (background) states
- Error handling with user-friendly messages
- Expose `setExpeditions` for optimistic updates
- `initialLoad` option for flexibility

**Examples**:
- `useExpeditionsList` - Fetch expeditions list
- `useExpeditionDetails` - Fetch single expedition details
- `useDashboardData` - Fetch dashboard data (timeline, analytics)
- `useExpeditionPirates` - Fetch pirate names for expedition

---

### 2. Mutation/CRUD Hooks

**Purpose**: Handle create, update, delete operations with optimistic updates

**Pattern**:
```typescript
export const useExpeditionCRUD = ({
  onSuccess,
}: {
  onSuccess?: () => void;
} = {}) => {
  const [error, setError] = useState<string | null>(null);

  const createExpedition = useCallback(
    async (data: CreateExpeditionRequest): Promise<Expedition | null> => {
      setError(null);
      try {
        const newExpedition = await expeditionApi.createExpedition(data);
        onSuccess?.();
        return newExpedition;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create expedition');
        return null;
      }
    },
    [onSuccess]
  );

  const updateExpeditionStatus = useCallback(
    async (id: number, status: string): Promise<Expedition | null> => {
      setError(null);
      try {
        const updated = await expeditionApi.updateExpeditionStatus(id, status);
        onSuccess?.();
        return updated;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to update expedition');
        return null;
      }
    },
    [onSuccess]
  );

  const deleteExpedition = useCallback(
    async (id: number): Promise<boolean> => {
      setError(null);
      try {
        await expeditionApi.deleteExpedition(id);
        onSuccess?.();
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete expedition');
        return false;
      }
    },
    [onSuccess]
  );

  return {
    error,
    createExpedition,
    updateExpeditionStatus,
    deleteExpedition,
  };
};
```

**Key Features**:
- Return `null` or `false` on error (easy to check in caller)
- Optional `onSuccess` callback for side effects
- Centralized error state
- Type-safe return values

**Examples**:
- `useExpeditionCRUD` - Create, update, delete expeditions
- `useItemConsumption` - Consume items from expedition
- `useExpeditionPirates` - Generate/decrypt pirate names

---

### 3. Transformation Hooks

**Purpose**: Derive computed values from raw data (pure functions)

**Pattern**:
```typescript
export const useDashboardStats = (
  expeditions: Expedition[],
  timelineData: TimelineData | null
): DashboardStats => {
  return useMemo(() => {
    const activeExpeditions = expeditions.filter(e => e.status === 'active');
    const completedExpeditions = expeditions.filter(e => e.status === 'completed');

    const totalRevenue = timelineData?.total_revenue || 0;
    const totalProfit = timelineData?.total_profit || 0;

    return {
      totalExpeditions: expeditions.length,
      activeExpeditions: activeExpeditions.length,
      completedExpeditions: completedExpeditions.length,
      totalRevenue,
      totalProfit,
      profitMargin: totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0,
    };
  }, [expeditions, timelineData]);
};
```

**Key Features**:
- Use `useMemo` to avoid recalculation on every render
- Pure function - same input = same output
- No side effects or API calls
- Returns computed value directly (no loading/error state)

**Examples**:
- `useDashboardStats` - Calculate dashboard statistics
- `useTimelineExpeditions` - Transform expeditions for timeline view

---

### 4. Action Hooks

**Purpose**: Encapsulate event handlers and navigation logic

**Pattern**:
```typescript
export const useDashboardActions = (
  navigate: NavigateFunction,
  refreshExpeditions: () => Promise<void>
) => {
  const [refreshing, setRefreshing] = useState(false);

  const handleViewExpedition = useCallback(
    (id: number) => {
      navigate(`/expeditions/${id}`);
    },
    [navigate]
  );

  const handleManageExpedition = useCallback(
    (id: number) => {
      navigate(`/expeditions/${id}/manage`);
    },
    [navigate]
  );

  const handleCreateExpedition = useCallback(() => {
    navigate('/expeditions/create');
  }, [navigate]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await refreshExpeditions();
    setRefreshing(false);
  }, [refreshExpeditions]);

  return {
    handleViewExpedition,
    handleManageExpedition,
    handleCreateExpedition,
    handleRefresh,
    refreshing,
  };
};
```

**Key Features**:
- All handlers wrapped in `useCallback` for stable references
- Centralized action logic (easy to test)
- Returns object of handlers for easy spreading

**Examples**:
- `useDashboardActions` - Dashboard navigation and refresh actions
- `useExpeditionWizard` - Multi-step form navigation and submission

---

### 5. Side-Effect Hooks

**Purpose**: Manage side effects like polling, WebSocket subscriptions, timers

**Pattern 1: Polling** (`useAutoRefresh`)
```typescript
export const useAutoRefresh = ({
  enabled,
  interval,
  onRefresh,
}: {
  enabled: boolean;
  interval: number;
  onRefresh: () => Promise<void>;
}) => {
  useEffect(() => {
    if (!enabled) return;

    const timer = setInterval(() => {
      onRefresh().catch((err) => {
        console.error('Auto-refresh failed:', err);
      });
    }, interval);

    return () => clearInterval(timer);
  }, [enabled, interval, onRefresh]);
};
```

**Pattern 2: WebSocket Subscriptions** (`useExpeditionRealTime`)
```typescript
export const useExpeditionRealTime = ({
  enabled,
  onExpeditionUpdate,
  onItemConsumed,
  onExpeditionCompleted,
  onExpeditionCreated,
}: UseExpeditionRealTimeOptions) => {
  useEffect(() => {
    if (!enabled) return;

    // Subscribe to events
    const handleExpeditionUpdate = (data: any) => {
      console.log('Expedition updated:', data);
      onExpeditionUpdate?.(data);
    };

    const handleItemConsumed = (data: any) => {
      console.log('Item consumed:', data);
      onItemConsumed?.(data);
    };

    websocketService.on('expedition_updated', handleExpeditionUpdate);
    websocketService.on('item_consumed', handleItemConsumed);
    websocketService.on('expedition_completed', onExpeditionCompleted);
    websocketService.on('expedition_created', onExpeditionCreated);

    // Cleanup
    return () => {
      websocketService.off('expedition_updated', handleExpeditionUpdate);
      websocketService.off('item_consumed', handleItemConsumed);
      websocketService.off('expedition_completed', onExpeditionCompleted);
      websocketService.off('expedition_created', onExpeditionCreated);
    };
  }, [enabled, onExpeditionUpdate, onItemConsumed, onExpeditionCompleted, onExpeditionCreated]);
};
```

**Key Features**:
- `enabled` flag for conditional activation
- Proper cleanup in return function
- Callback pattern for flexibility
- Error handling for robustness

**Examples**:
- `useAutoRefresh` - Polling timer
- `useExpeditionRealTime` - WebSocket event subscriptions
- `useWebSocketUpdates` - WebSocket connection management
- `useUpdateNotifications` - Notification display

---

### 6. Utility Hooks

**Purpose**: Reusable utilities (caching, debouncing, etc.)

**Pattern**: `useCachedQuery`
```typescript
interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

const cache = new Map<string, CacheEntry<any>>();

export const useCachedQuery = <T>(
  key: string,
  fetcher: () => Promise<T>,
  options: { ttl?: number } = {}
) => {
  const { ttl = 60000 } = options; // Default 1 minute
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    // Check cache
    const cached = cache.get(key);
    if (cached && Date.now() - cached.timestamp < ttl) {
      setData(cached.data);
      return;
    }

    // Fetch fresh data
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      cache.set(key, { data: result, timestamp: Date.now() });
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fetch failed');
    } finally {
      setLoading(false);
    }
  }, [key, fetcher, ttl]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
};
```

**Examples**:
- `useCachedQuery` - Query result caching with TTL
- `useWebSocketStatus` - WebSocket connection status tracking

---

## Composition Patterns

### Pattern 1: Main Hook Composition

**Strategy**: Create a "main hook" that composes multiple focused hooks

**Example**: `useExpeditions`
```typescript
export const useExpeditions = (options: UseExpeditionsOptions = {}): UseExpeditionsReturn => {
  const {
    autoRefresh = true,
    refreshInterval = 30000,
    realTimeUpdates = true,
  } = options;

  // Hook 1: List management
  const {
    expeditions,
    loading,
    error: listError,
    refreshing,
    fetchExpeditions,
    setExpeditions,
  } = useExpeditionsList({ initialLoad: true });

  // Hook 2: CRUD operations
  const {
    error: crudError,
    createExpedition: createExpeditionAPI,
    updateExpeditionStatus: updateExpeditionStatusAPI,
    deleteExpedition: deleteExpeditionAPI,
  } = useExpeditionCRUD({
    onSuccess: () => {
      fetchTimeline();
      fetchAnalytics();
    },
  });

  // Hook 3: Dashboard data
  const {
    timelineData,
    analytics,
    fetchTimeline,
    fetchAnalytics,
    refreshDashboard,
  } = useDashboardData();

  // Combine errors
  const error = listError || crudError;

  // Combined refresh function
  const refreshExpeditions = useCallback(async () => {
    await Promise.all([
      fetchExpeditions(false),
      refreshDashboard(),
    ]);
  }, [fetchExpeditions, refreshDashboard]);

  // Hook 4: Auto-refresh
  useAutoRefresh({
    enabled: autoRefresh,
    interval: refreshInterval,
    onRefresh: refreshExpeditions,
  });

  // Hook 5: Real-time updates
  useExpeditionRealTime({
    enabled: realTimeUpdates,
    onExpeditionUpdate: (data) => {
      fetchExpeditions(false);
      if (data.type === 'EXPEDITION_COMPLETED') {
        refreshDashboard();
      }
    },
    onItemConsumed: () => {
      fetchExpeditions(false);
      fetchAnalytics();
    },
  });

  // Wrapped CRUD with optimistic updates
  const createExpedition = useCallback(
    async (data: CreateExpeditionRequest): Promise<Expedition | null> => {
      const newExpedition = await createExpeditionAPI(data);
      if (newExpedition) {
        setExpeditions((prev) => [newExpedition, ...prev]);
      }
      return newExpedition;
    },
    [createExpeditionAPI, setExpeditions]
  );

  // Return combined interface
  return {
    expeditions,
    timelineData,
    analytics,
    loading,
    error,
    refreshing,
    refreshExpeditions,
    createExpedition,
    updateExpeditionStatus,
    deleteExpedition,
    refreshTimeline: fetchTimeline,
    refreshAnalytics: fetchAnalytics,
  };
};
```

**Benefits**:
- Single import for complete functionality
- Focused hooks remain testable in isolation
- Flexible configuration via options
- Clean separation of concerns

---

### Pattern 2: Container Hook Composition

**Strategy**: Compose hooks directly in Container components

**Example**: `DashboardContainer`
```typescript
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

  // Transformations
  const stats = useDashboardStats(expeditions, timelineData);
  const timelineExpeditions = useTimelineExpeditions(expeditions, timelineData);

  // Actions
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

**Benefits**:
- Clear data flow from hooks → props → Presenter
- Easy to see all dependencies
- Container is thin orchestrator
- Each hook is independently testable

---

## Best Practices

### 1. Return Stable References

Always use `useCallback` and `useMemo` for returned functions and objects:

```typescript
// GOOD
const handleClick = useCallback(() => {
  console.log('clicked');
}, []);

return { handleClick };
```

```typescript
// BAD - creates new function on every render
const handleClick = () => {
  console.log('clicked');
};

return { handleClick };
```

### 2. Expose Set Functions for Optimistic Updates

```typescript
// GOOD - allows external optimistic updates
const useExpeditionsList = () => {
  const [expeditions, setExpeditions] = useState<Expedition[]>([]);

  return {
    expeditions,
    setExpeditions, // Expose setter
    fetchExpeditions,
  };
};

// Usage in parent hook
const createExpedition = async (data) => {
  const newExpedition = await api.createExpedition(data);
  setExpeditions(prev => [newExpedition, ...prev]); // Optimistic update
  return newExpedition;
};
```

### 3. Use Options Objects for Flexibility

```typescript
// GOOD - easy to extend with new options
const useAutoRefresh = ({
  enabled = true,
  interval = 30000,
  onRefresh,
  onError,
}: UseAutoRefreshOptions) => {
  // ...
};
```

```typescript
// BAD - hard to extend, many parameters
const useAutoRefresh = (
  enabled: boolean,
  interval: number,
  onRefresh: () => void,
  onError: (err: Error) => void
) => {
  // ...
};
```

### 4. Separate Loading States

```typescript
const [loading, setLoading] = useState(false);      // Initial load
const [refreshing, setRefreshing] = useState(false); // Background refresh

const fetchData = async (showLoading = true) => {
  if (showLoading) setLoading(true);
  else setRefreshing(true);

  try {
    // fetch
  } finally {
    setLoading(false);
    setRefreshing(false);
  }
};
```

### 5. Combine Related Errors

```typescript
const { error: listError } = useExpeditionsList();
const { error: crudError } = useExpeditionCRUD();

// Combine into single error
const error = listError || crudError;

return { error }; // Single error to check
```

---

## Testing Hooks

### Test in Isolation

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { useExpeditionsList } from './useExpeditionsList';
import { expeditionApi } from '@/services/expeditionApi';

vi.mock('@/services/expeditionApi');

describe('useExpeditionsList', () => {
  it('fetches expeditions on mount', async () => {
    const mockExpeditions = [{ id: 1, name: 'Test' }];
    vi.mocked(expeditionApi.getExpeditions).mockResolvedValue(mockExpeditions);

    const { result } = renderHook(() => useExpeditionsList({ initialLoad: true }));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.expeditions).toEqual(mockExpeditions);
      expect(result.current.loading).toBe(false);
    });
  });

  it('handles errors', async () => {
    vi.mocked(expeditionApi.getExpeditions).mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useExpeditionsList({ initialLoad: true }));

    await waitFor(() => {
      expect(result.current.error).toBe('API Error');
      expect(result.current.loading).toBe(false);
    });
  });
});
```

### Test Composition

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { useExpeditions } from './useExpeditions';
import { expeditionApi } from '@/services/expeditionApi';
import { websocketService } from '@/services/websocketService';

vi.mock('@/services/expeditionApi');
vi.mock('@/services/websocketService');

describe('useExpeditions', () => {
  it('composes all hooks correctly', async () => {
    const mockExpeditions = [{ id: 1, name: 'Test' }];
    const mockTimeline = { total_revenue: 100 };
    const mockAnalytics = { total_profit: 50 };

    vi.mocked(expeditionApi.getExpeditions).mockResolvedValue(mockExpeditions);
    vi.mocked(expeditionApi.getDashboardTimeline).mockResolvedValue(mockTimeline);
    vi.mocked(expeditionApi.getAnalytics).mockResolvedValue(mockAnalytics);

    const { result } = renderHook(() => useExpeditions({
      autoRefresh: false,
      realTimeUpdates: false,
    }));

    await waitFor(() => {
      expect(result.current.expeditions).toEqual(mockExpeditions);
      expect(result.current.timelineData).toEqual(mockTimeline);
      expect(result.current.analytics).toEqual(mockAnalytics);
    });
  });
});
```

---

## Summary

The hook composition pattern provides:

1. **Modularity**: Small, focused hooks with single responsibilities
2. **Reusability**: Hooks can be used across different components
3. **Testability**: Easy to test hooks in isolation
4. **Maintainability**: Clear separation of concerns
5. **Flexibility**: Easy to add new functionality by composing existing hooks

**Remember**: Mock at the boundary you control (API service), not your own business logic (hooks).

For more information, see:
- [Architecture Documentation](./ARCHITECTURE.md)
- [Service Layer Guide](./SERVICE_LAYER.md)
- [Testing Guide](./TESTING.md)
