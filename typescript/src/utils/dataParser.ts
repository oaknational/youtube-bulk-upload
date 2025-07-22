import type { VideoData } from '../types/index.js';

export function parseVideoRow(row: string[]): VideoData | null {
  if (row.length < 5) return null;

  const [driveLink, title, description, tagString, uniqueId] = row;

  if (!driveLink || !title || !description || !uniqueId) {
    return null;
  }

  return {
    driveLink,
    title,
    description,
    tags: tagString ? tagString.split(',').map((tag) => tag.trim()) : [],
    uniqueId,
  };
}
