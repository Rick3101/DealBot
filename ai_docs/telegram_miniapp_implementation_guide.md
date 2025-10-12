# 🏴‍☠️ Pirates Expedition Mini App Implementation Guide

## Overview

This comprehensive guide details how to transform the existing Python Telegram bot into a **Telegram Mini App** with a React frontend, providing a rich visual interface for the pirates expedition management system while preserving all current bot functionality.

---

## 🎯 1. Mini App Setup & Integration

### 1.1 Telegram Mini App Configuration

#### Bot Configuration Changes
Add to your `BotFather` configuration:

```bash
# Set Mini App URL for your bot
/setmenubutton
@YourBotName
text: 🏴‍☠️ Pirates Dashboard
url: https://your-domain.com/miniapp
```

#### Mini App Authentication Flow
```python
# Add to app.py - Mini App Authentication
from telegram.constants import ParseMode
import hashlib
import hmac
import json
from urllib.parse import unquote

@app.route("/miniapp")
def miniapp():
    """Serve Mini App entry point."""
    return render_template('miniapp.html')

@app.route("/api/auth/telegram", methods=["POST"])
def authenticate_miniapp():
    """Validate Telegram Mini App authentication."""
    try:
        data = request.get_json()
        init_data = data.get('initData')

        if not init_data:
            return jsonify({"error": "Missing initData"}), 400

        # Validate initData signature
        if not validate_telegram_init_data(init_data):
            return jsonify({"error": "Invalid authentication"}), 401

        # Extract user data
        user_data = extract_user_from_init_data(init_data)

        # Get user permissions from existing system
        from core.modern_service_container import get_user_service
        user_service = get_user_service(None)
        user_level = user_service.get_user_permission_level(user_data['id'])

        if not user_level:
            return jsonify({"error": "User not authenticated in bot"}), 401

        # Generate session token
        session_token = generate_session_token(user_data['id'])

        return jsonify({
            "success": True,
            "user": {
                "id": user_data['id'],
                "username": user_data.get('username'),
                "first_name": user_data.get('first_name'),
                "permission_level": user_level.value
            },
            "session_token": session_token
        })

    except Exception as e:
        logger.error(f"Mini App auth error: {e}")
        return jsonify({"error": "Authentication failed"}), 500

def validate_telegram_init_data(init_data: str) -> bool:
    """Validate Telegram Mini App initData signature."""
    try:
        # Parse init data
        data_pairs = [pair.split('=', 1) for pair in init_data.split('&')]
        data_dict = {k: unquote(v) for k, v in data_pairs}

        # Extract and remove hash
        received_hash = data_dict.pop('hash', '')

        # Create data check string
        data_check_items = [f"{k}={v}" for k, v in sorted(data_dict.items())]
        data_check_string = '\n'.join(data_check_items)

        # Calculate hash
        secret_key = hmac.new(
            "WebAppData".encode(),
            self.config.telegram.bot_token.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        return calculated_hash == received_hash

    except Exception as e:
        logger.error(f"Init data validation error: {e}")
        return False

def extract_user_from_init_data(init_data: str) -> dict:
    """Extract user data from initData."""
    data_pairs = [pair.split('=', 1) for pair in init_data.split('&')]
    data_dict = {k: unquote(v) for k, v in data_pairs}

    user_json = data_dict.get('user', '{}')
    return json.loads(user_json)

def generate_session_token(user_id: int) -> str:
    """Generate session token for Mini App."""
    import jwt
    import time

    payload = {
        'user_id': user_id,
        'iat': int(time.time()),
        'exp': int(time.time()) + 86400  # 24 hours
    }

    return jwt.encode(payload, self.config.telegram.bot_token, algorithm='HS256')
```

### 1.2 React Project Setup

#### Initialize React TypeScript Project
```bash
# Create React app with TypeScript and Vite
npm create vite@latest pirates-miniapp -- --template react-ts
cd pirates-miniapp

# Install required dependencies
npm install @telegram-apps/sdk
npm install @tanstack/react-query
npm install react-router-dom
npm install styled-components
npm install @types/styled-components
npm install recharts
npm install socket.io-client
npm install date-fns
npm install react-hook-form
npm install @hookform/resolvers yup

# Install pirate-themed dependencies
npm install animate.css
npm install @fontsource/pirata-one
npm install @fontsource/roboto
```

#### Telegram Mini App Integration
```typescript
// src/telegram/telegramApp.ts
import { initInitData, initViewport, postEvent } from '@telegram-apps/sdk';

class TelegramApp {
  private initData: any = null;

  async initialize(): Promise<boolean> {
    try {
      // Initialize Telegram Mini App SDK
      const [initDataResult] = await Promise.allSettled([
        initInitData(),
        initViewport()
      ]);

      if (initDataResult.status === 'fulfilled') {
        this.initData = initDataResult.value;

        // Set viewport properties
        postEvent('web_app_expand');
        postEvent('web_app_setup_main_button', { is_visible: false });

        return true;
      }

      return false;
    } catch (error) {
      console.error('Telegram App initialization failed:', error);
      return false;
    }
  }

  getInitData(): string | null {
    return this.initData?.raw || null;
  }

  getUserData() {
    return this.initData?.user || null;
  }

  showMainButton(text: string, callback: () => void) {
    postEvent('web_app_setup_main_button', {
      is_visible: true,
      text: text
    });

    // Store callback for main button clicks
    window.addEventListener('telegram-web-app-main-button-clicked', callback);
  }

  hideMainButton() {
    postEvent('web_app_setup_main_button', { is_visible: false });
  }

  close() {
    postEvent('web_app_close');
  }

  hapticFeedback(type: 'impact' | 'notification' | 'selection' = 'impact') {
    postEvent('web_app_trigger_haptic_feedback', { type });
  }
}

export const telegramApp = new TelegramApp();
```

---

## 🔧 2. Backend API Adaptations

### 2.1 Mini App Specific Endpoints

#### Enhanced Authentication Middleware
```python
# Add to app.py - Mini App middleware
from functools import wraps
import jwt

def require_miniapp_auth(f):
    """Decorator to require Mini App authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401

        token = auth_header.split(' ')[1]

        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            request.miniapp_user_id = payload['user_id']
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

    return decorated_function

# Enhanced expedition endpoints for Mini App
@app.route("/api/miniapp/expeditions/dashboard", methods=["GET"])
@require_miniapp_auth
def miniapp_expeditions_dashboard():
    """Mini App specific expedition dashboard."""
    try:
        user_id = request.miniapp_user_id

        from core.modern_service_container import get_expedition_service, get_user_service
        expedition_service = get_expedition_service()
        user_service = get_user_service(None)

        # Get user permission level
        user_level = user_service.get_user_permission_level(user_id)

        if user_level.value == 'owner':
            expeditions = expedition_service.get_all_expeditions()
        else:
            expeditions = expedition_service.get_expeditions_by_owner(user_id)

        # Enhanced data for Mini App
        dashboard_data = {
            "expeditions": [],
            "stats": {
                "total_expeditions": len(expeditions),
                "active_expeditions": 0,
                "completed_expeditions": 0,
                "overdue_expeditions": 0,
                "total_value": 0.0,
                "consumed_value": 0.0
            },
            "recent_activity": [],
            "overdue_alerts": []
        }

        current_time = datetime.now()

        for expedition in expeditions:
            expedition_response = expedition_service.get_expedition_response(expedition.id)

            # Check if overdue
            is_overdue = (
                expedition.deadline and
                expedition.deadline < current_time and
                expedition.status.value == 'active'
            )

            expedition_data = {
                "id": expedition.id,
                "name": expedition.name,
                "owner_chat_id": expedition.owner_chat_id,
                "status": expedition.status.value,
                "deadline": expedition.deadline.isoformat() if expedition.deadline else None,
                "created_at": expedition.created_at.isoformat() if expedition.created_at else None,
                "completed_at": expedition.completed_at.isoformat() if expedition.completed_at else None,
                "is_overdue": is_overdue,
                "days_remaining": (expedition.deadline.date() - current_time.date()).days if expedition.deadline else None,
                "progress": {
                    "completion_percentage": expedition_response.completion_percentage if expedition_response else 0,
                    "total_items": expedition_response.total_items if expedition_response else 0,
                    "consumed_items": expedition_response.consumed_items if expedition_response else 0,
                    "remaining_items": expedition_response.remaining_items if expedition_response else 0,
                    "total_value": float(expedition_response.total_value) if expedition_response else 0.0,
                    "consumed_value": float(expedition_response.consumed_value) if expedition_response else 0.0,
                    "remaining_value": float(expedition_response.remaining_value) if expedition_response else 0.0
                }
            }

            dashboard_data["expeditions"].append(expedition_data)

            # Update stats
            if expedition.status.value == 'active':
                dashboard_data["stats"]["active_expeditions"] += 1
                if is_overdue:
                    dashboard_data["stats"]["overdue_expeditions"] += 1
                    dashboard_data["overdue_alerts"].append({
                        "expedition_id": expedition.id,
                        "expedition_name": expedition.name,
                        "days_overdue": abs((expedition.deadline.date() - current_time.date()).days)
                    })
            elif expedition.status.value == 'completed':
                dashboard_data["stats"]["completed_expeditions"] += 1

            if expedition_response:
                dashboard_data["stats"]["total_value"] += float(expedition_response.total_value)
                dashboard_data["stats"]["consumed_value"] += float(expedition_response.consumed_value)

        # Sort expeditions by priority (overdue first, then by deadline)
        dashboard_data["expeditions"].sort(key=lambda x: (
            not x["is_overdue"],
            x["deadline"] or "9999-12-31"
        ))

        return jsonify(dashboard_data)

    except Exception as e:
        logger.error(f"Mini App dashboard error: {e}")
        return jsonify({"error": "Failed to load dashboard"}), 500

@app.route("/api/miniapp/expeditions/<int:expedition_id>/realtime", methods=["GET"])
@require_miniapp_auth
def miniapp_expedition_realtime(expedition_id: int):
    """Real-time expedition data for Mini App."""
    try:
        user_id = request.miniapp_user_id

        from core.modern_service_container import get_expedition_service, get_brambler_service
        expedition_service = get_expedition_service()
        brambler_service = get_brambler_service()

        # Get expedition with full details
        expedition_response = expedition_service.get_expedition_response(expedition_id)

        if not expedition_response:
            return jsonify({"error": "Expedition not found"}), 404

        # Check access permission
        expedition = expedition_response.expedition
        user_level = get_user_service(None).get_user_permission_level(user_id)

        if expedition.owner_chat_id != user_id and user_level.value not in ['owner', 'admin']:
            return jsonify({"error": "Access denied"}), 403

        # Get pirate names (anonymized for non-owners)
        pirate_names = brambler_service.get_expedition_pirate_names(expedition_id)
        show_real_names = expedition.owner_chat_id == user_id or user_level.value == 'owner'

        pirates_data = []
        for pirate in pirate_names:
            pirates_data.append({
                "id": pirate.id,
                "pirate_name": pirate.pirate_name,
                "original_name": pirate.original_name if show_real_names else None,
                "created_at": pirate.created_at.isoformat() if pirate.created_at else None
            })

        # Enhanced real-time data
        realtime_data = {
            "expedition": {
                "id": expedition.id,
                "name": expedition.name,
                "status": expedition.status.value,
                "deadline": expedition.deadline.isoformat() if expedition.deadline else None,
                "created_at": expedition.created_at.isoformat() if expedition.created_at else None
            },
            "progress": {
                "completion_percentage": expedition_response.completion_percentage,
                "total_items": expedition_response.total_items,
                "consumed_items": expedition_response.consumed_items,
                "remaining_items": expedition_response.remaining_items,
                "total_value": float(expedition_response.total_value),
                "consumed_value": float(expedition_response.consumed_value),
                "remaining_value": float(expedition_response.remaining_value)
            },
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "product_emoji": item.product_emoji,
                    "quantity_needed": item.quantity_needed,
                    "unit_price": float(item.unit_price),
                    "added_at": item.added_at.isoformat() if item.added_at else None
                } for item in expedition_response.items
            ],
            "pirates": pirates_data,
            "recent_consumptions": [
                {
                    "id": consumption.id,
                    "consumer_name": consumption.consumer_name,
                    "product_name": consumption.product_name,
                    "quantity": consumption.quantity,
                    "unit_price": float(consumption.unit_price),
                    "total_price": float(consumption.total_price),
                    "payment_status": consumption.payment_status.value,
                    "consumed_at": consumption.consumed_at.isoformat() if consumption.consumed_at else None
                } for consumption in expedition_response.consumptions[-10:]  # Last 10 consumptions
            ],
            "last_updated": datetime.now().isoformat()
        }

        return jsonify(realtime_data)

    except Exception as e:
        logger.error(f"Mini App realtime error: {e}")
        return jsonify({"error": "Failed to load expedition data"}), 500
```

