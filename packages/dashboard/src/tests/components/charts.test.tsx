import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LineChart, BarChart, AreaChart } from '@/components/ui/charts';

// Mock the Recharts library
jest.mock('recharts', () => {
  const OriginalModule = jest.requireActual('recharts');
  
  return {
    ...OriginalModule,
    ResponsiveContainer: ({ children, height, width }: any) => (
      <div data-testid="recharts-responsive-container" style={{ width, height }}>
        {children}
      </div>
    ),
    LineChart: ({ children }: any) => <div data-testid="recharts-line-chart">{children}</div>,
    Line: ({ dataKey }: any) => <div data-testid={`recharts-line-${dataKey}`} />,
    BarChart: ({ children }: any) => <div data-testid="recharts-bar-chart">{children}</div>,
    Bar: ({ dataKey }: any) => <div data-testid={`recharts-bar-${dataKey}`} />,
    AreaChart: ({ children }: any) => <div data-testid="recharts-area-chart">{children}</div>,
    Area: ({ dataKey }: any) => <div data-testid={`recharts-area-${dataKey}`} />,
    XAxis: () => <div data-testid="recharts-xaxis" />,
    YAxis: () => <div data-testid="recharts-yaxis" />,
    CartesianGrid: () => <div data-testid="recharts-cartesian-grid" />,
    Tooltip: () => <div data-testid="recharts-tooltip" />,
    Legend: () => <div data-testid="recharts-legend" />,
  };
});

describe('Chart Components', () => {
  describe('LineChart Component', () => {
    const mockData = [
      { name: '2024-01', value: 100 },
      { name: '2024-02', value: 150 },
      { name: '2024-03', value: 200 },
      { name: '2024-04', value: 180 },
      { name: '2024-05', value: 220 },
    ];

    it('should render the LineChart component correctly', () => {
      render(
        <LineChart 
          data={mockData} 
          xAxisDataKey="name"
          yAxisDataKey="value"
          className="mt-6 h-80"
          data-testid="test-line-chart"
        />
      );
      
      // Check if the chart container renders
      expect(screen.getByTestId('recharts-responsive-container')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-line-chart')).toBeInTheDocument();
      
      // Check for axis and chart elements
      expect(screen.getByTestId('recharts-line-value')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-xaxis')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-yaxis')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-tooltip')).toBeInTheDocument();
    });

    it('should handle empty data gracefully', () => {
      render(
        <LineChart 
          data={[]} 
          xAxisDataKey="name"
          yAxisDataKey="value"
          className="mt-6 h-80"
          data-testid="test-line-chart-empty"
        />
      );
      
      // Should still render the container even with empty data
      expect(screen.getByTestId('recharts-responsive-container')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-line-chart')).toBeInTheDocument();
      
      // Chart elements should still be rendered
      expect(screen.getByTestId('recharts-xaxis')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-yaxis')).toBeInTheDocument();
    });
  });

  // BarChart tests
  describe('BarChart Component', () => {
    const mockData = [
      { name: 'A', value: 100 },
      { name: 'B', value: 150 },
      { name: 'C', value: 200 },
      { name: 'D', value: 180 },
      { name: 'E', value: 220 },
    ];

    it('should render the BarChart component correctly', () => {
      render(
        <BarChart 
          data={mockData} 
          xAxisDataKey="name"
          yAxisDataKey="value"
          className="mt-6 h-80"
          data-testid="test-bar-chart"
        />
      );
      
      // Check if the chart container renders
      expect(screen.getByTestId('recharts-responsive-container')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-bar-chart')).toBeInTheDocument();
      
      // Check for axis and chart elements
      expect(screen.getByTestId('recharts-bar-value')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-xaxis')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-yaxis')).toBeInTheDocument();
    });

    it('should handle empty data gracefully', () => {
      render(
        <BarChart 
          data={[]} 
          xAxisDataKey="name"
          yAxisDataKey="value"
          className="mt-6 h-80"
          data-testid="test-bar-chart-empty"
        />
      );
      
      // Should still render the container even with empty data
      expect(screen.getByTestId('recharts-responsive-container')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-bar-chart')).toBeInTheDocument();
      
      // Chart elements should still be rendered
      expect(screen.getByTestId('recharts-xaxis')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-yaxis')).toBeInTheDocument();
    });
  });

  describe('AreaChart Component', () => {
    const mockData = [
      { name: '2024-01', value: 100 },
      { name: '2024-02', value: 150 },
    ];

    it('should render the AreaChart component correctly', () => {
      render(
        <AreaChart
          data={mockData}
          xAxisDataKey="name"
          yAxisDataKey="value"
          className="mt-6 h-80"
          data-testid="test-area-chart"
        />
      );
      
      // We're using a mock, so we're checking for the mocked responsive container
      expect(screen.getByTestId('recharts-responsive-container')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-area-chart')).toBeInTheDocument();
      
      // Check for axis and chart elements
      expect(screen.getByTestId('recharts-area-value')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-xaxis')).toBeInTheDocument();
      expect(screen.getByTestId('recharts-yaxis')).toBeInTheDocument();
      expect(screen.getByTestId('test-area-chart')).toBeInTheDocument();
    });
  });
});
