'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ApiError } from '@/lib/api-client';
import { Button } from '@/components/ui/button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * ErrorBoundary component for catching and handling errors in React components
 * Particularly useful for API integration errors
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
  }

  resetErrorBoundary = (): void => {
    if (this.props.onReset) {
      this.props.onReset();
    }
    this.setState({
      hasError: false,
      error: null
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // If a custom fallback is provided, use it
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-6 flex flex-col items-center justify-center gap-4 text-center">
          <h2 className="text-lg font-semibold text-destructive">Something went wrong</h2>
          <div className="text-muted-foreground">
            {this.state.error instanceof ApiError ? (
              <>
                <p className="font-medium">{this.state.error.message}</p>
                <p className="text-sm">Status: {this.state.error.status} {this.state.error.statusText}</p>
              </>
            ) : (
              <p>{this.state.error?.message || 'An unexpected error occurred'}</p>
            )}
          </div>
          <Button variant="outline" onClick={this.resetErrorBoundary}>
            Try again
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * withErrorBoundary HOC for wrapping components with ErrorBoundary
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
): React.FC<P> {
  const displayName = Component.displayName || Component.name || 'Component';
  
  const ComponentWithErrorBoundary = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );
  
  ComponentWithErrorBoundary.displayName = `withErrorBoundary(${displayName})`;
  
  return ComponentWithErrorBoundary;
}

/**
 * APIErrorFallback component for displaying API errors
 */
export function APIErrorFallback({ 
  error, 
  resetErrorBoundary 
}: { 
  error: Error; 
  resetErrorBoundary: () => void;
}) {
  const isApiError = error instanceof ApiError;
  
  return (
    <div className="rounded-md border border-destructive/50 bg-destructive/10 p-6 flex flex-col items-center justify-center gap-4 text-center">
      <h2 className="text-lg font-semibold text-destructive">API Error</h2>
      <div className="text-muted-foreground">
        {isApiError ? (
          <>
            <p className="font-medium">{error.message}</p>
            <p className="text-sm">Status: {(error as ApiError).status} {(error as ApiError).statusText}</p>
          </>
        ) : (
          <p>{error?.message || 'An unexpected error occurred'}</p>
        )}
      </div>
      <Button variant="outline" onClick={resetErrorBoundary}>
        Retry
      </Button>
    </div>
  );
}
