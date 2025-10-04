/**
 * Contract: Real-time Pricing Data Stream to Data Bridge
 * Direction: OANDA Collector → Data Bridge
 * Protocol: NATS
 * Subject: market.pricing.oanda.{instrument}
 */

const Joi = require('joi');

const PricingStreamSchema = Joi.object({
    // Message routing
    subject: Joi.string().pattern(/^market\.pricing\.oanda\.[A-Z_]+$/).required(),
    message_id: Joi.string().required(),
    timestamp: Joi.number().integer().required(),

    // Source metadata
    source: Joi.object({
        collector: Joi.string().valid('oanda-collector').required(),
        instance_id: Joi.string().required(),
        account_id: Joi.string().required(),
        environment: Joi.string().valid('practice', 'live').required()
    }).required(),

    // Pricing data
    data: Joi.object({
        // Instrument info
        instrument: Joi.string().required(), // e.g., "EUR_USD"
        type: Joi.string().valid('PRICE').required(),

        // Timestamp info
        time: Joi.string().isoDate().required(), // ISO 8601 format from OANDA

        // Bid/Ask prices
        bids: Joi.array().items(
            Joi.object({
                price: Joi.string().required(), // String to preserve precision
                liquidity: Joi.number().integer().min(0).required()
            })
        ).min(1).required(),

        asks: Joi.array().items(
            Joi.object({
                price: Joi.string().required(),
                liquidity: Joi.number().integer().min(0).required()
            })
        ).min(1).required(),

        // Derived values
        closeoutBid: Joi.string().optional(),
        closeoutAsk: Joi.string().optional(),

        // Status
        status: Joi.string().valid('tradeable', 'non-tradeable', 'invalid').optional(),
        tradeable: Joi.boolean().optional()
    }).required(),

    // Collector metadata
    metadata: Joi.object({
        collector_timestamp: Joi.string().isoDate().required(),
        latency_ms: Joi.number().min(0).optional(), // Time from OANDA to collector
        sequence_number: Joi.number().integer().min(0).optional()
    }).required()
});

/**
 * Process pricing stream data
 */
function processPricingStream(inputData, context = {}) {
    // Validate input
    const { error, value } = PricingStreamSchema.validate(inputData);
    if (error) {
        throw new Error(`Contract validation failed: ${error.details[0].message}`);
    }

    // Calculate mid price for convenience
    const bestBid = parseFloat(value.data.bids[0].price);
    const bestAsk = parseFloat(value.data.asks[0].price);
    const midPrice = ((bestBid + bestAsk) / 2).toFixed(5);
    const spread = (bestAsk - bestBid).toFixed(5);

    // Enrich pricing data
    const pricingData = {
        ...value,
        computed: {
            mid_price: midPrice,
            spread: spread,
            spread_pips: (parseFloat(spread) * 10000).toFixed(1) // For forex pairs
        },
        processed_at: Date.now()
    };

    return {
        type: 'pricing_stream',
        data: pricingData,
        routing_targets: ['data-bridge'],
        subject_pattern: `market.pricing.oanda.${value.data.instrument}`,
        retention_policy: 'limits', // Keep last N messages
        max_age_seconds: 60 // Pricing data expires quickly
    };
}

/**
 * Generate NATS subject for instrument
 */
function generateSubject(instrument) {
    return `market.pricing.oanda.${instrument.replace('/', '_')}`;
}

module.exports = {
    schema: PricingStreamSchema,
    process: processPricingStream,
    generateSubject: generateSubject,
    contractName: 'pricing-stream',
    direction: 'to-data-bridge',
    protocol: 'nats',
    subjectPattern: 'market.pricing.oanda.{instrument}'
};
