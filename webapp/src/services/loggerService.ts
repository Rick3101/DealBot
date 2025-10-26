import { openDB, DBSchema, IDBPDatabase } from 'idb';

// Log levels
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
  FATAL = 'fatal',
}

// Log entry interface
export interface LogEntry {
  id?: number;
  timestamp: number;
  level: LogLevel;
  message: string;
  context?: string;
  data?: any;
  userAgent?: string;
  url?: string;
  stackTrace?: string;
}

// Database schema
interface LogDB extends DBSchema {
  logs: {
    key: number;
    value: LogEntry;
    indexes: {
      'by-timestamp': number;
      'by-level': LogLevel;
      'by-context': string;
    };
  };
}

class LoggerService {
  private db: IDBPDatabase<LogDB> | null = null;
  private readonly DB_NAME = 'PiratesExpeditionLogs';
  private readonly DB_VERSION = 1;
  private readonly STORE_NAME = 'logs';
  private readonly MAX_LOGS = 10000; // Maximum number of logs to keep
  private initPromise: Promise<void>;

  constructor() {
    this.initPromise = this.initDB();
  }

  private async initDB(): Promise<void> {
    try {
      this.db = await openDB<LogDB>(this.DB_NAME, this.DB_VERSION, {
        upgrade(db) {
          // Create logs store if it doesn't exist
          if (!db.objectStoreNames.contains('logs')) {
            const store = db.createObjectStore('logs', {
              keyPath: 'id',
              autoIncrement: true,
            });

            // Create indexes for efficient querying
            store.createIndex('by-timestamp', 'timestamp');
            store.createIndex('by-level', 'level');
            store.createIndex('by-context', 'context');
          }
        },
      });

      console.log('Logger Service: IndexedDB initialized');
    } catch (error) {
      console.error('Logger Service: Failed to initialize IndexedDB', error);
    }
  }

  private async ensureDB(): Promise<void> {
    await this.initPromise;
  }

  // Core logging method
  private async log(
    level: LogLevel,
    message: string,
    context?: string,
    data?: any,
    error?: Error
  ): Promise<void> {
    await this.ensureDB();

    if (!this.db) {
      console.warn('Logger Service: Database not available, logging to console only');
      this.consoleLog(level, message, context, data, error);
      return;
    }

    const logEntry: LogEntry = {
      timestamp: Date.now(),
      level,
      message,
      context,
      data,
      userAgent: navigator.userAgent,
      url: window.location.href,
      stackTrace: error?.stack || new Error().stack,
    };

    try {
      // Add to IndexedDB
      await this.db.add(this.STORE_NAME, logEntry);

      // Also log to console in development
      if (import.meta.env.DEV) {
        this.consoleLog(level, message, context, data, error);
      }

      // Clean up old logs if we exceed max
      await this.cleanupOldLogs();
    } catch (err) {
      console.error('Logger Service: Failed to store log', err);
      this.consoleLog(level, message, context, data, err instanceof Error ? err : undefined);
    }
  }

  private consoleLog(
    level: LogLevel,
    message: string,
    context?: string,
    data?: any,
    error?: Error
  ): void {
    const prefix = context ? `[${context}]` : '';
    const fullMessage = `${prefix} ${message}`;

    switch (level) {
      case LogLevel.DEBUG:
        console.debug(fullMessage, data || '');
        break;
      case LogLevel.INFO:
        console.info(fullMessage, data || '');
        break;
      case LogLevel.WARN:
        console.warn(fullMessage, data || '');
        break;
      case LogLevel.ERROR:
      case LogLevel.FATAL:
        console.error(fullMessage, data || '', error || '');
        break;
    }
  }

  // Public logging methods
  public async debug(message: string, context?: string, data?: any): Promise<void> {
    await this.log(LogLevel.DEBUG, message, context, data);
  }

  public async info(message: string, context?: string, data?: any): Promise<void> {
    await this.log(LogLevel.INFO, message, context, data);
  }

  public async warn(message: string, context?: string, data?: any): Promise<void> {
    await this.log(LogLevel.WARN, message, context, data);
  }

  public async error(message: string, context?: string, error?: Error, data?: any): Promise<void> {
    await this.log(LogLevel.ERROR, message, context, data, error);
  }

  public async fatal(message: string, context?: string, error?: Error, data?: any): Promise<void> {
    await this.log(LogLevel.FATAL, message, context, data, error);
  }

  // Query logs
  public async getLogs(options?: {
    level?: LogLevel;
    context?: string;
    startTime?: number;
    endTime?: number;
    limit?: number;
  }): Promise<LogEntry[]> {
    await this.ensureDB();

    if (!this.db) return [];

    try {
      let logs: LogEntry[] = [];

      // Query by level if specified
      if (options?.level) {
        logs = await this.db.getAllFromIndex(this.STORE_NAME, 'by-level', options.level);
      }
      // Query by context if specified
      else if (options?.context) {
        logs = await this.db.getAllFromIndex(this.STORE_NAME, 'by-context', options.context);
      }
      // Get all logs
      else {
        logs = await this.db.getAll(this.STORE_NAME);
      }

      // Filter by time range
      if (options?.startTime || options?.endTime) {
        logs = logs.filter((log) => {
          if (options.startTime && log.timestamp < options.startTime) return false;
          if (options.endTime && log.timestamp > options.endTime) return false;
          return true;
        });
      }

      // Sort by timestamp descending (newest first)
      logs.sort((a, b) => b.timestamp - a.timestamp);

      // Limit results
      if (options?.limit) {
        logs = logs.slice(0, options.limit);
      }

      return logs;
    } catch (error) {
      console.error('Logger Service: Failed to query logs', error);
      return [];
    }
  }

