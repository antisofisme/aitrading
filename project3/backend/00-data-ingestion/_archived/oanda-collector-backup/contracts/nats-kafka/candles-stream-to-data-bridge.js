/**
 * Contract: Historical Candles Data Stream to Data Bridge
 * Direction: OANDA Collector → Data Bridge
 * Protocol: NATS
 * Subject: market.candles.oanda.{instrument}.{granularity}
 */

const Joi = require('joi');

const CandlesStreamSchema = Joi.object({
    // Message routing
    subject: Joi.string().pattern(/^market\.candles\.oanda\.[A-Z_]+\.(S\d+|M\d+|H\d+|D|W|M)$/).required(),
    message_id: Joi.string().required(),
    timestamp: Joi.number().integer().required(),

    // Source metadata
    source: Joi.object({
        collector: Joi.string().valid('oanda-collector').required(),
        instance_id: Joi.string().required(),
        account_id: Joi.string().required(),
        environment: Joi.string().valid('practice', 'live').required()
    }).required(),

    // Candle data
    data: Joi.object({
        // Instrument and timeframe
        instrument: Joi.string().required(), // e.g., "EUR_USD"
        granularity: Joi.string().valid(
            'S5', 'S10', 'S15', 'S30',  // Seconds
            'M1', 'M2', 'M4', 'M5', 'M10', 'M15', 'M30',  // Minutes
            'H1', 'H2', 'H3', 'H4', 'H6', 'H8', 'H12',    // Hours
            'D', 'W', 'M'  // Day, Week, Month
        ).required(),

        // Candles array
        candles: Joi.array().items(
            Joi.object({
                // Timestamp
                time: Joi.string().isoDate().required(),
                volume: Joi.number().integer().min(0).required(),
                complete: Joi.boolean().required(),

                // Mid prices
                mid: Joi.object({
                    o: Joi.string().required(), // Open
                    h: Joi.string().required(), // High
                    l: Joi.string().required(), // Low
                    c: Joi.string().required()  // Close
                }).optional(),

                // Bid prices
                bid: Joi.object({
                    o: Joi.string().required(),
                    h: Joi.string().required(),
                    l: Joi.string().required(),
                    c: Joi.string().required()
                }).optional(),

                // Ask prices
                ask: Joi.object({
                    o: Joi.string().required(),
                    h: Joi.string().required(),
                    l: Joi.string().required(),
                    c: Joi.string().required()
                }).optional()
            }).or('mid', 'bid', 'ask') // At least one price type required
        ).min(1).required(),

        // Request parameters
        request_params: Joi.object({
            count: Joi.number().integer().min(1).max(5000).optional(),
            from_time: Joi.string().isoDate().optional(),
            to_time: Joi.string().isoDate().optional(),
            price_type: Joi.string().valid('M', 'B', 'A', 'MBA').default('MBA')
        }).optional()
    }).required(),

    // Collector metadata
    metadata: Joi.object({
        collector_timestamp: Joi.string().isoDate().required(),
        total_candles: Joi.number().integer().min(0).required(),
        complete_candles: Joi.number().integer().min(0).required(),
        sequence_number: Joi.number().integer().min(0).optional()
    }).required()
});

/**
 * Process candles stream data
 */
function processCandlesStream(inputData, context = {}) {
    // Validate input
    const { error, value } = CandlesStreamSchema.validate(inputData);
    if (error) {
        throw new Error(`Contract validation failed: ${error.details[0].message}`);
    }

    // Enrich candle data with computed fields
    const enrichedCandles = value.data.candles.map(candle => {
        const priceData = candle.mid || candle.bid || candle.ask;
        const open = parseFloat(priceData.o);
        const high = parseFloat(priceData.h);
        const low = parseFloat(priceData.l);
        const close = parseFloat(priceData.c);

        return {
            ...candle,
            computed: {
                change: (close - open).toFixed(5),
                change_percent: (((close - open) / open) * 100).toFixed(2),
                range: (high - low).toFixed(5),
                is_bullish: close > open,
                body_size: Math.abs(close - open).toFixed(5),
                upper_wick: (high - Math.max(open, close)).toFixed(5),
                lower_wick: (Math.min(open, close) - low).toFixed(5)
            }
        };
    });

    const candlesData = {
        ...value,
        data: {
            ...value.data,
            candles: enrichedCandles
        },
        processed_at: Date.now()
    };

    return {
        type: 'candles_stream',
        data: candlesData,
        routing_targets: ['data-bridge'],
        subject_pattern: `market.candles.oanda.${value.data.instrument}.${value.data.granularity}`,
        retention_policy: 'limits',
        max_age_seconds: 3600 // Historical data can be kept longer
    };
}

/**
 * Generate NATS subject for instrument and granularity
 */
function generateSubject(instrument, granularity) {
    return `market.candles.oanda.${instrument.replace('/', '_')}.${granularity}`;
}

module.exports = {
    schema: CandlesStreamSchema,
    process: processCandlesStream,
    generateSubject: generateSubject,
    contractName: 'candles-stream',
    direction: 'to-data-bridge',
    protocol: 'nats',
    subjectPattern: 'market.candles.oanda.{instrument}.{granularity}'
};
