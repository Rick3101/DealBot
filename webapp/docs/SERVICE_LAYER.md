# Service Layer Guide

## Overview

The service layer provides a **centralized, type-safe abstraction** over HTTP and WebSocket communication with the backend. It handles authentication, error handling, and provides a clean API for the rest of the application.

## Service Architecture

```
Application Layer (Hooks)
         ↓
Service Layer (expeditionApi, websocketService)
         ↓
Transport Layer (Axios, Socket.io)
         ↓
Backend API (Flask)
```

---

## API Service (`expeditionApi`)

### Overview

**Location**: `src/services/expeditionApi.ts`

The `ExpeditionApiService` class provides:
- Type-safe HTTP client
- Automatic authentication header injection
- Centralized error handling
- Environment-aware configuration
- Request/response interceptors

### Architecture

```typescript
class ExpeditionApiService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    // Environment-aware base URL
    const envApiUrl = import.meta.env.VITE_API_URL;

    if (import.meta.env.DEV && !envApiUrl) {
      this.baseURL = ''; // Use Vite proxy in dev
    } else {
      this.baseURL = envApiUrl || window.location.origin;
    }

    // Create Axios instance
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: { 'Content-Type': 'application/json' },
    });

    // Setup interceptors
    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor: Add auth headers
    this.api.interceptors.request.use((config) => {
      const authHeaders = getAuthHeaders();
      Object.assign(config.headers, authHeaders);
      return config;
    });

    // Response interceptor: Handle errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        throw error;
      }
    );
  }

  // API methods...
}

// Export singleton instance
export const expeditionApi = new ExpeditionApiService();
```

---

## API Methods

### Expedition CRUD

#### Get All Expeditions
```typescript
async getExpeditions(): Promise<Expedition[]> {
  const response = await this.api.get<{ expeditions: Expedition[] }>('/api/expeditions');
  return response.data.expeditions;
}
```

**Usage**:
```typescript
const expeditions = await expeditionApi.getExpeditions();
// Returns: Expedition[]
```

#### Get Expedition by ID
```typescript
async getExpeditionById(id: number): Promise<ExpeditionDetails> {
  const response = await this.api.get<ExpeditionDetails>(`/api/expeditions/${id}`);
  return response.data;
}
```

**Usage**:
```typescript
const expedition = await expeditionApi.getExpeditionById(1);
// Returns: ExpeditionDetails (includes items, consumptions, pirate names)
```

#### Create Expedition
```typescript
async createExpedition(data: CreateExpeditionRequest): Promise<Expedition> {
  const response = await this.api.post<Expedition>('/api/expeditions', data);
  return response.data;
}
```

**Usage**:
```typescript
const newExpedition = await expeditionApi.createExpedition({
  name: 'Treasure Hunt',
  description: 'Find the lost treasure',
  deadline_days: 30,
  items: [
    { product_id: 1, quantity: 10, target_price: 25.00 }
  ]
});
// Returns: Expedition
```

#### Update Expedition Status
```typescript
async updateExpeditionStatus(id: number, status: string): Promise<Expedition> {
  const response = await this.api.put<Expedition>(`/api/expeditions/${id}`, { status });
  return response.data;
}
```

**Usage**:
```typescript
const updated = await expeditionApi.updateExpeditionStatus(1, 'completed');
// Returns: Expedition
```

#### Delete Expedition
```typescript
async deleteExpedition(id: number): Promise<void> {
  await this.api.delete(`/api/expeditions/${id}`);
}
```

**Usage**:
```typescript
await expeditionApi.deleteExpedition(1);
// Returns: void (throws on error)
```

---

### Expedition Items

#### Get Items for Expedition
```typescript
async getExpeditionItems(expeditionId: number): Promise<ExpeditionItem[]> {
  const response = await this.api.get<{ items: ExpeditionItem[] }>(
    `/api/expeditions/${expeditionId}/items`
  );
  return response.data.items;
}
```

#### Add Items to Expedition
```typescript
async addItemsToExpedition(
  expeditionId: number,
  data: CreateExpeditionItemRequest
): Promise<ExpeditionItem[]> {
  const response = await this.api.post<{ items: ExpeditionItem[] }>(
    `/api/expeditions/${expeditionId}/items`,
    data
  );
  return response.data.items;
}
```

**Usage**:
```typescript
const items = await expeditionApi.addItemsToExpedition(1, {
  items: [
    { product_id: 2, quantity: 5, target_price: 15.00 }
  ]
});
// Returns: ExpeditionItem[]
```

---

### Item Consumption

#### Consume Item
```typescript
async consumeItem(
  expeditionId: number,
  data: ConsumeItemRequest
): Promise<ItemConsumption> {
  const response = await this.api.post<ItemConsumption>(
    `/api/expeditions/${expeditionId}/consume`,
    data
  );
  return response.data;
}
```

