const MetricsCollector = require('../../src/monitoring/metrics/MetricsCollector');

describe('MetricsCollector', () => {
    let metricsCollector;
    let mockConfig;

    beforeEach(() => {
        mockConfig = {
            aggregationInterval: 1000,
            retentionPeriod: 3600000,
            batchSize: 100,
            enableRealTime: true
        };

        metricsCollector = new MetricsCollector(mockConfig);
    });

    afterEach(() => {
        if (metricsCollector && metricsCollector.isCollecting) {
            metricsCollector.stop();
        }
    });

    describe('Initialization', () => {
        it('should initialize with default configuration', () => {
            const collector = new MetricsCollector();
            expect(collector).toBeDefined();
            expect(collector.isCollecting).toBe(false);
        });

        it('should initialize with custom configuration', () => {
            expect(metricsCollector.config.aggregationInterval).toBe(1000);
            expect(metricsCollector.config.enableRealTime).toBe(true);
        });

        it('should initialize default metrics', () => {
            expect(metricsCollector.counters.has('trades.executed')).toBe(true);
            expect(metricsCollector.gauges.has('system.cpu_usage')).toBe(true);
            expect(metricsCollector.histograms.has('latency.order_execution')).toBe(true);
        });
    });

    describe('Counter Metrics', () => {
        it('should create counter metric', () => {
            const counter = metricsCollector.createCounter('test.counter', { app: 'test' });

            expect(counter).toBeDefined();
            expect(counter.name).toBe('test.counter');
            expect(counter.type).toBe('counter');
            expect(counter.value).toBe(0);
        });

        it('should increment counter', () => {
            metricsCollector.createCounter('test.increment');

            const updateSpy = jest.spyOn(metricsCollector, 'emit');
            metricsCollector.incrementCounter('test.increment', 5);

            const counter = metricsCollector.counters.get('test.increment');
            expect(counter.value).toBe(5);
            expect(updateSpy).toHaveBeenCalledWith('metric.updated', expect.objectContaining({
                type: 'counter',
                name: 'test.increment',
                value: 5,
                increment: 5
            }));
        });

        it('should throw error for non-existent counter', () => {
            expect(() => {
                metricsCollector.incrementCounter('non.existent');
            }).toThrow('Counter non.existent not found');
        });

        it('should track counter history', () => {
            metricsCollector.createCounter('test.history');
            metricsCollector.incrementCounter('test.history', 1);
            metricsCollector.incrementCounter('test.history', 2);

            const counter = metricsCollector.counters.get('test.history');
            expect(counter.history.length).toBe(2);
            expect(counter.value).toBe(3);
        });
    });

    describe('Gauge Metrics', () => {
        it('should create gauge metric', () => {
            const gauge = metricsCollector.createGauge('test.gauge');

            expect(gauge).toBeDefined();
            expect(gauge.name).toBe('test.gauge');
            expect(gauge.type).toBe('gauge');
            expect(gauge.value).toBe(0);
        });

        it('should set gauge value', () => {
            metricsCollector.createGauge('test.set');

            const updateSpy = jest.spyOn(metricsCollector, 'emit');
            metricsCollector.setGauge('test.set', 42.5);

            const gauge = metricsCollector.gauges.get('test.set');
            expect(gauge.value).toBe(42.5);
            expect(updateSpy).toHaveBeenCalledWith('metric.updated', expect.objectContaining({
                type: 'gauge',
                name: 'test.set',
                value: 42.5
            }));
        });

        it('should track gauge changes', () => {
            metricsCollector.createGauge('test.changes');
            metricsCollector.setGauge('test.changes', 10);
            metricsCollector.setGauge('test.changes', 20);

            const gauge = metricsCollector.gauges.get('test.changes');
            expect(gauge.history.length).toBe(2);
            expect(gauge.history[1].previousValue).toBe(10);
        });
    });

    describe('Histogram Metrics', () => {
        it('should create histogram metric', () => {
            const histogram = metricsCollector.createHistogram('test.histogram');

            expect(histogram).toBeDefined();
            expect(histogram.name).toBe('test.histogram');
            expect(histogram.type).toBe('histogram');
            expect(histogram.count).toBe(0);
            expect(histogram.sum).toBe(0);
            expect(Array.isArray(histogram.buckets)).toBe(true);
        });

        it('should observe histogram values', () => {
            metricsCollector.createHistogram('test.observe');

            const updateSpy = jest.spyOn(metricsCollector, 'emit');
            metricsCollector.observeHistogram('test.observe', 150);

            const histogram = metricsCollector.histograms.get('test.observe');
            expect(histogram.count).toBe(1);
            expect(histogram.sum).toBe(150);

            expect(updateSpy).toHaveBeenCalledWith('metric.updated', expect.objectContaining({
                type: 'histogram',
                name: 'test.observe',
                value: 150,
                count: 1,
                sum: 150,
                mean: 150
            }));
        });

        it('should update histogram buckets correctly', () => {
            const buckets = [10, 50, 100, 500];
            metricsCollector.createHistogram('test.buckets', buckets);

            metricsCollector.observeHistogram('test.buckets', 75);

            const histogram = metricsCollector.histograms.get('test.buckets');

            // Should increment buckets for 100 and 500 (75 <= 100, 75 <= 500)
            expect(histogram.buckets.find(b => b.le === 10).count).toBe(0);
            expect(histogram.buckets.find(b => b.le === 50).count).toBe(0);
            expect(histogram.buckets.find(b => b.le === 100).count).toBe(1);
            expect(histogram.buckets.find(b => b.le === 500).count).toBe(1);
        });

        it('should calculate percentiles', () => {
            metricsCollector.createHistogram('test.percentiles');

            // Add multiple observations
            for (let i = 1; i <= 100; i++) {
                metricsCollector.observeHistogram('test.percentiles', i);
            }

            const histogram = metricsCollector.histograms.get('test.percentiles');
            const percentiles = metricsCollector.calculatePercentiles(histogram);

            expect(percentiles.p50).toBeDefined();
            expect(percentiles.p75).toBeDefined();
            expect(percentiles.p90).toBeDefined();
            expect(percentiles.p95).toBeDefined();
            expect(percentiles.p99).toBeDefined();
        });
    });

    describe('Timer Functionality', () => {
        it('should start and end timer', async () => {
            metricsCollector.createHistogram('test.timer');

            const timerId = metricsCollector.startTimer('test.timer');
            expect(timerId).toBeDefined();
            expect(metricsCollector.timers.has(timerId)).toBe(true);

            // Wait a small amount of time
            await new Promise(resolve => setTimeout(resolve, 10));

            const duration = metricsCollector.endTimer(timerId);
            expect(typeof duration).toBe('number');
            expect(duration).toBeGreaterThan(0);
            expect(metricsCollector.timers.has(timerId)).toBe(false);

            // Should have recorded in histogram
            const histogram = metricsCollector.histograms.get('test.timer');
            expect(histogram.count).toBe(1);
        });

        it('should throw error for non-existent timer', () => {
            expect(() => {
                metricsCollector.endTimer('non-existent');
            }).toThrow('Timer non-existent not found');
        });
    });

    describe('Trading Metrics', () => {
        it('should record trade metrics', () => {
            const trade = {
                pnl: 150.50,
                duration: 3600000, // 1 hour
                quantity: 100,
                slippage: 0.02
            };

            const emitSpy = jest.spyOn(metricsCollector, 'emit');
            metricsCollector.recordTrade(trade);

            // Should increment trade counters
            expect(metricsCollector.counters.get('trades.executed').value).toBe(1);
            expect(metricsCollector.counters.get('trades.profitable').value).toBe(1);

            // Should record in histograms
            expect(metricsCollector.histograms.get('trading.trade_pnl').count).toBe(1);
            expect(metricsCollector.histograms.get('trading.trade_duration').count).toBe(1);

            expect(emitSpy).toHaveBeenCalledWith('trade.recorded', trade);
        });

        it('should record losing trade correctly', () => {
            const trade = {
                pnl: -75.25,
                duration: 1800000,
                quantity: 50
            };

            metricsCollector.recordTrade(trade);

            expect(metricsCollector.counters.get('trades.executed').value).toBe(1);
            expect(metricsCollector.counters.get('trades.losses').value).toBe(1);
            expect(metricsCollector.counters.get('trades.profitable').value).toBe(0);
        });

        it('should record order metrics', () => {
            const order = {
                status: 'filled',
                executionTime: 45
            };

            const emitSpy = jest.spyOn(metricsCollector, 'emit');
            metricsCollector.recordOrder(order);

            expect(metricsCollector.counters.get('orders.placed').value).toBe(1);
            expect(metricsCollector.counters.get('orders.filled').value).toBe(1);
            expect(metricsCollector.histograms.get('latency.order_execution').count).toBe(1);

            expect(emitSpy).toHaveBeenCalledWith('order.recorded', order);
        });

        it('should record cancelled order', () => {
            const order = { status: 'cancelled' };
            metricsCollector.recordOrder(order);

            expect(metricsCollector.counters.get('orders.placed').value).toBe(1);
            expect(metricsCollector.counters.get('orders.cancelled').value).toBe(1);
            expect(metricsCollector.counters.get('orders.filled').value).toBe(0);
        });
    });

    describe('Error Metrics', () => {
        it('should record error metrics', () => {
            const error = new Error('Test error');
            error.name = 'TestError';

            const emitSpy = jest.spyOn(metricsCollector, 'emit');
            metricsCollector.recordError('trading', error);

            expect(metricsCollector.counters.get('errors.trading').value).toBe(1);
            expect(emitSpy).toHaveBeenCalledWith('error.recorded', {
                type: 'trading',
                error
            });
        });
    });

    describe('Portfolio Metrics', () => {
        it('should update portfolio metrics', () => {
            const portfolio = {
                totalValue: 100000,
                unrealizedPnl: 1500,
                realizedPnl: 2500,
                positionCount: 5
            };

            const emitSpy = jest.spyOn(metricsCollector, 'emit');
            metricsCollector.updatePortfolioMetrics(portfolio);

            expect(metricsCollector.gauges.get('trading.portfolio_value').value).toBe(100000);
            expect(metricsCollector.gauges.get('trading.unrealized_pnl').value).toBe(1500);
            expect(metricsCollector.gauges.get('trading.active_positions').value).toBe(5);

            expect(emitSpy).toHaveBeenCalledWith('portfolio.updated', portfolio);
        });
    });

    describe('Risk Metrics', () => {
        it('should update risk metrics', () => {
            const risk = {
                exposureRatio: 0.75,
                varEstimate: 5000
            };

            const emitSpy = jest.spyOn(metricsCollector, 'emit');
            metricsCollector.updateRiskMetrics(risk);

            expect(metricsCollector.gauges.get('risk.exposure_ratio').value).toBe(0.75);
            expect(metricsCollector.gauges.get('risk.var_estimate').value).toBe(5000);

            expect(emitSpy).toHaveBeenCalledWith('risk.updated', risk);
        });
    });

    describe('Collection Lifecycle', () => {
        it('should start collection', () => {
            const emitSpy = jest.spyOn(metricsCollector, 'emit');
            metricsCollector.start();

            expect(metricsCollector.isCollecting).toBe(true);
            expect(metricsCollector.aggregationTimer).toBeDefined();
            expect(emitSpy).toHaveBeenCalledWith('collection.started');
        });

        it('should stop collection', () => {
            metricsCollector.start();
            const emitSpy = jest.spyOn(metricsCollector, 'emit');

            metricsCollector.stop();

            expect(metricsCollector.isCollecting).toBe(false);
            expect(metricsCollector.aggregationTimer).toBeNull();
            expect(emitSpy).toHaveBeenCalledWith('collection.stopped');
        });
    });

    describe('Aggregation', () => {
        it('should aggregate metrics', () => {
            // Setup some metrics
            metricsCollector.createCounter('test.counter');
            metricsCollector.incrementCounter('test.counter', 5);

            metricsCollector.createGauge('test.gauge');
            metricsCollector.setGauge('test.gauge', 42);

            metricsCollector.createHistogram('test.histogram');
            metricsCollector.observeHistogram('test.histogram', 100);

            const emitSpy = jest.spyOn(metricsCollector, 'emit');
            metricsCollector.aggregateMetrics();

            expect(emitSpy).toHaveBeenCalledWith('metrics.aggregated', expect.objectContaining({
                timestamp: expect.any(Date),
                counters: expect.objectContaining({
                    'test.counter': expect.objectContaining({
                        value: 5,
                        rate: expect.any(Number)
                    })
                }),
                gauges: expect.objectContaining({
                    'test.gauge': expect.objectContaining({
                        value: 42,
                        change: expect.any(Number)
                    })
                }),
                histograms: expect.objectContaining({
                    'test.histogram': expect.objectContaining({
                        count: 1,
                        sum: 100,
                        mean: 100
                    })
                })
            }));
        });
    });

    describe('Data Cleanup', () => {
        it('should clean up old data', () => {
            // Set very short retention period
            metricsCollector.config.retentionPeriod = 100;

            metricsCollector.createCounter('test.cleanup');
            metricsCollector.incrementCounter('test.cleanup', 1);

            const counter = metricsCollector.counters.get('test.cleanup');
            expect(counter.history.length).toBe(1);

            // Wait for retention period
            setTimeout(() => {
                metricsCollector.cleanupOldData();
                expect(counter.history.length).toBe(0);
            }, 150);
        });
    });

    describe('Export Functionality', () => {
        it('should export Prometheus metrics', () => {
            metricsCollector.createCounter('test.prometheus');
            metricsCollector.incrementCounter('test.prometheus', 5);

            const prometheus = metricsCollector.exportPrometheusMetrics();

            expect(typeof prometheus).toBe('string');
            expect(prometheus).toContain('test.prometheus');
            expect(prometheus).toContain('# TYPE test.prometheus counter');
            expect(prometheus).toContain('test.prometheus 5');
        });

        it('should get metrics summary', () => {
            const summary = metricsCollector.getMetricsSummary();

            expect(summary).toBeDefined();
            expect(summary.counters).toBeDefined();
            expect(summary.gauges).toBeDefined();
            expect(summary.histograms).toBeDefined();
            expect(typeof summary.isCollecting).toBe('boolean');
        });
    });

    describe('Rate Calculation', () => {
        it('should calculate counter rate', () => {
            metricsCollector.createCounter('test.rate');

            // Add multiple increments with timestamps
            const counter = metricsCollector.counters.get('test.rate');
            const now = Date.now();

            counter.history.push({
                timestamp: new Date(now - 5000),
                value: 0,
                increment: 0
            });

            counter.history.push({
                timestamp: new Date(now),
                value: 10,
                increment: 10
            });

            const rate = metricsCollector.calculateRate(counter);
            expect(typeof rate).toBe('number');
            expect(rate).toBeGreaterThanOrEqual(0);
        });

        it('should calculate gauge change', () => {
            metricsCollector.createGauge('test.change');
            metricsCollector.setGauge('test.change', 10);
            metricsCollector.setGauge('test.change', 15);

            const gauge = metricsCollector.gauges.get('test.change');
            const change = metricsCollector.calculateChange(gauge);

            expect(change).toBe(5);
        });
    });
});