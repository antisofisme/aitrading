/**
 * Cache Manager - Handles caching with Claude Flow memory integration
 * Supports memory, file, and Claude Flow memory strategies
 */

import { promises as fs } from 'fs';
import * as path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import {
  CacheConfig,
  CacheEntry,
  Logger
} from '../types';

const execAsync = promisify(exec);

export class CacheManager {
  private memoryCache: Map<string, CacheEntry> = new Map();
  private config: CacheConfig;
  private logger: Logger;
  private hitCount = 0;
  private missCount = 0;
  private cacheDir: string;

  constructor(config: CacheConfig, logger: Logger) {
    this.config = config;
    this.logger = logger;
    this.cacheDir = path.join(process.cwd(), '.cache', 'analysis');
  }

  async initialize(): Promise<void> {
    this.logger.info('Initializing Cache Manager...');

    if (this.config.strategy === 'file') {
      await this.ensureCacheDirectory();
    }

    if (this.config.strategy === 'claude-flow') {
      await this.initializeClaudeFlowCache();
    }

    // Start cleanup interval
    setInterval(() => this.cleanup(), 60000); // Cleanup every minute

    this.logger.info(`Cache Manager initialized with strategy: ${this.config.strategy}`);
  }

  async get<T = any>(key: string): Promise<T | null> {
    if (!this.config.enabled) {
      this.missCount++;
      return null;
    }

    const fullKey = this.getFullKey(key);

    try {
      let entry: CacheEntry<T> | null = null;

      switch (this.config.strategy) {
        case 'memory':
          entry = this.getFromMemory(fullKey);
          break;
        case 'file':
          entry = await this.getFromFile(fullKey);
          break;
        case 'claude-flow':
          entry = await this.getFromClaudeFlow(fullKey);
          break;
      }

      if (entry && this.isValid(entry)) {
        entry.hits++;
        this.hitCount++;
        this.logger.debug(`Cache hit for key: ${key}`);
        return entry.value;
      } else {
        this.missCount++;
        this.logger.debug(`Cache miss for key: ${key}`);
        return null;
      }

    } catch (error) {
      this.logger.error(`Cache get error for key ${key}:`, error);
      this.missCount++;
      return null;
    }
  }

  async set<T = any>(key: string, value: T, ttlOverride?: number): Promise<void> {
    if (!this.config.enabled) {
      return;
    }

    const fullKey = this.getFullKey(key);
    const ttl = ttlOverride || this.config.ttl;

    const entry: CacheEntry<T> = {
      key: fullKey,
      value,
      timestamp: new Date(),
      ttl,
      hits: 0,
      metadata: {
        size: this.estimateSize(value),
        strategy: this.config.strategy
      }
    };

    try {
      switch (this.config.strategy) {
        case 'memory':
          this.setInMemory(fullKey, entry);
          break;
        case 'file':
          await this.setInFile(fullKey, entry);
          break;
        case 'claude-flow':
          await this.setInClaudeFlow(fullKey, entry);
          break;
      }

      this.logger.debug(`Cache set for key: ${key} (TTL: ${ttl}s)`);

    } catch (error) {
      this.logger.error(`Cache set error for key ${key}:`, error);
    }
  }

  async invalidate(key: string): Promise<void> {
    const fullKey = this.getFullKey(key);

    try {
      switch (this.config.strategy) {
        case 'memory':
          this.memoryCache.delete(fullKey);
          break;
        case 'file':
          await this.deleteFromFile(fullKey);
          break;
        case 'claude-flow':
          await this.deleteFromClaudeFlow(fullKey);
          break;
      }

      this.logger.debug(`Cache invalidated for key: ${key}`);

    } catch (error) {
      this.logger.error(`Cache invalidation error for key ${key}:`, error);
    }
  }