**Usage**:
```typescript
const consumption = await expeditionApi.consumeItem(1, {
  item_id: 5,
  consumer_name: 'Jack Sparrow',
  quantity: 2,
  price_paid: 30.00,
  payment_status: 'pending'
});
// Returns: ItemConsumption
```

#### Get Consumptions
```typescript
async getConsumptions(params?: {
  consumer_name?: string;
  payment_status?: string;
}): Promise<ItemConsumption[]> {
  const response = await this.api.get<{ consumptions: ItemConsumption[] }>(
    '/api/expeditions/consumptions',
    { params }
  );
  return response.data.consumptions;
}
```

**Usage**:
```typescript
// Get all consumptions
const allConsumptions = await expeditionApi.getConsumptions();

// Filter by consumer
const jackConsumptions = await expeditionApi.getConsumptions({
  consumer_name: 'Jack Sparrow'
});

// Filter by payment status
const pendingConsumptions = await expeditionApi.getConsumptions({
  payment_status: 'pending'
});
```

---

### Brambler (Pirate Name Anonymization)

#### Generate Pirate Names
```typescript
async generatePirateNames(
  expeditionId: number,
  data: BramblerGenerateRequest
): Promise<PirateName[]> {
  const response = await this.api.post<{ pirate_names: PirateName[] }>(
    `/api/brambler/generate/${expeditionId}`,
    data
  );
  return response.data.pirate_names;
}
```

**Usage**:
```typescript
const pirateNames = await expeditionApi.generatePirateNames(1, {
  real_names: ['Alice', 'Bob', 'Charlie'],
  owner_key: 'secret-encryption-key'
});
// Returns: PirateName[] with encrypted mappings
```

#### Decrypt Pirate Names
```typescript
async decryptPirateNames(
  expeditionId: number,
  data: BramblerDecryptRequest
): Promise<Record<string, string>> {
  const response = await this.api.post<{ decrypted_mapping: Record<string, string> }>(
    `/api/brambler/decrypt/${expeditionId}`,
    data
  );
  return response.data.decrypted_mapping;
}
```

**Usage**:
```typescript
const mapping = await expeditionApi.decryptPirateNames(1, {
  owner_key: 'secret-encryption-key'
});
// Returns: { 'Captain Blackbeard': 'Alice', 'Pirate Pete': 'Bob' }
```

#### Get Pirate Names
```typescript
async getPirateNames(expeditionId: number): Promise<PirateName[]> {
  const response = await this.api.get<{ pirate_names: PirateName[] }>(
    `/api/brambler/names/${expeditionId}`
  );
  return response.data.pirate_names;
}
```

---

### Dashboard & Analytics

#### Get Dashboard Timeline
```typescript
async getDashboardTimeline(): Promise<TimelineData> {
  const response = await this.api.get<TimelineData>('/api/dashboard/timeline');
  return response.data;
}
```

**Returns**:
```typescript
interface TimelineData {
  active_expeditions: number;
  completed_expeditions: number;
  total_revenue: number;
  total_profit: number;
  timeline_entries: TimelineEntry[];
}
```

#### Get Overdue Expeditions
```typescript
async getOverdueExpeditions(): Promise<OverdueData> {
  const response = await this.api.get('/api/dashboard/overdue');
  return response.data;
}
```

#### Get Analytics
```typescript
async getAnalytics(): Promise<AnalyticsData> {
  const response = await this.api.get<AnalyticsData>('/api/dashboard/analytics');
  return response.data;
}
```

**Returns**:
```typescript
interface AnalyticsData {
  total_expeditions: number;
  total_items: number;
  total_consumptions: number;
  total_revenue: number;
  total_profit: number;
  avg_profit_margin: number;
  top_products: Array<{ product_name: string; total_quantity: number }>;
  top_consumers: Array<{ consumer_name: string; total_spent: number }>;
}
```

---

### Products & Users

#### Get Products
```typescript
async getProducts(): Promise<Product[]> {
  const response = await this.api.get<{ products: Product[] }>('/api/products');
  return response.data.products;
}
```

#### Get Users
```typescript
async getUsers(): Promise<User[]> {
  const response = await this.api.get<{ users: User[] }>('/api/users');
  return response.data.users;
}
```

#### Get Buyers
```typescript
async getBuyers(): Promise<{ name: string }[]> {
  const response = await this.api.get<{ buyers: { name: string }[] }>('/api/buyers');
  return response.data.buyers;
}
```

---

### Export Functionality

#### Export Expedition Data
```typescript
async exportExpeditionData(params?: {
  expedition_id?: number;
  status?: string;
  date_from?: string;
  date_to?: string;
}): Promise<{ file_path: string; filename: string; download_url: string }> {
  const response = await this.api.get('/api/expeditions/export', { params });
  return response.data;
}
```

