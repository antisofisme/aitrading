/**
 * Shared Protocol Definitions for Suho AI Trading System
 *
 * This module exports all Protocol Buffer definitions and utilities
 * for use across all backend services.
 */

// Re-export all generated Protocol Buffer types
export * from './trading_pb';

// Utility types and constants
export interface SuhoProtocolVersion {
  major: number;
  minor: number;
  patch: number;
}

export const PROTOCOL_VERSION: SuhoProtocolVersion = {
  major: 2,
  minor: 0,
  patch: 0
};

// Suho Binary Protocol constants
export const SUHO_BINARY = {
  MAGIC_NUMBER: 0x53554854, // "SUHO"
  VERSION: 0x0001,
  PACKET_SIZE: 144,
  HEADER_SIZE: 16,
  DATA_SIZE: 128,
  MAX_SYMBOLS_PER_PACKET: 7
} as const;

// Message type enums for binary protocol
export enum SuhoMessageType {
  PRICE_STREAM = 0x01,
  TRADING_COMMAND = 0x02,
  ACCOUNT_PROFILE = 0x03,
  EXECUTION_RESP = 0x04,
  HEARTBEAT = 0x05,
  ERROR_RESPONSE = 0x06,
  SYSTEM_STATUS = 0x07
}

// Symbol enumeration matching binary protocol
export enum SuhoSymbol {
  SYMBOL_UNKNOWN = 0,
  EURUSD = 1,
  GBPUSD = 2,
  USDJPY = 3,
  AUDUSD = 4,
  USDCAD = 5,
  USDCHF = 6,
  NZDUSD = 7,
  EURGBP = 8,
  EURJPY = 9,
  GBPJPY = 10,
  AUDJPY = 11,
  EURAUD = 12,
  EURCHF = 13,
  GBPCHF = 14,
  AUDCAD = 15,
  AUDCHF = 16,
  CADCHF = 17,
  CADJPY = 18,
  CHFJPY = 19,
  XAUUSD = 36,
  XAGUSD = 37,
  USOIL = 38,
  BRENT = 39
}

// Utility functions for protocol conversion
export class ProtocolUtils {
  /**
   * Convert binary symbol enum to Protocol Buffer Symbol
   */
  static binaryToProtobufSymbol(binarySymbol: number): number {
    return binarySymbol; // Direct mapping for now
  }

  /**
   * Convert binary price (integer) to Protocol Buffer price (double)
   */
  static binaryToProtobufPrice(binaryPrice: number): number {
    return binaryPrice / 100000.0;
  }

  /**
   * Convert Protocol Buffer price (double) to binary price (integer)
   */
  static protobufToBinaryPrice(price: number): number {
    return Math.round(price * 100000);
  }

  /**
   * Convert binary timestamp (microseconds) to Protocol Buffer Timestamp
   */
  static binaryToProtobufTimestamp(microseconds: number): { seconds: number; nanos: number } {
    return {
      seconds: Math.floor(microseconds / 1000000),
      nanos: (microseconds % 1000000) * 1000
    };
  }

  /**
   * Convert Protocol Buffer Timestamp to binary timestamp (microseconds)
   */
  static protobufToBinaryTimestamp(timestamp: { seconds: number; nanos: number }): number {
    return timestamp.seconds * 1000000 + Math.floor(timestamp.nanos / 1000);
  }

  /**
   * Validate Suho Binary packet header
   */
  static validateBinaryHeader(header: ArrayBuffer): boolean {
    const view = new DataView(header);
    const magic = view.getUint32(0, true); // little-endian
    const version = view.getUint16(4, true);
    const msgType = view.getUint8(6);

    return magic === SUHO_BINARY.MAGIC_NUMBER &&
           version === SUHO_BINARY.VERSION &&
           msgType >= 1 && msgType <= 7;
  }

  /**
   * Get symbol name from enum value
   */
  static getSymbolName(symbol: SuhoSymbol): string {
    return SuhoSymbol[symbol] || 'UNKNOWN';
  }

  /**
   * Get symbol enum from name
   */
  static getSymbolEnum(symbolName: string): SuhoSymbol {
    return (SuhoSymbol as any)[symbolName.toUpperCase()] || SuhoSymbol.SYMBOL_UNKNOWN;
  }
}

// Type guards for Protocol Buffer messages
export function isPriceStream(message: any): boolean {
  return message && typeof message.prices !== 'undefined' && Array.isArray(message.prices);
}

export function isTradingCommand(message: any): boolean {
  return message && typeof message.command_id !== 'undefined' && typeof message.action !== 'undefined';
}

export function isAccountProfile(message: any): boolean {
  return message && typeof message.account_number !== 'undefined' && typeof message.balance !== 'undefined';
}

export function isTradingEngineOutput(message: any): boolean {
  return message && (
    (typeof message.signals !== 'undefined' && Array.isArray(message.signals)) ||
    (typeof message.responses !== 'undefined' && Array.isArray(message.responses))
  );
}

export function isAnalyticsOutput(message: any): boolean {
  return message && typeof message.performance_metrics !== 'undefined';
}

export function isMLOutput(message: any): boolean {
  return message && typeof message.predictions !== 'undefined' && Array.isArray(message.predictions);
}

export function isNotificationOutput(message: any): boolean {
  return message && typeof message.channels !== 'undefined' && Array.isArray(message.channels);
}

// Error types for protocol handling
export class ProtocolError extends Error {
  constructor(message: string, public code: string) {
    super(message);
    this.name = 'ProtocolError';
  }
}

export class BinaryParseError extends ProtocolError {
  constructor(message: string) {
    super(message, 'BINARY_PARSE_ERROR');
  }
}

export class ProtobufSerializeError extends ProtocolError {
  constructor(message: string) {
    super(message, 'PROTOBUF_SERIALIZE_ERROR');
  }
}

export class InvalidMessageTypeError extends ProtocolError {
  constructor(messageType: string) {
    super(`Invalid message type: ${messageType}`, 'INVALID_MESSAGE_TYPE');
  }
}