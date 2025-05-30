import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card';

describe('Dashboard Stat Card', () => {
  // Test basic rendering of a stat card as used in the dashboard
  it('should render a card with title and value correctly', () => {
    const title = 'Total Credentials';
    const value = '1,234';
    const testId = 'test-stat-card';

    const { container } = render(
      <Card data-testid={testId}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{value}</div>
        </CardContent>
      </Card>
    );
    
    // Check that the component renders
    expect(container.firstChild).toHaveAttribute('data-testid', testId);
    
    // Check for the title and value
    expect(screen.getByText(title)).toBeInTheDocument();
    expect(screen.getByText(value)).toBeInTheDocument();
  });

  // Test with trend indicator (positive)
  it('should render with positive trend indicator correctly', () => {
    const title = 'Active Wallets';
    const value = '89';
    const trendValue = '+15%';
    const trendLabel = 'from last month';
    const testId = 'test-stat-card-positive';

    const { container } = render(
      <Card data-testid={testId}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{value}</div>
          <p className="text-xs text-muted-foreground">
            <span className="text-emerald-600">{trendValue}</span> {trendLabel}
          </p>
        </CardContent>
      </Card>
    );
    
    // Check for the positive trend indicator
    expect(screen.getByText(trendValue)).toHaveClass('text-emerald-600');
    expect(screen.getByText(trendLabel)).toBeInTheDocument();
  });

  // Test with trend indicator (negative)
  it('should render with negative trend indicator correctly', () => {
    const title = 'Verification Rate';
    const value = '98.2%';
    const trendValue = '-1.3%';
    const trendLabel = 'from last month';
    const testId = 'test-stat-card-negative';

    const { container } = render(
      <Card data-testid={testId}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{value}</div>
          <p className="text-xs text-muted-foreground">
            <span className="text-rose-600">{trendValue}</span> {trendLabel}
          </p>
        </CardContent>
      </Card>
    );
    
    // Check for the negative trend indicator
    expect(screen.getByText(trendValue)).toHaveClass('text-rose-600');
    expect(screen.getByText(trendLabel)).toBeInTheDocument();
  });

  // Test with custom content
  it('should render with custom content correctly', () => {
    const title = 'Compliance Score';
    const value = '94';
    const customText = 'High compliance level';
    const testId = 'test-stat-card-custom';

    render(
      <Card data-testid={testId}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{value}</div>
          <div className="mt-2 h-1.5 w-full rounded-full bg-secondary">
            <div className="h-1.5 rounded-full bg-primary" style={{ width: `${value}%` }} />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">{customText}</p>
        </CardContent>
      </Card>
    );
    
    // Check for basic information
    expect(screen.getByText(title)).toBeInTheDocument();
    expect(screen.getByText(value)).toBeInTheDocument();
    expect(screen.getByText(customText)).toBeInTheDocument();
  });
});