### 2.2 WebSocket Integration for Real-time Updates

#### Enhanced WebSocket Events for Mini App
```python
# Add to existing WebSocket configuration in app.py

@socketio.on('miniapp_join_expedition')
def handle_miniapp_join_expedition(data):
    """Handle Mini App client joining expedition room."""
    try:
        expedition_id = data.get('expedition_id')
        session_token = data.get('session_token')

        if not expedition_id or not session_token:
            emit('error', {'message': 'Missing expedition_id or session_token'})
            return

        # Validate session token
        try:
            payload = jwt.decode(
                session_token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            user_id = payload['user_id']
        except jwt.InvalidTokenError:
            emit('error', {'message': 'Invalid session token'})
            return

        # Verify expedition access
        from core.modern_service_container import get_expedition_service, get_user_service
        expedition_service = get_expedition_service()
        user_service = get_user_service(None)

        expedition = expedition_service.get_expedition_by_id(expedition_id)
        user_level = user_service.get_user_permission_level(user_id)

        if not expedition:
            emit('error', {'message': 'Expedition not found'})
            return

        # Check access permission
        has_access = (
            expedition.owner_chat_id == user_id or
            user_level.value in ['owner', 'admin']
        )

        if not has_access:
            emit('error', {'message': 'Access denied'})
            return

        # Join expedition room
        room_name = f"expedition_{expedition_id}"
        join_room(room_name)

        # Subscribe to updates
        websocket_service = get_websocket_service()
        websocket_service.subscribe_to_expedition(user_id, expedition_id)

        logger.info(f"Mini App user {user_id} joined expedition {expedition_id}")
        emit('expedition_joined', {
            'expedition_id': expedition_id,
            'room': room_name,
            'user_id': user_id
        })

        # Send initial expedition data
        initial_data = get_expedition_realtime_data(expedition_id)
        emit('expedition_update', initial_data)

    except Exception as e:
        logger.error(f"Mini App join expedition error: {e}")
        emit('error', {'message': 'Failed to join expedition'})

def get_expedition_realtime_data(expedition_id: int) -> dict:
    """Get real-time expedition data for WebSocket updates."""
    try:
        from core.modern_service_container import get_expedition_service
        expedition_service = get_expedition_service()

        expedition_response = expedition_service.get_expedition_response(expedition_id)

        if not expedition_response:
            return {}

        return {
            "expedition_id": expedition_id,
            "progress": {
                "completion_percentage": expedition_response.completion_percentage,
                "consumed_items": expedition_response.consumed_items,
                "remaining_items": expedition_response.remaining_items,
                "consumed_value": float(expedition_response.consumed_value),
                "remaining_value": float(expedition_response.remaining_value)
            },
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting realtime data: {e}")
        return {}

# Enhanced notification system for Mini App
def notify_miniapp_expedition_update(expedition_id: int, update_type: str, data: dict):
    """Send expedition updates to Mini App clients."""
    try:
        room_name = f"expedition_{expedition_id}"

        update_payload = {
            "type": update_type,
            "expedition_id": expedition_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        socketio.emit('expedition_update', update_payload, room=room_name)

        logger.info(f"Sent Mini App update to expedition {expedition_id}: {update_type}")

    except Exception as e:
        logger.error(f"Error sending Mini App update: {e}")
```

---

## ⚛️ 3. Frontend Architecture Implementation

### 3.1 App Structure and Routing

#### Main App Component
```typescript
// src/App.tsx
import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'styled-components';
import { telegramApp } from './telegram/telegramApp';
import { AuthProvider } from './contexts/AuthContext';
import { pirateTheme } from './utils/pirateTheme';
import { Dashboard } from './pages/Dashboard';
import { ExpeditionDetails } from './pages/ExpeditionDetails';
import { CreateExpedition } from './pages/CreateExpedition';
import { BramblerManager } from './pages/BramblerManager';
import { LoadingScreen } from './components/ui/LoadingScreen';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import './styles/pirates.css';
import '@fontsource/pirata-one';
import '@fontsource/roboto';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 30000, // 30 seconds
      refetchOnWindowFocus: false
    }
  }
});

function App() {
  const [isInitialized, setIsInitialized] = useState(false);
  const [initError, setInitError] = useState<string | null>(null);

  useEffect(() => {
    const initializeApp = async () => {
      try {
        const success = await telegramApp.initialize();
        if (success) {
          setIsInitialized(true);
        } else {
          setInitError('Failed to initialize Telegram Mini App');
        }
      } catch (error) {
        console.error('App initialization error:', error);
        setInitError('Initialization error occurred');
      }
    };

    initializeApp();
  }, []);

  if (initError) {
    return (
      <div className="pirate-error">
        <h1>💀 Initialization Error</h1>
        <p>{initError}</p>
      </div>
    );
  }

  if (!isInitialized) {
    return <LoadingScreen message="🏴‍☠️ Loading Pirates Dashboard..." />;
  }

  return (
    <ErrorBoundary>
      <ThemeProvider theme={pirateTheme}>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <Router>
              <div className="pirates-app">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/expedition/:id" element={<ExpeditionDetails />} />
                  <Route path="/create-expedition" element={<CreateExpedition />} />
                  <Route path="/brambler" element={<BramblerManager />} />
                </Routes>
              </div>
            </Router>
          </AuthProvider>
        </QueryClientProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
```

