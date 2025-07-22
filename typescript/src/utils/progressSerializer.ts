import type { UploadProgress } from '../types/index.js';

export function serializeProgress(progress: UploadProgress): string {
  const data = {
    processedIds: Array.from(progress.processedIds),
    lastProcessedRow: progress.lastProcessedRow,
    failedUploads: progress.failedUploads,
  };
  return JSON.stringify(data, null, 2);
}

export function deserializeProgress(data: string): UploadProgress {
  try {
    const parsed = JSON.parse(data);
    return {
      processedIds: new Set(parsed.processedIds ?? []),
      lastProcessedRow: parsed.lastProcessedRow ?? 0,
      failedUploads: parsed.failedUploads ?? [],
    };
  } catch {
    return {
      processedIds: new Set(),
      lastProcessedRow: 0,
      failedUploads: [],
    };
  }
}
