/**
 * HTTP Client
 *
 * Base HTTP client with interceptors for authentication and error handling.
 * All API services should use this client for consistency.
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { getAuthHeaders } from '@/utils/telegram';

/**
 * API Error Response structure
 */
export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
}

/**
 * HTTP Client configuration
 */
export interface HttpClientConfig {
  baseURL?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

/**
 * Creates and configures an Axios instance with interceptors
 */
class HttpClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(config?: HttpClientConfig) {
    // Use environment variable API URL, fallback to window.location.origin
    const envApiUrl = import.meta.env.VITE_API_URL;

    // For local development, use Vite proxy (empty string = relative URLs)
    if (import.meta.env.DEV && !envApiUrl) {
      this.baseURL = ''; // Use Vite proxy - requests go to http://localhost:3000/api
      console.log('[HttpClient] DEV mode: Using Vite proxy for Flask backend');
    } else {
      this.baseURL = config?.baseURL || envApiUrl || window.location.origin;
    }

    console.log('[HttpClient] Final API Base URL:', this.baseURL);

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: config?.timeout || 30000, // 30 seconds default (increased from 10s)
      headers: {
        'Content-Type': 'application/json',
        ...config?.headers,
      },
    });

    this.setupInterceptors();
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor: Add authentication headers
    this.client.interceptors.request.use(
      (config) => {
        const authHeaders = getAuthHeaders();
        Object.assign(config.headers, authHeaders);
        console.log(`[HttpClient] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('[HttpClient] Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor: Handle errors consistently
    this.client.interceptors.response.use(
      (response) => {
        console.log(`[HttpClient] Response ${response.status} from ${response.config.url}`);
        return response;
      },
      (error: AxiosError) => {
        const apiError = this.handleError(error);
        return Promise.reject(apiError);
      }
    );
  }

  /**
   * Standardized error handler
   */
  private handleError(error: AxiosError): ApiError {
    const errorResponse = error.response?.data as any;

    const apiError: ApiError = {
      message: errorResponse?.message || error.message || 'An unknown error occurred',
      status: error.response?.status,
      code: errorResponse?.code || error.code,
      details: errorResponse?.details,
    };

    console.error('[HttpClient] API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: apiError.status,
      message: apiError.message,
    });

    return apiError;
  }

  /**
   * GET request
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config);
  }

  /**
   * POST request
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config);
  }

  /**
   * PUT request
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config);
  }

  /**
   * PATCH request
   */
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.patch<T>(url, data, config);
  }

  /**
   * DELETE request
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config);
  }

  /**
   * Get full URL for a given path
   */
  getFullUrl(path: string): string {
    return `${this.baseURL}${path}`;
  }

  /**
   * Get the underlying Axios instance (for advanced usage)
   */
  getClient(): AxiosInstance {
    return this.client;
  }
}

// Create and export singleton instance
export const httpClient = new HttpClient();

// Export class for testing and custom instances
export { HttpClient };
