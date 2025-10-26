# Architecture Documentation

## Overview

The Pirates Expedition Mini App follows a modern React architecture based on **Container/Presenter pattern**, **focused hook composition**, and a **layered service architecture**. This design promotes separation of concerns, testability, and maintainability.

## Core Architectural Patterns

### 1. Container/Presenter Pattern

The application uses a strict separation between **Container** components (logic) and **Presenter** components (UI).

#### Container Components
**Location**: `src/containers/`

**Responsibilities**:
- Hook composition and orchestration
- Data fetching and state management
- Action handler delegation
- Business logic coordination
- **NO UI rendering** (except delegation to Presenter)

**Example**: `DashboardContainer.tsx`
```typescript
export const DashboardContainer: React.FC = () => {
  const navigate = useNavigate();

  // 1. Data fetching hooks
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

  // 2. Calculation/transformation hooks
  const stats = useDashboardStats(expeditions, timelineData);
  const timelineExpeditions = useTimelineExpeditions(expeditions, timelineData);

  // 3. Action hooks
  const actions = useDashboardActions(navigate, refreshExpeditions);

  // 4. Delegate to presenter (no UI logic here)
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

**Key Principles**:
- Containers have NO styled-components or UI elements
- All props are passed down to Presenter
- Hooks are composed for specific concerns
- Zero business logic in JSX

#### Presenter Components
**Location**: `src/components/[feature]/`

**Responsibilities**:
- Pure UI rendering based on props
- Conditional rendering (loading, error, success states)
- Layout composition
- Styled components and animations
- **NO business logic or data fetching**

**Example**: `DashboardPresenter.tsx`
```typescript
export interface DashboardPresenterProps {
  loading: boolean;
  error: string | null;
  stats: DashboardStatsType;
  expeditions: ExpeditionTimelineEntry[];
  actions: DashboardActions;
  refreshing: boolean;
}

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
          <Loader2 size={48} />
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
          <EmptyTitle>Arrr! Something went wrong</EmptyTitle>
          <EmptyDescription>{error}</EmptyDescription>
          <PirateButton onClick={actions.handleRefresh}>
            Try Again
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
          refreshing={refreshing}
        />
      </DashboardContainer>
    </CaptainLayout>
  );
};
```

**Key Principles**:
- All data comes from props (no hooks for data fetching)
- Focuses on UI rendering and user interaction
- Uses styled-components for styling
- Handles all conditional rendering states
- Testable in isolation with mock props

---

### 2. Hook Composition Pattern

The application uses **focused, single-responsibility hooks** that compose together to provide complete functionality.

#### Hook Categories

**1. Data Fetching Hooks**
- `useExpeditionsList`: Manages expedition list state
- `useDashboardData`: Fetches timeline and analytics data
- `useExpeditionDetails`: Fetches single expedition details

**2. Mutation/CRUD Hooks**
- `useExpeditionCRUD`: Create, update, delete operations
- `useItemConsumption`: Item consumption operations
- `useExpeditionPirates`: Pirate name generation/management

**3. Transformation Hooks**
- `useDashboardStats`: Calculates statistics from raw data
- `useTimelineExpeditions`: Transforms expeditions for timeline view

**4. Action Hooks**
- `useDashboardActions`: Navigation and refresh actions
- `useExpeditionWizard`: Multi-step form state management

**5. Side-Effect Hooks**
- `useAutoRefresh`: Polling functionality
- `useExpeditionRealTime`: WebSocket real-time updates
- `useWebSocketUpdates`: WebSocket connection management
- `useUpdateNotifications`: Notification handling

**6. Utility Hooks**
- `useCachedQuery`: Query result caching
- `useWebSocketStatus`: WebSocket connection status

#### Composition Pattern

The **main hook** (`useExpeditions`) orchestrates focused hooks:

```typescript
export const useExpeditions = (options: UseExpeditionsOptions = {}): UseExpeditionsReturn => {
  const {
    autoRefresh = true,
    refreshInterval = 30000,
    realTimeUpdates = true,
  } = options;

  // Hook 1: Expedition list management
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

  // Hook 3: Dashboard data (timeline & analytics)
  const {
    timelineData,
    analytics,
    fetchTimeline,
    fetchAnalytics,
    refreshDashboard,
  } = useDashboardData();

  // Hook 4: Auto-refresh functionality
  useAutoRefresh({
    enabled: autoRefresh,
    interval: refreshInterval,
    onRefresh: refreshExpeditions,
  });

  // Hook 5: Real-time WebSocket updates
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

  // Return combined interface
  return {
    expeditions,
    timelineData,
    analytics,
    loading,
    error: listError || crudError,
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
- Each hook has a single, focused responsibility
- Easy to test individual hooks in isolation
- Hooks can be reused across different components
- Clear separation of concerns
- Improved code organization and maintainability

---

### 3. Service Layer Architecture

The application uses a **layered service architecture** for API communication and business logic.

#### Service Structure

```
src/services/
├── expeditionApi.ts          # Main API service (HTTP client)
├── websocketService.ts        # WebSocket communication
└── loggerService.ts           # Centralized logging
```

#### API Service Pattern

**Location**: `src/services/expeditionApi.ts`

The `ExpeditionApiService` class provides:
- Centralized HTTP client configuration
- Request/response interceptors
- Authentication header injection
- Error handling
- Type-safe API methods

```typescript
class ExpeditionApiService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    // Environment-aware base URL configuration
    const envApiUrl = import.meta.env.VITE_API_URL;

    if (import.meta.env.DEV && !envApiUrl) {
      this.baseURL = ''; // Use Vite proxy
    } else {
      this.baseURL = envApiUrl || window.location.origin;
    }

    // Axios instance with interceptors
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: { 'Content-Type': 'application/json' },
    });

    // Request interceptor: Add auth headers
    this.api.interceptors.request.use((config) => {
      const authHeaders = getAuthHeaders();
      Object.assign(config.headers, authHeaders);
      return config;
    });

    // Response interceptor: Error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        throw error;
      }
    );
  }

  // Type-safe API methods
  async getExpeditions(): Promise<Expedition[]> {
    const response = await this.api.get<{ expeditions: Expedition[] }>('/api/expeditions');
    return response.data.expeditions;
  }

  async createExpedition(data: CreateExpeditionRequest): Promise<Expedition> {
    const response = await this.api.post<Expedition>('/api/expeditions', data);
    return response.data;
  }

  // ... more methods
}

// Singleton instance export
export const expeditionApi = new ExpeditionApiService();
```

**Key Features**:
- **Singleton pattern**: Single instance across the app
- **Type safety**: Full TypeScript types for requests/responses
- **Interceptors**: Automatic auth header injection and error handling
- **Environment-aware**: Different base URLs for dev/prod
- **Centralized configuration**: All API config in one place

#### WebSocket Service Pattern

**Location**: `src/services/websocketService.ts`

The WebSocket service provides:
- Connection lifecycle management
- Room-based subscriptions
- Event-driven updates
- Automatic reconnection
- Connection status tracking

```typescript
class WebSocketService {
  private socket: Socket | null = null;
  private listeners: Map<string, Set<Function>> = new Map();

  connect(): void {
    this.socket = io(WEBSOCKET_URL, {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.notifyListeners('connection_status', { connected: true });
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      this.notifyListeners('connection_status', { connected: false });
    });
  }

  joinRoom(room: string): void {
    if (this.socket) {
      this.socket.emit('join_room', { room });
    }
  }

  on(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);

    // Register with socket
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  off(event: string, callback: Function): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.delete(callback);
    }

    if (this.socket) {
      this.socket.off(event, callback);
    }
  }
}

export const websocketService = new WebSocketService();
```

---

## Component Hierarchy

```
App.tsx
├── AppRouter.tsx
│   ├── Dashboard.tsx (page)
│   │   └── DashboardContainer.tsx
│   │       └── DashboardPresenter.tsx
│   │           ├── DashboardStats.tsx
│   │           └── ExpeditionTimeline.tsx
│   │               └── ExpeditionCard.tsx
│   │
│   ├── CreateExpedition.tsx (page)
│   │   └── CreateExpeditionContainer.tsx
│   │       └── CreateExpeditionPresenter.tsx
│   │           └── StepWizard.tsx
│   │               ├── ExpeditionDetailsStep.tsx
│   │               ├── ProductSelectionStep.tsx
│   │               ├── ProductConfigurationStep.tsx
│   │               └── ReviewStep.tsx
│   │
│   └── ExpeditionDetails.tsx (page)
│       └── ExpeditionDetailsContainer.tsx
│           └── ExpeditionDetailsPresenter.tsx
│               ├── OverviewTab.tsx
│               ├── ItemsTab.tsx
│               ├── ConsumptionsTab.tsx
│               ├── PiratesTab.tsx
│               └── AnalyticsTab.tsx
│
└── Shared Components
    ├── CaptainLayout.tsx (layout)
    ├── ExpeditionErrorBoundary.tsx (error handling)
    ├── ConnectionStatus.tsx (WebSocket status)
    └── UI Components
        ├── PirateButton.tsx
        ├── PirateCard.tsx
        └── DeadlineTimer.tsx
```

---

## Data Flow

### 1. Initial Load Flow

```
1. App.tsx
   └── useAppInitialization() hook
       ├── Initialize WebSocket connection
       ├── Set up Telegram Mini App SDK
       └── Load user preferences

2. Dashboard.tsx
   └── DashboardContainer.tsx
       └── useExpeditions({ autoRefresh: true, realTimeUpdates: true })
           ├── useExpeditionsList() - Fetch expeditions
           ├── useDashboardData() - Fetch timeline & analytics
           ├── useAutoRefresh() - Set up polling
           └── useExpeditionRealTime() - Subscribe to WebSocket updates

3. DashboardPresenter.tsx
   └── Render UI with fetched data
```

### 2. User Action Flow (Create Expedition)

```
1. User clicks "Create Expedition" button
   └── DashboardPresenter.tsx
       └── actions.handleCreateExpedition()
           └── navigate('/expeditions/create')

2. CreateExpedition.tsx page loads
   └── CreateExpeditionContainer.tsx
       └── useExpeditionWizard() hook
           ├── Manage multi-step form state
           ├── Handle step validation
           └── Handle form submission

3. User completes wizard and submits
   └── CreateExpeditionContainer.tsx
       └── handleSubmit()
           └── expeditionApi.createExpedition(data)
               └── POST /api/expeditions

4. Server responds with new expedition
   └── useExpeditions() hook (via WebSocket)
       ├── Receives 'EXPEDITION_CREATED' event
       ├── Updates local state optimistically
       └── Refreshes dashboard data

5. Navigate back to Dashboard
   └── DashboardPresenter.tsx
       └── Shows new expedition in timeline
```

### 3. Real-Time Update Flow

```
1. External event occurs (e.g., item consumed in another client)
   └── Flask server emits WebSocket event
       └── 'ITEM_CONSUMED' event

2. WebSocket service receives event
   └── websocketService.on('item_consumed', callback)
       └── Notifies all listeners

3. useExpeditionRealTime() hook receives event
   └── Calls onItemConsumed callback
       ├── fetchExpeditions(false) - Refresh list
       └── fetchAnalytics() - Update analytics

4. Component re-renders with updated data
   └── DashboardPresenter.tsx
       └── Shows updated progress/statistics
```

---

## State Management Strategy

The application uses **local component state** with React hooks instead of a global state management library (Redux, MobX, etc.).

### Rationale
- **Simplicity**: No global state boilerplate
- **Colocated state**: State lives close to where it's used
- **Performance**: Minimizes unnecessary re-renders
- **Type safety**: Full TypeScript support with hooks

### State Categories

**1. Server State** (cached, synchronized)
- Managed by custom hooks (`useExpeditions`, `useDashboardData`)
- Cached with `useCachedQuery` hook
- Synchronized via WebSocket real-time updates
- Refreshed via polling (`useAutoRefresh`)

**2. UI State** (ephemeral, local)
- Form state: `react-hook-form` + `useExpeditionWizard`
- Modal state: Local `useState` in parent components
- Tab state: URL params via `react-router-dom`

**3. Application State** (global, persistent)
- WebSocket connection: `websocketService` singleton
- Auth headers: Telegram SDK global state
- Theme: CSS variables (no runtime state)

---

## Error Handling Strategy

### Error Boundary Pattern

**Location**: `src/components/errors/`

The application uses **hierarchical error boundaries** at different levels:

```
App.tsx
└── ExpeditionErrorBoundary (top-level)
    ├── Catches all uncaught errors
    ├── Shows full-screen error UI
    └── Provides recovery actions

DashboardContainer.tsx
└── Local try-catch in hooks
    ├── Catches API errors
    ├── Sets error state
    └── DashboardPresenter shows error UI

CreateExpeditionContainer.tsx
└── Form validation errors
    ├── react-hook-form validation
    ├── API error handling
    └── User-friendly error messages
```

**Example**: `ExpeditionErrorBoundary.tsx`
```typescript
export class ExpeditionErrorBoundary extends React.Component<Props, State> {
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <ExpeditionErrorFallback
          error={this.state.error}
          resetError={() => this.setState({ hasError: false, error: null })}
        />
      );
    }

    return this.props.children;
  }
}
```

### Error Types

**1. Network Errors** (API failures)
- Caught by Axios interceptor
- Displayed in Presenter error state
- Retry mechanism via refresh button

**2. Validation Errors** (user input)
- Caught by `react-hook-form`
- Displayed inline with form fields
- Prevents submission

**3. Runtime Errors** (bugs)
- Caught by Error Boundary
- Full-screen error UI
- Option to reset and retry

---

## Testing Strategy

### Test Organization

```
src/
├── components/
│   └── dashboard/
│       ├── DashboardPresenter.tsx
│       └── DashboardPresenter.test.tsx
│
├── containers/
│   └── DashboardContainer.tsx
│       └── DashboardContainer.integration.test.tsx
│
├── hooks/
│   └── useExpeditions.ts
│       └── useExpeditions.test.ts
│
├── services/
│   └── expeditionApi.ts
│       └── expeditionApi.test.ts
│
└── flows/
    ├── create-expedition.flow.test.tsx
    ├── consume-item.flow.test.tsx
    └── add-pirate.flow.test.tsx
```

### Test Types

**1. Unit Tests** (isolated component/hook testing)
- Presenter components: Mock all props
- Hooks: Mock API service
- Services: Mock Axios

**2. Integration Tests** (container + hooks)
- Container components: Mock API, test hook integration
- Verify data flows correctly through hooks to Presenter

**3. Flow Tests** (end-to-end user journeys)
- Complete user workflows (create expedition, consume item)
- Mock API responses
- Verify UI updates correctly

### Testing Principles

**From CLAUDE.md**:
> "Mock at the boundary you control, not your own business logic"

This means:
- **DO**: Mock `expeditionApi` (external boundary)
- **DON'T**: Mock your own hooks or utilities
- **DO**: Test real hook composition
- **DON'T**: Test implementation details

---

## Performance Optimizations

### 1. Caching Strategy

**Hook**: `useCachedQuery`
- Caches API responses with TTL (time-to-live)
- Reduces redundant network requests
- Invalidation on mutations

```typescript
const { data, loading, error } = useCachedQuery(
  'expeditions-list',
  () => expeditionApi.getExpeditions(),
  { ttl: 60000 } // 1 minute cache
);
```

### 2. Real-Time Updates

**Strategy**: WebSocket subscriptions instead of polling
- Reduces server load (no constant polling)
- Instant updates for all clients
- Fallback to polling if WebSocket fails

### 3. Optimistic Updates

**Pattern**: Update UI immediately, rollback on error
```typescript
const createExpedition = async (data: CreateExpeditionRequest) => {
  const newExpedition = await createExpeditionAPI(data);

  if (newExpedition) {
    // Optimistically update local state
    setExpeditions((prev) => [newExpedition, ...prev]);
  }

  return newExpedition;
};
```

### 4. Code Splitting

**Strategy**: Lazy-load routes
```typescript
const Dashboard = lazy(() => import('./pages/Dashboard'));
const CreateExpedition = lazy(() => import('./pages/CreateExpedition'));
const ExpeditionDetails = lazy(() => import('./pages/ExpeditionDetails'));
```

---

## Development Workflow

### Adding a New Feature

**1. Create Service Method** (if needed)
```typescript
// src/services/expeditionApi.ts
async getExpeditionAnalytics(id: number): Promise<AnalyticsData> {
  const response = await this.api.get<AnalyticsData>(`/api/expeditions/${id}/analytics`);
  return response.data;
}
```

**2. Create Focused Hook**
```typescript
// src/hooks/useExpeditionAnalytics.ts
export const useExpeditionAnalytics = (expeditionId: number) => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await expeditionApi.getExpeditionAnalytics(expeditionId);
      setAnalytics(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [expeditionId]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return { analytics, loading, error, refetch: fetchAnalytics };
};
```

**3. Add to Container**
```typescript
// src/containers/ExpeditionDetailsContainer.tsx
export const ExpeditionDetailsContainer: React.FC = () => {
  const { id } = useParams();
  const expeditionId = parseInt(id!, 10);

  const { expedition, loading, error } = useExpeditionDetails(expeditionId);
  const { analytics, loading: analyticsLoading } = useExpeditionAnalytics(expeditionId);

  return (
    <ExpeditionDetailsPresenter
      expedition={expedition}
      analytics={analytics}
      loading={loading || analyticsLoading}
      error={error}
    />
  );
};
```

**4. Update Presenter**
```typescript
// src/components/expedition/ExpeditionDetailsPresenter.tsx
export interface ExpeditionDetailsPresenterProps {
  expedition: ExpeditionDetails | null;
  analytics: AnalyticsData | null;  // Add new prop
  loading: boolean;
  error: string | null;
}

export const ExpeditionDetailsPresenter: React.FC<ExpeditionDetailsPresenterProps> = ({
  expedition,
  analytics,
  loading,
  error,
}) => {
  // Render analytics section
  return (
    <CaptainLayout>
      {/* ... existing UI ... */}
      {analytics && <AnalyticsSection data={analytics} />}
    </CaptainLayout>
  );
};
```

**5. Write Tests**
```typescript
// src/hooks/useExpeditionAnalytics.test.ts
describe('useExpeditionAnalytics', () => {
  it('fetches analytics on mount', async () => {
    const mockAnalytics = { total_profit: 100 };
    vi.mocked(expeditionApi.getExpeditionAnalytics).mockResolvedValue(mockAnalytics);

    const { result } = renderHook(() => useExpeditionAnalytics(1));

    await waitFor(() => {
      expect(result.current.analytics).toEqual(mockAnalytics);
      expect(result.current.loading).toBe(false);
    });
  });
});
```

---

## Summary

The Pirates Expedition Mini App architecture is built on three core principles:

1. **Container/Presenter Separation**: Clear split between logic (Containers) and UI (Presenters)
2. **Focused Hook Composition**: Small, single-responsibility hooks that compose into powerful abstractions
3. **Layered Service Architecture**: Centralized API client with type safety and error handling

This architecture provides:
- **Testability**: Easy to test each layer in isolation
- **Maintainability**: Clear separation of concerns
- **Scalability**: Easy to add new features without breaking existing code
- **Type Safety**: Full TypeScript coverage across all layers
- **Performance**: Optimized caching, real-time updates, and code splitting

For more details, see:
- [Hook Composition Guide](./HOOK_COMPOSITION.md)
- [Service Layer Guide](./SERVICE_LAYER.md)
- [Testing Guide](./TESTING.md)
