/**
 * Circuit Breaker Implementation for EU Digital Markets Act Compliance
 * Implements automatic trading halts based on market conditions
 */

import { EventEmitter } from 'events';

export interface CircuitBreakerConfig {
  priceDeviation: number; // percentage threshold
  volumeThreshold: number; // volume threshold
  timeWindow: number; // time window in milliseconds
  cooldownPeriod: number; // cooldown period in milliseconds
  enablePriceBreaker?: boolean;
  enableVolumeBreaker?: boolean;
  enableVolatilityBreaker?: boolean;
}

export interface MarketData {
  symbol: string;
  price: number;
  volume: number;
  timestamp: string;
  volatility?: number;
}

export interface CircuitBreakerEvent {
  symbol: string;
  triggerType: 'PRICE_DEVIATION' | 'VOLUME_SPIKE' | 'VOLATILITY_SURGE';
  triggerValue: number;
  threshold: number;
  timestamp: string;
  marketData: MarketData;
  action: 'HALT' | 'PAUSE' | 'THROTTLE';
  duration: number; // milliseconds
}

export class CircuitBreaker extends EventEmitter {
  private config: CircuitBreakerConfig;
  private priceHistory: Map<string, { price: number; timestamp: number }[]> = new Map();
  private volumeHistory: Map<string, { volume: number; timestamp: number }[]> = new Map();
  private breakers: Map<string, { triggered: boolean; triggerTime: number; type: string }> = new Map();
  private basePrices: Map<string, number> = new Map();
  private baseVolumes: Map<string, number> = new Map();

  constructor(config: CircuitBreakerConfig) {
    super();
    this.config = {
      enablePriceBreaker: true,
      enableVolumeBreaker: true,
      enableVolatilityBreaker: true,
      ...config
    };
  }

  /**
   * Check market conditions and trigger circuit breakers if necessary
   */
  public async checkConditions(marketData: MarketData): Promise<void> {
    const { symbol, price, volume, timestamp } = marketData;
    const now = new Date(timestamp).getTime();

    // Update price and volume history
    this.updatePriceHistory(symbol, price, now);
    this.updateVolumeHistory(symbol, volume, now);

    // Check if circuit breaker is already triggered and still in cooldown
    if (this.isInCooldown(symbol)) {
      return;
    }

    // Check for price deviation breaker
    if (this.config.enablePriceBreaker) {
      await this.checkPriceDeviation(symbol, price, now, marketData);
    }

    // Check for volume spike breaker
    if (this.config.enableVolumeBreaker) {
      await this.checkVolumeSpike(symbol, volume, now, marketData);
    }

    // Check for volatility surge breaker
    if (this.config.enableVolatilityBreaker && marketData.volatility) {
      await this.checkVolatilitySurge(symbol, marketData.volatility, now, marketData);
    }
  }

  private updatePriceHistory(symbol: string, price: number, timestamp: number): void {
    if (!this.priceHistory.has(symbol)) {
      this.priceHistory.set(symbol, []);
      this.basePrices.set(symbol, price); // Set initial base price
    }

    const history = this.priceHistory.get(symbol)!;
    history.push({ price, timestamp });

    // Keep only data within time window
    const cutoff = timestamp - this.config.timeWindow;
    const filtered = history.filter(entry => entry.timestamp > cutoff);
    this.priceHistory.set(symbol, filtered);

    // Update base price periodically (using moving average)
    if (filtered.length > 10) {
      const avgPrice = filtered.reduce((sum, entry) => sum + entry.price, 0) / filtered.length;
      this.basePrices.set(symbol, avgPrice);
    }
  }

  private updateVolumeHistory(symbol: string, volume: number, timestamp: number): void {
    if (!this.volumeHistory.has(symbol)) {
      this.volumeHistory.set(symbol, []);
      this.baseVolumes.set(symbol, volume); // Set initial base volume
    }

    const history = this.volumeHistory.get(symbol)!;
    history.push({ volume, timestamp });

    // Keep only data within time window
    const cutoff = timestamp - this.config.timeWindow;
    const filtered = history.filter(entry => entry.timestamp > cutoff);
    this.volumeHistory.set(symbol, filtered);

    // Update base volume (using moving average)
    if (filtered.length > 10) {
      const avgVolume = filtered.reduce((sum, entry) => sum + entry.volume, 0) / filtered.length;
      this.baseVolumes.set(symbol, avgVolume);
    }
  }

