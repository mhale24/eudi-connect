'use client';

import React, { ReactNode } from 'react';
import { ApiError } from '@/lib/api-client';
import { Loading } from '@/components/ui/loading';
import { ApiErrorMessage } from '@/components/ui/api-error';
import { ErrorBoundary } from '@/components/error-boundary';

interface ApiDataWrapperProps<T> {
  /**
   * The data to display when loaded
   */
  data: T | null;
  
  /**
   * Whether the data is currently loading
   */
  isLoading: boolean;
  
  /**
   * Any error that occurred during data fetching
   */
  error: ApiError | null;
  
  /**
   * Function to retry the data fetching
   */
  onRetry: () => void;
  
  /**
   * The content to render when data is successfully loaded
   */
  children: (data: T) => ReactNode;
  
  /**
   * Custom loading component to display
   */
  loadingComponent?: ReactNode;
  
  /**
   * Custom error component to display
   */
  errorComponent?: ReactNode;
  
  /**
   * Custom empty state component to display when data is null or empty
   */
  emptyComponent?: ReactNode;
  
  /**
   * Function to check if data is empty (default checks for null, empty arrays, or empty objects)
   */
  isEmpty?: (data: T | null) => boolean;
  
  /**
   * CSS class name for the wrapper
   */
  className?: string;
  
  /**
   * Whether to use an ErrorBoundary to catch rendering errors
   */
  withErrorBoundary?: boolean;
}

/**
 * Default function to check if data is empty
 */
function defaultIsEmpty<T>(data: T | null): boolean {
  if (data === null || data === undefined) return true;
  if (Array.isArray(data)) return data.length === 0;
  if (typeof data === 'object') return Object.keys(data).length === 0;
  return false;
}

/**
 * ApiDataWrapper component for handling API data loading, errors, and empty states
 */
export function ApiDataWrapper<T>({
  data,
  isLoading,
  error,
  onRetry,
  children,
  loadingComponent,
  errorComponent,
  emptyComponent,
  isEmpty = defaultIsEmpty,
  className = '',
  withErrorBoundary = true
}: ApiDataWrapperProps<T>) {
  // Default loading component
  const defaultLoadingComponent = (
    <div className="flex h-40 items-center justify-center">
      <Loading size={32} text="Loading..." />
    </div>
  );
  
  // Default error component
  const defaultErrorComponent = (
    <div className="my-4">
      <ApiErrorMessage error={error} onRetry={onRetry} />
    </div>
  );
  
  // Default empty state component
  const defaultEmptyComponent = (
    <div className="flex h-40 items-center justify-center text-muted-foreground">
      <p>No data available</p>
    </div>
  );
  
  // Render based on the current state
  const renderContent = () => {
    if (isLoading) {
      return loadingComponent || defaultLoadingComponent;
    }
    
    if (error) {
      return errorComponent || defaultErrorComponent;
    }
    
    if (isEmpty(data)) {
      return emptyComponent || defaultEmptyComponent;
    }
    
    return children(data as T);
  };
  
  // Wrap with ErrorBoundary if needed
  if (withErrorBoundary) {
    return (
      <ErrorBoundary onReset={onRetry}>
        <div className={className}>
          {renderContent()}
        </div>
      </ErrorBoundary>
    );
  }
  
  return <div className={className}>{renderContent()}</div>;
}

/**
 * Example usage:
 * 
 * ```tsx
 * const { data, isLoading, error, refetch } = useApi<User[]>();
 * 
 * useEffect(() => {
 *   refetch('/api/users');
 * }, []);
 * 
 * return (
 *   <ApiDataWrapper
 *     data={data}
 *     isLoading={isLoading}
 *     error={error}
 *     onRetry={() => refetch('/api/users')}
 *   >
 *     {(users) => (
 *       <div>
 *         {users.map(user => (
 *           <UserCard key={user.id} user={user} />
 *         ))}
 *       </div>
 *     )}
 *   </ApiDataWrapper>
 * );
 * ```
 */
