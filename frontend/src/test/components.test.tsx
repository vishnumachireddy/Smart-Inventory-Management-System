import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Package } from 'lucide-react';
import { StatCard, Badge, Modal, EmptyState, LoadingSpinner } from '../components/common';

describe('Common UI Components', () => {
  it('renders StatCard with title, value, and triggers click callback', () => {
    const handleClick = vi.fn();
    render(
      <StatCard
        title="Total Stock"
        value={150}
        subtitle="Eligible units"
        icon={Package}
        variant="info"
        onClick={handleClick}
      />
    );

    expect(screen.getByText('Total Stock')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('Eligible units')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Total Stock'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders Badge with appropriate styling variant', () => {
    render(<Badge variant="danger">Expired</Badge>);
    const badge = screen.getByText('Expired');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('text-rose-800');
  });

  it('renders Modal when isOpen is true and invokes onClose', () => {
    const handleClose = vi.fn();
    const { rerender } = render(
      <Modal isOpen={true} onClose={handleClose} title="Test Dialog">
        <p>Modal Body Content</p>
      </Modal>
    );

    expect(screen.getByText('Test Dialog')).toBeInTheDocument();
    expect(screen.getByText('Modal Body Content')).toBeInTheDocument();

    fireEvent.click(screen.getByText('✕'));
    expect(handleClose).toHaveBeenCalledTimes(1);

    rerender(
      <Modal isOpen={false} onClose={handleClose} title="Test Dialog">
        <p>Modal Body Content</p>
      </Modal>
    );
    expect(screen.queryByText('Test Dialog')).not.toBeInTheDocument();
  });

  it('renders EmptyState with action callback', () => {
    const handleAction = vi.fn();
    render(
      <EmptyState
        title="No Inventory Found"
        description="Try clearing your filters."
        actionText="Reset Filters"
        onAction={handleAction}
      />
    );

    expect(screen.getByText('No Inventory Found')).toBeInTheDocument();
    expect(screen.getByText('Try clearing your filters.')).toBeInTheDocument();

    const actionBtn = screen.getByText('Reset Filters');
    fireEvent.click(actionBtn);
    expect(handleAction).toHaveBeenCalledTimes(1);
  });

  it('renders LoadingSpinner with custom label', () => {
    render(<LoadingSpinner label="Auditing database records..." />);
    expect(screen.getByText('Auditing database records...')).toBeInTheDocument();
  });
});