  // Get log statistics
  public async getStats(): Promise<{
    total: number;
    byLevel: Record<LogLevel, number>;
    oldestLog?: number;
    newestLog?: number;
  }> {
    await this.ensureDB();

    if (!this.db) {
      return {
        total: 0,
        byLevel: {
          [LogLevel.DEBUG]: 0,
          [LogLevel.INFO]: 0,
          [LogLevel.WARN]: 0,
          [LogLevel.ERROR]: 0,
          [LogLevel.FATAL]: 0,
        },
      };
    }

    try {
      const allLogs = await this.db.getAll(this.STORE_NAME);

      const byLevel = {
        [LogLevel.DEBUG]: 0,
        [LogLevel.INFO]: 0,
        [LogLevel.WARN]: 0,
        [LogLevel.ERROR]: 0,
        [LogLevel.FATAL]: 0,
      };

      let oldestLog: number | undefined;
      let newestLog: number | undefined;

      allLogs.forEach((log) => {
        byLevel[log.level]++;
        if (!oldestLog || log.timestamp < oldestLog) oldestLog = log.timestamp;
        if (!newestLog || log.timestamp > newestLog) newestLog = log.timestamp;
      });

      return {
        total: allLogs.length,
        byLevel,
        oldestLog,
        newestLog,
      };
    } catch (error) {
      console.error('Logger Service: Failed to get stats', error);
      return {
        total: 0,
        byLevel: {
          [LogLevel.DEBUG]: 0,
          [LogLevel.INFO]: 0,
          [LogLevel.WARN]: 0,
          [LogLevel.ERROR]: 0,
          [LogLevel.FATAL]: 0,
        },
      };
    }
  }

  // Clean up old logs to prevent database from growing too large
  private async cleanupOldLogs(): Promise<void> {
    if (!this.db) return;

    try {
      const count = await this.db.count(this.STORE_NAME);

      if (count > this.MAX_LOGS) {
        const logsToDelete = count - this.MAX_LOGS;
        const oldestLogs = await this.db.getAllFromIndex(
          this.STORE_NAME,
          'by-timestamp',
          undefined,
          logsToDelete
        );

        const tx = this.db.transaction(this.STORE_NAME, 'readwrite');

        for (const log of oldestLogs) {
          if (log.id) {
            await tx.store.delete(log.id);
          }
        }

        await tx.done;

        console.log(`Logger Service: Cleaned up ${logsToDelete} old logs`);
      }
    } catch (error) {
      console.error('Logger Service: Failed to cleanup logs', error);
    }
  }

  // Clear all logs
  public async clearLogs(): Promise<void> {
    await this.ensureDB();

    if (!this.db) return;

    try {
      await this.db.clear(this.STORE_NAME);
      console.log('Logger Service: All logs cleared');
    } catch (error) {
      console.error('Logger Service: Failed to clear logs', error);
    }
  }

  // Export logs as JSON
  public async exportLogs(): Promise<string> {
    const logs = await this.getLogs();
    return JSON.stringify(logs, null, 2);
  }

  // Export logs as CSV
  public async exportLogsCSV(): Promise<string> {
    const logs = await this.getLogs();

    if (logs.length === 0) return '';

    const headers = ['Timestamp', 'Level', 'Context', 'Message', 'Data', 'URL', 'User Agent'];
    const rows = logs.map((log) => [
      new Date(log.timestamp).toISOString(),
      log.level,
      log.context || '',
      log.message,
      log.data ? JSON.stringify(log.data) : '',
      log.url || '',
      log.userAgent || '',
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) =>
        row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')
      ),
    ].join('\n');

    return csvContent;
  }

  // Download logs
  public async downloadLogs(format: 'json' | 'csv' = 'json'): Promise<void> {
    const content = format === 'json' ? await this.exportLogs() : await this.exportLogsCSV();
    const blob = new Blob([content], {
      type: format === 'json' ? 'application/json' : 'text/csv',
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pirates-expedition-logs-${Date.now()}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    await this.info('Logs downloaded', 'LoggerService', { format });
  }
}

// Create and export singleton instance
export const logger = new LoggerService();

// Export convenience functions
export const logDebug = (message: string, context?: string, data?: any) =>
  logger.debug(message, context, data);

export const logInfo = (message: string, context?: string, data?: any) =>
  logger.info(message, context, data);

export const logWarn = (message: string, context?: string, data?: any) =>
  logger.warn(message, context, data);

export const logError = (message: string, context?: string, error?: Error, data?: any) =>
  logger.error(message, context, error, data);

export const logFatal = (message: string, context?: string, error?: Error, data?: any) =>
  logger.fatal(message, context, error, data);
