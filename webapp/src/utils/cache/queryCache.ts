/**
 * Query Cache Utilities
 *
 * Generic caching implementation with TTL management and invalidation logic.
 * Provides intelligent caching to reduce API calls and improve performance.
 */

/**
 * Cache entry with TTL
 */
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in milliseconds
}

/**
 * Cache configuration
 */
export interface CacheConfig {
  defaultTTL?: number; // Default TTL in milliseconds (default: 5 minutes)
  maxSize?: number; // Maximum number of entries (default: 100)
  onEvict?: (key: string) => void; // Callback when entry is evicted
}

/**
 * Query cache implementation
 */
export class QueryCache {
  private cache = new Map<string, CacheEntry<any>>();
  private config: Required<CacheConfig>;

  constructor(config: CacheConfig = {}) {
    this.config = {
      defaultTTL: config.defaultTTL || 5 * 60 * 1000, // 5 minutes
      maxSize: config.maxSize || 100,
      onEvict: config.onEvict || (() => {}),
    };
  }

  /**
   * Gets cached data
   *
   * Returns null if not found or expired
   *
   * @param key - Cache key
   * @returns Cached data or null
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      return null;
    }

    // Check if expired
    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.delete(key);
      return null;
    }

    return entry.data as T;
  }

  /**
   * Sets cached data
   *
   * @param key - Cache key
   * @param data - Data to cache
   * @param ttl - Optional custom TTL in milliseconds
   */
  set<T>(key: string, data: T, ttl?: number): void {
    // Enforce max size by removing oldest entry
    if (this.cache.size >= this.config.maxSize && !this.cache.has(key)) {
      const oldestKey = this.cache.keys().next().value;
      if (oldestKey) {
        this.delete(oldestKey);
      }
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.config.defaultTTL,
    });
  }

  /**
   * Checks if key exists and is not expired
   *
   * @param key - Cache key
   * @returns true if key exists and is fresh
   */
  has(key: string): boolean {
    return this.get(key) !== null;
  }

  /**
   * Deletes cache entry
   *
   * @param key - Cache key
   */
  delete(key: string): void {
    if (this.cache.has(key)) {
      this.config.onEvict(key);
      this.cache.delete(key);
    }
  }

  /**
   * Invalidates cache entries matching pattern
   *
   * Supports wildcard pattern (e.g., "expeditions/*")
   *
   * @param pattern - Pattern to match (supports "*" wildcard)
   */
  invalidate(pattern: string): void {
    const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');

    const keysToDelete: string[] = [];
    this.cache.forEach((_, key) => {
      if (regex.test(key)) {
        keysToDelete.push(key);
      }
    });

    keysToDelete.forEach(key => this.delete(key));
  }

  /**
   * Clears all cache entries
   */
  clear(): void {
    this.cache.forEach((_, key) => this.config.onEvict(key));
    this.cache.clear();
  }

  /**
   * Gets cache statistics
   *
   * @returns Cache statistics
   */
  getStats(): {
    size: number;
    maxSize: number;
    keys: string[];
    hitRate?: number;
  } {
    return {
      size: this.cache.size,
      maxSize: this.config.maxSize,
      keys: Array.from(this.cache.keys()),
    };
  }

  /**
   * Removes expired entries
   *
   * Should be called periodically to free memory
   */
  cleanup(): void {
    const now = Date.now();
    const keysToDelete: string[] = [];

    this.cache.forEach((entry, key) => {
      if (now - entry.timestamp > entry.ttl) {
        keysToDelete.push(key);
      }
    });

    keysToDelete.forEach(key => this.delete(key));
  }

  /**
   * Gets or sets cached data with loader function
   *
   * @param key - Cache key
   * @param loader - Function to load data if not cached
   * @param ttl - Optional custom TTL
   * @returns Cached or loaded data
   */
  async getOrSet<T>(
    key: string,
    loader: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    const cached = this.get<T>(key);

    if (cached !== null) {
      return cached;
    }

    const data = await loader();
    this.set(key, data, ttl);
    return data;
  }
}

/**
 * Global query cache instance
 */
export const globalQueryCache = new QueryCache({
  defaultTTL: 5 * 60 * 1000, // 5 minutes
  maxSize: 200, // Increased for larger apps
});

/**
 * Cache key builders
 */
export const cacheKeys = {
  expeditions: {
    all: () => 'expeditions',
    list: () => 'expeditions/list',
    details: (id: string) => `expeditions/details/${id}`,
    timeline: () => 'expeditions/timeline',
    analytics: (id: string) => `expeditions/analytics/${id}`,
    items: (id: string) => `expeditions/items/${id}`,
    pirates: (id: string) => `expeditions/pirates/${id}`,
    consumptions: (id: string) => `expeditions/consumptions/${id}`,
  },
  products: {
    all: () => 'products',
    list: () => 'products/list',
    details: (id: string) => `products/details/${id}`,
  },
  users: {
    all: () => 'users',
    list: () => 'users/list',
    buyers: () => 'users/buyers',
  },
  dashboard: {
    all: () => 'dashboard',
    stats: () => 'dashboard/stats',
    timeline: () => 'dashboard/timeline',
    analytics: () => 'dashboard/analytics',
  },
};

/**
 * Cache invalidation helpers
 */
export const invalidateCache = {
  /**
   * Invalidates all expedition-related cache
   */
  expeditions: () => {
    globalQueryCache.invalidate('expeditions/*');
    globalQueryCache.invalidate('dashboard/*');
  },

  /**
   * Invalidates specific expedition cache
   */
  expedition: (id: string) => {
    globalQueryCache.invalidate(`expeditions/details/${id}`);
    globalQueryCache.invalidate(`expeditions/analytics/${id}`);
    globalQueryCache.invalidate(`expeditions/items/${id}`);
    globalQueryCache.invalidate(`expeditions/pirates/${id}`);
    globalQueryCache.invalidate(`expeditions/consumptions/${id}`);
    globalQueryCache.invalidate('expeditions/list');
    globalQueryCache.invalidate('expeditions/timeline');
    globalQueryCache.invalidate('dashboard/*');
  },

  /**
   * Invalidates all product-related cache
   */
  products: () => {
    globalQueryCache.invalidate('products/*');
  },

  /**
   * Invalidates specific product cache
   */
  product: (id: string) => {
    globalQueryCache.invalidate(`products/details/${id}`);
    globalQueryCache.invalidate('products/list');
  },

  /**
   * Invalidates all user-related cache
   */
  users: () => {
    globalQueryCache.invalidate('users/*');
  },

  /**
   * Invalidates dashboard cache
   */
  dashboard: () => {
    globalQueryCache.invalidate('dashboard/*');
  },

  /**
   * Invalidates all cache
   */
  all: () => {
    globalQueryCache.clear();
  },
};

/**
 * Auto-cleanup interval (runs every 5 minutes)
 */
let cleanupInterval: NodeJS.Timeout | null = null;

export const startAutoCleanup = (intervalMs = 5 * 60 * 1000): void => {
  if (cleanupInterval) {
    clearInterval(cleanupInterval);
  }

  cleanupInterval = setInterval(() => {
    globalQueryCache.cleanup();
  }, intervalMs);
};

export const stopAutoCleanup = (): void => {
  if (cleanupInterval) {
    clearInterval(cleanupInterval);
    cleanupInterval = null;
  }
};

// Auto-start cleanup on module load
if (typeof window !== 'undefined') {
  startAutoCleanup();
}