  private async checkPriceDeviation(
    symbol: string,
    currentPrice: number,
    timestamp: number,
    marketData: MarketData
  ): Promise<void> {
    const basePrice = this.basePrices.get(symbol);
    if (!basePrice) return;

    const deviationPercent = Math.abs((currentPrice - basePrice) / basePrice) * 100;

    if (deviationPercent > this.config.priceDeviation) {
      await this.triggerCircuitBreaker({
        symbol,
        triggerType: 'PRICE_DEVIATION',
        triggerValue: deviationPercent,
        threshold: this.config.priceDeviation,
        timestamp: new Date(timestamp).toISOString(),
        marketData,
        action: this.getActionForDeviation(deviationPercent),
        duration: this.getDurationForDeviation(deviationPercent)
      });
    }
  }

  private async checkVolumeSpike(
    symbol: string,
    currentVolume: number,
    timestamp: number,
    marketData: MarketData
  ): Promise<void> {
    const baseVolume = this.baseVolumes.get(symbol);
    if (!baseVolume) return;

    const volumeRatio = currentVolume / baseVolume;

    if (volumeRatio > this.config.volumeThreshold) {
      await this.triggerCircuitBreaker({
        symbol,
        triggerType: 'VOLUME_SPIKE',
        triggerValue: volumeRatio,
        threshold: this.config.volumeThreshold,
        timestamp: new Date(timestamp).toISOString(),
        marketData,
        action: this.getActionForVolume(volumeRatio),
        duration: this.getDurationForVolume(volumeRatio)
      });
    }
  }

  private async checkVolatilitySurge(
    symbol: string,
    volatility: number,
    timestamp: number,
    marketData: MarketData
  ): Promise<void> {
    // Calculate volatility threshold as 2x normal volatility
    const volatilityThreshold = 2.0; // This could be configurable

    if (volatility > volatilityThreshold) {
      await this.triggerCircuitBreaker({
        symbol,
        triggerType: 'VOLATILITY_SURGE',
        triggerValue: volatility,
        threshold: volatilityThreshold,
        timestamp: new Date(timestamp).toISOString(),
        marketData,
        action: 'PAUSE',
        duration: this.config.cooldownPeriod
      });
    }
  }

  private async triggerCircuitBreaker(event: CircuitBreakerEvent): Promise<void> {
    const breakerKey = `${event.symbol}_${event.triggerType}`;

    // Set breaker state
    this.breakers.set(breakerKey, {
      triggered: true,
      triggerTime: new Date(event.timestamp).getTime(),
      type: event.triggerType
    });

    // Emit circuit breaker event
    this.emit('circuit:triggered', event);

    // Log the event for audit trail
    this.emit('circuit:log', {
      level: 'CRITICAL',
      message: `Circuit breaker triggered for ${event.symbol}`,
      data: event
    });

    // Schedule automatic reset after cooldown
    setTimeout(() => {
      this.resetCircuitBreaker(event.symbol, event.triggerType);
    }, event.duration);
  }

  private getActionForDeviation(deviation: number): 'HALT' | 'PAUSE' | 'THROTTLE' {
    if (deviation > this.config.priceDeviation * 2) {
      return 'HALT';
    } else if (deviation > this.config.priceDeviation * 1.5) {
      return 'PAUSE';
    } else {
      return 'THROTTLE';
    }
  }

  private getDurationForDeviation(deviation: number): number {
    // Progressive duration based on severity
    const baseDuration = this.config.cooldownPeriod;
    const multiplier = Math.min(Math.floor(deviation / this.config.priceDeviation), 5);
    return baseDuration * multiplier;
  }

