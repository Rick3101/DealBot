/**
 * Tests for Brambler Service
 *
 * Tests pirate name generation, decryption, and retrieval.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { bramblerService, BramblerService } from './bramblerService';
import { httpClient } from './httpClient';

// Mock httpClient
vi.mock('./httpClient', () => ({
  httpClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('BramblerService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockPirateNames = [
    {
      pirate_name: 'Captain Blackbeard',
      real_name_encrypted: 'encrypted_string_1',
    },
    {
      pirate_name: 'Red Rackham',
      real_name_encrypted: 'encrypted_string_2',
    },
  ];

  const mockDecryptedMapping = {
    'Captain Blackbeard': 'John Doe',
    'Red Rackham': 'Jane Smith',
  };

  describe('generateNames', () => {
    const generateRequest = {
      buyer_names: ['John Doe', 'Jane Smith'],
      owner_key: 'test_owner_key',
    };

    it('should generate pirate names', async () => {
      vi.mocked(httpClient.post).mockResolvedValue({
        data: { pirate_names: mockPirateNames },
      } as any);

      const result = await bramblerService.generateNames(1, generateRequest);

      expect(httpClient.post).toHaveBeenCalledWith('/api/brambler/generate/1', generateRequest);
      expect(result).toEqual(mockPirateNames);
    });

    it('should handle single buyer', async () => {
      const singleBuyer = {
        buyer_names: ['John Doe'],
        owner_key: 'test_key',
      };

      vi.mocked(httpClient.post).mockResolvedValue({
        data: { pirate_names: [mockPirateNames[0]] },
      } as any);

      const result = await bramblerService.generateNames(1, singleBuyer);

      expect(result).toHaveLength(1);
    });

    it('should handle multiple buyers', async () => {
      const multipleBuyers = {
        buyer_names: ['John', 'Jane', 'Bob', 'Alice'],
        owner_key: 'test_key',
      };

      vi.mocked(httpClient.post).mockResolvedValue({
        data: { pirate_names: mockPirateNames },
      } as any);

      await bramblerService.generateNames(1, multipleBuyers);

      expect(httpClient.post).toHaveBeenCalledWith('/api/brambler/generate/1', multipleBuyers);
    });

    it('should propagate errors', async () => {
      const error = new Error('Failed to generate names');
      vi.mocked(httpClient.post).mockRejectedValue(error);

      await expect(bramblerService.generateNames(1, generateRequest)).rejects.toThrow(
        'Failed to generate names'
      );
    });
  });

  describe('decryptNames', () => {
    const decryptRequest = {
      owner_key: 'test_owner_key',
    };

    it('should decrypt pirate names', async () => {
      vi.mocked(httpClient.post).mockResolvedValue({
        data: { decrypted_mapping: mockDecryptedMapping },
      } as any);

      const result = await bramblerService.decryptNames(1, decryptRequest);

      expect(httpClient.post).toHaveBeenCalledWith('/api/brambler/decrypt/1', decryptRequest);
      expect(result).toEqual(mockDecryptedMapping);
    });

    it('should handle empty mapping', async () => {
      vi.mocked(httpClient.post).mockResolvedValue({
        data: { decrypted_mapping: {} },
      } as any);

      const result = await bramblerService.decryptNames(1, decryptRequest);

      expect(result).toEqual({});
    });

    it('should propagate errors for invalid key', async () => {
      const error = new Error('Invalid owner key');
      vi.mocked(httpClient.post).mockRejectedValue(error);

      await expect(bramblerService.decryptNames(1, decryptRequest)).rejects.toThrow(
        'Invalid owner key'
      );
    });
  });

  describe('getNames', () => {
    it('should fetch pirate names for expedition', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { pirate_names: mockPirateNames },
      } as any);

      const result = await bramblerService.getNames(1);

      expect(httpClient.get).toHaveBeenCalledWith('/api/brambler/names/1');
      expect(result).toEqual(mockPirateNames);
    });

    it('should handle expedition with no pirates', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { pirate_names: [] },
      } as any);

      const result = await bramblerService.getNames(1);

      expect(result).toEqual([]);
    });

    it('should handle different expedition IDs', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { pirate_names: mockPirateNames },
      } as any);

      await bramblerService.getNames(42);

      expect(httpClient.get).toHaveBeenCalledWith('/api/brambler/names/42');
    });

    it('should propagate errors', async () => {
      const error = new Error('Failed to fetch names');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(bramblerService.getNames(1)).rejects.toThrow('Failed to fetch names');
    });
  });

  describe('Service Instance', () => {
    it('should export a singleton instance', () => {
      expect(bramblerService).toBeInstanceOf(BramblerService);
    });

    it('should export the class for testing', () => {
      expect(BramblerService).toBeDefined();
      const newInstance = new BramblerService();
      expect(newInstance).toBeInstanceOf(BramblerService);
    });
  });
});
