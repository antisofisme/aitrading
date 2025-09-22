/**
 * Audit Trail System for Regulatory Compliance
 * Implements immutable, encrypted audit logging for AI trading decisions
 */

import { EventEmitter } from 'events';
import * as crypto from 'crypto';
import * as zlib from 'zlib';
import { promises as fs } from 'fs';
import { join } from 'path';

export interface AuditEvent {
  id: string;
  timestamp: string;
  eventType: string;
  data: any;
  hash: string;
  previousHash?: string;
  signature?: string;
}

export interface AuditTrailConfig {
  retentionPeriod: number; // days
  encryption: boolean;
  compression: boolean;
  immutable: boolean;
  storageLocation?: string;
  encryptionKey?: string;
}

export class AuditTrail extends EventEmitter {
  private config: AuditTrailConfig;
  private events: AuditEvent[] = [];
  private lastEventHash: string = '';
  private eventCounter: number = 0;
  private storageLocation: string;
  private encryptionKey: Buffer;

  constructor(config: AuditTrailConfig) {
    super();
    this.config = config;
    this.storageLocation = config.storageLocation || './audit_logs';
    this.encryptionKey = config.encryptionKey
      ? Buffer.from(config.encryptionKey, 'hex')
      : crypto.randomBytes(32);

    this.initializeStorage();
  }

  private async initializeStorage(): Promise<void> {
    try {
      await fs.mkdir(this.storageLocation, { recursive: true });

      // Load existing events if immutable storage is enabled
      if (this.config.immutable) {
        await this.loadExistingEvents();
      }

      this.emit('audit:initialized', {
        location: this.storageLocation,
        eventsLoaded: this.events.length
      });
    } catch (error) {
      this.emit('audit:error', { error: error.message });
      throw error;
    }
  }

  private async loadExistingEvents(): Promise<void> {
    try {
      const files = await fs.readdir(this.storageLocation);
      const auditFiles = files.filter(f => f.endsWith('.audit'));

      for (const file of auditFiles.sort()) {
        const content = await fs.readFile(join(this.storageLocation, file), 'utf8');
        const events = JSON.parse(content);
        this.events.push(...events);
      }

      if (this.events.length > 0) {
        this.lastEventHash = this.events[this.events.length - 1].hash;
        this.eventCounter = this.events.length;
      }
    } catch (error) {
      // If no existing events, start fresh
      this.events = [];
      this.lastEventHash = '';
      this.eventCounter = 0;
    }
  }

  /**
   * Log an audit event with immutable chaining
   */
  public async logEvent(eventType: string, data: any): Promise<string> {
    const event: AuditEvent = {
      id: this.generateEventId(),
      timestamp: new Date().toISOString(),
      eventType,
      data: this.config.encryption ? this.encryptData(data) : data,
      hash: '',
      previousHash: this.lastEventHash || undefined
    };

    // Generate hash for event integrity
    event.hash = this.generateEventHash(event);

    // Add digital signature if immutable storage
    if (this.config.immutable) {
      event.signature = this.signEvent(event);
    }

    // Store event
    this.events.push(event);
    this.lastEventHash = event.hash;
    this.eventCounter++;

    // Persist to storage
    await this.persistEvent(event);

    this.emit('audit:event_logged', {
      eventId: event.id,
      eventType: event.eventType,
      timestamp: event.timestamp
    });

    return event.id;
  }

  private generateEventId(): string {
    return `AE_${Date.now()}_${this.eventCounter.toString().padStart(6, '0')}`;
  }

  private generateEventHash(event: Omit<AuditEvent, 'hash'>): string {
    const eventString = JSON.stringify({
      id: event.id,
      timestamp: event.timestamp,
      eventType: event.eventType,
      data: event.data,
      previousHash: event.previousHash
    });

    return crypto.createHash('sha256').update(eventString).digest('hex');
  }

  private signEvent(event: AuditEvent): string {
    const eventString = JSON.stringify(event);
    return crypto.createHmac('sha256', this.encryptionKey).update(eventString).digest('hex');
  }

