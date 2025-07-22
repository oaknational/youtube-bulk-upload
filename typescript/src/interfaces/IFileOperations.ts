import type { ReadStream, WriteStream, Stats } from 'fs';

export interface IFileOperations {
  readFile(path: string): string | null;
  writeFile(path: string, content: string): void;
  appendFile(path: string, content: string): void;
  exists(path: string): boolean;
  unlink(path: string): void;
  mkdir(path: string): void;
  createReadStream(path: string): ReadStream;
  createWriteStream(path: string): WriteStream;
  stat(path: string): Stats;
}
