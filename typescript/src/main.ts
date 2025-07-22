import * as dotenv from 'dotenv';
import { DependencyContainer } from './core/DependencyContainer.js';
import type { Config } from './types/index.js';
import { buildConfigFromEnv } from './utils/configBuilder.js';
import { validateRequiredConfigFields } from './utils/configValidator.js';
import { printMissingConfigError } from './utils/errorPrinter.js';

// Load environment variables
dotenv.config();

export async function main(args: string[] = process.argv): Promise<void> {
  // Build config from environment
  const config = buildConfigFromEnv(args[2]);

  // Validate config
  const missingFields = validateRequiredConfigFields(config);

  if (missingFields.length > 0) {
    printMissingConfigError(missingFields);
    process.exit(1);
  }

  // Create dependency container and run
  await runApplication(config, args);
}

async function runApplication(config: Config, args: string[]): Promise<void> {
  const container = new DependencyContainer(config);

  try {
    const uploader = await container.createYouTubeBulkUploader();

    if (args.includes('--retry-failed')) {
      await uploader.retryFailedUploads();
    } else {
      await uploader.processSpreadsheet();
    }
  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

// Only run main if this is the entry point
if (import.meta.url === `file://${process.argv[1]}`) {
  void main();
}