#### Authentication Context
```typescript
// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { telegramApp } from '../telegram/telegramApp';
import { authService } from '../services/authService';

interface User {
  id: number;
  username?: string;
  first_name?: string;
  permission_level: 'user' | 'admin' | 'owner';
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  sessionToken: string | null;
  login: () => Promise<boolean>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const login = async (): Promise<boolean> => {
    try {
      setLoading(true);

      const initData = telegramApp.getInitData();
      if (!initData) {
        throw new Error('No Telegram init data available');
      }

      const response = await authService.authenticateWithTelegram(initData);

      if (response.success) {
        setUser(response.user);
        setSessionToken(response.session_token);

        // Store session token for API requests
        localStorage.setItem('pirates_session_token', response.session_token);

        return true;
      }

      return false;
    } catch (error) {
      console.error('Authentication error:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setSessionToken(null);
    localStorage.removeItem('pirates_session_token');
  };

  useEffect(() => {
    const initAuth = async () => {
      // Try to restore session from localStorage
      const storedToken = localStorage.getItem('pirates_session_token');
      if (storedToken) {
        try {
          // Validate stored token
          const userData = await authService.validateSession(storedToken);
          if (userData) {
            setUser(userData);
            setSessionToken(storedToken);
            setLoading(false);
            return;
          }
        } catch (error) {
          console.error('Session validation error:', error);
          localStorage.removeItem('pirates_session_token');
        }
      }

      // No valid session, attempt login
      await login();
    };

    initAuth();
  }, []);

  const isAuthenticated = !!user && !!sessionToken;

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated,
      sessionToken,
      login,
      logout,
      loading
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

### 3.2 Core Services

#### API Service
```typescript
// src/services/apiService.ts
class ApiService {
  private baseUrl: string;
  private sessionToken: string | null = null;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://your-domain.com';
  }

  setSessionToken(token: string) {
    this.sessionToken = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.sessionToken) {
      headers['Authorization'] = `Bearer ${this.sessionToken}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Authentication
  async authenticateWithTelegram(initData: string) {
    return this.request<{
      success: boolean;
      user: any;
      session_token: string;
    }>('/api/auth/telegram', {
      method: 'POST',
      body: JSON.stringify({ initData }),
    });
  }

  async validateSession(token: string) {
    this.setSessionToken(token);
    return this.request<any>('/api/auth/validate');
  }

  // Expeditions
  async getExpeditionsDashboard() {
    return this.request<{
      expeditions: any[];
      stats: any;
      recent_activity: any[];
      overdue_alerts: any[];
    }>('/api/miniapp/expeditions/dashboard');
  }

  async getExpeditionDetails(expeditionId: number) {
    return this.request<any>(`/api/expeditions/${expeditionId}`);
  }

  async getExpeditionRealtime(expeditionId: number) {
    return this.request<any>(`/api/miniapp/expeditions/${expeditionId}/realtime`);
  }

  async createExpedition(data: {
    name: string;
    deadline: string;
  }) {
    return this.request<any>('/api/expeditions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateExpeditionStatus(expeditionId: number, status: string) {
    return this.request<any>(`/api/expeditions/${expeditionId}`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  }

  // Expedition Items
  async addExpeditionItems(expeditionId: number, items: any[]) {
    return this.request<any>(`/api/expeditions/${expeditionId}/items`, {
      method: 'POST',
      body: JSON.stringify({ items }),
    });
  }

  async consumeExpeditionItem(expeditionId: number, data: {
    product_id: number;
    quantity: number;
  }) {
    return this.request<any>(`/api/expeditions/${expeditionId}/consume`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Brambler (Pirate Names)
  async generatePirateNames(expeditionId: number, originalNames: string[]) {
    return this.request<any>(`/api/brambler/generate/${expeditionId}`, {
      method: 'POST',
      body: JSON.stringify({ original_names: originalNames }),
    });
  }

  async getPirateNames(expeditionId: number) {
    return this.request<any>(`/api/brambler/names/${expeditionId}`);
  }

  async decryptPirateNames(expeditionId: number, data: {
    encrypted_mapping: string;
    owner_key: string;
  }) {
    return this.request<any>(`/api/brambler/decrypt/${expeditionId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const apiService = new ApiService();
```

#### WebSocket Service
```typescript
// src/services/websocketService.ts
import io, { Socket } from 'socket.io-client';

class WebSocketService {
  private socket: Socket | null = null;
  private sessionToken: string | null = null;
  private expeditionRooms: Set<number> = new Set();

  connect(sessionToken: string): Promise<boolean> {
    return new Promise((resolve, reject) => {
      try {
        this.sessionToken = sessionToken;

        this.socket = io(import.meta.env.VITE_WS_URL || 'wss://your-domain.com', {
          auth: {
            session_token: sessionToken
          },
          transports: ['websocket']
        });

        this.socket.on('connect', () => {
          console.log('WebSocket connected');
          resolve(true);
        });

        this.socket.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error);
          reject(error);
        });

        this.socket.on('expedition_update', (data) => {
          this.handleExpeditionUpdate(data);
        });

        this.socket.on('expedition_joined', (data) => {
          console.log('Joined expedition room:', data);
        });

        this.socket.on('error', (error) => {
          console.error('WebSocket error:', error);
        });

      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.expeditionRooms.clear();
  }

  joinExpedition(expeditionId: number): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.sessionToken) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      this.socket.emit('miniapp_join_expedition', {
        expedition_id: expeditionId,
        session_token: this.sessionToken
      });

      const timeout = setTimeout(() => {
        reject(new Error('Join expedition timeout'));
      }, 5000);

      this.socket.once('expedition_joined', (data) => {
        clearTimeout(timeout);
        if (data.expedition_id === expeditionId) {
          this.expeditionRooms.add(expeditionId);
          resolve();
        }
      });

      this.socket.once('error', (error) => {
        clearTimeout(timeout);
        reject(error);
      });
    });
  }

  leaveExpedition(expeditionId: number) {
    if (this.socket && this.expeditionRooms.has(expeditionId)) {
      this.socket.emit('leave_expedition', {
        expedition_id: expeditionId
      });
      this.expeditionRooms.delete(expeditionId);
    }
  }

  private handleExpeditionUpdate(data: any) {
    // Emit custom events for React components to listen to
    const event = new CustomEvent('expedition-update', {
      detail: data
    });
    window.dispatchEvent(event);
  }

  // Subscribe to expedition updates
  onExpeditionUpdate(callback: (data: any) => void) {
    const handler = (event: CustomEvent) => {
      callback(event.detail);
    };

    window.addEventListener('expedition-update', handler as EventListener);

    return () => {
      window.removeEventListener('expedition-update', handler as EventListener);
    };
  }
}

export const websocketService = new WebSocketService();
```

### 3.3 Real-time Update Hooks

#### Expedition Hook with Real-time Updates
```typescript
// src/hooks/useExpeditions.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { apiService } from '../services/apiService';
import { websocketService } from '../services/websocketService';
import { useAuth } from '../contexts/AuthContext';
import { telegramApp } from '../telegram/telegramApp';

export const useExpeditions = () => {
  const { sessionToken } = useAuth();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (sessionToken) {
      apiService.setSessionToken(sessionToken);
    }
  }, [sessionToken]);

  return useQuery({
    queryKey: ['expeditions', 'dashboard'],
    queryFn: () => apiService.getExpeditionsDashboard(),
    enabled: !!sessionToken,
    refetchInterval: 60000, // Refetch every minute as backup
  });
};

export const useExpeditionDetails = (expeditionId: number) => {
  const { sessionToken } = useAuth();
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState(false);

  // Real-time updates
  useEffect(() => {
    if (!sessionToken || !expeditionId) return;

    const connectAndJoin = async () => {
      try {
        // Connect to WebSocket if not already connected
        if (!isConnected) {
          await websocketService.connect(sessionToken);
          setIsConnected(true);
        }

        // Join expedition room
        await websocketService.joinExpedition(expeditionId);

        // Listen for updates
        const unsubscribe = websocketService.onExpeditionUpdate((data) => {
          if (data.expedition_id === expeditionId) {
            // Update query cache with real-time data
            queryClient.setQueryData(
              ['expedition', expeditionId, 'realtime'],
              (oldData: any) => ({
                ...oldData,
                ...data.data,
                last_updated: data.timestamp
              })
            );

            // Trigger haptic feedback for updates
            telegramApp.hapticFeedback('notification');
          }
        });

        return unsubscribe;
      } catch (error) {
        console.error('WebSocket connection error:', error);
      }
    };

    const cleanup = connectAndJoin();

    return () => {
      cleanup?.then(fn => fn?.());
      websocketService.leaveExpedition(expeditionId);
    };
  }, [sessionToken, expeditionId, queryClient, isConnected]);

  const realtimeQuery = useQuery({
    queryKey: ['expedition', expeditionId, 'realtime'],
    queryFn: () => apiService.getExpeditionRealtime(expeditionId),
    enabled: !!sessionToken && !!expeditionId,
    refetchInterval: 30000, // Fallback polling every 30 seconds
  });

  const detailsQuery = useQuery({
    queryKey: ['expedition', expeditionId, 'details'],
    queryFn: () => apiService.getExpeditionDetails(expeditionId),
    enabled: !!sessionToken && !!expeditionId,
  });

  return {
    ...realtimeQuery,
    details: detailsQuery.data,
    detailsLoading: detailsQuery.isLoading,
    detailsError: detailsQuery.error,
  };
};

export const useCreateExpedition = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { name: string; deadline: string }) =>
      apiService.createExpedition(data),
    onSuccess: () => {
      // Invalidate and refetch expeditions
      queryClient.invalidateQueries({ queryKey: ['expeditions'] });

      // Trigger success haptic feedback
      telegramApp.hapticFeedback('notification');
    },
    onError: () => {
      // Trigger error haptic feedback
      telegramApp.hapticFeedback('impact');
    }
  });
};

export const useConsumeItem = (expeditionId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { product_id: number; quantity: number }) =>
      apiService.consumeExpeditionItem(expeditionId, data),
    onSuccess: () => {
      // Invalidate expedition data to refetch
      queryClient.invalidateQueries({
        queryKey: ['expedition', expeditionId]
      });
      queryClient.invalidateQueries({
        queryKey: ['expeditions']
      });

      // Trigger success haptic feedback
      telegramApp.hapticFeedback('notification');
    },
    onError: () => {
      // Trigger error haptic feedback
      telegramApp.hapticFeedback('impact');
    }
  });
};
```

---

## 🎨 4. Pirate Theme System

### 4.1 Theme Configuration

#### Pirate Theme Definition
```typescript
// src/utils/pirateTheme.ts
import { DefaultTheme } from 'styled-components';

