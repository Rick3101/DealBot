import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { Expedition, ExpeditionTimelineEntry, ExpeditionDetails } from '@/types/expedition';
import {
  createFallbackStats,
  createEmptyProgress,
  isExpeditionOverdue,
  toTimelineEntry,
  toTimelineEntries,
  calculateProgressPercentage,
  toFormData,
  calculateDaysRemaining,
  isDeadlineApproaching,
  getDeadlineStatus,
  sortByPriority,
  filterByStatus,
  groupByStatus
} from './expeditionTransforms';

describe('expeditionTransforms', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2025-10-05T12:00:00Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('createFallbackStats', () => {
    it('should calculate correct stats from expeditions', () => {
      const expeditions: Expedition[] = [
        { id: 1, status: 'active', name: 'E1', deadline: '2025-10-10' } as Expedition,
        { id: 2, status: 'active', name: 'E2', deadline: '2025-10-03' } as Expedition,
        { id: 3, status: 'completed', name: 'E3' } as Expedition,
        { id: 4, status: 'active', name: 'E4' } as Expedition,
      ];

      const stats = createFallbackStats(expeditions);

      expect(stats.total_expeditions).toBe(4);
      expect(stats.active_expeditions).toBe(3);
      expect(stats.completed_expeditions).toBe(1);
      expect(stats.overdue_expeditions).toBe(1); // E2 is overdue
    });

    it('should handle empty array', () => {
      const stats = createFallbackStats([]);

      expect(stats.total_expeditions).toBe(0);
      expect(stats.active_expeditions).toBe(0);
      expect(stats.completed_expeditions).toBe(0);
      expect(stats.overdue_expeditions).toBe(0);
    });

    it('should not count completed expeditions as overdue', () => {
      const expeditions: Expedition[] = [
        { id: 1, status: 'completed', name: 'E1', deadline: '2025-10-03' } as Expedition,
      ];

      const stats = createFallbackStats(expeditions);
      expect(stats.overdue_expeditions).toBe(0);
    });
  });

  describe('createEmptyProgress', () => {
    it('should create progress with all zeros', () => {
      const progress = createEmptyProgress();

      expect(progress.completion_percentage).toBe(0);
      expect(progress.total_items).toBe(0);
      expect(progress.consumed_items).toBe(0);
      expect(progress.remaining_items).toBe(0);
      expect(progress.total_value).toBe(0);
      expect(progress.consumed_value).toBe(0);
      expect(progress.remaining_value).toBe(0);
    });
  });

  describe('isExpeditionOverdue', () => {
    it('should return true for active expedition with past deadline', () => {
      const expedition: Expedition = {
        id: 1,
        status: 'active',
        deadline: '2025-10-03',
        name: 'Test'
      } as Expedition;

      expect(isExpeditionOverdue(expedition)).toBe(true);
    });

    it('should return false for active expedition with future deadline', () => {
      const expedition: Expedition = {
        id: 1,
        status: 'active',
        deadline: '2025-10-10',
        name: 'Test'
      } as Expedition;

      expect(isExpeditionOverdue(expedition)).toBe(false);
    });

    it('should return false for completed expedition with past deadline', () => {
      const expedition: Expedition = {
        id: 1,
        status: 'completed',
        deadline: '2025-10-03',
        name: 'Test'
      } as Expedition;

      expect(isExpeditionOverdue(expedition)).toBe(false);
    });

    it('should return false for expedition without deadline', () => {
      const expedition: Expedition = {
        id: 1,
        status: 'active',
        name: 'Test'
      } as Expedition;

      expect(isExpeditionOverdue(expedition)).toBe(false);
    });
  });

  describe('toTimelineEntry', () => {
    it('should add is_overdue flag and empty progress', () => {
      const expedition: Expedition = {
        id: 1,
        status: 'active',
        deadline: '2025-10-03',
        name: 'Test'
      } as Expedition;

      const entry = toTimelineEntry(expedition);

      expect(entry.is_overdue).toBe(true);
      expect(entry.progress).toEqual(createEmptyProgress());
    });

    it('should use provided progress', () => {
      const expedition: Expedition = {
        id: 1,
        status: 'active',
        name: 'Test'
      } as Expedition;

      const progress = {
        completion_percentage: 50,
        total_items: 10,
        consumed_items: 5,
        remaining_items: 5,
        total_value: 100,
        consumed_value: 50,
        remaining_value: 50
      };

      const entry = toTimelineEntry(expedition, progress);

      expect(entry.progress).toEqual(progress);
    });
  });

  describe('toTimelineEntries', () => {
    it('should transform array of expeditions', () => {
      const expeditions: Expedition[] = [
        { id: 1, status: 'active', name: 'E1' } as Expedition,
        { id: 2, status: 'active', name: 'E2' } as Expedition,
      ];

      const entries = toTimelineEntries(expeditions);

      expect(entries).toHaveLength(2);
      expect(entries[0]).toHaveProperty('is_overdue');
      expect(entries[0]).toHaveProperty('progress');
      expect(entries[1]).toHaveProperty('is_overdue');
      expect(entries[1]).toHaveProperty('progress');
    });
  });

  describe('calculateProgressPercentage', () => {
    it('should calculate correct percentage', () => {
      expect(calculateProgressPercentage(5, 10)).toBe(50);
      expect(calculateProgressPercentage(7, 10)).toBe(70);
      expect(calculateProgressPercentage(3, 10)).toBe(30);
    });

    it('should round to nearest integer', () => {
      expect(calculateProgressPercentage(1, 3)).toBe(33);
      expect(calculateProgressPercentage(2, 3)).toBe(67);
    });

    it('should handle 100% correctly', () => {
      expect(calculateProgressPercentage(10, 10)).toBe(100);
    });

    it('should handle 0% correctly', () => {
      expect(calculateProgressPercentage(0, 10)).toBe(0);
    });

    it('should return 0 for division by zero', () => {
      expect(calculateProgressPercentage(5, 0)).toBe(0);
    });
  });

  describe('toFormData', () => {
    it('should extract form fields from expedition details', () => {
      const expedition: ExpeditionDetails = {
        id: 1,
        name: 'Test Expedition',
        description: 'Test Description',
        deadline: '2025-10-10',
        status: 'active',
        owner_chat_id: 123,
        items: [],
        consumptions: [],
        progress: {
          total_items: 0,
          consumed_items: 0,
          remaining_items: 0,
          completion_percentage: 0,
          total_value: 0,
          consumed_value: 0,
          remaining_value: 0
        }
      };

      const formData = toFormData(expedition);

      expect(formData.name).toBe('Test Expedition');
      expect(formData.description).toBe('Test Description');
      expect(formData.deadline).toBe('2025-10-10');
    });

    it('should handle missing optional fields', () => {
      const expedition: ExpeditionDetails = {
        id: 1,
        name: 'Test Expedition',
        status: 'active',
        owner_chat_id: 123,
        items: [],
        consumptions: [],
        progress: {
          total_items: 0,
          consumed_items: 0,
          remaining_items: 0,
          completion_percentage: 0,
          total_value: 0,
          consumed_value: 0,
          remaining_value: 0
        }
      };

      const formData = toFormData(expedition);

      expect(formData.name).toBe('Test Expedition');
      expect(formData.description).toBe('');
      expect(formData.deadline).toBe('');
    });
  });

  describe('calculateDaysRemaining', () => {
    it('should calculate positive days for future dates', () => {
      // Today is Oct 5, deadline is Oct 10
      expect(calculateDaysRemaining('2025-10-10')).toBe(5);
      expect(calculateDaysRemaining('2025-10-08')).toBe(3);
    });

    it('should calculate negative days for past dates', () => {
      // Today is Oct 5, deadline was Oct 3
      expect(calculateDaysRemaining('2025-10-03')).toBe(-2);
    });

    it('should return 0 for today', () => {
      const result = calculateDaysRemaining('2025-10-05');
      // Accept both 0 and -0 as they are equivalent
      expect(Math.abs(result)).toBe(0);
    });

    it('should use ceiling for fractional days', () => {
      // Partial day should round up
      expect(calculateDaysRemaining('2025-10-05T18:00:00Z')).toBe(1);
    });
  });

  describe('isDeadlineApproaching', () => {
    it('should return true for deadlines within 3 days', () => {
      expect(isDeadlineApproaching('2025-10-08')).toBe(true); // 3 days
      expect(isDeadlineApproaching('2025-10-07')).toBe(true); // 2 days
      expect(isDeadlineApproaching('2025-10-06')).toBe(true); // 1 day
    });

    it('should return false for deadlines beyond 3 days', () => {
      expect(isDeadlineApproaching('2025-10-09')).toBe(false); // 4 days
      expect(isDeadlineApproaching('2025-10-15')).toBe(false); // 10 days
    });

    it('should return false for past deadlines', () => {
      expect(isDeadlineApproaching('2025-10-03')).toBe(false);
      expect(isDeadlineApproaching('2025-10-04')).toBe(false);
    });
  });

  describe('getDeadlineStatus', () => {
    it('should return "overdue" for past deadlines on active expeditions', () => {
      expect(getDeadlineStatus('2025-10-03', 'active')).toBe('overdue');
    });

    it('should return "approaching" for deadlines within 3 days', () => {
      expect(getDeadlineStatus('2025-10-08', 'active')).toBe('approaching');
      expect(getDeadlineStatus('2025-10-06', 'active')).toBe('approaching');
    });

    it('should return "normal" for deadlines beyond 3 days', () => {
      expect(getDeadlineStatus('2025-10-09', 'active')).toBe('normal');
      expect(getDeadlineStatus('2025-10-15', 'active')).toBe('normal');
    });

    it('should return "none" for expeditions without deadline', () => {
      expect(getDeadlineStatus(undefined, 'active')).toBe('none');
    });

    it('should return "none" for non-active expeditions', () => {
      expect(getDeadlineStatus('2025-10-03', 'completed')).toBe('none');
      expect(getDeadlineStatus('2025-10-03', 'cancelled')).toBe('none');
    });
  });

  describe('sortByPriority', () => {
    it('should sort overdue expeditions first', () => {
      const expeditions: ExpeditionTimelineEntry[] = [
        { id: 1, status: 'active', deadline: '2025-10-10', is_overdue: false } as ExpeditionTimelineEntry,
        { id: 2, status: 'active', deadline: '2025-10-03', is_overdue: true } as ExpeditionTimelineEntry,
      ];

      const sorted = sortByPriority(expeditions);
      expect(sorted[0].id).toBe(2);
      expect(sorted[1].id).toBe(1);
    });

    it('should sort approaching deadlines after overdue', () => {
      const expeditions: ExpeditionTimelineEntry[] = [
        { id: 1, status: 'active', deadline: '2025-10-15', is_overdue: false } as ExpeditionTimelineEntry,
        { id: 2, status: 'active', deadline: '2025-10-03', is_overdue: true } as ExpeditionTimelineEntry,
        { id: 3, status: 'active', deadline: '2025-10-07', is_overdue: false } as ExpeditionTimelineEntry,
      ];

      const sorted = sortByPriority(expeditions);
      expect(sorted[0].id).toBe(2); // overdue
      expect(sorted[1].id).toBe(3); // approaching (within 3 days)
      expect(sorted[2].id).toBe(1); // normal
    });

    it('should prioritize overdue, approaching, then by status', () => {
      // This test verifies the overall priority system works
      const expeditions: ExpeditionTimelineEntry[] = [
        { id: 1, status: 'active', is_overdue: true, deadline: '2025-10-03' } as ExpeditionTimelineEntry,
        { id: 2, status: 'cancelled', is_overdue: false, deadline: undefined } as ExpeditionTimelineEntry,
        { id: 3, status: 'active', is_overdue: false, deadline: '2025-10-07' } as ExpeditionTimelineEntry,
      ];

      const sorted = sortByPriority(expeditions);

      // Overdue should be first
      expect(sorted[0].is_overdue).toBe(true);
      // Approaching deadline should be second
      expect(sorted[1].deadline).toBe('2025-10-07');
      // No deadline/cancelled last
      expect(sorted[2].status).toBe('cancelled');
    });

    it('should not mutate original array', () => {
      const expeditions: ExpeditionTimelineEntry[] = [
        { id: 1, status: 'completed', is_overdue: false } as ExpeditionTimelineEntry,
        { id: 2, status: 'active', is_overdue: false } as ExpeditionTimelineEntry,
      ];

      const original = [...expeditions];
      sortByPriority(expeditions);

      expect(expeditions).toEqual(original);
    });
  });

  describe('filterByStatus', () => {
    const expeditions: Expedition[] = [
      { id: 1, status: 'active', name: 'E1' } as Expedition,
      { id: 2, status: 'completed', name: 'E2' } as Expedition,
      { id: 3, status: 'active', name: 'E3' } as Expedition,
      { id: 4, status: 'cancelled', name: 'E4' } as Expedition,
    ];

    it('should filter by active status', () => {
      const filtered = filterByStatus(expeditions, 'active');
      expect(filtered).toHaveLength(2);
      expect(filtered.every(e => e.status === 'active')).toBe(true);
    });

    it('should filter by completed status', () => {
      const filtered = filterByStatus(expeditions, 'completed');
      expect(filtered).toHaveLength(1);
      expect(filtered[0].id).toBe(2);
    });

    it('should filter by cancelled status', () => {
      const filtered = filterByStatus(expeditions, 'cancelled');
      expect(filtered).toHaveLength(1);
      expect(filtered[0].id).toBe(4);
    });

    it('should return empty array if no matches', () => {
      const singleExpedition: Expedition[] = [
        { id: 1, status: 'active', name: 'E1' } as Expedition,
      ];
      const filtered = filterByStatus(singleExpedition, 'completed');
      expect(filtered).toHaveLength(0);
    });
  });

  describe('groupByStatus', () => {
    it('should group expeditions by status', () => {
      const expeditions: Expedition[] = [
        { id: 1, status: 'active', name: 'E1' } as Expedition,
        { id: 2, status: 'completed', name: 'E2' } as Expedition,
        { id: 3, status: 'active', name: 'E3' } as Expedition,
        { id: 4, status: 'cancelled', name: 'E4' } as Expedition,
        { id: 5, status: 'completed', name: 'E5' } as Expedition,
      ];

      const grouped = groupByStatus(expeditions);

      expect(grouped.active).toHaveLength(2);
      expect(grouped.completed).toHaveLength(2);
      expect(grouped.cancelled).toHaveLength(1);
    });

    it('should handle empty arrays for missing statuses', () => {
      const expeditions: Expedition[] = [
        { id: 1, status: 'active', name: 'E1' } as Expedition,
      ];

      const grouped = groupByStatus(expeditions);

      expect(grouped.active).toHaveLength(1);
      expect(grouped.completed).toHaveLength(0);
      expect(grouped.cancelled).toHaveLength(0);
    });
  });
});
