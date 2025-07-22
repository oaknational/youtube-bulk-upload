import * as fs from 'fs';
import type { ReadStream, WriteStream, Stats } from 'fs';
import type { IFileOperations } from '../interfaces/IFileOperations.js';

export class FileOperations implements IFileOperations {
  readFile(path: string): string | null {
    try {
      return fs.readFileSync(path, 'utf8');
    } catch {
      return null;
    }
  }

  writeFile(path: string, content: string): void {
    fs.writeFileSync(path, content);
  }

  appendFile(path: string, content: string): void {
    fs.appendFileSync(path, content);
  }

  exists(path: string): boolean {
    return fs.existsSync(path);
  }

  unlink(path: string): void {
    fs.unlinkSync(path);
  }

  mkdir(path: string): void {
    if (!fs.existsSync(path)) {
      fs.mkdirSync(path, { recursive: true });
    }
  }

  createReadStream(path: string): ReadStream {
    return fs.createReadStream(path);
  }

  createWriteStream(path: string): WriteStream {
    return fs.createWriteStream(path);
  }

  stat(path: string): Stats {
    return fs.statSync(path);
  }
}