export const pirateTheme: DefaultTheme = {
  colors: {
    primary: '#8B4513',       // Pirate brown
    secondary: '#DAA520',     // Gold
    accent: '#CD853F',        // Peru
    danger: '#DC143C',        // Crimson
    success: '#228B22',       // Forest green
    warning: '#FF8C00',       // Dark orange
    info: '#4682B4',          // Steel blue
    water: '#20B2AA',         // Light sea green
    parchment: '#F5DEB3',     // Wheat
    wood: '#DEB887',          // Burlywood
    rope: '#CD853F',          // Peru
    metal: '#708090',         // Slate gray
    background: {
      primary: '#2F1B14',     // Dark brown
      secondary: '#1A0E0A',   // Very dark brown
      card: '#3D2817',        // Medium brown
      overlay: 'rgba(47, 27, 20, 0.9)'
    },
    text: {
      primary: '#F5DEB3',     // Light parchment
      secondary: '#DAA520',   // Gold
      disabled: '#8B7355',    // Dark khaki
      inverse: '#2F1B14'      // Dark brown
    },
    border: {
      primary: '#8B4513',     // Pirate brown
      secondary: '#CD853F',   // Peru
      light: '#DEB887'        // Burlywood
    }
  },
  typography: {
    fontFamily: {
      heading: '"Pirata One", cursive',
      body: '"Roboto", sans-serif',
      mono: '"Roboto Mono", monospace'
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem'
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700
    }
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem'
  },
  breakpoints: {
    mobile: '320px',
    tablet: '768px',
    desktop: '1024px'
  },
  shadows: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px rgba(0, 0, 0, 0.1)',
    treasure: '0 0 20px rgba(218, 165, 32, 0.4)',
    danger: '0 0 15px rgba(220, 20, 60, 0.3)'
  },
  animations: {
    transition: {
      fast: '150ms ease-in-out',
      normal: '250ms ease-in-out',
      slow: '350ms ease-in-out'
    },
    bounce: 'bounce 1s infinite',
    pulse: 'pulse 2s infinite',
    spin: 'spin 1s linear infinite',
    treasure: 'treasureSparkle 2s infinite',
    sway: 'sway 3s ease-in-out infinite',
    wave: 'wave 4s linear infinite'
  }
};

export const pirateEmojis = {
  expedition: '⛵',
  treasure: '💰',
  skull: '💀',
  map: '🗺️',
  compass: '🧭',
  sword: '⚔️',
  anchor: '⚓',
  flag: '🏴‍☠️',
  parrot: '🦜',
  telescope: '🔭',
  cannon: '💣',
  chest: '📦',
  items: {
    berry: '🫐',
    syrup: '🍯',
    salt: '🧂',
    candy: '🍬',
    rum: '🍺',
    coin: '🪙'
  },
  status: {
    active: '🏴‍☠️',
    completed: '✅',
    overdue: '💀',
    planning: '📋'
  }
};

// Keyframe animations
export const keyframes = `
  @keyframes treasureSparkle {
    0%, 100% {
      transform: scale(1) rotate(0deg);
      filter: brightness(1);
    }
    25% {
      transform: scale(1.1) rotate(90deg);
      filter: brightness(1.2);
    }
    50% {
      transform: scale(1.2) rotate(180deg);
      filter: brightness(1.3);
    }
    75% {
      transform: scale(1.1) rotate(270deg);
      filter: brightness(1.2);
    }
  }

  @keyframes sway {
    0%, 100% { transform: translateX(0) rotate(0deg); }
    25% { transform: translateX(-5px) rotate(-2deg); }
    75% { transform: translateX(5px) rotate(2deg); }
  }

  @keyframes wave {
    0% { background-position-x: 0; }
    100% { background-position-x: 1000px; }
  }

  @keyframes bounce {
    0%, 20%, 53%, 80%, 100% { transform: translateY(0); }
    40%, 43% { transform: translateY(-10px); }
    70% { transform: translateY(-5px); }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;
```

### 4.2 Styled Components

#### Base UI Components
```typescript
// src/components/ui/PirateButton.tsx
import React from 'react';
import styled, { css } from 'styled-components';
import { telegramApp } from '../../telegram/telegramApp';

interface PirateButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  icon?: string;
  children: React.ReactNode;
  onClick?: () => void;
  haptic?: boolean;
}

const StyledButton = styled.button<{
  $variant: string;
  $size: string;
  $disabled: boolean;
  $loading: boolean;
}>`
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: ${props => props.theme.spacing.sm};
  font-family: ${props => props.theme.typography.fontFamily.heading};
  font-weight: ${props => props.theme.typography.fontWeight.bold};
  border: 2px solid;
  border-radius: 8px;
  cursor: pointer;
  transition: all ${props => props.theme.animations.transition.normal};
  text-decoration: none;
  white-space: nowrap;

  ${props => {
    const colors = props.theme.colors;

    switch (props.$variant) {
      case 'primary':
        return css`
          background: linear-gradient(135deg, ${colors.primary}, ${colors.accent});
          border-color: ${colors.primary};
          color: ${colors.text.primary};

          &:hover:not(:disabled) {
            background: linear-gradient(135deg, ${colors.accent}, ${colors.primary});
            box-shadow: ${props.theme.shadows.treasure};
            transform: translateY(-2px);
          }
        `;
      case 'secondary':
        return css`
          background: linear-gradient(135deg, ${colors.secondary}, #B8860B);
          border-color: ${colors.secondary};
          color: ${colors.background.primary};

          &:hover:not(:disabled) {
            background: linear-gradient(135deg, #B8860B, ${colors.secondary});
            box-shadow: ${props.theme.shadows.treasure};
            transform: translateY(-2px);
          }
        `;
      case 'danger':
        return css`
          background: linear-gradient(135deg, ${colors.danger}, #B22222);
          border-color: ${colors.danger};
          color: ${colors.text.primary};

          &:hover:not(:disabled) {
            background: linear-gradient(135deg, #B22222, ${colors.danger});
            box-shadow: ${props.theme.shadows.danger};
            transform: translateY(-2px);
          }
        `;
      case 'success':
        return css`
          background: linear-gradient(135deg, ${colors.success}, #006400);
          border-color: ${colors.success};
          color: ${colors.text.primary};

          &:hover:not(:disabled) {
            background: linear-gradient(135deg, #006400, ${colors.success});
            transform: translateY(-2px);
          }
        `;
      default:
        return '';
    }
  }}

  ${props => {
    switch (props.$size) {
      case 'sm':
        return css`
          padding: ${props.theme.spacing.xs} ${props.theme.spacing.sm};
          font-size: ${props.theme.typography.fontSize.sm};
        `;
      case 'lg':
        return css`
          padding: ${props.theme.spacing.md} ${props.theme.spacing.xl};
          font-size: ${props.theme.typography.fontSize.lg};
        `;
      default:
        return css`
          padding: ${props.theme.spacing.sm} ${props.theme.spacing.md};
          font-size: ${props.theme.typography.fontSize.base};
        `;
    }
  }}

  ${props => props.$disabled && css`
    opacity: 0.5;
    cursor: not-allowed;

    &:hover {
      transform: none !important;
      box-shadow: none !important;
    }
  `}

  ${props => props.$loading && css`
    cursor: not-allowed;

    &::before {
      content: '';
      position: absolute;
      width: 16px;
      height: 16px;
      border: 2px solid transparent;
      border-top: 2px solid currentColor;
      border-radius: 50%;
      animation: ${props.theme.animations.spin};
    }
  `}
`;

const IconSpan = styled.span`
  font-size: 1.2em;
  display: flex;
  align-items: center;
`;

export const PirateButton: React.FC<PirateButtonProps> = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon,
  children,
  onClick,
  haptic = true,
  ...props
}) => {
  const handleClick = () => {
    if (disabled || loading) return;

    if (haptic) {
      telegramApp.hapticFeedback('impact');
    }

    onClick?.();
  };

  return (
    <StyledButton
      $variant={variant}
      $size={size}
      $disabled={disabled || loading}
      $loading={loading}
      onClick={handleClick}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? null : (
        <>
          {icon && <IconSpan>{icon}</IconSpan>}
          {children}
        </>
      )}
    </StyledButton>
  );
};
```

#### Expedition Card Component
```typescript
// src/components/expedition/ExpeditionCard.tsx
import React from 'react';
import styled from 'styled-components';
import { format, formatDistanceToNow } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import { PirateButton } from '../ui/PirateButton';
import { ProgressBar } from '../ui/ProgressBar';
import { pirateEmojis } from '../../utils/pirateTheme';

interface Expedition {
  id: number;
  name: string;
  status: string;
  deadline: string | null;
  is_overdue: boolean;
  days_remaining: number | null;
  progress: {
    completion_percentage: number;
    total_items: number;
    consumed_items: number;
    remaining_items: number;
    total_value: number;
    consumed_value: number;
    remaining_value: number;
  };
}

interface ExpeditionCardProps {
  expedition: Expedition;
  isOverdue: boolean;
}

const CardContainer = styled.div<{ $isOverdue: boolean; $status: string }>`
  background: linear-gradient(135deg, ${props => props.theme.colors.parchment}, #f0e68c);
  border: 2px solid ${props => props.$isOverdue ? props.theme.colors.danger : props.theme.colors.border.primary};
  border-radius: 12px;
  padding: ${props => props.theme.spacing.lg};
  margin-bottom: ${props => props.theme.spacing.md};
  box-shadow: ${props => props.theme.shadows.lg};
  transition: all ${props => props.theme.animations.transition.normal};
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-4px);
    box-shadow: ${props => props.theme.shadows.xl};
  }

  ${props => props.$isOverdue && `
    animation: ${props.theme.animations.pulse};
    box-shadow: ${props.theme.shadows.danger};
  `}

  ${props => props.$status === 'completed' && `
    border-color: ${props.theme.colors.success};
    background: linear-gradient(135deg, #f0f8e7, #e8f5e8);
  `}

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, ${props => props.theme.colors.secondary}, ${props => props.theme.colors.primary});
  }
`;

const CardHeader = styled.div`
  display: flex;
  justify-content: between;
  align-items: flex-start;
  margin-bottom: ${props => props.theme.spacing.md};
`;

const TitleSection = styled.div`
  flex: 1;