  private encryptData(data: any): string {
    if (!this.config.encryption) return data;

    const jsonString = JSON.stringify(data);
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipher('aes-256-cbc', this.encryptionKey);

    let encrypted = cipher.update(jsonString, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    return iv.toString('hex') + ':' + encrypted;
  }

  private decryptData(encryptedData: string): any {
    if (!this.config.encryption || typeof encryptedData !== 'string') {
      return encryptedData;
    }

    const [ivHex, encrypted] = encryptedData.split(':');
    const decipher = crypto.createDecipher('aes-256-cbc', this.encryptionKey);

    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return JSON.parse(decrypted);
  }

  private async persistEvent(event: AuditEvent): Promise<void> {
    const filename = `audit_${new Date().toISOString().split('T')[0]}.audit`;
    const filepath = join(this.storageLocation, filename);

    let content = JSON.stringify([event], null, 2);

    if (this.config.compression) {
      content = zlib.gzipSync(content).toString('base64');
    }

    try {
      // Check if file exists and append, otherwise create new
      const exists = await fs.access(filepath).then(() => true).catch(() => false);

      if (exists) {
        let existingContent = await fs.readFile(filepath, 'utf8');

        if (this.config.compression) {
          existingContent = zlib.gunzipSync(Buffer.from(existingContent, 'base64')).toString();
        }

        const existingEvents = JSON.parse(existingContent);
        existingEvents.push(event);

        content = JSON.stringify(existingEvents, null, 2);

        if (this.config.compression) {
          content = zlib.gzipSync(content).toString('base64');
        }
      }

      await fs.writeFile(filepath, content);
    } catch (error) {
      this.emit('audit:error', { error: error.message, event: event.id });
      throw error;
    }
  }

  /**
   * Query audit events by criteria
   */
  public async queryEvents(criteria: {
    eventType?: string;
    startDate?: Date;
    endDate?: Date;
    dataFilter?: (data: any) => boolean;
  }): Promise<AuditEvent[]> {
    let filteredEvents = this.events;

    if (criteria.eventType) {
      filteredEvents = filteredEvents.filter(e => e.eventType === criteria.eventType);
    }

    if (criteria.startDate) {
      filteredEvents = filteredEvents.filter(e =>
        new Date(e.timestamp) >= criteria.startDate!
      );
    }

    if (criteria.endDate) {
      filteredEvents = filteredEvents.filter(e =>
        new Date(e.timestamp) <= criteria.endDate!
      );
    }

    if (criteria.dataFilter) {
      filteredEvents = filteredEvents.filter(e => {
        const data = this.config.encryption ? this.decryptData(e.data) : e.data;
        return criteria.dataFilter!(data);
      });
    }

    // Decrypt data for response if encryption is enabled
    return filteredEvents.map(event => ({
      ...event,
      data: this.config.encryption ? this.decryptData(event.data) : event.data
    }));
  }

  /**
   * Verify audit trail integrity
   */
  public verifyIntegrity(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    for (let i = 0; i < this.events.length; i++) {
      const event = this.events[i];

      // Verify hash
      const expectedHash = this.generateEventHash({
        id: event.id,
        timestamp: event.timestamp,
        eventType: event.eventType,
        data: event.data,
        previousHash: event.previousHash
      });

      if (event.hash !== expectedHash) {
        errors.push(`Hash mismatch for event ${event.id}`);
      }

      // Verify chain
      if (i > 0 && event.previousHash !== this.events[i - 1].hash) {
        errors.push(`Chain broken at event ${event.id}`);
      }

      // Verify signature if immutable
      if (this.config.immutable && event.signature) {
        const expectedSignature = this.signEvent(event);
        if (event.signature !== expectedSignature) {
          errors.push(`Signature invalid for event ${event.id}`);
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Generate compliance report for regulatory submission
   */
  public async generateComplianceReport(startDate: Date, endDate: Date): Promise<any> {
    const events = await this.queryEvents({ startDate, endDate });

    const report = {
      reportId: `AUDIT_${Date.now()}`,
      period: {
        start: startDate.toISOString(),
        end: endDate.toISOString()
      },
      summary: {
        totalEvents: events.length,
        eventTypes: this.getEventTypeSummary(events),
        integrity: this.verifyIntegrity()
      },
      events: events.map(event => ({
        id: event.id,
        timestamp: event.timestamp,
        type: event.eventType,
        hash: event.hash,
        dataHash: crypto.createHash('sha256').update(JSON.stringify(event.data)).digest('hex')
      })),
      generatedAt: new Date().toISOString(),
      framework: 'AI Trading Compliance Framework v1.0'
    };

    // Log report generation
    await this.logEvent('COMPLIANCE_REPORT_GENERATED', {
      reportId: report.reportId,
      eventCount: events.length,
      period: report.period
    });

    return report;
  }

  private getEventTypeSummary(events: AuditEvent[]): Record<string, number> {
    return events.reduce((summary, event) => {
      summary[event.eventType] = (summary[event.eventType] || 0) + 1;
      return summary;
    }, {} as Record<string, number>);
  }

  /**
   * Clean up old events based on retention policy
   */
  public async cleanupOldEvents(): Promise<void> {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - this.config.retentionPeriod);

    const eventsToKeep = this.events.filter(event =>
      new Date(event.timestamp) > cutoffDate
    );

    const removedCount = this.events.length - eventsToKeep.length;
    this.events = eventsToKeep;

    if (removedCount > 0) {
      await this.logEvent('AUDIT_CLEANUP', {
        removedEvents: removedCount,
        cutoffDate: cutoffDate.toISOString()
      });
    }
  }

  /**
   * Get audit trail status
   */
  public getStatus(): any {
    return {
      eventCount: this.events.length,
      lastEventHash: this.lastEventHash,
      storageLocation: this.storageLocation,
      config: {
        encryption: this.config.encryption,
        compression: this.config.compression,
        immutable: this.config.immutable,
        retentionPeriod: this.config.retentionPeriod
      },
      integrity: this.verifyIntegrity()
    };
  }

  /**
   * Flush pending operations
   */
  public async flush(): Promise<void> {
    // Any pending async operations can be completed here
    this.emit('audit:flushed', {
      timestamp: new Date().toISOString(),
      eventCount: this.events.length
    });
  }
}

export default AuditTrail;