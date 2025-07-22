export function printMissingConfigError(missingFields: string[]): void {
  if (missingFields.length === 0) return;

  const firstField = missingFields[0];
  if (firstField) {
    console.error(`Missing required environment variable: ${firstField.toUpperCase()}`);
  }

  console.error('Please set the following environment variables:');
  console.error('- CLIENT_ID');
  console.error('- CLIENT_SECRET');
  console.error('- REDIRECT_URI');
  console.error('- SPREADSHEET_ID (or pass as first argument)');
}
