import { useState, useEffect, useCallback } from 'react';
import { apiClient, ApiError } from '@/lib/api-client';

/**
 * Custom hook for making API requests with loading and error states
 */
export function useApi<T = any>(
  initialData: T | null = null,
) {
  const [data, setData] = useState<T | null>(initialData);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const request = useCallback(async <R = T>(
    endpointOrCallback: string | (() => Promise<R>),
    options: { 
      method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
      body?: any;
      headers?: Record<string, string>;
    } = {}
  ): Promise<R | null> => {
    setIsLoading(true);
    setError(null);

    try {
      let result: R;
      
      if (typeof endpointOrCallback === 'string') {
        // If the first argument is a string, treat it as an API endpoint
        result = await apiClient<R>(endpointOrCallback, options);
      } else {
        // If the first argument is a function, execute it directly
        result = await endpointOrCallback();
      }
      
      setData(result as unknown as T);
      setIsLoading(false);
      return result;
    } catch (err) {
      const apiError = err instanceof ApiError 
        ? err 
        : new ApiError(500, 'Unknown Error', 'An unexpected error occurred');
      
      setError(apiError);
      setIsLoading(false);
      return null;
    }
  }, []);

  // Alias for request to make the API more intuitive
  const refetch = request;

  return {
    data,
    setData,
    isLoading,
    error,
    request,
    refetch,
  };
}

/**
 * Hook for fetching data when component mounts
 */
export function useFetch<T = any>(
  endpoint: string,
  options: { 
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
    body?: any;
    headers?: Record<string, string>;
    skip?: boolean;
    dependencies?: any[];
  } = {}
) {
  const { skip = false, dependencies = [], ...requestOptions } = options;
  const { data, isLoading, error, request } = useApi<T>();

  useEffect(() => {
    if (!skip) {
      request(endpoint, requestOptions);
    }
  }, [endpoint, skip, request, ...dependencies]);

  return { data, isLoading, error, refetch: () => request(endpoint, requestOptions) };
}

/**
 * Hook for pagination
 */
export function usePagination<T = any>(
  endpoint: string,
  options: {
    pageSize?: number;
    initialPage?: number;
    query?: Record<string, any>;
    skip?: boolean;
  } = {}
) {
  const { pageSize = 10, initialPage = 1, query = {}, skip = false } = options;
  
  const [page, setPage] = useState(initialPage);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const buildQueryString = useCallback(() => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('limit', pageSize.toString());
    
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, value.toString());
      }
    });
    
    return `${endpoint}?${params.toString()}`;
  }, [endpoint, page, pageSize, query]);

  const { 
    data, 
    isLoading, 
    error, 
    refetch 
  } = useFetch<{ items: T[], total: number, page: number, pageSize: number, totalPages: number }>(
    buildQueryString(),
    { skip, dependencies: [page, pageSize, ...Object.values(query)] }
  );

  useEffect(() => {
    if (data) {
      setTotalItems(data.total);
      setTotalPages(data.totalPages);
    }
  }, [data]);

  const nextPage = useCallback(() => {
    if (page < totalPages) {
      setPage(p => p + 1);
    }
  }, [page, totalPages]);

  const prevPage = useCallback(() => {
    if (page > 1) {
      setPage(p => p - 1);
    }
  }, [page]);

  const goToPage = useCallback((pageNum: number) => {
    if (pageNum >= 1 && pageNum <= totalPages) {
      setPage(pageNum);
    }
  }, [totalPages]);

  return {
    data: data?.items || [],
    isLoading,
    error,
    page,
    totalItems,
    totalPages,
    nextPage,
    prevPage,
    goToPage,
    refetch,
  };
}