`;

const Title = styled.h3`
  font-family: ${props => props.theme.typography.fontFamily.heading};
  font-size: ${props => props.theme.typography.fontSize['2xl']};
  color: ${props => props.theme.colors.text.inverse};
  margin: 0 0 ${props => props.theme.spacing.xs} 0;
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
`;

const StatusBadge = styled.div<{ $status: string; $isOverdue: boolean }>`
  display: inline-flex;
  align-items: center;
  gap: ${props => props.theme.spacing.xs};
  padding: ${props => props.theme.spacing.xs} ${props => props.theme.spacing.sm};
  border-radius: 20px;
  font-size: ${props => props.theme.typography.fontSize.sm};
  font-weight: ${props => props.theme.typography.fontWeight.semibold};

  ${props => {
    if (props.$isOverdue) {
      return `
        background: ${props.theme.colors.danger};
        color: ${props.theme.colors.text.primary};
      `;
    }

    switch (props.$status) {
      case 'active':
        return `
          background: ${props.theme.colors.primary};
          color: ${props.theme.colors.text.primary};
        `;
      case 'completed':
        return `
          background: ${props.theme.colors.success};
          color: ${props.theme.colors.text.primary};
        `;
      default:
        return `
          background: ${props.theme.colors.info};
          color: ${props.theme.colors.text.primary};
        `;
    }
  }}
`;

const DeadlineInfo = styled.div<{ $isOverdue: boolean }>`
  font-size: ${props => props.theme.typography.fontSize.sm};
  color: ${props => props.$isOverdue ? props.theme.colors.danger : props.theme.colors.text.secondary};
  font-weight: ${props => props.theme.typography.fontWeight.medium};
  margin-bottom: ${props => props.theme.spacing.sm};
`;

const ProgressSection = styled.div`
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const ProgressLabel = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${props => props.theme.spacing.xs};
  font-size: ${props => props.theme.typography.fontSize.sm};
  color: ${props => props.theme.colors.text.inverse};
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: ${props => props.theme.spacing.sm};
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const StatItem = styled.div`
  text-align: center;
  padding: ${props => props.theme.spacing.sm};
  background: rgba(139, 69, 19, 0.1);
  border-radius: 6px;
`;

const StatValue = styled.div`
  font-size: ${props => props.theme.typography.fontSize.lg};
  font-weight: ${props => props.theme.typography.fontWeight.bold};
  color: ${props => props.theme.colors.primary};
`;

const StatLabel = styled.div`
  font-size: ${props => props.theme.typography.fontSize.xs};
  color: ${props => props.theme.colors.text.inverse};
  margin-top: ${props => props.theme.spacing.xs};
`;

const Actions = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.sm};
  justify-content: flex-end;
`;

export const ExpeditionCard: React.FC<ExpeditionCardProps> = ({
  expedition,
  isOverdue
}) => {
  const navigate = useNavigate();

  const getStatusEmoji = (status: string, isOverdue: boolean) => {
    if (isOverdue) return pirateEmojis.skull;
    return pirateEmojis.status[status as keyof typeof pirateEmojis.status] || pirateEmojis.expedition;
  };

  const getStatusText = (status: string, isOverdue: boolean) => {
    if (isOverdue) return 'Overdue';
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  const getDeadlineText = () => {
    if (!expedition.deadline) return 'No deadline set';

    const deadline = new Date(expedition.deadline);
    const now = new Date();

    if (isOverdue) {
      return `💀 Overdue by ${Math.abs(expedition.days_remaining || 0)} days`;
    }

    if (expedition.days_remaining === 0) {
      return '⏰ Due today!';
    }

    if (expedition.days_remaining && expedition.days_remaining <= 3) {
      return `🔥 ${expedition.days_remaining} days remaining`;
    }

    return `📅 Due ${format(deadline, 'MMM dd, yyyy')} (${formatDistanceToNow(deadline, { addSuffix: true })})`;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  return (
    <CardContainer $isOverdue={isOverdue} $status={expedition.status}>
      <CardHeader>
        <TitleSection>
          <Title>
            {getStatusEmoji(expedition.status, isOverdue)}
            {expedition.name}
          </Title>
          <StatusBadge $status={expedition.status} $isOverdue={isOverdue}>
            {getStatusText(expedition.status, isOverdue)}
          </StatusBadge>
        </TitleSection>
      </CardHeader>

      <DeadlineInfo $isOverdue={isOverdue}>
        {getDeadlineText()}
      </DeadlineInfo>

      <ProgressSection>
        <ProgressLabel>
          <span>Progress</span>
          <span>{expedition.progress.completion_percentage.toFixed(1)}%</span>
        </ProgressLabel>
        <ProgressBar
          percentage={expedition.progress.completion_percentage}
          variant={isOverdue ? 'danger' : 'primary'}
        />
      </ProgressSection>

      <StatsGrid>
        <StatItem>
          <StatValue>{expedition.progress.consumed_items}</StatValue>
          <StatLabel>Items Consumed</StatLabel>
        </StatItem>
        <StatItem>
          <StatValue>{expedition.progress.remaining_items}</StatValue>
          <StatLabel>Remaining</StatLabel>
        </StatItem>
        <StatItem>
          <StatValue>{formatCurrency(expedition.progress.consumed_value)}</StatValue>
          <StatLabel>Value Consumed</StatLabel>
        </StatItem>
        <StatItem>
          <StatValue>{formatCurrency(expedition.progress.remaining_value)}</StatValue>
          <StatLabel>Remaining Value</StatLabel>
        </StatItem>
      </StatsGrid>

      <Actions>
        <PirateButton
          variant="primary"
          size="sm"
          icon={pirateEmojis.telescope}
          onClick={() => navigate(`/expedition/${expedition.id}`)}
        >
          View Details
        </PirateButton>
      </Actions>
    </CardContainer>
  );
};
```

---

## 🚀 5. Core Features Development

### 5.1 Dashboard Implementation

#### Main Dashboard Component
```tsx
// src/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useExpeditions } from '../hooks/useExpeditions';
import { ExpeditionCard } from '../components/expedition/ExpeditionCard';
import { StatsOverview } from '../components/dashboard/StatsOverview';
import { OverdueAlerts } from '../components/dashboard/OverdueAlerts';
import { RecentActivity } from '../components/dashboard/RecentActivity';
import { PirateButton } from '../components/ui/PirateButton';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { pirateEmojis } from '../utils/pirateTheme';
import { telegramApp } from '../telegram/telegramApp';

const DashboardContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg,
    ${props => props.theme.colors.background.primary} 0%,
    ${props => props.theme.colors.background.secondary} 100%
  );
  padding: ${props => props.theme.spacing.md};

  @media (min-width: ${props => props.theme.breakpoints.tablet}) {
    padding: ${props => props.theme.spacing.lg};
  }
`;

const Header = styled.header`
  text-align: center;
  margin-bottom: ${props => props.theme.spacing.xl};
  position: relative;
`;

const Title = styled.h1`
  font-family: ${props => props.theme.typography.fontFamily.heading};
  font-size: ${props => props.theme.typography.fontSize['4xl']};
  color: ${props => props.theme.colors.text.primary};
  margin: 0 0 ${props => props.theme.spacing.sm} 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
  animation: ${props => props.theme.animations.sway};
`;

const Subtitle = styled.p`
  font-size: ${props => props.theme.typography.fontSize.lg};
  color: ${props => props.theme.colors.text.secondary};
  margin: 0;
`;

const ActionBar = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${props => props.theme.spacing.lg};
  flex-wrap: wrap;
  gap: ${props => props.theme.spacing.sm};

  @media (max-width: ${props => props.theme.breakpoints.tablet}) {
    flex-direction: column;
    align-items: stretch;
  }
`;

const FilterControls = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.sm};
  flex-wrap: wrap;
`;

const FilterButton = styled.button<{ $active: boolean }>`
  padding: ${props => props.theme.spacing.xs} ${props => props.theme.spacing.sm};
  border: 1px solid ${props => props.theme.colors.border.primary};
  border-radius: 20px;
  background: ${props => props.$active
    ? props.theme.colors.secondary
    : 'transparent'
  };
  color: ${props => props.$active
    ? props.theme.colors.text.inverse
    : props.theme.colors.text.primary
  };
  font-size: ${props => props.theme.typography.fontSize.sm};
  cursor: pointer;
  transition: all ${props => props.theme.animations.transition.fast};

  &:hover {
    background: ${props => props.$active
      ? props.theme.colors.secondary
      : props.theme.colors.secondary + '20'
    };
  }
`;

const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr;
  gap: ${props => props.theme.spacing.lg};

  @media (min-width: ${props => props.theme.breakpoints.desktop}) {
    grid-template-columns: 2fr 1fr;
  }
`;

const MainContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.lg};
`;

const Sidebar = styled.aside`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.lg};
`;

const ExpeditionsGrid = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.md};
`;

const EmptyState = styled.div`
  text-align: center;
  padding: ${props => props.theme.spacing['3xl']};
  color: ${props => props.theme.colors.text.secondary};
`;

const EmptyStateIcon = styled.div`
  font-size: 4rem;
  margin-bottom: ${props => props.theme.spacing.lg};
