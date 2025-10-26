# 🏴‍☠️ Pirates Expedition Mini App

A Telegram Mini App for managing pirate expeditions with real-time tracking, crew management, and treasure monitoring.

## 🚀 Features

### Core Functionality
- **Expedition Timeline Dashboard**: Visual timeline of all expeditions with real-time progress
- **Real-time Updates**: WebSocket integration for live expedition tracking
- **Pirate Theme**: Immersive pirate-themed UI with authentic styling
- **Mobile-First Design**: Optimized for Telegram's mobile experience

### Expedition Management
- Create and manage expeditions with deadlines
- Track item consumption and progress
- Monitor treasure collection and financial metrics
- View overdue expeditions and deadline warnings

### Brambler Feature
- Secure name anonymization for expedition participants
- Pirate character name generation
- Owner-only decryption with secure key management

### Real-time Features
- Live progress updates via WebSocket
- Instant notifications for expedition events
- Real-time completion tracking
- Deadline monitoring with haptic feedback

## 🛠 Technology Stack

### Frontend
- **React 18** with TypeScript
- **Styled Components** for pirate-themed styling
- **Framer Motion** for smooth animations
- **React Router** for navigation
- **Telegram WebApp SDK** for native integration

### Backend Integration
- **Flask REST API** with comprehensive expedition endpoints
- **WebSocket** for real-time updates
- **PostgreSQL** database with expedition schemas
- **Authentication** via Telegram init data validation

### Development Tools
- **Vite** for fast development and building
- **TypeScript** for type safety
- **ESLint** for code quality
- **Progressive Web App** capabilities

## 📦 Project Structure

```
webapp/
├── src/
│   ├── components/          # Presenter components (UI only)
│   │   ├── ui/             # Reusable UI components (PirateButton, PirateCard)
│   │   ├── dashboard/      # Dashboard presenters
│   │   ├── expedition/     # Expedition presenters
│   │   ├── errors/         # Error boundaries
│   │   └── websocket/      # WebSocket status components
│   ├── containers/          # Container components (logic only)
│   │   ├── DashboardContainer.tsx
│   │   ├── CreateExpeditionContainer.tsx
│   │   └── ExpeditionDetailsContainer.tsx
│   ├── pages/              # Page components (routing)
│   │   ├── Dashboard.tsx
│   │   ├── CreateExpedition.tsx
│   │   └── ExpeditionDetails.tsx
│   ├── hooks/              # Custom React hooks (focused, single-responsibility)
│   │   ├── useExpeditions.ts          # Main expedition hook (composition)
│   │   ├── useExpeditionsList.ts      # List management
│   │   ├── useExpeditionCRUD.ts       # CRUD operations
│   │   ├── useDashboardStats.ts       # Statistics calculation
│   │   ├── useAutoRefresh.ts          # Polling logic
│   │   └── useExpeditionRealTime.ts   # WebSocket updates
│   ├── services/           # Service layer (API clients)
│   │   ├── expeditionApi.ts           # HTTP client
│   │   ├── websocketService.ts        # WebSocket client
│   │   └── loggerService.ts           # Logging
│   ├── layouts/            # Layout components
│   │   └── CaptainLayout.tsx
│   ├── utils/              # Utility functions
│   │   ├── pirateTheme.ts             # Theme configuration
│   │   ├── telegram.ts                # Telegram WebApp utilities
│   │   ├── formatters.ts              # Data formatters
│   │   └── transforms.ts              # Data transformations
│   ├── types/              # TypeScript type definitions
│   │   └── expedition.ts
│   ├── flows/              # End-to-end flow tests
│   └── stories/            # Storybook stories
├── docs/                   # Architecture documentation
│   ├── ARCHITECTURE.md     # Container/Presenter pattern guide
│   ├── HOOK_COMPOSITION.md # Hook composition guide
│   └── SERVICE_LAYER.md    # Service layer guide
├── .storybook/             # Storybook configuration
├── public/                 # Static assets
└── package.json           # Dependencies and scripts
```

