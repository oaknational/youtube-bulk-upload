export function createLogMessage(message: string): string {
  const timestamp = new Date().toISOString();
  return `[${timestamp}] ${message}\n`;
}
