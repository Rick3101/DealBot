/**
 * User Service
 *
 * Handles user and buyer-related operations.
 * Domain: User management only.
 */

import { httpClient } from './httpClient';

/**
 * User data interface
 */
export interface User {
  username: string;
  level: string;
  total_purchases: string;
  last_access: string;
  status: string;
}

/**
 * Buyer data interface
 */
export interface Buyer {
  name: string;
}

/**
 * User Service
 *
 * Responsible for:
 * - Getting user list
 * - Getting buyer list
 * - User management operations (future expansion)
 */
class UserService {
  private readonly usersPath = '/api/users';
  private readonly buyersPath = '/api/buyers';

  /**
   * Get all users
   */
  async getUsers(): Promise<User[]> {
    const response = await httpClient.get<{ users: User[] }>(this.usersPath);
    return response.data.users;
  }

  /**
   * Get all buyers (from sales)
   */
  async getBuyers(): Promise<Buyer[]> {
    const response = await httpClient.get<{ buyers: Buyer[] }>(this.buyersPath);
    return response.data.buyers;
  }
}

// Create and export singleton instance
export const userService = new UserService();

// Export class for testing
export { UserService };