## 🏗️ Architecture

This application follows a modern **Container/Presenter pattern** with **focused hook composition** and a **layered service architecture**.

### Container/Presenter Pattern

**Container Components** (Logic):
- Located in `src/containers/`
- Handle hook composition and orchestration
- Manage data fetching and state
- Delegate rendering to Presenter components
- **NO UI code** - only hook calls and prop passing

**Presenter Components** (UI):
- Located in `src/components/`
- Pure UI rendering based on props
- Conditional rendering (loading, error, success states)
- Styled components and layout
- **NO business logic** - only visual rendering

**Example**:
```typescript
// Container - Logic only
export const DashboardContainer: React.FC = () => {
  const { expeditions, loading, error } = useExpeditions();
  const stats = useDashboardStats(expeditions);
  const actions = useDashboardActions();

  return (
    <DashboardPresenter
      loading={loading}
      error={error}
      stats={stats}
      expeditions={expeditions}
      actions={actions}
    />
  );
};

// Presenter - UI only
export const DashboardPresenter: React.FC<Props> = ({
  loading,
  error,
  stats,
  expeditions,
  actions
}) => {
  if (loading) return <LoadingScreen />;
  if (error) return <ErrorScreen error={error} />;

  return (
    <Layout>
      <DashboardStats stats={stats} />
      <ExpeditionTimeline expeditions={expeditions} />
    </Layout>
  );
};
```

### Hook Composition

Hooks are **small, focused, and composable**:

**Categories**:
1. **Data Fetching**: `useExpeditionsList`, `useDashboardData`
2. **Mutations**: `useExpeditionCRUD`, `useItemConsumption`
3. **Transformations**: `useDashboardStats`, `useTimelineExpeditions`
4. **Actions**: `useDashboardActions`, `useExpeditionWizard`
5. **Side Effects**: `useAutoRefresh`, `useExpeditionRealTime`
6. **Utilities**: `useCachedQuery`, `useWebSocketStatus`

**Main Hooks** compose focused hooks:
```typescript
export const useExpeditions = () => {
  const list = useExpeditionsList();      // Fetch list
  const crud = useExpeditionCRUD();       // CRUD operations
  const dashboard = useDashboardData();   // Timeline & analytics
  useAutoRefresh({ onRefresh: list.fetchExpeditions }); // Polling
  useExpeditionRealTime({ onUpdate: list.fetchExpeditions }); // WebSocket

  return { ...list, ...crud, ...dashboard };
};
```

### Service Layer

**Type-safe API clients** with:
- Centralized HTTP configuration (Axios)
- Automatic authentication header injection
- Request/response interceptors
- Error handling
- WebSocket management

**Services**:
- `expeditionApi` - REST API client
- `websocketService` - WebSocket client
- `loggerService` - Logging service

**Example**:
```typescript
// Type-safe API calls
const expeditions = await expeditionApi.getExpeditions();
const expedition = await expeditionApi.createExpedition({
  name: 'Treasure Hunt',
  deadline_days: 30,
  items: [{ product_id: 1, quantity: 10, target_price: 25.00 }]
});
```

For detailed architecture documentation, see:
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Hook Composition Guide](docs/HOOK_COMPOSITION.md)
- [Service Layer Guide](docs/SERVICE_LAYER.md)

## 🎨 Design System

### Pirate Theme Colors
- **Primary**: `#8B4513` (Pirate Brown)
- **Secondary**: `#DAA520` (Gold)
- **Success**: `#228B22` (Forest Green)
- **Danger**: `#DC143C` (Crimson)
- **Background**: `#F5DEB3` (Parchment)

### Typography
- **Headings**: 'Pirata One' (Pirate-themed font)
- **Body**: 'Roboto' (Clean, readable font)