`;

type FilterType = 'all' | 'active' | 'overdue' | 'completed';

export const Dashboard: React.FC = () => {
  const { data, isLoading, error, refetch } = useExpeditions();
  const [filter, setFilter] = useState<FilterType>('all');
  const [refreshing, setRefreshing] = useState(false);

  // Set up Telegram main button for refresh
  useEffect(() => {
    telegramApp.showMainButton('🔄 Refresh', async () => {
      setRefreshing(true);
      await refetch();
      setRefreshing(false);
      telegramApp.hapticFeedback('success');
    });

    return () => {
      telegramApp.hideMainButton();
    };
  }, [refetch]);

  if (isLoading) {
    return (
      <DashboardContainer>
        <LoadingSpinner message="Loading your expeditions..." />
      </DashboardContainer>
    );
  }

  if (error) {
    return (
      <DashboardContainer>
        <ErrorMessage
          message="Failed to load expeditions"
          onRetry={refetch}
        />
      </DashboardContainer>
    );
  }

  const expeditions = data?.expeditions || [];
  const stats = data?.stats || {};
  const overdueAlerts = data?.overdue_alerts || [];
  const recentActivity = data?.recent_activity || [];

  const filteredExpeditions = expeditions.filter(expedition => {
    switch (filter) {
      case 'active':
        return expedition.status === 'active' && !expedition.is_overdue;
      case 'overdue':
        return expedition.is_overdue;
      case 'completed':
        return expedition.status === 'completed';
      default:
        return true;
    }
  });

  const filterCounts = {
    all: expeditions.length,
    active: expeditions.filter(e => e.status === 'active' && !e.is_overdue).length,
    overdue: expeditions.filter(e => e.is_overdue).length,
    completed: expeditions.filter(e => e.status === 'completed').length
  };

  return (
    <DashboardContainer>
      <Header>
        <Title>{pirateEmojis.flag} Captain's Dashboard</Title>
        <Subtitle>Manage your pirate expeditions</Subtitle>
      </Header>

      <StatsOverview stats={stats} />

      <ActionBar>
        <FilterControls>
          {Object.entries(filterCounts).map(([key, count]) => (
            <FilterButton
              key={key}
              $active={filter === key}
              onClick={() => setFilter(key as FilterType)}
            >
              {key.charAt(0).toUpperCase() + key.slice(1)} ({count})
            </FilterButton>
          ))}
        </FilterControls>

        <PirateButton
          variant="secondary"
          icon={pirateEmojis.map}
          onClick={() => window.location.href = '/create-expedition'}
        >
          New Expedition
        </PirateButton>
      </ActionBar>

      <ContentGrid>
        <MainContent>
          <ExpeditionsGrid>
            {filteredExpeditions.length > 0 ? (
              filteredExpeditions.map(expedition => (
                <ExpeditionCard
                  key={expedition.id}
                  expedition={expedition}
                  isOverdue={expedition.is_overdue}
                />
              ))
            ) : (
              <EmptyState>
                <EmptyStateIcon>{pirateEmojis.map}</EmptyStateIcon>
                <h3>No expeditions found</h3>
                <p>
                  {filter === 'all'
                    ? "Start your first pirate expedition!"
                    : `No ${filter} expeditions at the moment.`
                  }
                </p>
                {filter === 'all' && (
                  <PirateButton
                    variant="primary"
                    icon={pirateEmojis.expedition}
                    onClick={() => window.location.href = '/create-expedition'}
                  >
                    Create First Expedition
                  </PirateButton>
                )}
              </EmptyState>
            )}
          </ExpeditionsGrid>
        </MainContent>

        <Sidebar>
          {overdueAlerts.length > 0 && (
            <OverdueAlerts alerts={overdueAlerts} />
          )}
          <RecentActivity activities={recentActivity} />
        </Sidebar>
      </ContentGrid>
    </DashboardContainer>
  );
};
```

### 5.2 Expedition Details with Real-time Updates

#### Expedition Details Component
```tsx
// src/pages/ExpeditionDetails.tsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useExpeditionDetails, useConsumeItem } from '../hooks/useExpeditions';
import { useBrambler } from '../hooks/useBrambler';
import { ExpeditionHeader } from '../components/expedition/ExpeditionHeader';
import { ProgressIndicator } from '../components/expedition/ProgressIndicator';
import { ItemsGrid } from '../components/expedition/ItemsGrid';
import { PiratesList } from '../components/expedition/PiratesList';
import { ConsumptionHistory } from '../components/expedition/ConsumptionHistory';
import { PirateButton } from '../components/ui/PirateButton';
import { Modal } from '../components/ui/Modal';
import { ConsumeItemForm } from '../components/forms/ConsumeItemForm';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { pirateEmojis } from '../utils/pirateTheme';
import { telegramApp } from '../telegram/telegramApp';

const DetailsContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg,
    ${props => props.theme.colors.background.primary} 0%,
    ${props => props.theme.colors.background.secondary} 100%
  );
  padding: ${props => props.theme.spacing.md};

  @media (min-width: ${props => props.theme.breakpoints.tablet}) {
    padding: ${props => props.theme.spacing.lg};
  }
`;

const BackButton = styled.button`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.xs};
  background: none;
  border: none;
  color: ${props => props.theme.colors.text.secondary};
  font-size: ${props => props.theme.typography.fontSize.sm};
  cursor: pointer;
  margin-bottom: ${props => props.theme.spacing.lg};
  padding: ${props => props.theme.spacing.xs};
  border-radius: 4px;
  transition: all ${props => props.theme.animations.transition.fast};

  &:hover {
    background: ${props => props.theme.colors.background.card};
    color: ${props => props.theme.colors.text.primary};
  }
`;

const TabsContainer = styled.div`
  display: flex;
  border-bottom: 2px solid ${props => props.theme.colors.border.primary};
  margin-bottom: ${props => props.theme.spacing.lg};
  overflow-x: auto;
`;

const Tab = styled.button<{ $active: boolean }>`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.xs};
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border: none;
  background: none;
  color: ${props => props.$active
    ? props.theme.colors.text.primary
    : props.theme.colors.text.secondary
  };
  font-weight: ${props => props.$active
    ? props.theme.typography.fontWeight.semibold
    : props.theme.typography.fontWeight.normal
  };
  border-bottom: 2px solid ${props => props.$active
    ? props.theme.colors.secondary
    : 'transparent'
  };
  cursor: pointer;
  transition: all ${props => props.theme.animations.transition.fast};
  white-space: nowrap;

  &:hover {
    color: ${props => props.theme.colors.text.primary};
    background: ${props => props.theme.colors.background.card};
  }
`;

const TabContent = styled.div`
  animation: fadeIn 0.3s ease-in-out;

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;

const ActionButtons = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.sm};
  justify-content: flex-end;
  margin-bottom: ${props => props.theme.spacing.lg};
  flex-wrap: wrap;

  @media (max-width: ${props => props.theme.breakpoints.tablet}) {
    justify-content: stretch;

    button {
      flex: 1;
    }
  }
`;

const RealtimeIndicator = styled.div<{ $connected: boolean }>`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.xs};
  font-size: ${props => props.theme.typography.fontSize.sm};
  color: ${props => props.$connected
    ? props.theme.colors.success
    : props.theme.colors.text.secondary
  };
  margin-bottom: ${props => props.theme.spacing.md};
`;

const StatusDot = styled.div<{ $connected: boolean }>`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${props => props.$connected
    ? props.theme.colors.success
    : props.theme.colors.text.secondary
  };
  animation: ${props => props.$connected ? 'pulse 2s infinite' : 'none'};
`;

type TabType = 'overview' | 'items' | 'pirates' | 'history';

export const ExpeditionDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const expeditionId = parseInt(id || '0');

  const {
    data: expeditionData,
    isLoading,
    error,
    refetch
  } = useExpeditionDetails(expeditionId);

  const { data: pirateNames } = useBrambler(expeditionId);
  const consumeItemMutation = useConsumeItem(expeditionId);

  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [showConsumeModal, setShowConsumeModal] = useState(false);
  const [realtimeConnected, setRealtimeConnected] = useState(false);

  // Real-time connection status monitoring
  useEffect(() => {
    const checkConnection = () => {
      // This would be connected to your WebSocket service
      setRealtimeConnected(true); // Simplified for this example
    };

    checkConnection();
    const interval = setInterval(checkConnection, 5000);

    return () => clearInterval(interval);
  }, []);

  // Setup Telegram main button
  useEffect(() => {
    if (expeditionData?.expedition?.status === 'active') {
      telegramApp.showMainButton('⚔️ Consume Item', () => {
        setShowConsumeModal(true);
        telegramApp.hapticFeedback('impact');
      });
    } else {
      telegramApp.hideMainButton();
    }

    return () => {
      telegramApp.hideMainButton();
    };
  }, [expeditionData]);

  const handleConsumeItem = async (data: { product_id: number; quantity: number }) => {
    try {
      await consumeItemMutation.mutateAsync(data);
      setShowConsumeModal(false);
      telegramApp.hapticFeedback('success');
    } catch (error) {
      console.error('Failed to consume item:', error);
      telegramApp.hapticFeedback('error');
    }
  };

  if (isLoading) {
    return (
      <DetailsContainer>
        <LoadingSpinner message="Loading expedition details..." />
      </DetailsContainer>
    );
  }

  if (error || !expeditionData) {
    return (
      <DetailsContainer>
        <ErrorMessage
          message="Failed to load expedition details"
          onRetry={refetch}
        />
      </DetailsContainer>
    );
  }

  const { expedition, progress, items, pirates, recent_consumptions } = expeditionData;

  const tabs = [
    { key: 'overview', label: 'Overview', icon: pirateEmojis.compass },
    { key: 'items', label: 'Items', icon: pirateEmojis.chest },
    { key: 'pirates', label: 'Pirates', icon: pirateEmojis.flag },
    { key: 'history', label: 'History', icon: pirateEmojis.map }
  ];

  return (
    <DetailsContainer>
      <BackButton onClick={() => navigate('/')}>
        ← Back to Dashboard
      </BackButton>

      <RealtimeIndicator $connected={realtimeConnected}>
        <StatusDot $connected={realtimeConnected} />
        {realtimeConnected ? 'Real-time updates active' : 'Connecting...'}
      </RealtimeIndicator>

      <ExpeditionHeader expedition={expedition} />
      <ProgressIndicator progress={progress} />

      <ActionButtons>
        {expedition.status === 'active' && (
          <PirateButton
            variant="primary"
            icon={pirateEmojis.sword}
            onClick={() => setShowConsumeModal(true)}
            disabled={consumeItemMutation.isPending}
          >
            Consume Item
          </PirateButton>
        )}
        <PirateButton
          variant="secondary"
          icon="🔄"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          Refresh
        </PirateButton>
      </ActionButtons>

      <TabsContainer>
        {tabs.map(tab => (
          <Tab
            key={tab.key}
            $active={activeTab === tab.key}
            onClick={() => setActiveTab(tab.key as TabType)}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </Tab>
        ))}
      </TabsContainer>

      <TabContent>
        {activeTab === 'overview' && (
          <div>
            <ProgressIndicator progress={progress} detailed />
            <ItemsGrid items={items} compact />
          </div>
        )}

        {activeTab === 'items' && (
          <ItemsGrid
            items={items}
            onConsumeItem={(item) => {
              // Pre-fill consume form with selected item
              setShowConsumeModal(true);
            }}
          />
        )}

        {activeTab === 'pirates' && (
          <PiratesList
            pirates={pirates}
            expeditionId={expeditionId}
          />
        )}

        {activeTab === 'history' && (
          <ConsumptionHistory consumptions={recent_consumptions} />
        )}
      </TabContent>

      <Modal
        isOpen={showConsumeModal}
        onClose={() => setShowConsumeModal(false)}
        title="⚔️ Consume Item"
      >
        <ConsumeItemForm
          items={items}
          onSubmit={handleConsumeItem}
          onCancel={() => setShowConsumeModal(false)}
          loading={consumeItemMutation.isPending}
        />
      </Modal>
    </DetailsContainer>
  );
};
```

### 5.3 Brambler (Name Anonymization) Interface

#### Brambler Manager Component
```tsx
// src/pages/BramblerManager.tsx
import React, { useState } from 'react';
import styled from 'styled-components';
import { useBrambler } from '../hooks/useBrambler';
import { PirateButton } from '../components/ui/PirateButton';
import { Modal } from '../components/ui/Modal';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { pirateEmojis } from '../utils/pirateTheme';
import { telegramApp } from '../telegram/telegramApp';

const BramblerContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg,
    ${props => props.theme.colors.background.primary} 0%,
    ${props => props.theme.colors.background.secondary} 100%
  );
  padding: ${props => props.theme.spacing.lg};
`;

const Header = styled.header`
  text-align: center;
  margin-bottom: ${props => props.theme.spacing.xl};
`;

const Title = styled.h1`
  font-family: ${props => props.theme.typography.fontFamily.heading};
  font-size: ${props => props.theme.typography.fontSize['3xl']};
  color: ${props => props.theme.colors.text.primary};
  margin: 0 0 ${props => props.theme.spacing.sm} 0;
`;

const Description = styled.p`
  color: ${props => props.theme.colors.text.secondary};
  font-size: ${props => props.theme.typography.fontSize.lg};
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
`;

const FeatureGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: ${props => props.theme.spacing.lg};
  margin-bottom: ${props => props.theme.spacing.xl};
`;

const FeatureCard = styled.div`
  background: linear-gradient(135deg, ${props => props.theme.colors.parchment}, #f0e68c);
  border: 2px solid ${props => props.theme.colors.border.primary};
  border-radius: 12px;
  padding: ${props => props.theme.spacing.lg};
  text-align: center;
`;

const FeatureIcon = styled.div`
  font-size: 3rem;
  margin-bottom: ${props => props.theme.spacing.md};
`;

const FeatureTitle = styled.h3`
  font-family: ${props => props.theme.typography.fontFamily.heading};
  color: ${props => props.theme.colors.text.inverse};
  margin: 0 0 ${props => props.theme.spacing.sm} 0;
`;

const FeatureDescription = styled.p`
  color: ${props => props.theme.colors.text.inverse};
  margin: 0 0 ${props => props.theme.spacing.md} 0;
  line-height: 1.5;
`;

const ExpeditionSelector = styled.div`
  background: ${props => props.theme.colors.background.card};
  border-radius: 8px;
  padding: ${props => props.theme.spacing.lg};
  margin-bottom: ${props => props.theme.spacing.xl};
`;

const SelectorTitle = styled.h2`
  font-family: ${props => props.theme.typography.fontFamily.heading};
  color: ${props => props.theme.colors.text.primary};
  margin: 0 0 ${props => props.theme.spacing.md} 0;
`;

const ExpeditionGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: ${props => props.theme.spacing.md};
`;

const ExpeditionCard = styled.button<{ $selected: boolean }>`
  background: ${props => props.$selected
    ? props.theme.colors.secondary
    : props.theme.colors.parchment
  };
  border: 2px solid ${props => props.$selected
    ? props.theme.colors.secondary
    : props.theme.colors.border.primary
  };
  border-radius: 8px;
  padding: ${props => props.theme.spacing.md};
  cursor: pointer;
  transition: all ${props => props.theme.animations.transition.normal};
  text-align: left;
  width: 100%;

  &:hover {
    transform: translateY(-2px);
    box-shadow: ${props => props.theme.shadows.md};
  }
`;

const ExpeditionName = styled.div`
  font-weight: ${props => props.theme.typography.fontWeight.semibold};
  color: ${props => props.theme.colors.text.inverse};
  margin-bottom: ${props => props.theme.spacing.xs};
`;

const ExpeditionStatus = styled.div`
  font-size: ${props => props.theme.typography.fontSize.sm};
  color: ${props => props.theme.colors.text.inverse};
  opacity: 0.8;
`;

const ActionsSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.lg};
  margin-top: ${props => props.theme.spacing.xl};
`;

const ActionCard = styled.div`
  background: ${props => props.theme.colors.background.card};
  border-radius: 8px;
  padding: ${props => props.theme.spacing.lg};
`;

const ActionTitle = styled.h3`
  font-family: ${props => props.theme.typography.fontFamily.heading};
  color: ${props => props.theme.colors.text.primary};
  margin: 0 0 ${props => props.theme.spacing.sm} 0;
`;

const ActionDescription = styled.p`
  color: ${props => props.theme.colors.text.secondary};
  margin: 0 0 ${props => props.theme.spacing.md} 0;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.sm};
  flex-wrap: wrap;
`;

