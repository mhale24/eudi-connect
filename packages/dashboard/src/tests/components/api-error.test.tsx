import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ApiErrorMessage, ApiErrorFull } from '@/components/ui/api-error';
import { ApiError } from '@/lib/api-client';

describe('ApiErrorMessage Component', () => {
  // Test 1: Basic rendering with an API error
  it('should render the API error message with correct title and message', () => {
    // Create a test API error
    const testError = new ApiError(404, 'Not Found', 'The requested resource was not found');
    
    // Render the component
    const { container } = render(<ApiErrorMessage error={testError} />);
    
    // Check that the component renders
    expect(container.firstChild).not.toBeNull();
    
    // Check for the error title and message
    expect(screen.getByText('Error 404')).toBeInTheDocument();
    expect(screen.getByText('The requested resource was not found.')).toBeInTheDocument();
    
    // Retry button should not be present without an onRetry prop
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  // Test 2: Testing the retry button functionality
  it('should call onRetry function when retry button is clicked', () => {
    // Create a mock function for onRetry
    const mockRetry = jest.fn();
    
    // Create a test API error
    const testError = new ApiError(500, 'Internal Server Error', 'Something went wrong');
    
    // Render the component with retry function
    render(<ApiErrorMessage error={testError} onRetry={mockRetry} />);
    
    // Find and click the retry button
    const retryButton = screen.getByRole('button', { name: /try again/i });
    fireEvent.click(retryButton);
    
    // Check if the retry function was called
    expect(mockRetry).toHaveBeenCalledTimes(1);
  });

  // Test 3: Handling standard JS Error object
  it('should handle standard Error objects gracefully', () => {
    // Create a standard JS error
    const jsError = new Error('Standard JavaScript error');
    
    // Render the component
    render(<ApiErrorMessage error={jsError} />);
    
    // Check that the component renders with appropriate fallback text
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Standard JavaScript error')).toBeInTheDocument();
  });

  // Test 4: Full error component
  it('should render the full error component correctly', () => {
    // Create a test API error
    const testError = new ApiError(401, 'Unauthorized', 'You are not authenticated');
    
    // Render the full error component
    const { container } = render(<ApiErrorFull error={testError} />);
    
    // Check that the component renders with the expected content
    expect(container.querySelector('.h-16')).toBeInTheDocument(); // The alert icon
    expect(screen.getByText('Error 401')).toBeInTheDocument();
    expect(screen.getByText(/You are not authenticated/)).toBeInTheDocument();
  });
});
