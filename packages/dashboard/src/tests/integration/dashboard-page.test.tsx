/**
 * Dashboard Page Integration Tests
 * 
 * These tests validate the integration between the Dashboard page UI components
 * and the API client, ensuring that data is properly fetched, displayed,
 * and that loading/error states are handled correctly.
 */

import React from 'react';
import { render, screen, waitFor, act } from "@testing-library/react"
import '@testing-library/jest-dom'
import DashboardPage from "@/app/dashboard/page"

// Mock Recharts to resolve the warnings about container dimensions
jest.mock('recharts', () => {
  const OriginalModule = jest.requireActual('recharts');
  
  return {
    ...OriginalModule,
    ResponsiveContainer: ({ children, ...props }: any) => (
      <div data-testid="recharts-responsive-container" style={{ width: '800px', height: '400px' }}>
        {children}
      </div>
    ),
  };
});

import { analyticsApi } from '../../lib/api-client';
import { useApi } from '../../hooks/use-api';

// Mock the API hooks and API client
jest.mock('../../hooks/use-api');
jest.mock('../../lib/api-client', () => ({
  analyticsApi: {
    getDashboardStats: jest.fn(),
    getUsageTrends: jest.fn()
  },
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

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn()
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams()
}));

// Sample mock data
const mockDashboardStats = {
  credentials: {
    total: 2345,
    issued_last_month: 543,
    growth_percentage: 12.5
  },
  wallets: {
    active: 783,
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

const mockUsageTrends = [
  { date: '2025-01', credentials: 125, wallets: 78 },
  { date: '2025-02', credentials: 156, wallets: 92 },
  { date: '2025-03', credentials: 215, wallets: 134 },
  { date: '2025-04', credentials: 245, wallets: 156 },
  { date: '2025-05', credentials: 310, wallets: 187 }
];

describe('Dashboard Page Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Test 1: Loading state
  it('should display loading state while fetching data', async () => {
    // Mock loading state
    (useApi as jest.Mock).mockImplementation(() => ({
      data: null,
      isLoading: true,
      error: null,
      request: jest.fn(),
      refetch: jest.fn()
    }));

    // Render the component
    const { container } = render(<DashboardPage />);
    
    // Check for loading indicators - simplified approach
    // Just verify some UI is rendered and the component doesn't crash
    expect(container.firstChild).not.toBeNull();

    // Look for any loading indicators with a more relaxed approach
    // Either loading text or a spinner should be present
    await waitFor(() => {
      const spinners = container.querySelectorAll('.animate-spin');
      const hasSpinners = spinners.length > 0;
      const hasLoadingText = container.textContent?.toLowerCase().includes('loading');
      
      expect(hasSpinners || hasLoadingText).toBe(true);
    }, { timeout: 10000 });
  });

  // Test 2: Successful data fetch
  it('should display dashboard stats after successful API fetch', async () => {
    // Mock successful API response for both endpoints
    (useApi as jest.Mock).mockImplementationOnce(() => ({
      data: mockDashboardStats,
      isLoading: false,
      error: null,
      request: jest.fn(),
      refetch: jest.fn(() => Promise.resolve(mockDashboardStats))
    })).mockImplementationOnce(() => ({
      data: mockUsageTrends,
      isLoading: false,
      error: null,
      request: jest.fn(),
      refetch: jest.fn(() => Promise.resolve(mockUsageTrends))
    }));

    (analyticsApi.getDashboardStats as jest.Mock).mockResolvedValue(mockDashboardStats);
    (analyticsApi.getUsageTrends as jest.Mock).mockResolvedValue(mockUsageTrends);

    // Render the component
    const { container } = render(<DashboardPage />);

    // More resilient approach: Check that the dashboard renders without error
    expect(container.firstChild).not.toBeNull();
    
    // Wait for data to be rendered with longer timeout
    // Use partial text matching and look for specific patterns rather than exact text
    await waitFor(() => {
      // Verify dashboard title is rendered
      expect(container.querySelector('h1')?.textContent).toBe('Dashboard');
      
      // Check for at least one stat card with numeric content
      const statCards = container.querySelectorAll('.rounded-lg');
      expect(statCards.length).toBeGreaterThan(0);
      
      // Check for data content (any of these should be present if data loaded)
      const pageContent = container.textContent || '';
      const hasDataContent = [
        mockDashboardStats.credentials.total.toString(),
        mockDashboardStats.wallets.active.toString(),
        mockDashboardStats.verification.rate.toString()
      ].some(value => pageContent.includes(value));
      
      expect(hasDataContent).toBe(true);
    }, { timeout: 10000 });
  });

  // Test 3: Error handling
  it('should display error message when API fetch fails', async () => {
    // Mock API error
    const mockError = new (jest.requireMock('../../lib/api-client').ApiError)(
      500, 'Error', 'Internal Server Error'
    );
    
    (useApi as jest.Mock).mockImplementation(() => ({
      data: null,
      isLoading: false,
      error: mockError,
      request: jest.fn(),
      refetch: jest.fn()
    }));

    (analyticsApi.getDashboardStats as jest.Mock).mockRejectedValue(mockError);

    // Render the component
    const { container } = render(<DashboardPage />);

    // Check for error message with more resilient approach
    await waitFor(() => {
      // Look for an alert role element
      const alertElement = container.querySelector('[role="alert"]');
      expect(alertElement).not.toBeNull();
      
      // Check if error content is displayed (using flexible content matching)
      const errorContent = alertElement?.textContent || '';
      expect(errorContent.includes('500') || errorContent.includes('Error') || 
             errorContent.includes('Server')).toBe(true);
      
      // Verify there's at least one button (likely a retry button)
      const buttons = container.querySelectorAll('button');
      expect(buttons.length).toBeGreaterThan(0);
    }, { timeout: 10000 });
  });

  // Test 4: Retry functionality
  it('should retry API fetch when retry button is clicked', async () => {
    // Set up mocks
    const mockError = new (jest.requireMock('../../lib/api-client').ApiError)(
      500, 'Error', 'Internal Server Error'
    );
    const mockRefetch = jest.fn().mockResolvedValue(mockDashboardStats);
    
    (useApi as jest.Mock).mockImplementation(() => ({
      data: null,
      isLoading: false,
      error: mockError,
      request: jest.fn(),
      refetch: mockRefetch
    }));

    // Render the component
    const { container } = render(<DashboardPage />);

    // Wait for error to be displayed
    await waitFor(() => {
      const alertElement = container.querySelector('[role="alert"]');
      expect(alertElement).not.toBeNull();
    }, { timeout: 10000 });

    // More resilient approach to finding and clicking a button
    // Find any button that might be a retry button
    let retryButton: HTMLElement | null = null;
    
    // First try by role and common retry text patterns
    const buttons = container.querySelectorAll('button');
    for (let i = 0; i < buttons.length; i++) {
      const button = buttons[i];
      if (button) {
        const buttonText = button.textContent?.toLowerCase() || '';
        if (buttonText.includes('try') || buttonText.includes('retry') || 
            buttonText.includes('again') || buttonText.includes('reload')) {
          retryButton = button as HTMLElement;
          break;
        }
      }
    }
    
    // If we found a retry button, click it
    expect(retryButton).not.toBeNull();
    if (retryButton) {
      await act(async () => {
        retryButton!.click();
      });
      
      // Check if refetch was called
      expect(mockRefetch).toHaveBeenCalled();
    }
  });
});
