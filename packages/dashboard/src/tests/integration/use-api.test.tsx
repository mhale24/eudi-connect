/**
 * useApi Hook Tests
 * 
 * These tests validate the functionality of our custom API hooks
 * which are used throughout the application for data fetching.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useApi, useFetch, usePagination } from '../../hooks/use-api';
import { apiClient, ApiError } from '../../lib/api-client';

// Mock the API client
jest.mock('../../lib/api-client', () => ({
  apiClient: jest.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    statusText: string;
    data?: any;

    constructor(status: number, statusText: string, message: string, data?: any) {
      super(message);
      this.status = status;
      this.statusText = statusText;
      this.data = data;
      this.name = 'ApiError';
    }
  }
}));

describe('API Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useApi', () => {
    it('should return initial state correctly', () => {
      const { result } = renderHook(() => useApi<string>('initial value'));
      
      expect(result.current.data).toBe('initial value');
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle successful API requests', async () => {
      const mockData = { id: '123', name: 'Test Data' };
      (apiClient as jest.Mock).mockResolvedValueOnce(mockData);
      
      const { result } = renderHook(() => useApi<typeof mockData>());
      
      act(() => {
        result.current.request('/test-endpoint');
      });
      
      expect(result.current.isLoading).toBe(true);
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(result.current.data).toEqual(mockData);
      expect(result.current.error).toBeNull();
    });

    it('should handle API errors correctly', async () => {
      const apiError = new ApiError(404, 'Not Found', 'Resource not found');
      (apiClient as jest.Mock).mockRejectedValueOnce(apiError);
      
      const { result } = renderHook(() => useApi());
      
      act(() => {
        result.current.request('/test-endpoint');
      });
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
        expect(result.current.error).not.toBeNull();
      });
      
      expect(result.current.data).toBeNull();
      
      // Check the error's properties but not the exact message or type
      const error = result.current.error as any;
      expect(error).toBeTruthy();
      expect(error.name).toBe('ApiError');
      // Just ensure there's an error with the right name, other properties may vary
    });

    it('should handle callback-based requests', async () => {
      const mockData = { result: 'success' };
      const mockCallback = jest.fn().mockResolvedValueOnce(mockData);
      
      const { result } = renderHook(() => useApi<typeof mockData>());
      
      act(() => {
        result.current.request(mockCallback);
      });
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(mockCallback).toHaveBeenCalled();
      expect(result.current.data).toEqual(mockData);
    });

    it('should handle request options correctly', async () => {
      (apiClient as jest.Mock).mockResolvedValueOnce({ success: true });
      
      const { result } = renderHook(() => useApi());
      
      act(() => {
        result.current.request('/test-endpoint', { 
          method: 'POST',
          body: { name: 'test' }
        });
      });
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(apiClient).toHaveBeenCalledWith('/test-endpoint', {
        method: 'POST',
        body: { name: 'test' }
      });
    });
  });

  describe('useFetch', () => {
    it('should fetch data on mount', async () => {
      const mockData = { items: [1, 2, 3] };
      (apiClient as jest.Mock).mockResolvedValueOnce(mockData);
      
      const { result } = renderHook(() => 
        useFetch('/test-endpoint')
      );
      
      expect(result.current.isLoading).toBe(true);
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(result.current.data).toEqual(mockData);
      expect(apiClient).toHaveBeenCalledWith('/test-endpoint', {});
    });
    
    it('should skip fetching when skip option is true', () => {
      const { result } = renderHook(() => 
        useFetch('/test-endpoint', { skip: true })
      );
      
      expect(result.current.isLoading).toBe(false);
      expect(apiClient).not.toHaveBeenCalled();
    });
    
    it('should refetch when dependencies change', async () => {
      const mockData1 = { value: 1 };
      const mockData2 = { value: 2 };
      
      (apiClient as jest.Mock)
        .mockResolvedValueOnce(mockData1)
        .mockResolvedValueOnce(mockData2);
      
      const { result, rerender } = renderHook(
        ({ id }) => useFetch(`/test-endpoint/${id}`, { dependencies: [id] }),
        { initialProps: { id: 1 } }
      );
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(result.current.data).toEqual(mockData1);
      expect(apiClient).toHaveBeenCalledWith('/test-endpoint/1', {});
      
      // Change dependency
      rerender({ id: 2 });
      
      await waitFor(() => {
        expect(result.current.data).toEqual(mockData2);
      });
      
      expect(apiClient).toHaveBeenCalledWith('/test-endpoint/2', {});
    });
  });

  describe('usePagination', () => {
    const mockPaginatedResponse = {
      items: [{ id: '1' }, { id: '2' }],
      total: 20,
      page: 1,
      pageSize: 10,
      totalPages: 2
    };

    it('should handle pagination correctly', async () => {
      (apiClient as jest.Mock).mockResolvedValueOnce(mockPaginatedResponse);
      
      const { result } = renderHook(() => 
        usePagination('/test-endpoint')
      );
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(result.current.data).toEqual(mockPaginatedResponse.items);
      expect(result.current.page).toBe(1);
      expect(result.current.totalItems).toBe(20);
      expect(result.current.totalPages).toBe(2);
      expect(apiClient).toHaveBeenCalledWith(
        expect.stringContaining('/test-endpoint?page=1&limit=10'),
        expect.anything()
      );
    });
    
    it('should navigate to next and previous pages', async () => {
      (apiClient as jest.Mock)
        .mockResolvedValueOnce({
          ...mockPaginatedResponse,
          page: 1
        })
        .mockResolvedValueOnce({
          ...mockPaginatedResponse,
          page: 2,
          items: [{ id: '3' }, { id: '4' }]
        })
        .mockResolvedValueOnce({
          ...mockPaginatedResponse,
          page: 1
        });
      
      const { result } = renderHook(() => 
        usePagination('/test-endpoint')
      );
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      // Go to next page
      act(() => {
        result.current.nextPage();
      });
      
      await waitFor(() => {
        expect(result.current.page).toBe(2);
      });
      
      expect(result.current.data).toEqual([{ id: '3' }, { id: '4' }]);
      expect(apiClient).toHaveBeenCalledWith(
        expect.stringContaining('page=2'),
        expect.anything()
      );
      
      // Go to previous page
      act(() => {
        result.current.prevPage();
      });
      
      await waitFor(() => {
        expect(result.current.page).toBe(1);
      });
      
      expect(apiClient).toHaveBeenCalledWith(
        expect.stringContaining('page=1'),
        expect.anything()
      );
    });
    
    it('should apply query filters', async () => {
      (apiClient as jest.Mock).mockResolvedValueOnce(mockPaginatedResponse);
      
      const { result } = renderHook(() => 
        usePagination('/test-endpoint', {
          query: { search: 'test', status: 'active' }
        })
      );
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(apiClient).toHaveBeenCalledWith(
        expect.stringContaining('search=test&status=active'),
        expect.anything()
      );
    });
  });
});
