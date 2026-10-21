/**
 * Comprehensive logging utility for V.I.S.I.O.N. frontend
 * Handles console, localStorage, and remote logging
 */

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  module: string;
  message: string;
  data?: Record<string, any>;
  stack?: string;
}

class Logger {
  private module: string;
  private isDev: boolean;
  private logs: LogEntry[] = [];
  private maxLogs = 500; // Keep last 500 logs in memory
  private enableRemote: boolean;

  constructor(module: string, enableRemote = false) {
    this.module = module;
    this.isDev = import.meta.env.DEV;
    this.enableRemote = enableRemote;
    this.loadStoredLogs();
  }

  /**
   * Load previously stored logs from localStorage
   */
  private loadStoredLogs() {
    try {
      const stored = sessionStorage.getItem('vision_logs');
      if (stored) {
        this.logs = JSON.parse(stored).slice(-this.maxLogs);
      }
    } catch {
      // Silently fail if localStorage is unavailable
    }
  }

  /**
   * Save logs to sessionStorage (cleared on tab close)
   */
  private persistLogs() {
    try {
      sessionStorage.setItem('vision_logs', JSON.stringify(this.logs));
    } catch {
      // Silently fail if storage quota exceeded
    }
  }

  /**
   * Format log entry for console output
   */
  private formatConsole(entry: LogEntry): string {
    const time = new Date(entry.timestamp).toLocaleTimeString();
    const color = this.getColorForLevel(entry.level);
    return `%c[${time}] [${entry.level}] [${entry.module}] ${entry.message}`;
  }

  /**
   * Get console color for log level
   */
  private getColorForLevel(level: LogLevel): string {
    const colors: Record<LogLevel, string> = {
      [LogLevel.DEBUG]: 'color: #888; font-weight: normal;',
      [LogLevel.INFO]: 'color: #0088ff; font-weight: bold;',
      [LogLevel.WARN]: 'color: #ff8800; font-weight: bold;',
      [LogLevel.ERROR]: 'color: #ff0000; font-weight: bold;',
    };
    return colors[level];
  }

  /**
   * Internal log method
   */
  private log(level: LogLevel, message: string, data?: Record<string, any>, error?: Error) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      module: this.module,
      message,
      data,
      stack: error?.stack,
    };

    // Add to in-memory logs
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // Persist to sessionStorage
    this.persistLogs();

    // Console output (always in dev, errors in prod)
    if (this.isDev || level === LogLevel.ERROR) {
      const formatted = this.formatConsole(entry);
      const style = this.getColorForLevel(level);

      if (data || error) {
        // log: formatted, style, { data, error });
      } else {
        // log: formatted, style);
      }
    }

    // Remote logging for errors
    if (this.enableRemote && level === LogLevel.ERROR) {
      this.sendToRemote(entry);
    }
  }

  /**
   * Send error logs to backend
   */
  private async sendToRemote(entry: LogEntry) {
    try {
      const baseUrl = window.location.hostname === 'localhost'
        ? 'http://127.0.0.1:8000'
        : window.location.origin;

      await fetch(`${baseUrl}/api/logs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry),
      });
    } catch {
      // Silently fail if remote logging unavailable
    }
  }

  /**
   * Log at DEBUG level
   */
  debug(message: string, data?: Record<string, any>) {
    this.log(LogLevel.DEBUG, message, data);
  }

  /**
   * Log at INFO level
   */
  info(message: string, data?: Record<string, any>) {
    this.log(LogLevel.INFO, message, data);
  }

  /**
   * Log at WARN level
   */
  warn(message: string, data?: Record<string, any>) {
    this.log(LogLevel.WARN, message, data);
  }

  /**
   * Log at ERROR level with optional error object
   */
  error(message: string, error?: Error, data?: Record<string, any>) {
    this.log(LogLevel.ERROR, message, data, error);
  }

  /**
   * Get all stored logs
   */
  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  /**
   * Clear all logs
   */
  clear() {
    this.logs = [];
    try {
      sessionStorage.removeItem('vision_logs');
    } catch {
      // Silently fail
    }
  }

  /**
   * Export logs as JSON
   */
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  /**
   * Export logs as CSV
   */
  exportLogsCSV(): string {
    const headers = ['Timestamp', 'Level', 'Module', 'Message', 'Data'];
    const rows = this.logs.map(log => [
      log.timestamp,
      log.level,
      log.module,
      log.message,
      JSON.stringify(log.data || ''),
    ]);

    const csv = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    return csv;
  }

  /**
   * Download logs as file
   */
  downloadLogs(format: 'json' | 'csv' = 'json') {
    const content = format === 'json' ? this.exportLogs() : this.exportLogsCSV();
    const filename = `vision-logs-${new Date().toISOString().slice(0, 10)}.${format}`;

    const blob = new Blob([content], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }
}

/**
 * Create a logger for a specific module
 * Usage: const log = createLogger('ChatInput');
 */
export function createLogger(module: string, enableRemote = false): Logger {
  return new Logger(module, enableRemote);
}

/**
 * Global logger instance
 */
export const globalLogger = new Logger('VISION-GLOBAL', true);