### Components
- **PirateButton**: Themed buttons with haptic feedback
- **PirateCard**: Parchment-styled content cards
- **DeadlineTimer**: Real-time countdown with visual alerts
- **ExpeditionCard**: Timeline expedition display

## 🔧 Development

### Prerequisites
- Node.js 16+
- npm or yarn
- Access to the backend Flask API

### Installation

1. Navigate to webapp directory:
```bash
cd webapp
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

4. Build for production:
```bash
npm run build
```

### Available Scripts

- `npm run dev` - Start Vite development server (hot reload)
- `npm run build` - Build for production (TypeScript + Vite)
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint code quality checks
- `npm run type-check` - Run TypeScript type checking
- `npm test` - Run tests in watch mode (Vitest)
- `npm run test:ui` - Run tests with UI dashboard
- `npm run test:coverage` - Generate test coverage report
- `npm run test:run` - Run tests once (CI mode)
- `npm run storybook` - Start Storybook component library
- `npm run build-storybook` - Build static Storybook

### Environment Variables

**Development**:
- Uses Vite proxy (configured in `vite.config.ts`)
- Proxies `/api` requests to `http://127.0.0.1:5000` (Flask backend)
- No environment variables needed for local development

**Production**:
- Set `VITE_API_URL` to your backend URL (e.g., `https://api.myapp.com`)
- Create `.env.production` file:
```
VITE_API_URL=https://your-backend-url.com
```

### Development Workflow

**Adding a New Feature**:

1. **Create Service Method** (if needed):
```typescript
// src/services/expeditionApi.ts
async getExpeditionAnalytics(id: number): Promise<AnalyticsData> {
  const response = await this.api.get(`/api/expeditions/${id}/analytics`);
  return response.data;
}
```

2. **Create Focused Hook**:
```typescript
// src/hooks/useExpeditionAnalytics.ts
export const useExpeditionAnalytics = (id: number) => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const data = await expeditionApi.getExpeditionAnalytics(id);
      setAnalytics(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetchAnalytics(); }, [fetchAnalytics]);

  return { analytics, loading, error, refetch: fetchAnalytics };
};
```

3. **Add to Container**:
```typescript
// src/containers/ExpeditionDetailsContainer.tsx
const { analytics } = useExpeditionAnalytics(expeditionId);

return (
  <ExpeditionDetailsPresenter
    expedition={expedition}
    analytics={analytics}
  />
);
```

4. **Update Presenter**:
```typescript
// src/components/expedition/ExpeditionDetailsPresenter.tsx
export const ExpeditionDetailsPresenter = ({ expedition, analytics }) => (
  <Layout>
    {/* ... existing UI ... */}
    {analytics && <AnalyticsSection data={analytics} />}
  </Layout>
);
```

5. **Write Tests**:
```typescript
// src/hooks/useExpeditionAnalytics.test.ts
describe('useExpeditionAnalytics', () => {
  it('fetches analytics on mount', async () => {
    const mockAnalytics = { total_profit: 100 };
    vi.mocked(expeditionApi.getExpeditionAnalytics).mockResolvedValue(mockAnalytics);

    const { result } = renderHook(() => useExpeditionAnalytics(1));

    await waitFor(() => {
      expect(result.current.analytics).toEqual(mockAnalytics);
    });
  });
});
```

6. **Create Storybook Story**:
```typescript
// src/components/expedition/AnalyticsSection.stories.tsx
export const Default: Story = {
  args: {
    data: { total_profit: 100, total_revenue: 500 }
  }
};
```

### Development Features
- **Hot Module Replacement** - Instant updates without page reload
- **TypeScript Type Checking** - Catch errors at compile time
- **ESLint Code Quality** - Enforce code standards
- **Vitest Testing** - Fast unit and integration tests
- **Storybook** - Component library and visual testing
- **Responsive Design** - Mobile-first development

## 📱 Telegram Integration

### WebApp Features
- **Native UI**: Adapts to Telegram's theme and UI patterns
- **Haptic Feedback**: Touch feedback for better UX
- **MainButton/BackButton**: Native Telegram button integration
- **Viewport Handling**: Proper mobile viewport management
- **Authentication**: Secure Telegram user validation