**Usage**:
```typescript
const exportResult = await expeditionApi.exportExpeditionData({
  expedition_id: 1,
  status: 'completed'
});
// Returns: { file_path: '...', filename: 'expedition_1.csv', download_url: '/exports/...' }

// Download the file
const blob = await expeditionApi.downloadFile(exportResult.download_url);
```

#### Export Pirate Activity Report
```typescript
async exportPirateActivityReport(params?: {
  expedition_id?: number;
  anonymized?: boolean;
  date_from?: string;
  date_to?: string;
}): Promise<ExportResult> {
  const response = await this.api.get('/api/expeditions/reports/pirate-activity', { params });
  return response.data;
}
```

#### Export Profit/Loss Report
```typescript
async exportProfitLossReport(params?: {
  expedition_id?: number;
  date_from?: string;
  date_to?: string;
}): Promise<ExportResult> {
  const response = await this.api.get('/api/expeditions/reports/profit-loss', { params });
  return response.data;
}
```

---

### Search

#### Search Expeditions
```typescript
async searchExpeditions(params: {
  q?: string;
  status?: string;
  owner_chat_id?: number;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_order?: string;
  limit?: number;
  offset?: number;
}): Promise<SearchResults> {
  const response = await this.api.get('/api/expeditions/search', { params });
  return response.data;
}
```

**Usage**:
```typescript
const results = await expeditionApi.searchExpeditions({
  q: 'treasure',
  status: 'active',
  sort_by: 'created_at',
  sort_order: 'desc',
  limit: 10,
  offset: 0
});
// Returns: { results: Expedition[], total_count: number, has_more: boolean }
```

---

### Utilities

#### Health Check
```typescript
async healthCheck(): Promise<HealthStatus> {
  const response = await this.api.get('/health');
  return response.data;
}
```

#### Download File
```typescript
async downloadFile(url: string): Promise<Blob> {
  const response = await this.api.get(url, { responseType: 'blob' });
  return response.data;
}
```

**Usage**:
```typescript
const blob = await expeditionApi.downloadFile('/exports/expedition_1.csv');

// Create download link
const url = window.URL.createObjectURL(blob);
const link = document.createElement('a');
link.href = url;
link.download = 'expedition_1.csv';
link.click();
window.URL.revokeObjectURL(url);
```

#### Get Full URL
```typescript
getFullUrl(path: string): string {
  return `${this.baseURL}${path}`;
}
```

---

## WebSocket Service (`websocketService`)

### Overview

**Location**: `src/services/websocketService.ts`

The WebSocket service provides:
- Real-time bi-directional communication
- Room-based subscriptions
- Automatic reconnection
- Event-driven architecture
- Connection status tracking

### Architecture

```typescript
class WebSocketService {
  private socket: Socket | null = null;
  private listeners: Map<string, Set<Function>> = new Map();
  private connected: boolean = false;

  connect(): void {
    // Initialize Socket.io connection
    this.socket = io(WEBSOCKET_URL, {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    // Connection events
    this.socket.on('connect', () => {
      this.connected = true;
      this.notifyListeners('connection_status', { connected: true });
    });

    this.socket.on('disconnect', () => {
      this.connected = false;
      this.notifyListeners('connection_status', { connected: false });
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  isConnected(): boolean {
    return this.connected;
  }

  // Room management
  joinRoom(room: string): void {
    if (this.socket) {
      this.socket.emit('join_room', { room });
    }
  }

  leaveRoom(room: string): void {
    if (this.socket) {
      this.socket.emit('leave_room', { room });
    }
  }

  // Event subscription
  on(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);

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

  // Emit events
  emit(event: string, data: any): void {
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }

  private notifyListeners(event: string, data: any): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(callback => callback(data));
    }
  }
}

export const websocketService = new WebSocketService();
```

### Events

#### Server → Client Events

**Connection Events**:
- `connect` - WebSocket connection established
- `disconnect` - WebSocket connection lost
- `connection_status` - Connection status changed

**Expedition Events**:
- `expedition_created` - New expedition created
- `expedition_updated` - Expedition status/details changed
- `expedition_completed` - Expedition marked as completed
- `expedition_deleted` - Expedition deleted

**Item Events**:
- `item_consumed` - Item consumed from expedition
- `item_added` - Item added to expedition
- `item_updated` - Item details updated

**Pirate Events**:
- `pirate_names_generated` - Pirate names generated for expedition
- `pirate_name_revealed` - Pirate name decrypted

### Usage Example

