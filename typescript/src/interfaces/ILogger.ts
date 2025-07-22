/**
 * Interface for logging operations.
 * Provides a standardized way to output log messages at different severity levels.
 * Implementations can write to console, files, or external logging services.
 */
export interface ILogger {
  /**
   * Logs an informational message.
   * @param message - The message to log at info level
   */
  log(message: string): void;

  /**
   * Logs an error message.
   * @param message - The error message to log at error level
   */
  error(message: string): void;

  /**
   * Logs a warning message.
   * @param message - The warning message to log at warning level
   */
  warn(message: string): void;
}
