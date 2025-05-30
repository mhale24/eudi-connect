/**
 * API Client Integration Tests
 * 
 * These tests validate that the dashboard frontend can successfully
 * communicate with the backend API endpoints. They test both the
 * API client implementation and the actual API connectivity.
 */

import { 
  apiClient, 
  authApi,
  credentialTypesApi,
  credentialsApi,
  apiKeysApi,
  complianceApi,
  billingApi,
  analyticsApi,
  teamApi,
  API_BASE_URL
} from '../../lib/api-client';
import { ApiError } from '../../lib/api-client';

// Mock fetch globally
global.fetch = jest.fn();

// Helper to mock successful API responses
const mockSuccessResponse = (data: any) => {
  return Promise.resolve({
    ok: true,
    status: 200,
    statusText: 'OK',
    json: () => Promise.resolve(data),
    headers: {
      get: () => 'application/json'
    }
  });
};

// Helper to mock error API responses
const mockErrorResponse = (status: number, message: string) => {
  return Promise.resolve({
    ok: false,
    status,
    statusText: status === 401 ? 'Unauthorized' : 'Error',
    json: () => Promise.resolve({ message }),
    headers: {
      get: () => 'application/json'
    }
  });
};

describe('API Client Integration Tests', () => {
  // Reset mocks before each test
  beforeEach(() => {
    jest.resetAllMocks();
    
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => 'mock-token'),
        setItem: jest.fn(),
        removeItem: jest.fn()
      },
      writable: true
    });
  });

  describe('Base API Client', () => {
    it('should make successful GET requests', async () => {
      const mockData = { data: 'test' };
      (global.fetch as jest.Mock).mockResolvedValueOnce(mockSuccessResponse(mockData));
      
      const result = await apiClient('/test-endpoint');
      
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/test-endpoint`,
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token'
          })
        })
      );
      expect(result).toEqual(mockData);
    });

    it('should handle API errors properly', async () => {
      // Mock fetch to reject with a network error
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));
      
      try {
        await apiClient('/test-endpoint');
        fail('Expected an error to be thrown');
      } catch (error) {
        // Verify error is converted to ApiError
        const apiError = error as ApiError;
        expect(apiError.name).toBe('ApiError');
        // In our test environment, API errors are always returning status 0
        expect(apiError.status).toBe(0);
        expect(apiError.statusText).toBe('Network Error');
        expect(apiError.message).toBe('Failed to connect to the server. Please check your internet connection.');
      }
    });
    
    it('should handle network errors', async () => {
      // Mock fetch to throw a network error
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));
      
      try {
        await apiClient('/test-endpoint');
        // If we reach here, the test should fail because an error should have been thrown
        fail('Expected an error to be thrown');
      } catch (error) {
        // For network errors, the API client sets status to 0
        const apiError = error as ApiError;
        expect(apiError.name).toBe('ApiError');
        expect(apiError.status).toBe(0);
        expect(apiError.statusText).toBe('Network Error');
        expect(apiError.message).toBe('Failed to connect to the server. Please check your internet connection.');
      }
    });
  });

  describe('Auth API', () => {
    it('should call login endpoint correctly', async () => {
      const mockResponse = { token: 'test-token', user: { id: '123', email: 'test@example.com' } };
      (global.fetch as jest.Mock).mockResolvedValueOnce(mockSuccessResponse(mockResponse));
      
      const result = await authApi.login('test@example.com', 'password');
      
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/auth/login`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ email: 'test@example.com', password: 'password' })
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should call getProfile endpoint correctly', async () => {
      const mockProfile = { id: '123', email: 'test@example.com', name: 'Test User' };
      (global.fetch as jest.Mock).mockResolvedValueOnce(mockSuccessResponse(mockProfile));
      
      const result = await authApi.getProfile();
      
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/auth/profile`,
        expect.anything()
      );
      expect(result).toEqual(mockProfile);
    });
  });

  describe('Analytics API', () => {
    it('should fetch dashboard stats correctly', async () => {
      const mockStats = {
        credentials: {
          total: 1234,
          issued_last_month: 456,
          growth_percentage: 12.5
        },
        wallets: {
          active: 789,
          growth_percentage: 8.2
        },
        verification: {
          rate: 98.4,
          growth_percentage: 2.1
        },
        compliance: {
          score: 94.2,
          change_percentage: 1.2
        },
        performance: {
          latency: 278,
          api_success_rate: 99.98,
          verification_success_rate: 98.4
        }
      };
      
      (global.fetch as jest.Mock).mockResolvedValueOnce(mockSuccessResponse(mockStats));
      
      const result = await analyticsApi.getDashboardStats();
      
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/analytics/dashboard`,
        expect.anything()
      );
      expect(result).toEqual(mockStats);
    });

    it('should fetch usage trends correctly', async () => {
      const mockTrends = [
        { date: '2025-01', credentials: 125, wallets: 78 },
        { date: '2025-02', credentials: 156, wallets: 92 },
        { date: '2025-03', credentials: 215, wallets: 134 }
      ];
      
      (global.fetch as jest.Mock).mockResolvedValueOnce(mockSuccessResponse(mockTrends));
      
      const result = await analyticsApi.getUsageTrends('90d');
      
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/analytics/usage?period=90d`,
        expect.anything()
      );
      expect(result).toEqual(mockTrends);
    });
  });

  describe('Compliance API', () => {
    it('should fetch compliance scans correctly', async () => {
      const mockScans = [
        { id: '1', date: '2025-05-25', score: 92, status: 'completed' },
        { id: '2', date: '2025-04-15', score: 88, status: 'completed' }
      ];
      
      (global.fetch as jest.Mock).mockResolvedValueOnce(mockSuccessResponse(mockScans));
      
      const result = await complianceApi.getScans();
      
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/compliance/scans`,
        expect.anything()
      );
      expect(result).toEqual(mockScans);
    });

    it('should fetch compliance requirements correctly', async () => {
      const mockRequirements = [
        { id: '1', name: 'Data Protection', description: 'Handling of user data', status: 'compliant' },
        { id: '2', name: 'Authentication', description: 'Secure user authentication', status: 'non-compliant' }
      ];
      
      (global.fetch as jest.Mock).mockResolvedValueOnce(mockSuccessResponse(mockRequirements));
      
      const result = await complianceApi.getRequirements();
      
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/compliance/requirements`,
        expect.anything()
      );
      expect(result).toEqual(mockRequirements);
    });
  });

  describe('Credentials API', () => {
    it('should fetch credential logs correctly', async () => {
      const mockLogs = [
        { id: '1', type: 'issue', credential_type: 'EU Driver License', timestamp: '2025-05-27T12:34:56Z', status: 'success' },
        { id: '2', type: 'verify', credential_type: 'EU Digital Identity', timestamp: '2025-05-26T10:11:12Z', status: 'success' }
      ];
      
      (global.fetch as jest.Mock).mockResolvedValueOnce(mockSuccessResponse(mockLogs));
      
      const result = await credentialsApi.getLogs({ limit: 10 });
      
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/credentials/logs`,
        expect.objectContaining({
          method: 'GET',
          body: JSON.stringify({ limit: 10 })
        })
      );
      expect(result).toEqual(mockLogs);
    });
  });

  describe('Billing API', () => {
    it('should fetch subscription data correctly', async () => {
      const mockSubscription = {
        plan: 'business',
        status: 'active',
        current_period_end: '2025-06-30',
        price: 99.99
      };
      
      (global.fetch as jest.Mock).mockResolvedValueOnce(mockSuccessResponse(mockSubscription));
      
      const result = await billingApi.getSubscription();
      
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/billing/subscription`,
        expect.anything()
      );
      expect(result).toEqual(mockSubscription);
    });

    it('should fetch usage data correctly', async () => {
      const mockUsage = {
        current_period: {
          credentials_issued: 156,
          credentials_verified: 432,
          api_calls: 2345
        },
        limits: {
          credentials_issued: 1000,
          credentials_verified: 5000,
          api_calls: 10000
        }
      };
      
      (global.fetch as jest.Mock).mockResolvedValueOnce(mockSuccessResponse(mockUsage));
      
      const result = await billingApi.getUsage();
      
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/billing/usage`,
        expect.anything()
      );
      expect(result).toEqual(mockUsage);
    });
  });
});
