import axios, { AxiosInstance } from 'axios';
import {
  Expedition,
  ExpeditionDetails,
  CreateExpeditionRequest,
  CreateExpeditionItemRequest,
  ConsumeItemRequest,
  PirateName,
  BramblerGenerateRequest,
  BramblerDecryptRequest,
  TimelineData,
  AnalyticsData,
  ItemConsumption,
  Product,
} from '@/types/expedition';
import { getAuthHeaders } from '@/utils/telegram';

class ExpeditionApiService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    // Use environment variable API URL, fallback to window.location.origin for development
    const envApiUrl = import.meta.env.VITE_API_URL;

    console.log('Environment variables:', import.meta.env);
    console.log('VITE_API_URL from env:', envApiUrl);
    console.log('window.location.origin:', window.location.origin);

    // For local development, use Vite proxy (empty string = relative URLs)
    if (import.meta.env.DEV && !envApiUrl) {
      this.baseURL = ''; // Use Vite proxy - requests go to http://localhost:3000/api which proxies to Flask
      console.log('DEV mode: Using Vite proxy for Flask backend');
    } else {
      this.baseURL = envApiUrl || window.location.origin;
    }

    console.log('Final API Base URL:', this.baseURL);

    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 10000, // 10 seconds - reduced from 30s for better UX
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include auth headers
    this.api.interceptors.request.use((config) => {
      const authHeaders = getAuthHeaders();
      Object.assign(config.headers, authHeaders);
      return config;
    });

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        throw error;
      }
    );
  }

  // Expedition CRUD operations
  async getExpeditions(): Promise<Expedition[]> {
    const response = await this.api.get<{ expeditions: Expedition[] }>('/api/expeditions');
    return response.data.expeditions;
  }

  async getExpeditionById(id: number): Promise<ExpeditionDetails> {
    const response = await this.api.get<ExpeditionDetails>(`/api/expeditions/${id}`);
    return response.data;
  }

  async createExpedition(data: CreateExpeditionRequest): Promise<Expedition> {
    const response = await this.api.post<Expedition>('/api/expeditions', data);
    return response.data;
  }

  async updateExpeditionStatus(id: number, status: string): Promise<Expedition> {
    const response = await this.api.put<Expedition>(`/api/expeditions/${id}`, { status });
    return response.data;
  }

  async deleteExpedition(id: number): Promise<void> {
    await this.api.delete(`/api/expeditions/${id}`);
  }

  // Expedition items management
  async getExpeditionItems(expeditionId: number): Promise<any[]> {
    const response = await this.api.get<{ items: any[] }>(`/api/expeditions/${expeditionId}/items`);
    return response.data.items;
  }

  async addItemsToExpedition(expeditionId: number, data: CreateExpeditionItemRequest): Promise<any[]> {
    const response = await this.api.post<{ items: any[] }>(`/api/expeditions/${expeditionId}/items`, data);
    return response.data.items;
  }

  // Item consumption
  async consumeItem(expeditionId: number, data: ConsumeItemRequest): Promise<ItemConsumption> {
    const response = await this.api.post<ItemConsumption>(`/api/expeditions/${expeditionId}/consume`, data);
    return response.data;
  }

  async getConsumptions(params?: {
    consumer_name?: string;
    payment_status?: string;
  }): Promise<ItemConsumption[]> {
    const response = await this.api.get<{ consumptions: ItemConsumption[] }>('/api/expeditions/consumptions', {
      params,
    });
    return response.data.consumptions;
  }

  // Brambler (name anonymization) operations
  async generatePirateNames(expeditionId: number, data: BramblerGenerateRequest): Promise<PirateName[]> {
    const response = await this.api.post<{ pirate_names: PirateName[] }>(
      `/api/brambler/generate/${expeditionId}`,
      data
    );
    return response.data.pirate_names;
  }

  async decryptPirateNames(expeditionId: number, data: BramblerDecryptRequest): Promise<Record<string, string>> {
    const response = await this.api.post<{ decrypted_mapping: Record<string, string> }>(
      `/api/brambler/decrypt/${expeditionId}`,
      data
    );
    return response.data.decrypted_mapping;
  }

  async getPirateNames(expeditionId: number): Promise<PirateName[]> {
    const response = await this.api.get<{ pirate_names: PirateName[] }>(
      `/api/brambler/names/${expeditionId}`
    );
    return response.data.pirate_names;
  }

  // Dashboard and analytics
  async getDashboardTimeline(): Promise<TimelineData> {
    const response = await this.api.get<TimelineData>('/api/dashboard/timeline');
    return response.data;
  }

  async getOverdueExpeditions(): Promise<any> {
    const response = await this.api.get('/api/dashboard/overdue');
    return response.data;
  }

  async getAnalytics(): Promise<AnalyticsData> {
    const response = await this.api.get<AnalyticsData>('/api/dashboard/analytics');
    return response.data;
  }

  // Products
  async getProducts(): Promise<Product[]> {
    const response = await this.api.get<{ products: Product[] }>('/api/products');
    return response.data.products;
  }

  // Users
  async getUsers(): Promise<{ username: string; level: string; total_purchases: string; last_access: string; status: string }[]> {
    const response = await this.api.get<{ users: any[] }>('/api/users');
    return response.data.users;
  }

  // Buyers (from sales)
  async getBuyers(): Promise<{ name: string }[]> {
    const response = await this.api.get<{ buyers: { name: string }[] }>('/api/buyers');
    return response.data.buyers;
  }

  // Export functionality
  async exportExpeditionData(params?: {
    expedition_id?: number;
    status?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<{ file_path: string; filename: string; download_url: string }> {
    const response = await this.api.get('/api/expeditions/export', { params });
    return response.data;
  }

  async exportPirateActivityReport(params?: {
    expedition_id?: number;
    anonymized?: boolean;
    date_from?: string;
    date_to?: string;
  }): Promise<{ file_path: string; filename: string; download_url: string }> {
    const response = await this.api.get('/api/expeditions/reports/pirate-activity', { params });
    return response.data;
  }

  async exportProfitLossReport(params?: {
    expedition_id?: number;
    date_from?: string;
    date_to?: string;
  }): Promise<{ file_path: string; filename: string; download_url: string }> {
    const response = await this.api.get('/api/expeditions/reports/profit-loss', { params });
    return response.data;
  }

  // Search
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
  }): Promise<{
    results: any[];
    total_count: number;
    limit: number;
    offset: number;
    has_more: boolean;
  }> {
    const response = await this.api.get('/api/expeditions/search', { params });
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<any> {
    const response = await this.api.get('/health');
    return response.data;
  }

  // Download file helper
  async downloadFile(url: string): Promise<Blob> {
    const response = await this.api.get(url, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Utility method to get full URL
  getFullUrl(path: string): string {
    return `${this.baseURL}${path}`;
  }
}

// Create and export singleton instance
export const expeditionApi = new ExpeditionApiService();

// Export class for testing
export { ExpeditionApiService };