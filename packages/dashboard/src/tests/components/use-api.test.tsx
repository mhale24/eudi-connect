import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useApi } from '@/hooks/use-api';

// Create a mock for the api-client module
jest.mock('@/lib/api-client', () => ({
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

// Import the mocked ApiError class for TypeScript type checking
const { ApiError } = jest.requireMock('@/lib/api-client');

// Mock apiClient implementation
const { apiClient } = jest.requireMock('@/lib/api-client');

describe('useApi Hook', () => {
  // Clear all mocks before each test
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  // Test 1: Initial state
  it('should initialize with correct default values', () => {
    // Render the hook
    const { result } = renderHook(() => useApi<any>());
    
    // Check initial state
    expect(result.current.data).toBeNull();
    expect(result.current.isLoading).toBeFalsy();
    expect(result.current.error).toBeNull();
    expect(typeof result.current.request).toBe('function');
    expect(typeof result.current.refetch).toBe('function');
  });
  
  // Test 2: Successful data fetching
  it('should fetch data successfully', async () => {
    // Mock data
    const mockData = { 
      credentials: { total: 100, issued_last_month: 25, growth_percentage: 5.2 },
      wallets: { active: 50, growth_percentage: 10.5 }
    };
    const endpoint = '/api/dashboard/stats';
    
    // Set up the apiClient mock
    apiClient.mockResolvedValueOnce(mockData);
    
    // Render the hook
    const { result } = renderHook(() => useApi<typeof mockData>());
    
    // Execute request
    await act(async () => {
      await result.current.request(endpoint);
    });
    
    // Wait for state updates
    await waitFor(() => {
      expect(result.current.isLoading).toBeFalsy();
      expect(result.current.data).toEqual(mockData);
      expect(result.current.error).toBeNull();
    });
    
    // Verify apiClient was called with the correct endpoint
    expect(apiClient).toHaveBeenCalledWith(endpoint, expect.any(Object));
  });
  
  // Test 3: API error handling
  it('should handle API errors correctly', async () => {
    const errorStatus = 404;
    const errorMessage = 'Resource not found';
    const endpoint = '/api/nonexistent-endpoint';
    
    // Create an API error
    const apiError = new ApiError(errorStatus, 'Not Found', errorMessage);
    
    // Mock apiClient to reject with the API error
    apiClient.mockRejectedValueOnce(apiError);
    
    // Render the hook
    const { result } = renderHook(() => useApi<any>());
    
    // Execute request
    await act(async () => {
      await result.current.request(endpoint);
    });
    
    // Wait for state updates and check error handling
    await waitFor(() => {
      expect(result.current.isLoading).toBeFalsy();
      expect(result.current.data).toBeNull();
      expect(result.current.error).toBeInstanceOf(ApiError);
      expect(result.current.error?.status).toBe(errorStatus);
      expect(result.current.error?.message).toBe(errorMessage);
    });
    
    // Verify apiClient was called with the correct endpoint
    expect(apiClient).toHaveBeenCalledWith(endpoint, expect.any(Object));
  });
  
  // Test 4: Network error handling
  it('should handle network errors correctly', async () => {
    const endpoint = '/api/some-endpoint';
    const networkError = new Error('Network error');
    
    // Mock apiClient to reject with a network error
    apiClient.mockRejectedValueOnce(networkError);
    
    // Render the hook
    const { result } = renderHook(() => useApi<any>());
    
    // Execute request
    await act(async () => {
      await result.current.request(endpoint);
    });
    
    // Wait for state updates and check error handling
    await waitFor(() => {
      expect(result.current.isLoading).toBeFalsy();
      expect(result.current.data).toBeNull();
      expect(result.current.error).toBeInstanceOf(Error);
      // The actual implementation likely transforms network errors to a user-friendly message
      expect(result.current.error?.message).toBe('An unexpected error occurred');
    });
    
    // Verify apiClient was called with the correct endpoint
    expect(apiClient).toHaveBeenCalledWith(endpoint, expect.any(Object));
  });
  
  // Test 5: Refetch functionality
  it('should refetch data using the refetch function', async () => {
    // Mock data for initial fetch and refetch
    const initialData = { count: 5 };
    const updatedData = { count: 10 };
    const endpoint = '/api/data';
    
    // Set up the apiClient mock for the initial call
    apiClient.mockResolvedValueOnce(initialData);
    
    // Render the hook
    const { result } = renderHook(() => useApi<any>());
    
    // Execute initial request
    await act(async () => {
      await result.current.request(endpoint);
    });
    
    // Verify initial data
    await waitFor(() => {
      expect(result.current.data).toEqual(initialData);
    });
    
    // Set up the apiClient mock for the refetch call
    apiClient.mockResolvedValueOnce(updatedData);
    
    // Execute refetch with the same endpoint
    await act(async () => {
      await result.current.refetch(() => apiClient(endpoint));
    });
    
    // Verify refetched data
    await waitFor(() => {
      expect(result.current.data).toEqual(updatedData);
    });
  });
  
  // Test 6: Custom refetch with callback
  it('should use the provided callback for refetch', async () => {
    // Mock data
    const customData = { custom: true, value: 'test' };
    
    // Create a mock function that returns the custom data
    const mockCallback = jest.fn().mockResolvedValue(customData);
    
    // Render the hook
    const { result } = renderHook(() => useApi<any>());
    
    // Set up an initial state with a request
    apiClient.mockResolvedValueOnce({ initial: true });
    await act(async () => {
      await result.current.request('/api/initial-data');
    });
    
    // Clear mock to track future calls
    apiClient.mockClear();
    
    // Execute refetch with custom callback
    await act(async () => {
      await result.current.refetch(mockCallback);
    });
    
    // Verify callback was called and data was updated
    expect(mockCallback).toHaveBeenCalledTimes(1);
    
    // Wait for state updates
    await waitFor(() => {
      expect(result.current.data).toEqual(customData);
      expect(result.current.isLoading).toBeFalsy();
      expect(result.current.error).toBeNull();
    });
    
    // Verify that apiClient was not called directly (we used the custom callback instead)
    expect(apiClient).not.toHaveBeenCalled();
  });
});
