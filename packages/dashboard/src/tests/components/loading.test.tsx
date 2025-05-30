import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Loading, LoadingCard } from '@/components/ui/loading';

describe('Loading Components', () => {
  // Test 1: Loading component with default props
  it('should render the Loading component with default props', () => {
    // Render the Loading component
    const { container } = render(<Loading />);
    
    // Check that the component renders
    expect(container.firstChild).not.toBeNull();
    
    // Verify the spinner element is present
    const spinnerElement = container.querySelector('.animate-spin');
    expect(spinnerElement).toBeInTheDocument();
    
    // Without text prop, there should be no text rendered
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
  });

  // Test 2: Loading component with custom size and text
  it('should render the Loading component with custom size and text', () => {
    const customText = 'Custom Loading Message';
    const customSize = 48;
    
    // Render the Loading component with custom props
    const { container } = render(<Loading size={customSize} text={customText} />);
    
    // Verify the custom text is rendered
    expect(screen.getByText(customText)).toBeInTheDocument();
    
    // The size is harder to test directly, but we can check for the svg element
    const spinnerElement = container.querySelector('svg');
    expect(spinnerElement).toBeInTheDocument();
    // Check if the style has the correct size
    expect(spinnerElement).toHaveAttribute('style', expect.stringContaining(`${customSize}px`));
  });

  // Test 3: LoadingCard component
  it('should render the LoadingCard component', () => {
    // Render the LoadingCard component
    const { container } = render(<LoadingCard />);
    
    // Check that the component renders
    expect(container.firstChild).not.toBeNull();
    
    // Verify the card structure exists
    const cardElement = container.querySelector('.rounded-lg');
    expect(cardElement).toBeInTheDocument();
    
    // Check that it has some content (with null check)
    if (cardElement) {
      expect(cardElement.children.length).toBeGreaterThan(0);
    }
  });

  // Test 4: Multiple LoadingCard components
  it('should render multiple LoadingCard components', () => {
    // Render multiple LoadingCard components
    const { container } = render(
      <div>
        <LoadingCard />
        <LoadingCard />
      </div>
    );
    
    // Check that both components render
    const cardElements = container.querySelectorAll('.rounded-lg');
    expect(cardElements.length).toBe(2);
  });
});
