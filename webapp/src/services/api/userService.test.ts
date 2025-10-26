/**
 * Tests for User Service
 *
 * Tests user and buyer operations.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { userService, UserService } from './userService';
import { httpClient } from './httpClient';

// Mock httpClient
vi.mock('./httpClient', () => ({
  httpClient: {
    get: vi.fn(),
  },
}));

describe('UserService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockUsers = [
    {
      username: 'john_doe',
      level: 'admin',
      total_purchases: '150.00',
      last_access: '2025-01-01T00:00:00Z',
      status: 'active',
    },
    {
      username: 'jane_smith',
      level: 'user',
      total_purchases: '75.50',
      last_access: '2025-01-02T00:00:00Z',
      status: 'active',
    },
  ];

  const mockBuyers = [
    { name: 'John Doe' },
    { name: 'Jane Smith' },
    { name: 'Bob Johnson' },
  ];

  describe('getUsers', () => {
    it('should fetch all users', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { users: mockUsers },
      } as any);

      const result = await userService.getUsers();

      expect(httpClient.get).toHaveBeenCalledWith('/api/users');
      expect(result).toEqual(mockUsers);
    });

    it('should handle empty user list', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { users: [] },
      } as any);

      const result = await userService.getUsers();

      expect(result).toEqual([]);
    });

    it('should handle users with different levels', async () => {
      const usersWithLevels = [
        { ...mockUsers[0], level: 'owner' },
        { ...mockUsers[1], level: 'admin' },
      ];

      vi.mocked(httpClient.get).mockResolvedValue({
        data: { users: usersWithLevels },
      } as any);

      const result = await userService.getUsers();

      expect(result[0].level).toBe('owner');
      expect(result[1].level).toBe('admin');
    });

    it('should handle users with different statuses', async () => {
      const usersWithStatuses = [
        { ...mockUsers[0], status: 'active' },
        { ...mockUsers[1], status: 'inactive' },
      ];

      vi.mocked(httpClient.get).mockResolvedValue({
        data: { users: usersWithStatuses },
      } as any);

      const result = await userService.getUsers();

      expect(result[0].status).toBe('active');
      expect(result[1].status).toBe('inactive');
    });

    it('should propagate errors', async () => {
      const error = new Error('Failed to fetch users');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(userService.getUsers()).rejects.toThrow('Failed to fetch users');
    });
  });

  describe('getBuyers', () => {
    it('should fetch all buyers', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { buyers: mockBuyers },
      } as any);

      const result = await userService.getBuyers();

      expect(httpClient.get).toHaveBeenCalledWith('/api/buyers');
      expect(result).toEqual(mockBuyers);
    });

    it('should handle empty buyer list', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { buyers: [] },
      } as any);

      const result = await userService.getBuyers();

      expect(result).toEqual([]);
    });

    it('should handle single buyer', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { buyers: [mockBuyers[0]] },
      } as any);

      const result = await userService.getBuyers();

      expect(result).toHaveLength(1);
      expect(result[0].name).toBe('John Doe');
    });

    it('should handle large buyer list', async () => {
      const manyBuyers = Array.from({ length: 100 }, (_, i) => ({
        name: `Buyer ${i + 1}`,
      }));

      vi.mocked(httpClient.get).mockResolvedValue({
        data: { buyers: manyBuyers },
      } as any);

      const result = await userService.getBuyers();

      expect(result).toHaveLength(100);
    });

    it('should propagate errors', async () => {
      const error = new Error('Failed to fetch buyers');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(userService.getBuyers()).rejects.toThrow('Failed to fetch buyers');
    });
  });

  describe('Service Instance', () => {
    it('should export a singleton instance', () => {
      expect(userService).toBeInstanceOf(UserService);
    });

    it('should export the class for testing', () => {
      expect(UserService).toBeDefined();
      const newInstance = new UserService();
      expect(newInstance).toBeInstanceOf(UserService);
    });
  });
});
