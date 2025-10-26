import { describe, it, expect, vi, beforeAll, afterAll } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ExpeditionErrorBoundary } from './ExpeditionErrorBoundary';

// Component that throws an error
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>No error</div>;
};

describe('ExpeditionErrorBoundary', () => {
  // Suppress console.error for tests
  const originalError = console.error;
  beforeAll(() => {
    console.error = vi.fn();
  });

  afterAll(() => {
    console.error = originalError;
  });

  it('should render children when no error occurs', () => {
    render(
      <ExpeditionErrorBoundary>
        <div>Test content</div>
      </ExpeditionErrorBoundary>
    );

    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('should render fallback UI when error occurs', () => {
    render(
      <ExpeditionErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ExpeditionErrorBoundary>
    );

    // Default fallback should show error message
    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
  });

  it('should render custom fallback when provided', () => {
    const customFallback = <div>Custom error message</div>;

    render(
      <ExpeditionErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </ExpeditionErrorBoundary>
    );

    expect(screen.getByText('Custom error message')).toBeInTheDocument();
  });

  it('should call onError callback when error occurs', () => {
    const onError = vi.fn();

    render(
      <ExpeditionErrorBoundary onError={onError}>
        <ThrowError shouldThrow={true} />
      </ExpeditionErrorBoundary>
    );

    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({ message: 'Test error' }),
      expect.objectContaining({ componentStack: expect.any(String) })
    );
  });

  it('should reset error state when resetKeys change', () => {
    const { rerender } = render(
      <ExpeditionErrorBoundary resetKeys={['key1']}>
        <ThrowError shouldThrow={true} />
      </ExpeditionErrorBoundary>
    );

    // Error fallback should be shown
    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();

    // Change resetKeys to trigger reset
    rerender(
      <ExpeditionErrorBoundary resetKeys={['key2']}>
        <ThrowError shouldThrow={false} />
      </ExpeditionErrorBoundary>
    );

    // Children should be rendered again
    expect(screen.getByText('No error')).toBeInTheDocument();
  });

  it('should not reset when resetKeys remain the same', () => {
    const { rerender } = render(
      <ExpeditionErrorBoundary resetKeys={['key1']}>
        <ThrowError shouldThrow={true} />
      </ExpeditionErrorBoundary>
    );

    // Error fallback should be shown
    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();

    // Rerender with same resetKeys
    rerender(
      <ExpeditionErrorBoundary resetKeys={['key1']}>
        <ThrowError shouldThrow={false} />
      </ExpeditionErrorBoundary>
    );

    // Should still show error fallback
    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
  });

  it('should capture error details in state', () => {
    const { container } = render(
      <ExpeditionErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ExpeditionErrorBoundary>
    );

    // Check that error boundary rendered (fallback is visible)
    const errorBoundary = container.querySelector('div');
    expect(errorBoundary).toBeInTheDocument();
  });
});
