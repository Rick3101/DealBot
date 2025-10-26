import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AppErrorScreen } from './AppErrorScreen';

describe('AppErrorScreen', () => {
  it('should render error screen with default message', () => {
    render(<AppErrorScreen />);

    expect(screen.getByText('Application Error')).toBeInTheDocument();
    expect(screen.getByText(/The application encountered a critical error/i)).toBeInTheDocument();
  });

  it('should show error details in development mode', () => {
    const error = new Error('Test error message');
    error.stack = 'Error: Test error message\n  at Component (test.tsx:10:5)';

    // Mock development mode
    vi.stubEnv('DEV', true);

    render(<AppErrorScreen error={error} />);

    // Use getAllBy since text appears in multiple places
    const errorDetailsElements = screen.getAllByText(/Error Details/i);
    expect(errorDetailsElements.length).toBeGreaterThan(0);
    expect(screen.getByText('Test error message')).toBeInTheDocument();

    vi.unstubAllEnvs();
  });

  it('should hide error details in production mode', () => {
    const error = new Error('Test error message');

    // Mock production mode
    vi.stubEnv('DEV', false);

    render(<AppErrorScreen error={error} />);

    expect(screen.queryByText(/Error Details/i)).not.toBeInTheDocument();
    expect(screen.queryByText('Test error message')).not.toBeInTheDocument();

    vi.unstubAllEnvs();
  });

  it('should show retry button when onRetry is provided', () => {
    const onRetry = vi.fn();

    render(<AppErrorScreen onRetry={onRetry} />);

    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeInTheDocument();
  });

  it('should hide retry button when onRetry is not provided', () => {
    render(<AppErrorScreen />);

    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
  });

  it('should call onRetry when retry button is clicked', () => {
    const onRetry = vi.fn();

    render(<AppErrorScreen onRetry={onRetry} />);

    const retryButton = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryButton);

    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('should reload page when reload button is clicked', () => {
    // Mock window.location.reload
    const reloadMock = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: reloadMock },
      writable: true,
    });

    render(<AppErrorScreen />);

    const reloadButton = screen.getByRole('button', { name: /reload application/i });
    fireEvent.click(reloadButton);

    expect(reloadMock).toHaveBeenCalledTimes(1);
  });

  it('should show stack trace in details element', () => {
    const error = new Error('Test error');
    error.stack = 'Error: Test error\n  at Component (test.tsx:10:5)\n  at render (react.tsx:50:10)';

    vi.stubEnv('DEV', true);

    render(<AppErrorScreen error={error} />);

    // Check for stack trace summary
    const stackElements = screen.getAllByText(/Stack Trace/i);
    expect(stackElements.length).toBeGreaterThan(0);

    vi.unstubAllEnvs();
  });

  it('should show support information', () => {
    render(<AppErrorScreen />);

    expect(screen.getByText('Need help?')).toBeInTheDocument();
    expect(screen.getByText(/try reloading the page or contact support/i)).toBeInTheDocument();
  });

  it('should show development mode notice in dev environment', () => {
    vi.stubEnv('DEV', true);

    render(<AppErrorScreen />);

    // Use getAllBy since text may appear multiple times
    const devModeElements = screen.getAllByText(/Development Mode/i);
    expect(devModeElements.length).toBeGreaterThan(0);

    vi.unstubAllEnvs();
  });

  it('should hide development mode notice in production', () => {
    vi.stubEnv('DEV', false);

    render(<AppErrorScreen />);

    expect(screen.queryByText(/Development Mode/i)).not.toBeInTheDocument();

    vi.unstubAllEnvs();
  });

  it('should handle error without stack trace', () => {
    const error = new Error('Test error');
    error.stack = undefined;

    vi.stubEnv('DEV', true);

    render(<AppErrorScreen error={error} />);

    expect(screen.getByText('Test error')).toBeInTheDocument();
    // When no stack, the details element shouldn't be present
    const stackTraceElements = screen.queryAllByText(/Stack Trace/i);
    expect(stackTraceElements.length).toBe(0);

    vi.unstubAllEnvs();
  });

  it('should render all UI elements correctly', () => {
    const onRetry = vi.fn();
    const error = new Error('Critical error');

    vi.stubEnv('DEV', true);

    render(<AppErrorScreen error={error} onRetry={onRetry} />);

    // Check for icon
    const icon = document.querySelector('svg');
    expect(icon).toBeInTheDocument();

    // Check for main heading
    expect(screen.getByRole('heading', { name: 'Application Error' })).toBeInTheDocument();

    // Check for both buttons
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reload application/i })).toBeInTheDocument();

    // Check for error details
    const errorDetailsElements = screen.getAllByText(/Error Details/i);
    expect(errorDetailsElements.length).toBeGreaterThan(0);

    vi.unstubAllEnvs();
  });
});