```typescript
import { websocketService } from '@/services/websocketService';

// Connect to WebSocket
websocketService.connect();

// Subscribe to events
const handleExpeditionUpdate = (data: any) => {
  console.log('Expedition updated:', data);
  // Refresh expedition list
};

websocketService.on('expedition_updated', handleExpeditionUpdate);

// Join expedition room for updates
websocketService.joinRoom('expedition_1');

// Cleanup
useEffect(() => {
  return () => {
    websocketService.off('expedition_updated', handleExpeditionUpdate);
    websocketService.leaveRoom('expedition_1');
  };
}, []);
```

---

## Error Handling

### API Error Responses

All API errors follow this structure:

```typescript
interface ApiError {
  error: string;           // Error message
  details?: any;           // Additional error details
  status_code?: number;    // HTTP status code
}
```

### Common HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate)
- `500 Internal Server Error` - Server error

### Error Handling Pattern

```typescript
try {
  const expedition = await expeditionApi.getExpeditionById(id);
  // Success
} catch (error) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 404) {
      console.error('Expedition not found');
    } else if (error.response?.status === 401) {
      console.error('Unauthorized - please log in');
    } else {
      console.error('API Error:', error.response?.data?.error || error.message);
    }
  } else {
    console.error('Unexpected error:', error);
  }
}
```

---

## Authentication

### Telegram Mini App Authentication

The API service automatically injects Telegram authentication headers via the request interceptor:

```typescript
// In expeditionApi.ts
this.api.interceptors.request.use((config) => {
  const authHeaders = getAuthHeaders();
  Object.assign(config.headers, authHeaders);
  return config;
});
```

### Auth Headers (from Telegram SDK)

```typescript
// src/utils/telegram.ts
export const getAuthHeaders = (): Record<string, string> => {
  const initData = retrieveLaunchParams().initDataRaw;

  return {
    'X-Telegram-Init-Data': initData || '',
  };
};
```

The backend validates these headers to authenticate requests.

---

## Environment Configuration

### Development (Vite Proxy)

**vite.config.ts**:
```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      }
    }
  }
});
```

**API Base URL**: Empty string (relative URLs use Vite proxy)

### Production

**Environment Variable**: `VITE_API_URL`

**Example `.env.production`**:
```
VITE_API_URL=https://api.myapp.com
```

**API Base URL**: `https://api.myapp.com`

---

## Best Practices

### 1. Always Use Type-Safe Methods

```typescript
// GOOD - type-safe
const expeditions: Expedition[] = await expeditionApi.getExpeditions();

// BAD - bypasses type safety
const expeditions = await axios.get('/api/expeditions');
```

### 2. Handle Errors Gracefully

```typescript
// GOOD - handles all error cases
try {
  const expedition = await expeditionApi.getExpeditionById(id);
  return expedition;
} catch (error) {
  console.error('Failed to fetch expedition:', error);
  return null; // or throw with user-friendly message
}

// BAD - no error handling
const expedition = await expeditionApi.getExpeditionById(id);
```

### 3. Use Service Layer from Hooks Only

```typescript
// GOOD - service called from hook
const useExpeditionDetails = (id: number) => {
  const [expedition, setExpedition] = useState(null);

  useEffect(() => {
    expeditionApi.getExpeditionById(id).then(setExpedition);
  }, [id]);

  return expedition;
};

// BAD - service called directly in component
const ExpeditionDetails = ({ id }) => {
  const [expedition, setExpedition] = useState(null);

  useEffect(() => {
    expeditionApi.getExpeditionById(id).then(setExpedition);
  }, [id]);

  return <div>{expedition?.name}</div>;
};
```

### 4. Clean Up WebSocket Listeners

```typescript
// GOOD - cleanup in useEffect
useEffect(() => {
  const handleUpdate = (data) => {
    console.log('Update:', data);
  };

  websocketService.on('expedition_updated', handleUpdate);

  return () => {
    websocketService.off('expedition_updated', handleUpdate);
  };
}, []);

// BAD - no cleanup (memory leak!)
useEffect(() => {
  websocketService.on('expedition_updated', (data) => {
    console.log('Update:', data);
  });
}, []);
```

---

## Summary

The service layer provides:

1. **Type Safety**: Full TypeScript types for all API methods
2. **Centralized Configuration**: Single source of truth for API setup
3. **Authentication**: Automatic header injection
4. **Error Handling**: Consistent error handling across the app
5. **Environment Awareness**: Different configurations for dev/prod
6. **Real-Time Updates**: WebSocket integration for live data

**Remember**: Always use the service layer (expeditionApi, websocketService) instead of calling Axios or Socket.io directly.

For more information, see:
- [Architecture Documentation](./ARCHITECTURE.md)
- [Hook Composition Guide](./HOOK_COMPOSITION.md)
- [Testing Guide](./TESTING.md)