export const BramblerManager: React.FC = () => {
  const [selectedExpedition, setSelectedExpedition] = useState<number | null>(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [showDecryptModal, setShowDecryptModal] = useState(false);

  const {
    expeditions,
    generatePirateNames,
    decryptNames,
    isLoading,
    error
  } = useBrambler(selectedExpedition);

  const handleGenerate = async () => {
    if (!selectedExpedition) return;

    try {
      // This would typically get buyer names from your API
      const buyerNames = ['John Doe', 'Jane Smith', 'Bob Johnson'];
      await generatePirateNames.mutateAsync({
        expeditionId: selectedExpedition,
        originalNames: buyerNames
      });

      setShowGenerateModal(false);
      telegramApp.hapticFeedback('success');
    } catch (error) {
      console.error('Failed to generate pirate names:', error);
      telegramApp.hapticFeedback('error');
    }
  };

  const handleDecrypt = async (ownerKey: string, encryptedMapping: string) => {
    if (!selectedExpedition) return;

    try {
      const result = await decryptNames.mutateAsync({
        expeditionId: selectedExpedition,
        ownerKey,
        encryptedMapping
      });

      // Display decrypted results
      console.log('Decrypted mapping:', result);
      telegramApp.hapticFeedback('success');
    } catch (error) {
      console.error('Failed to decrypt names:', error);
      telegramApp.hapticFeedback('error');
    }
  };

  if (isLoading) {
    return (
      <BramblerContainer>
        <LoadingSpinner message="Loading Brambler..." />
      </BramblerContainer>
    );
  }

  if (error) {
    return (
      <BramblerContainer>
        <ErrorMessage message="Failed to load Brambler" />
      </BramblerContainer>
    );
  }

  return (
    <BramblerContainer>
      <Header>
        <Title>{pirateEmojis.parrot} Brambler - Name Anonymization</Title>
        <Description>
          Protect participant privacy by anonymizing real names with pirate aliases.
          Only expedition owners can decrypt the true identities.
        </Description>
      </Header>

      <FeatureGrid>
        <FeatureCard>
          <FeatureIcon>🎭</FeatureIcon>
          <FeatureTitle>Anonymization</FeatureTitle>
          <FeatureDescription>
            Replace real names with randomly generated pirate aliases to protect privacy
          </FeatureDescription>
        </FeatureCard>

        <FeatureCard>
          <FeatureIcon>🔐</FeatureIcon>
          <FeatureTitle>Secure Encryption</FeatureTitle>
          <FeatureDescription>
            Uses AES-GCM encryption with PBKDF2 key derivation for maximum security
          </FeatureDescription>
        </FeatureCard>

        <FeatureCard>
          <FeatureIcon>🗝️</FeatureIcon>
          <FeatureTitle>Owner Access</FeatureTitle>
          <FeatureDescription>
            Only expedition owners can decrypt and view real names when needed
          </FeatureDescription>
        </FeatureCard>
      </FeatureGrid>

      <ExpeditionSelector>
        <SelectorTitle>Select Expedition</SelectorTitle>
        <ExpeditionGrid>
          {expeditions?.map(expedition => (
            <ExpeditionCard
              key={expedition.id}
              $selected={selectedExpedition === expedition.id}
              onClick={() => setSelectedExpedition(expedition.id)}
            >
              <ExpeditionName>
                {pirateEmojis.expedition} {expedition.name}
              </ExpeditionName>
              <ExpeditionStatus>
                Status: {expedition.status} • {expedition.pirate_count} pirates
              </ExpeditionStatus>
            </ExpeditionCard>
          ))}
        </ExpeditionGrid>
      </ExpeditionSelector>

      {selectedExpedition && (
        <ActionsSection>
          <ActionCard>
            <ActionTitle>Generate Pirate Names</ActionTitle>
            <ActionDescription>
              Create anonymous pirate aliases for all participants in this expedition.
              This will replace real names with pirate nicknames.
            </ActionDescription>
            <ActionButtons>
              <PirateButton
                variant="primary"
                icon={pirateEmojis.parrot}
                onClick={() => setShowGenerateModal(true)}
                disabled={generatePirateNames.isPending}
                loading={generatePirateNames.isPending}
              >
                Generate Names
              </PirateButton>
            </ActionButtons>
          </ActionCard>

          <ActionCard>
            <ActionTitle>Decrypt Names</ActionTitle>
            <ActionDescription>
              Use your owner key to decrypt and view the real names behind the pirate aliases.
              This action is logged for security purposes.
            </ActionDescription>
            <ActionButtons>
              <PirateButton
                variant="secondary"
                icon="🗝️"
                onClick={() => setShowDecryptModal(true)}
                disabled={decryptNames.isPending}
                loading={decryptNames.isPending}
              >
                Decrypt Names
              </PirateButton>
            </ActionButtons>
          </ActionCard>
        </ActionsSection>
      )}
    </BramblerContainer>
  );
};
```

---

## 🚀 6. Deployment and Integration

### 6.1 Build Configuration

#### Vite Configuration for Mini App
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          telegram: ['@telegram-apps/sdk'],
          ui: ['styled-components', 'recharts'],
        },
      },
    },
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
      '/socket.io': {
        target: process.env.VITE_WS_URL || 'ws://localhost:5000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
});
```

#### Environment Configuration
```bash
# .env.production
VITE_API_BASE_URL=https://your-domain.com
VITE_WS_URL=wss://your-domain.com
VITE_APP_NAME=Pirates Expedition
VITE_TELEGRAM_BOT_NAME=@YourBotName
```

### 6.2 Flask Integration

#### Serve Mini App from Flask
```python
# Add to app.py - Mini App serving
import os
from flask import send_from_directory, send_file

# Serve Mini App static files
@app.route("/miniapp")
def serve_miniapp():
    """Serve Mini App entry point."""
    miniapp_path = os.path.join(os.path.dirname(__file__), 'miniapp_dist')
    return send_file(os.path.join(miniapp_path, 'index.html'))

@app.route("/miniapp/<path:filename>")
def serve_miniapp_static(filename):
    """Serve Mini App static assets."""
    miniapp_path = os.path.join(os.path.dirname(__file__), 'miniapp_dist')
    return send_from_directory(miniapp_path, filename)

# Add Mini App manifest endpoint
@app.route("/miniapp/manifest.json")
def miniapp_manifest():
    """Serve Mini App manifest."""
    manifest = {
        "name": "Pirates Expedition",
        "short_name": "Pirates",
        "description": "Pirate-themed expedition management dashboard",
        "start_url": "/miniapp",
        "display": "standalone",
        "background_color": "#2F1B14",
        "theme_color": "#8B4513",
        "icons": [
            {
                "src": "/miniapp/assets/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/miniapp/assets/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    return jsonify(manifest)
```

### 6.3 Bot Integration Commands

#### Add Mini App Launch Command
```python
# Add to handlers/commands_handler.py
@with_error_boundary("miniapp_command")
@require_permission("admin")
async def miniapp_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Launch Mini App dashboard."""
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

        # Create Mini App button
        webapp_url = f"{self.config.telegram.webhook_url}/miniapp"
        webapp_button = InlineKeyboardButton(
            "🏴‍☠️ Open Pirates Dashboard",
            web_app=WebAppInfo(url=webapp_url)
        )

        keyboard = InlineKeyboardMarkup([[webapp_button]])

        message_text = (
            "🏴‍☠️ **Pirates Expedition Dashboard**\n\n"
            "Access your complete expedition management dashboard with:\n\n"
            "⛵ Real-time expedition tracking\n"
            "📊 Visual progress indicators\n"
            "👥 Pirate crew management\n"
            "💰 Revenue and debt analytics\n"
            "🎭 Brambler name anonymization\n\n"
            "Tap the button below to launch the dashboard:"
        )

        await update.message.reply_text(
            message_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        self.logger.error(f"Mini App command error: {e}")
        await update.message.reply_text(
            "❌ Failed to launch Mini App. Please try again later."
        )

# Register the command in handler registration
def register_miniapp_command(application):
    """Register Mini App command."""
    application.add_handler(CommandHandler("dashboard", miniapp_command))
```

### 6.4 Deployment Scripts

#### Build and Deploy Script
```bash
#!/bin/bash
# deploy.sh - Complete deployment script

set -e

echo "🏴‍☠️ Deploying Pirates Expedition Mini App..."

# Build React app
echo "📦 Building React application..."
cd miniapp
npm install
npm run build

# Copy build to Flask static directory
echo "📁 Copying build files..."
rm -rf ../miniapp_dist
cp -r dist ../miniapp_dist

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd ..
pip install -r requirements.txt

# Run database migrations if needed
echo "🗄️ Running database migrations..."
python -c "
from database.schema import initialize_schema
initialize_schema()
print('Database migrations completed')
"

# Restart application (example for systemd)
echo "🔄 Restarting application..."
if command -v systemctl &> /dev/null; then
    sudo systemctl restart pirates-bot
    echo "✅ Application restarted"
else
    echo "⚠️ Please restart your application manually"
fi

echo "🎉 Deployment completed successfully!"
echo "🔗 Mini App URL: https://your-domain.com/miniapp"
```

#### Docker Deployment
```dockerfile
# Dockerfile.miniapp - Multi-stage build for complete application
FROM node:18-alpine AS frontend-builder

WORKDIR /app/miniapp
COPY miniapp/package*.json ./
RUN npm ci --only=production

COPY miniapp/ .
RUN npm run build

FROM python:3.10-slim AS backend

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend
COPY --from=frontend-builder /app/miniapp/dist ./miniapp_dist

# Create non-root user
RUN useradd --create-home --shell /bin/bash pirates
RUN chown -R pirates:pirates /app
USER pirates

EXPOSE 5000

CMD ["python", "app.py"]
```

#### Docker Compose for Development
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: pirates_expedition
      POSTGRES_USER: pirates_user
      POSTGRES_PASSWORD: pirates_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  bot:
    build:
      context: .
      dockerfile: Dockerfile.miniapp
    environment:
      DATABASE_URL: postgresql://pirates_user:pirates_password@postgres:5432/pirates_expedition
      BOT_TOKEN: ${BOT_TOKEN}
      RAILWAY_URL: ${RAILWAY_URL}
      ENVIRONMENT: development
    ports:
      - "5000:5000"
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

volumes:
  postgres_data:
```

### 6.5 Testing and Validation

#### Mini App Testing Strategy
```typescript
// src/utils/testing.ts
export const validateMiniAppEnvironment = () => {
  const tests = [
    {
      name: 'Telegram WebApp SDK',
      test: () => typeof window.Telegram !== 'undefined',
      required: true
    },
    {
      name: 'API Connectivity',
      test: async () => {
        try {
          const response = await fetch('/api/health');
          return response.ok;
        } catch {
          return false;
        }
      },
      required: true
    },
    {
      name: 'WebSocket Support',
      test: () => typeof WebSocket !== 'undefined',
      required: false
    },
    {
      name: 'Local Storage',
      test: () => {
        try {
          localStorage.setItem('test', 'test');
          localStorage.removeItem('test');
          return true;
        } catch {
          return false;
        }
      },
      required: true
    }
  ];

  return tests;
};

// Integration testing helper
export const runMiniAppHealthCheck = async () => {
  const tests = validateMiniAppEnvironment();
  const results = [];

  for (const test of tests) {
    try {
      const result = typeof test.test === 'function'
        ? await test.test()
        : test.test;

      results.push({
        name: test.name,
        passed: result,
        required: test.required
      });
    } catch (error) {
      results.push({
        name: test.name,
        passed: false,
        required: test.required,
        error: error.message
      });
    }
  }

  return results;
};
```

---

## 🎯 Implementation Summary

This comprehensive guide provides everything needed to transform your existing Telegram bot into a modern Mini App with a React frontend:

### ✅ **Completed Implementation Areas:**

1. **🔧 Mini App Setup & Integration**
   - Telegram authentication flow
   - React TypeScript project structure
   - SDK integration and configuration

2. **🔌 Backend API Adaptations**
   - Enhanced authentication middleware
   - Mini App specific endpoints
   - Real-time WebSocket integration

3. **⚛️ Frontend Architecture**
   - Component hierarchy and routing
   - Authentication context
   - API and WebSocket services

4. **🎨 Pirate Theme System**
   - Complete theme configuration
   - Styled components library
   - Animation and interaction systems

5. **🚀 Core Features**
   - Dashboard with real-time updates
   - Expedition management interface
   - Brambler name anonymization

6. **📦 Deployment Strategy**
   - Build configuration
   - Flask integration
   - Docker deployment
   - Testing validation

### 🎯 **Key Benefits:**

- **🔄 Real-time Updates**: WebSocket integration for live expedition tracking
- **📱 Native Feel**: Telegram-optimized UI with haptic feedback
- **🔒 Secure**: Proper authentication and encrypted name anonymization
- **📊 Rich Analytics**: Visual progress tracking and revenue analytics
- **🏴‍☠️ Immersive Theme**: Complete pirate aesthetic with animations
- **♿ Responsive Design**: Works perfectly on mobile and desktop

### 🚀 **Next Steps:**

1. Set up the React development environment
2. Implement the backend API adaptations
3. Build core components following the theme system
4. Integrate real-time updates with WebSocket
5. Test Mini App functionality end-to-end
6. Deploy to production with proper CI/CD

This implementation preserves all existing bot functionality while adding a rich, interactive Mini App interface that transforms the expedition management experience into an engaging pirate-themed dashboard! 🏴‍☠️

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Analyze existing bot architecture and API endpoints", "status": "completed", "activeForm": "Analyzing existing bot architecture"}, {"content": "Create Mini App setup and integration guide", "status": "completed", "activeForm": "Creating Mini App setup guide"}, {"content": "Design backend API adaptations for Mini App", "status": "completed", "activeForm": "Designing backend API adaptations"}, {"content": "Plan React frontend architecture implementation", "status": "completed", "activeForm": "Planning React frontend architecture"}, {"content": "Implement pirate theme system and components", "status": "completed", "activeForm": "Implementing pirate theme system"}, {"content": "Develop core features and real-time updates", "status": "in_progress", "activeForm": "Developing core features"}, {"content": "Create deployment and integration strategy", "status": "pending", "activeForm": "Creating deployment strategy"}]