### Bot Commands
- `/expedition` - Launch the Mini App
- `/dashboard` - Open expedition dashboard
- `/miniapp` - Access the full interface

### Security
- Telegram init data validation
- Chat ID authentication
- Permission-based access control
- HTTPS-only in production

## 🌊 Real-time Features

### WebSocket Events
- **expedition_update**: General expedition changes
- **item_consumed**: Item consumption events
- **expedition_completed**: Expedition completion
- **deadline_warning**: Approaching deadlines
- **expedition_created**: New expedition notifications

### Notifications
- Haptic feedback for different event types
- Visual alerts for important updates
- Real-time progress bar updates
- Live statistics refreshing

## 🏴‍☠️ Pirate Features

### Expedition System
- Create expeditions with items and deadlines
- Track consumption progress
- Monitor treasure collection
- Manage pirate crew assignments

### Brambler Name Anonymization
- Generate pirate names for participants
- Secure encryption with owner-only access
- Character-based name replacement
- Audit trail for transparency

### Visual Elements
- Ship and treasure animations
- Pirate emoji integration
- Parchment texture backgrounds
- Gold accent highlights

## 🚀 Deployment

### Building for Production

1. Build the application:
```bash
npm run build
```

2. The `dist/` folder contains the built application ready for deployment.

### Deployment Options

- **Static Hosting**: Vercel, Netlify, GitHub Pages
- **CDN**: CloudFlare, AWS CloudFront
- **Same-Origin**: Serve from the same domain as the Flask backend

### Configuration

Ensure the webapp is accessible at the URL configured in the bot's Mini App settings:
- Set the webapp URL in Telegram BotFather
- Configure CORS in the Flask backend
- Set up HTTPS for production

## 📈 Performance

### Optimization Features
- Code splitting by feature
- Lazy loading of components
- Image optimization
- PWA caching strategies
- Bundle size monitoring

### Metrics
- **Target Bundle Size**: <500KB gzipped
- **Load Time**: <2 seconds
- **Real-time Latency**: <100ms
- **Mobile Performance**: 90+ Lighthouse score

## 🛡 Security

### Data Protection
- No sensitive data stored in frontend
- Telegram auth validation
- HTTPS enforcement
- CORS configuration
- XSS protection

### Privacy
- Local storage minimal usage
- Session-based authentication
- No third-party tracking
- Secure WebSocket connections

## 🎯 Browser Support

- **Mobile**: iOS Safari 14+, Chrome Mobile 90+
- **Desktop**: Chrome 90+, Firefox 88+, Safari 14+
- **Telegram**: All platforms with WebApp support

## 🧪 Testing

The application has comprehensive test coverage across multiple levels:

### Test Structure

```
src/
├── hooks/
│   ├── useExpeditions.ts
│   └── useExpeditions.test.ts       # Hook unit tests
├── containers/
│   ├── DashboardContainer.tsx
│   └── DashboardContainer.integration.test.tsx  # Integration tests
├── flows/
│   ├── create-expedition.flow.test.tsx          # End-to-end flow tests
│   └── consume-item.flow.test.tsx
└── components/
    ├── DashboardPresenter.tsx
    └── DashboardPresenter.test.tsx  # Component tests
```

### Test Categories

**1. Unit Tests** (Hooks, Services, Transformers)
- Mock API service at the boundary
- Test individual hook logic in isolation
- Fast and focused

```typescript
describe('useDashboardStats', () => {
  it('calculates stats correctly', () => {
    const expeditions = [
      { id: 1, status: 'active', revenue: 1000, profit: 300 }
    ];
    const { result } = renderHook(() => useDashboardStats(expeditions));

    expect(result.current.totalExpeditions).toBe(1);
    expect(result.current.totalRevenue).toBe(1000);
  });
});
```

