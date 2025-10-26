/**
 * Expedition Transform Utilities
 *
 * Centralized data transformation functions for expeditions.
 * These pure functions ensure consistent data shape normalization
 * across the application.
 */

import {
  Expedition,
  ExpeditionTimelineEntry,
  ExpeditionProgress,
  DashboardStats,
  ExpeditionDetails,
} from '@/types/expedition';

/**
 * Creates fallback statistics from expedition array
 *
 * Used when timeline API doesn't return stats
 *
 * @param expeditions - Array of expeditions
 * @returns Dashboard statistics
 */
export const createFallbackStats = (expeditions: Expedition[]): DashboardStats => {
  return {
    total_expeditions: expeditions.length,
    active_expeditions: expeditions.filter(e => e.status === 'active').length,
    completed_expeditions: expeditions.filter(e => e.status === 'completed').length,
    overdue_expeditions: expeditions.filter(e =>
      e.deadline &&
      new Date(e.deadline) < new Date() &&
      e.status === 'active'
    ).length,
  };
};

/**
 * Creates empty progress object
 *
 * @returns Empty expedition progress
 */
export const createEmptyProgress = (): ExpeditionProgress => {
  return {
    completion_percentage: 0,
    total_items: 0,
    consumed_items: 0,
    remaining_items: 0,
    total_value: 0,
    consumed_value: 0,
    remaining_value: 0,
  };
};

/**
 * Checks if expedition is overdue
 *
 * @param expedition - The expedition to check
 * @returns true if expedition has a deadline in the past and is active
 */
export const isExpeditionOverdue = (expedition: Expedition): boolean => {
  return expedition.deadline
    ? new Date(expedition.deadline) < new Date() && expedition.status === 'active'
    : false;
};

/**
 * Transforms expedition to timeline entry
 *
 * Adds overdue flag and progress (with empty progress as default)
 *
 * @param expedition - The expedition to transform
 * @param progress - Optional progress data
 * @returns Timeline entry
 */
export const toTimelineEntry = (
  expedition: Expedition,
  progress?: ExpeditionProgress
): ExpeditionTimelineEntry => {
  return {
    ...expedition,
    is_overdue: isExpeditionOverdue(expedition),
    progress: progress || createEmptyProgress(),
  };
};

/**
 * Transforms expedition array to timeline entries
 *
 * Used as fallback when timeline API doesn't return data
 *
 * @param expeditions - Array of expeditions
 * @returns Array of timeline entries with default progress
 */
export const toTimelineEntries = (expeditions: Expedition[]): ExpeditionTimelineEntry[] => {
  return expeditions.map(exp => toTimelineEntry(exp));
};

/**
 * Calculates progress percentage
 *
 * @param consumed - Number of consumed items or value
 * @param total - Total number of items or value
 * @returns Progress percentage (0-100)
 */
export const calculateProgressPercentage = (consumed: number, total: number): number => {
  if (total === 0) return 0;
  return Math.round((consumed / total) * 100);
};

/**
 * Transforms expedition details to form data
 *
 * Useful for editing expeditions
 *
 * @param expedition - The expedition details
 * @returns Form data object
 */
export const toFormData = (expedition: ExpeditionDetails): {
  name: string;
  description: string;
  deadline: string;
} => {
  return {
    name: expedition.name,
    description: expedition.description || '',
    deadline: expedition.deadline || '',
  };
};

/**
 * Calculates remaining days until deadline
 *
 * @param deadline - ISO date string
 * @returns Number of days remaining (negative if overdue)
 */
export const calculateDaysRemaining = (deadline: string): number => {
  const deadlineDate = new Date(deadline);
  const today = new Date();
  const diffTime = deadlineDate.getTime() - today.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
};

/**
 * Checks if deadline is approaching (within 3 days)
 *
 * @param deadline - ISO date string
 * @returns true if deadline is within 3 days
 */
export const isDeadlineApproaching = (deadline: string): boolean => {
  const daysRemaining = calculateDaysRemaining(deadline);
  return daysRemaining >= 0 && daysRemaining <= 3;
};

/**
 * Gets deadline status
 *
 * @param deadline - ISO date string
 * @param status - Expedition status
 * @returns 'overdue' | 'approaching' | 'normal' | 'none'
 */
export const getDeadlineStatus = (
  deadline: string | undefined,
  status: string
): 'overdue' | 'approaching' | 'normal' | 'none' => {
  if (!deadline || status !== 'active') return 'none';

  const daysRemaining = calculateDaysRemaining(deadline);

  if (daysRemaining < 0) return 'overdue';
  if (daysRemaining <= 3) return 'approaching';
  return 'normal';
};

/**
 * Sorts expeditions by priority
 *
 * Priority order: overdue > approaching deadline > active > completed
 *
 * @param expeditions - Array of timeline entries
 * @returns Sorted array
 */
export const sortByPriority = (expeditions: ExpeditionTimelineEntry[]): ExpeditionTimelineEntry[] => {
  return [...expeditions].sort((a, b) => {
    // Overdue first
    if (a.is_overdue && !b.is_overdue) return -1;
    if (!a.is_overdue && b.is_overdue) return 1;

    // Then approaching deadline
    const aApproaching = a.deadline && isDeadlineApproaching(a.deadline);
    const bApproaching = b.deadline && isDeadlineApproaching(b.deadline);
    if (aApproaching && !bApproaching) return -1;
    if (!aApproaching && bApproaching) return 1;

    // Then by status (active > completed > cancelled)
    const statusOrder = { active: 0, completed: 1, cancelled: 2 };
    const aOrder = statusOrder[a.status] || 99;
    const bOrder = statusOrder[b.status] || 99;
    if (aOrder !== bOrder) return aOrder - bOrder;

    // Finally by creation date (newest first)
    if (a.created_at && b.created_at) {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    }

    return 0;
  });
};

/**
 * Filters expeditions by status
 *
 * @param expeditions - Array of expeditions
 * @param status - Status to filter by
 * @returns Filtered array
 */
export const filterByStatus = (
  expeditions: Expedition[],
  status: 'active' | 'completed' | 'cancelled'
): Expedition[] => {
  return expeditions.filter(e => e.status === status);
};

/**
 * Groups expeditions by status
 *
 * @param expeditions - Array of expeditions
 * @returns Object with expeditions grouped by status
 */
export const groupByStatus = (expeditions: Expedition[]): {
  active: Expedition[];
  completed: Expedition[];
  cancelled: Expedition[];
} => {
  return {
    active: filterByStatus(expeditions, 'active'),
    completed: filterByStatus(expeditions, 'completed'),
    cancelled: filterByStatus(expeditions, 'cancelled'),
  };
};
