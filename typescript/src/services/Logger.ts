import { createConsola } from 'consola';
import type { ILogger } from '../interfaces/ILogger.js';
import type { IFileOperations } from '../interfaces/IFileOperations.js';
import { createLogMessage } from '../utils/logging.js';

export class Logger implements ILogger {
  private consola;

  constructor(
    private readonly logFile: string,
    private readonly fileOps: IFileOperations
  ) {
    this.consola = createConsola({
      formatOptions: {
        date: true,
        colors: true,
      },
    });
  }

  log(message: string): void {
    this.consola.log(message);
    this.writeToFile(message);
  }

  error(message: string): void {
    this.consola.error(message);
    this.writeToFile(`ERROR: ${message}`);
  }

  warn(message: string): void {
    this.consola.warn(message);
    this.writeToFile(`WARN: ${message}`);
  }

  private writeToFile(message: string): void {
    const logMessage = createLogMessage(message);
    this.fileOps.appendFile(this.logFile, logMessage);
  }
}
