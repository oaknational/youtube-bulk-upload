import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import * as fs from 'fs';
import { FileOperations } from '../FileOperations.js';

// Mock fs module
vi.mock('fs');

describe('FileOperations', () => {
  let fileOps: FileOperations;
  let mockFs: {
    readFileSync: Mock;
    writeFileSync: Mock;
    appendFileSync: Mock;
    existsSync: Mock;
    unlinkSync: Mock;
    mkdirSync: Mock;
    createReadStream: Mock;
    createWriteStream: Mock;
    statSync: Mock;
  };

  beforeEach(() => {
    fileOps = new FileOperations();
    mockFs = fs as unknown as typeof mockFs;
    vi.clearAllMocks();
  });

  describe('readFile', () => {
    it('should return file content when file exists', () => {
      const mockContent = 'Hello, World!';
      mockFs.readFileSync.mockReturnValue(mockContent);

      const result = fileOps.readFile('/path/to/file.txt');

      expect(result).toBe(mockContent);
      expect(mockFs.readFileSync).toHaveBeenCalledWith('/path/to/file.txt', 'utf8');
    });

    it('should return null when file does not exist', () => {
      mockFs.readFileSync.mockImplementation(() => {
        throw new Error('ENOENT: no such file or directory');
      });

      const result = fileOps.readFile('/path/to/nonexistent.txt');

      expect(result).toBeNull();
      expect(mockFs.readFileSync).toHaveBeenCalledWith('/path/to/nonexistent.txt', 'utf8');
    });

    it('should return null on any read error', () => {
      mockFs.readFileSync.mockImplementation(() => {
        throw new Error('Permission denied');
      });

      const result = fileOps.readFile('/path/to/protected.txt');

      expect(result).toBeNull();
    });
  });

  describe('writeFile', () => {
    it('should write content to file', () => {
      const content = 'New content';
      const path = '/path/to/output.txt';

      fileOps.writeFile(path, content);

      expect(mockFs.writeFileSync).toHaveBeenCalledWith(path, content);
      expect(mockFs.writeFileSync).toHaveBeenCalledTimes(1);
    });

    it('should propagate write errors', () => {
      mockFs.writeFileSync.mockImplementation(() => {
        throw new Error('Disk full');
      });

      expect(() => fileOps.writeFile('/path/to/file.txt', 'content')).toThrow('Disk full');
    });
  });

  describe('appendFile', () => {
    it('should append content to file', () => {
      const content = 'Additional content';
      const path = '/path/to/log.txt';

      fileOps.appendFile(path, content);

      expect(mockFs.appendFileSync).toHaveBeenCalledWith(path, content);
      expect(mockFs.appendFileSync).toHaveBeenCalledTimes(1);
    });

    it('should propagate append errors', () => {
      mockFs.appendFileSync.mockImplementation(() => {
        throw new Error('Permission denied');
      });

      expect(() => fileOps.appendFile('/path/to/file.txt', 'content')).toThrow(
        'Permission denied'
      );
    });
  });

  describe('exists', () => {
    it('should return true when file exists', () => {
      mockFs.existsSync.mockReturnValue(true);

      const result = fileOps.exists('/path/to/existing.txt');

      expect(result).toBe(true);
      expect(mockFs.existsSync).toHaveBeenCalledWith('/path/to/existing.txt');
    });

    it('should return false when file does not exist', () => {
      mockFs.existsSync.mockReturnValue(false);

      const result = fileOps.exists('/path/to/nonexistent.txt');

      expect(result).toBe(false);
      expect(mockFs.existsSync).toHaveBeenCalledWith('/path/to/nonexistent.txt');
    });
  });

  describe('unlink', () => {
    it('should delete file', () => {
      const path = '/path/to/delete.txt';

      fileOps.unlink(path);

      expect(mockFs.unlinkSync).toHaveBeenCalledWith(path);
      expect(mockFs.unlinkSync).toHaveBeenCalledTimes(1);
    });

    it('should propagate deletion errors', () => {
      mockFs.unlinkSync.mockImplementation(() => {
        throw new Error('File not found');
      });

      expect(() => fileOps.unlink('/path/to/file.txt')).toThrow('File not found');
    });
  });

  describe('mkdir', () => {
    it('should create directory when it does not exist', () => {
      mockFs.existsSync.mockReturnValue(false);

      fileOps.mkdir('/path/to/new/dir');

      expect(mockFs.existsSync).toHaveBeenCalledWith('/path/to/new/dir');
      expect(mockFs.mkdirSync).toHaveBeenCalledWith('/path/to/new/dir', { recursive: true });
    });

    it('should not create directory when it already exists', () => {
      mockFs.existsSync.mockReturnValue(true);

      fileOps.mkdir('/path/to/existing/dir');

      expect(mockFs.existsSync).toHaveBeenCalledWith('/path/to/existing/dir');
      expect(mockFs.mkdirSync).not.toHaveBeenCalled();
    });

    it('should propagate mkdir errors', () => {
      mockFs.existsSync.mockReturnValue(false);
      mockFs.mkdirSync.mockImplementation(() => {
        throw new Error('Permission denied');
      });

      expect(() => fileOps.mkdir('/path/to/dir')).toThrow('Permission denied');
    });
  });

  describe('createReadStream', () => {
    it('should create and return a read stream', () => {
      const mockStream = { pipe: vi.fn() } as any;
      mockFs.createReadStream.mockReturnValue(mockStream);

      const result = fileOps.createReadStream('/path/to/file.txt');

      expect(result).toBe(mockStream);
      expect(mockFs.createReadStream).toHaveBeenCalledWith('/path/to/file.txt');
    });
  });

  describe('createWriteStream', () => {
    it('should create and return a write stream', () => {
      const mockStream = { write: vi.fn() } as any;
      mockFs.createWriteStream.mockReturnValue(mockStream);

      const result = fileOps.createWriteStream('/path/to/output.txt');

      expect(result).toBe(mockStream);
      expect(mockFs.createWriteStream).toHaveBeenCalledWith('/path/to/output.txt');
    });
  });

  describe('stat', () => {
    it('should return file stats', () => {
      const mockStats = {
        size: 1024,
        isFile: () => true,
        isDirectory: () => false,
        mtime: new Date()
      } as any;
      mockFs.statSync.mockReturnValue(mockStats);

      const result = fileOps.stat('/path/to/file.txt');

      expect(result).toBe(mockStats);
      expect(mockFs.statSync).toHaveBeenCalledWith('/path/to/file.txt');
    });

    it('should propagate stat errors', () => {
      mockFs.statSync.mockImplementation(() => {
        throw new Error('File not found');
      });

      expect(() => fileOps.stat('/path/to/nonexistent.txt')).toThrow('File not found');
    });
  });
});