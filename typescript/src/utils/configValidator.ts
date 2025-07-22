import type { Config } from '../types/index.js';

export function validateRequiredConfigFields(config: Config): string[] {
  const requiredFields: (keyof Config)[] = [
    'clientId',
    'clientSecret',
    'redirectUri',
    'spreadsheetId',
  ];

  const missingFields: string[] = [];

  for (const field of requiredFields) {
    if (!config[field]) {
      missingFields.push(field);
    }
  }

  return missingFields;
}