  private getActionForVolume(volumeRatio: number): 'HALT' | 'PAUSE' | 'THROTTLE' {
    if (volumeRatio > this.config.volumeThreshold * 3) {
      return 'HALT';
    } else if (volumeRatio > this.config.volumeThreshold * 2) {
      return 'PAUSE';
    } else {
      return 'THROTTLE';
    }
  }

  private getDurationForVolume(volumeRatio: number): number {
    const baseDuration = this.config.cooldownPeriod;
    const multiplier = Math.min(Math.floor(volumeRatio / this.config.volumeThreshold), 4);
    return baseDuration * multiplier;
  }

  private isInCooldown(symbol: string): boolean {
    const now = Date.now();

    for (const [key, breaker] of this.breakers.entries()) {
      if (key.startsWith(symbol) && breaker.triggered) {
        const timeSinceTrigger = now - breaker.triggerTime;
        if (timeSinceTrigger < this.config.cooldownPeriod) {
          return true;
        }
      }
    }

    return false;
  }

  private resetCircuitBreaker(symbol: string, triggerType: string): void {
    const breakerKey = `${symbol}_${triggerType}`;
    const breaker = this.breakers.get(breakerKey);

    if (breaker) {
      this.breakers.delete(breakerKey);

      this.emit('circuit:reset', {
        symbol,
        triggerType,
        timestamp: new Date().toISOString(),
        duration: Date.now() - breaker.triggerTime
      });
    }
  }

  /**
   * Check if trading is currently halted for a symbol
   */
  public isTradingHalted(symbol: string): boolean {
    return this.isInCooldown(symbol);
  }

  /**
   * Get current circuit breaker status for a symbol
   */
  public getSymbolStatus(symbol: string): any {
    const activeBreakers = Array.from(this.breakers.entries())
      .filter(([key]) => key.startsWith(symbol))
      .map(([key, breaker]) => ({
        type: breaker.type,
        triggered: breaker.triggered,
        triggerTime: new Date(breaker.triggerTime).toISOString(),
        remaining: Math.max(0, this.config.cooldownPeriod - (Date.now() - breaker.triggerTime))
      }));

    return {
      symbol,
      tradingHalted: this.isTradingHalted(symbol),
      activeBreakers,
      priceHistory: this.priceHistory.get(symbol)?.slice(-10) || [],
      volumeHistory: this.volumeHistory.get(symbol)?.slice(-10) || [],
      basePrice: this.basePrices.get(symbol),
      baseVolume: this.baseVolumes.get(symbol)
    };
  }

  /**
   * Manually trigger circuit breaker for testing or emergency
   */
  public async manualTrigger(
    symbol: string,
    triggerType: 'PRICE_DEVIATION' | 'VOLUME_SPIKE' | 'VOLATILITY_SURGE',
    reason: string
  ): Promise<void> {
    await this.triggerCircuitBreaker({
      symbol,
      triggerType,
      triggerValue: 999, // Manual trigger value
      threshold: 0,
      timestamp: new Date().toISOString(),
      marketData: {
        symbol,
        price: 0,
        volume: 0,
        timestamp: new Date().toISOString()
      },
      action: 'HALT',
      duration: this.config.cooldownPeriod
    });

    this.emit('circuit:manual_trigger', {
      symbol,
      triggerType,
      reason,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Get overall circuit breaker status
   */
  public getStatus(): any {
    const activeBreakers = Array.from(this.breakers.entries()).length;
    const trackedSymbols = new Set([
      ...this.priceHistory.keys(),
      ...this.volumeHistory.keys()
    ]).size;

    return {
      config: this.config,
      activeBreakers,
      trackedSymbols,
      status: activeBreakers > 0 ? 'ACTIVE_BREAKERS' : 'MONITORING'
    };
  }

  /**
   * Reset all circuit breakers (emergency use)
   */
  public reset(): void {
    this.breakers.clear();
    this.emit('circuit:reset_all', {
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Update configuration
   */
  public updateConfig(newConfig: Partial<CircuitBreakerConfig>): void {
    this.config = { ...this.config, ...newConfig };
    this.emit('circuit:config_updated', {
      config: this.config,
      timestamp: new Date().toISOString()
    });
  }
}

export default CircuitBreaker;