**2. Integration Tests** (Containers)
- Test hook composition
- Verify data flows correctly through hooks to presenter
- Mock API, test real hook integration

```typescript
describe('DashboardContainer', () => {
  it('integrates hooks and renders presenter', async () => {
    vi.mocked(expeditionApi.getExpeditions).mockResolvedValue(mockExpeditions);

    render(<DashboardContainer />);

    await waitFor(() => {
      expect(screen.getByText('Total Expeditions: 5')).toBeInTheDocument();
    });
  });
});
```

**3. Flow Tests** (End-to-End User Journeys)
- Complete user workflows
- Mock API responses
- Verify UI updates correctly

```typescript
describe('Create Expedition Flow', () => {
  it('completes full expedition creation', async () => {
    const user = userEvent.setup();

    render(<CreateExpeditionContainer />);

    // Fill wizard steps
    await user.type(screen.getByLabelText('Name'), 'Treasure Hunt');
    await user.click(screen.getByText('Next'));

    // Select products
    await user.click(screen.getByText('Gold Coins'));
    await user.click(screen.getByText('Next'));

    // Submit
    await user.click(screen.getByText('Create'));

    await waitFor(() => {
      expect(expeditionApi.createExpedition).toHaveBeenCalled();
    });
  });
});
```

**4. Component Tests** (Presenters)
- Test UI rendering with mock props
- Test conditional states (loading, error, success)
- No business logic testing

```typescript
describe('DashboardPresenter', () => {
  it('renders loading state', () => {
    render(<DashboardPresenter loading={true} />);
    expect(screen.getByText('Loading your expeditions...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    render(<DashboardPresenter error="Failed to load" />);
    expect(screen.getByText('Failed to load')).toBeInTheDocument();
  });
});
```

### Running Tests

```bash
# Watch mode (development)
npm test

# Run once (CI)
npm run test:run

# With UI dashboard
npm run test:ui

# Generate coverage report
npm run test:coverage
```

### Test Coverage

Current coverage (Phase 4.2 complete):
- **652 total tests** (576 unit + 76 integration)
- **Hooks**: 100% coverage
- **Services**: 100% coverage
- **Containers**: 95% coverage
- **Components**: 90% coverage

### Testing Best Practices

**From CLAUDE.md**:
> "Mock at the boundary you control, not your own business logic"

This means:
- **DO**: Mock `expeditionApi` (external boundary)
- **DON'T**: Mock your own hooks or utilities
- **DO**: Test real hook composition
- **DON'T**: Test implementation details

## 📚 API Integration

The Mini App integrates with the existing Flask backend APIs:

- **GET /api/expeditions** - List expeditions
- **POST /api/expeditions** - Create expedition
- **GET /api/expeditions/{id}** - Expedition details
- **POST /api/expeditions/{id}/consume** - Consume items
- **GET /api/dashboard/timeline** - Timeline data
- **WebSocket** - Real-time updates

## 📖 Documentation

### Architecture Documentation

Comprehensive guides are available in the `docs/` directory:

- **[Architecture Guide](docs/ARCHITECTURE.md)** - Container/Presenter pattern, component hierarchy, data flow
- **[Hook Composition Guide](docs/HOOK_COMPOSITION.md)** - Hook patterns, composition strategies, best practices
- **[Service Layer Guide](docs/SERVICE_LAYER.md)** - API client, WebSocket service, error handling

### Component Library

Run Storybook to explore all components:

```bash
npm run storybook
```

Browse components at: `http://localhost:6006`

**Storybook Features**:
- Interactive component playground
- Visual testing of all states
- Props documentation
- Code examples
- Accessibility testing

## 🤝 Contributing

1. Follow the existing code style
2. Use TypeScript for type safety
3. Test on mobile devices
4. Maintain pirate theme consistency
5. Update documentation

## 📄 License

This project is part of the Pirates Expedition bot system. See the main project license for details.

---

*⚓ Happy sailing, Captain!*