/**
 * useCachedQuery Hook
 *
 * React hook wrapper for cached queries.
 * Provides loading states and automatic cache management.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { globalQueryCache } from '@/utils/cache/queryCache';

/**
 * Query options
 */
export interface QueryOptions<T> {
  /**
   * Cache key
   */
  key: string;

  /**
   * Function to fetch data
   */
  fetcher: () => Promise<T>;

  /**
   * Cache TTL in milliseconds
   */
  ttl?: number;

  /**
   * Whether to fetch immediately on mount
   */
  enabled?: boolean;

  /**
   * Refetch interval in milliseconds (0 = disabled)
   */
  refetchInterval?: number;

  /**
   * Callback when data is updated
   */
  onSuccess?: (data: T) => void;

  /**
   * Callback when error occurs
   */
  onError?: (error: Error) => void;
}

/**
 * Query result
 */
export interface QueryResult<T> {
  /**
   * Query data
   */
  data: T | null;

  /**
   * Loading state
   */
  isLoading: boolean;

  /**
   * Error state
   */
  error: Error | null;

  /**
   * Whether data is from cache
   */
  isFromCache: boolean;

  /**
   * Refetch function
   */
  refetch: () => Promise<void>;

  /**
   * Invalidate cache and refetch
   */
  invalidate: () => Promise<void>;
}

/**
 * Hook for cached queries
 *
 * @param options - Query options
 * @returns Query result
 */
export function useCachedQuery<T>(options: QueryOptions<T>): QueryResult<T> {
  const {
    key,
    fetcher,
    ttl,
    enabled = true,
    refetchInterval = 0,
    onSuccess,
    onError,
  } = options;

  const [data, setData] = useState<T | null>(() => globalQueryCache.get<T>(key));
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  const [isFromCache, setIsFromCache] = useState<boolean>(!!globalQueryCache.get<T>(key));

  const isMounted = useRef(true);
  const refetchIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Store callbacks in refs to avoid dependency issues
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onSuccessRef.current = onSuccess;
    onErrorRef.current = onError;
  }, [onSuccess, onError]);

  /**
   * Fetches data and updates cache
   */
  const fetchData = useCallback(async () => {
    // Check cache first
    const cached = globalQueryCache.get<T>(key);
    if (cached !== null) {
      setData(cached);
      setIsFromCache(true);
      setError(null);
      return;
    }

    // Fetch from network
    setIsLoading(true);
    setIsFromCache(false);

    try {
      const result = await fetcher();

      if (!isMounted.current) return;

      // Update cache
      globalQueryCache.set(key, result, ttl);

      setData(result);
      setError(null);
      onSuccessRef.current?.(result);
    } catch (err) {
      if (!isMounted.current) return;

      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      onErrorRef.current?.(error);
    } finally {
      if (isMounted.current) {
        setIsLoading(false);
      }
    }
  }, [key, fetcher, ttl]);

  /**
   * Refetch function (bypasses cache)
   */
  const refetch = useCallback(async () => {
    globalQueryCache.delete(key);
    await fetchData();
  }, [key, fetchData]);

  /**
   * Invalidate and refetch
   */
  const invalidate = useCallback(async () => {
    await refetch();
  }, [refetch]);

  /**
   * Initial fetch on mount or when enabled changes
   */
  useEffect(() => {
    if (enabled) {
      fetchData();
    }
  }, [enabled, fetchData]);

  /**
   * Setup refetch interval
   */
  useEffect(() => {
    if (refetchInterval > 0 && enabled) {
      refetchIntervalRef.current = setInterval(() => {
        refetch();
      }, refetchInterval);

      return () => {
        if (refetchIntervalRef.current) {
          clearInterval(refetchIntervalRef.current);
        }
      };
    }
  }, [refetchInterval, enabled, refetch]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      isMounted.current = false;
      if (refetchIntervalRef.current) {
        clearInterval(refetchIntervalRef.current);
      }
    };
  }, []);

  return {
    data,
    isLoading,
    error,
    isFromCache,
    refetch,
    invalidate,
  };
}

/**
 * Hook for cached mutation
 *
 * Similar to useCachedQuery but for mutations (POST, PUT, DELETE)
 */
export interface MutationOptions<TData, TVariables> {
  /**
   * Mutation function
   */
  mutationFn: (variables: TVariables) => Promise<TData>;

  /**
   * Callback when mutation succeeds
   */
  onSuccess?: (data: TData, variables: TVariables) => void;

  /**
   * Callback when mutation fails
   */
  onError?: (error: Error, variables: TVariables) => void;

  /**
   * Cache keys to invalidate after mutation
   */
  invalidateKeys?: string[];
}

export interface MutationResult<TData, TVariables> {
  /**
   * Mutation data
   */
  data: TData | null;

  /**
   * Loading state
   */
  isLoading: boolean;

  /**
   * Error state
   */
  error: Error | null;

  /**
   * Mutation function
   */
  mutate: (variables: TVariables) => Promise<void>;

  /**
   * Reset mutation state
   */
  reset: () => void;
}

export function useCachedMutation<TData, TVariables>(
  options: MutationOptions<TData, TVariables>
): MutationResult<TData, TVariables> {
  const { mutationFn, onSuccess, onError, invalidateKeys = [] } = options;

  const [data, setData] = useState<TData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const isMounted = useRef(true);

  // Store callbacks in refs to avoid dependency issues
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onSuccessRef.current = onSuccess;
    onErrorRef.current = onError;
  }, [onSuccess, onError]);

  const mutate = useCallback(async (variables: TVariables) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await mutationFn(variables);

      if (!isMounted.current) return;

      setData(result);
      onSuccessRef.current?.(result, variables);

      // Invalidate specified cache keys
      invalidateKeys.forEach(pattern => {
        globalQueryCache.invalidate(pattern);
      });
    } catch (err) {
      if (!isMounted.current) return;

      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      onErrorRef.current?.(error, variables);
    } finally {
      if (isMounted.current) {
        setIsLoading(false);
      }
    }
  }, [mutationFn, invalidateKeys]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  return {
    data,
    isLoading,
    error,
    mutate,
    reset,
  };
}
