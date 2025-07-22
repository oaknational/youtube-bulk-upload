import type { ReadStream, WriteStream, Stats } from 'fs';

/**
 * Interface for file system operations.
 * Provides an abstraction layer over file system operations to enable
 * dependency injection and easier testing with mock implementations.
 */
export interface IFileOperations {
  /**
   * Reads the entire contents of a file synchronously.
   * @param path - The file path to read from
   * @returns The file contents as a string, or null if the file doesn't exist or an error occurs
   */
  readFile(path: string): string | null;

  /**
   * Writes content to a file synchronously, creating the file if it doesn't exist.
   * @param path - The file path to write to
   * @param content - The content to write to the file
   * @throws May throw an error if the write operation fails
   */
  writeFile(path: string, content: string): void;

  /**
   * Appends content to an existing file synchronously.
   * @param path - The file path to append to
   * @param content - The content to append to the file
   * @throws May throw an error if the file doesn't exist or the append operation fails
   */
  appendFile(path: string, content: string): void;

  /**
   * Checks if a file or directory exists at the given path.
   * @param path - The file or directory path to check
   * @returns true if the path exists, false otherwise
   */
  exists(path: string): boolean;

  /**
   * Deletes a file synchronously.
   * @param path - The file path to delete
   * @throws May throw an error if the file doesn't exist or deletion fails
   */
  unlink(path: string): void;

  /**
   * Creates a directory synchronously.
   * @param path - The directory path to create
   * @throws May throw an error if the directory already exists or creation fails
   */
  mkdir(path: string): void;

  /**
   * Creates a readable stream for reading file contents.
   * @param path - The file path to read from
   * @returns A ReadStream for the file
   * @throws May throw an error if the file doesn't exist or cannot be accessed
   */
  createReadStream(path: string): ReadStream;

  /**
   * Creates a writable stream for writing file contents.
   * @param path - The file path to write to
   * @returns A WriteStream for the file
   * @throws May throw an error if the file cannot be created or accessed
   */
  createWriteStream(path: string): WriteStream;

  /**
   * Retrieves file statistics synchronously.
   * @param path - The file path to get statistics for
   * @returns A Stats object containing file information
   * @throws May throw an error if the file doesn't exist or cannot be accessed
   */
  stat(path: string): Stats;
}