  async invalidatePattern(pattern: string): Promise<void> {
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));

    try {
      switch (this.config.strategy) {
        case 'memory':
          for (const key of this.memoryCache.keys()) {
            if (regex.test(key)) {
              this.memoryCache.delete(key);
            }
          }
          break;
        case 'file':
          await this.deleteFilesByPattern(regex);
          break;
        case 'claude-flow':
          await this.deleteClaudeFlowByPattern(pattern);
          break;
      }

      this.logger.debug(`Cache invalidated for pattern: ${pattern}`);

    } catch (error) {
      this.logger.error(`Cache pattern invalidation error for pattern ${pattern}:`, error);
    }
  }

  async clear(): Promise<void> {
    try {
      switch (this.config.strategy) {
        case 'memory':
          this.memoryCache.clear();
          break;
        case 'file':
          await this.clearFileCache();
          break;
        case 'claude-flow':
          await this.clearClaudeFlowCache();
          break;
      }

      this.hitCount = 0;
      this.missCount = 0;
      this.logger.info('Cache cleared');

    } catch (error) {
      this.logger.error('Cache clear error:', error);
    }
  }

  getStats(): Record<string, any> {
    const total = this.hitCount + this.missCount;
    const hitRate = total > 0 ? this.hitCount / total : 0;

    return {
      hitCount: this.hitCount,
      missCount: this.missCount,
      hitRate: Math.round(hitRate * 100) / 100,
      strategy: this.config.strategy,
      enabled: this.config.enabled,
      memorySize: this.memoryCache.size,
      ttl: this.config.ttl
    };
  }

  getHitRate(): number {
    const total = this.hitCount + this.missCount;
    return total > 0 ? this.hitCount / total : 0;
  }

  async dispose(): Promise<void> {
    await this.cleanup();
    this.memoryCache.clear();
    this.logger.info('Cache Manager disposed');
  }

  // Private methods

  private getFullKey(key: string): string {
    return `${this.config.namespace}:${key}`;
  }

  private isValid(entry: CacheEntry): boolean {
    const now = Date.now();
    const age = (now - entry.timestamp.getTime()) / 1000;
    return age < entry.ttl;
  }

  private getFromMemory<T>(key: string): CacheEntry<T> | null {
    return this.memoryCache.get(key) as CacheEntry<T> || null;
  }

  private setInMemory<T>(key: string, entry: CacheEntry<T>): void {
    this.memoryCache.set(key, entry);
  }

  private async getFromFile<T>(key: string): Promise<CacheEntry<T> | null> {
    const filePath = this.getFilePath(key);

    try {
      await fs.access(filePath);
      const content = await fs.readFile(filePath, 'utf-8');
      return JSON.parse(content);
    } catch {
      return null;
    }
  }

  private async setInFile<T>(key: string, entry: CacheEntry<T>): Promise<void> {
    const filePath = this.getFilePath(key);
    const content = JSON.stringify(entry, null, 2);

    await fs.mkdir(path.dirname(filePath), { recursive: true });
    await fs.writeFile(filePath, content);
  }

  private async deleteFromFile(key: string): Promise<void> {
    const filePath = this.getFilePath(key);

    try {
      await fs.unlink(filePath);
    } catch {
      // File doesn't exist, ignore
    }
  }

  private async deleteFilesByPattern(regex: RegExp): Promise<void> {
    try {
      const files = await fs.readdir(this.cacheDir);

      for (const file of files) {
        if (regex.test(file)) {
          await fs.unlink(path.join(this.cacheDir, file));
        }
      }
    } catch {
      // Directory doesn't exist, ignore
    }
  }

  private async clearFileCache(): Promise<void> {
    try {
      await fs.rm(this.cacheDir, { recursive: true, force: true });
    } catch {
      // Directory doesn't exist, ignore
    }
  }

  private async getFromClaudeFlow<T>(key: string): Promise<CacheEntry<T> | null> {
    try {
      const { stdout } = await execAsync(`npx claude-flow@alpha memory retrieve --key "${key}"`);
      const result = JSON.parse(stdout);

      if (result.success && result.value) {
        return JSON.parse(result.value) as CacheEntry<T>;
      }

      return null;
    } catch {
      return null;
    }
  }

  private async setInClaudeFlow<T>(key: string, entry: CacheEntry<T>): Promise<void> {
    try {
      const value = JSON.stringify(entry);
      await execAsync(`npx claude-flow@alpha memory store --key "${key}" --value '${value}' --ttl ${entry.ttl}`);
    } catch (error) {
      this.logger.warn(`Failed to store in Claude Flow cache: ${error}`);
    }
  }

  private async deleteFromClaudeFlow(key: string): Promise<void> {
    try {
      await execAsync(`npx claude-flow@alpha memory delete --key "${key}"`);
    } catch {
      // Key doesn't exist, ignore
    }
  }

  private async deleteClaudeFlowByPattern(pattern: string): Promise<void> {
    try {
      await execAsync(`npx claude-flow@alpha memory delete --pattern "${pattern}"`);
    } catch {
      // Pattern doesn't match, ignore
    }
  }

  private async clearClaudeFlowCache(): Promise<void> {
    try {
      await execAsync(`npx claude-flow@alpha memory clear --namespace "${this.config.namespace}"`);
    } catch {
      // Namespace doesn't exist, ignore
    }
  }

  private async initializeClaudeFlowCache(): Promise<void> {
    try {
      // Check if Claude Flow is available
      await execAsync('npx claude-flow@alpha --version');
      this.logger.info('Claude Flow cache initialized');
    } catch (error) {
      this.logger.warn('Claude Flow not available, falling back to memory cache');
      this.config.strategy = 'memory';
    }
  }

  private async ensureCacheDirectory(): Promise<void> {
    await fs.mkdir(this.cacheDir, { recursive: true });
  }

  private getFilePath(key: string): string {
    const fileName = key.replace(/[^a-zA-Z0-9_-]/g, '_') + '.json';
    return path.join(this.cacheDir, fileName);
  }

  private estimateSize(value: any): number {
    return JSON.stringify(value).length;
  }

  private async cleanup(): Promise<void> {
    const now = Date.now();

    // Cleanup memory cache
    for (const [key, entry] of this.memoryCache.entries()) {
      if (!this.isValid(entry)) {
        this.memoryCache.delete(key);
      }
    }

    // Cleanup file cache
    if (this.config.strategy === 'file') {
      try {
        const files = await fs.readdir(this.cacheDir);

        for (const file of files) {
          const filePath = path.join(this.cacheDir, file);
          const stats = await fs.stat(filePath);
          const content = await fs.readFile(filePath, 'utf-8');
          const entry = JSON.parse(content) as CacheEntry;

          if (!this.isValid(entry)) {
            await fs.unlink(filePath);
          }
        }
      } catch {
        // Directory doesn't exist or other error, ignore
      }
    }

    this.logger.debug('Cache cleanup completed');
  }
}