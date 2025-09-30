# Internal Contract: Output Formatting Engine

## Purpose
Centralized output formatting system dalam API Gateway yang mengkonversi internal Protocol Buffer messages ke format yang sesuai untuk setiap destination channel (JSON untuk WebSocket, Telegram format, MT5 binary).

## Architecture Overview
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Format        │────│   Transformation │────│   Template      │
│   Detector      │    │   Engine         │    │   Manager       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
    ┌────▼────┐              ┌────▼────┐              ┌────▼────┐
    │ Schema  │              │ Data     │              │ Output  │
    │ Manager │              │ Mapper   │              │ Encoder │
    └─────────┘              └─────────┘              └─────────┘
```

## Core Formatting Schema
```protobuf
message OutputFormatter {
  FormatterConfig config = 1;
  repeated FormatDefinition formats = 2;
  TemplateManager templates = 3;
  TransformationEngine transformer = 4;
  FormatterMetrics metrics = 5;
  int64 last_updated = 6;
}

message FormatterConfig {
  string formatter_id = 1;            // "output-formatter-v1"
  bool enable_caching = 2;            // Enable format caching
  int32 cache_ttl_seconds = 3;        // 300 seconds cache TTL
  bool enable_compression = 4;        // Enable output compression
  int32 max_output_size_kb = 5;      // 1024 KB max output size
  CompressionLevel compression = 6;   // Compression level
}

message FormatDefinition {
  string format_id = 1;               // "telegram-message", "websocket-json"
  OutputFormat format_type = 2;       // JSON/XML/BINARY/TEXT/TELEGRAM
  ChannelType target_channel = 3;     // TELEGRAM/WEBSOCKET/HTTP/MT5
  SchemaMapping schema_mapping = 4;   // Protocol Buffer to target mapping
  FormatRules rules = 5;              // Formatting rules
  TemplateConfig template = 6;        // Template configuration
  ValidationRules validation = 7;     // Output validation rules
}

message TemplateManager {
  repeated Template templates = 1;     // Available templates
  TemplateCache cache = 2;            // Template caching
  TemplateMetrics template_metrics = 3; // Template performance metrics
}

message Template {
  string template_id = 1;             // "trading-signal-telegram"
  TemplateType type = 2;              // MUSTACHE/HANDLEBARS/JINJA2/CUSTOM
  string template_content = 3;        // Template source code
  repeated TemplateVariable variables = 4; // Available variables
  TemplateMetadata metadata = 5;      // Template metadata
  int64 created_at = 6;              // Template creation time
  int64 updated_at = 7;              // Last update time
}

message SchemaMapping {
  string source_schema = 1;           // "TradingOutput"
  string target_schema = 2;           // "TelegramMessage"
  repeated FieldMapping field_mappings = 3; // Field-level mappings
  repeated TransformRule transform_rules = 4; // Transformation rules
  DefaultValues defaults = 5;         // Default values for missing fields
}

message FieldMapping {
  string source_field = 1;            // "trading_signal.confidence"
  string target_field = 2;            // "message.confidence_text"
  MappingType type = 3;               // DIRECT/COMPUTED/TEMPLATE/CONDITIONAL
  TransformFunction transform = 4;    // Transformation function
  ConditionalMapping condition = 5;   // Conditional mapping logic
}

message TransformFunction {
  FunctionType type = 1;              // FORMAT/CALCULATE/LOOKUP/CUSTOM
  string function_name = 2;           // "formatPercentage", "formatCurrency"
  repeated string parameters = 3;     // Function parameters
  string custom_script = 4;           // Custom JavaScript/Python script
}

message FormatRules {
  NumberFormatting numbers = 1;       // Number formatting rules
  DateTimeFormatting datetime = 2;    // Date/time formatting rules
  TextFormatting text = 3;            // Text formatting rules
  CurrencyFormatting currency = 4;    // Currency formatting rules
  LocalizationRules localization = 5; // Localization rules
}

message TransformationEngine {
  repeated Transformer transformers = 1; // Available transformers
  TransformCache cache = 2;           // Transformation caching
  EngineMetrics engine_metrics = 3;   // Engine performance metrics
}

message Transformer {
  string transformer_id = 1;          // "protobuf-to-json"
  TransformerType type = 2;           // PROTOBUF_JSON/JSON_XML/BINARY_TEXT
  TransformerConfig config = 3;       // Transformer configuration
  PerformanceProfile performance = 4; // Performance characteristics
}

// Channel-Specific Output Formats

message TelegramOutput {
  TelegramMessage message = 1;
  TelegramFormatting formatting = 2;
  TelegramKeyboard keyboard = 3;
}

message TelegramMessage {
  string text = 1;                    // Formatted message text
  string parse_mode = 2;              // "Markdown", "HTML", "MarkdownV2"
  bool disable_web_page_preview = 3;  // Disable link previews
  bool disable_notification = 4;     // Silent notification
}

message TelegramFormatting {
  EmojiConfig emojis = 1;             // Emoji configuration
  MarkdownConfig markdown = 2;        // Markdown formatting
  MessageLength length_limits = 3;    // Message length handling
}

message WebSocketOutput {
  WebSocketMessage message = 1;
  WebSocketFormatting formatting = 2;
  CompressionConfig compression = 3;
}

message WebSocketMessage {
  string type = 1;                    // "trading_status", "notification"
  string payload = 2;                 // JSON payload
  MessageMetadata metadata = 3;       // Message metadata
  int64 timestamp = 4;               // Message timestamp
}

message MT5Output {
  MT5Command command = 1;
  MT5Formatting formatting = 2;
  BinaryEncoding encoding = 3;
}

message MT5Command {
  bytes binary_data = 1;              // Protocol Buffer binary
  CommandMetadata metadata = 2;       // Command metadata
  ChecksumData checksum = 3;          // Data integrity checksum
}

// Formatting Utilities

message NumberFormatting {
  int32 decimal_places = 1;           // Number of decimal places
  string decimal_separator = 2;       // "." or ","
  string thousands_separator = 3;     // "," or " " or ""
  bool use_scientific = 4;            // Use scientific notation for large numbers
  NumberRounding rounding = 5;        // Rounding rules
}

message DateTimeFormatting {
  string date_format = 1;             // "YYYY-MM-DD", "DD/MM/YYYY"
  string time_format = 2;             // "HH:mm:ss", "HH:mm"
  string timezone = 3;                // "UTC", "Asia/Jakarta"
  bool use_relative = 4;              // "2 hours ago" vs absolute time
  LocaleSettings locale = 5;          // Locale-specific formatting
}

message CurrencyFormatting {
  string currency_code = 1;           // "USD", "EUR", "IDR"
  CurrencyPosition position = 2;      // BEFORE/AFTER symbol
  bool use_symbol = 3;                // Use symbol ($) vs code (USD)
  NumberFormatting number_format = 4; // Number formatting for currency
}

message EmojiConfig {
  map<string, string> signal_emojis = 1; // "BUY" -> "📈", "SELL" -> "📉"
  map<string, string> status_emojis = 2; // "SUCCESS" -> "✅", "ERROR" -> "❌"
  bool enable_emojis = 3;             // Enable/disable emoji usage
}

message ValidationRules {
  repeated FieldValidator validators = 1; // Field validation rules
  SizeConstraints size_limits = 2;    // Output size constraints
  ContentFilters content_filters = 3; // Content filtering rules
  SecurityValidation security = 4;    // Security validation
}

message FieldValidator {
  string field_path = 1;              // "message.text"
  ValidationType type = 2;            // REQUIRED/LENGTH/PATTERN/RANGE
  string validation_rule = 3;         // Validation rule specification
  string error_message = 4;           // Error message template
}

enum OutputFormat {
  JSON_FORMAT = 0;
  XML_FORMAT = 1;
  BINARY_FORMAT = 2;
  TEXT_FORMAT = 3;
  TELEGRAM_FORMAT = 4;
  HTML_FORMAT = 5;
}

enum ChannelType {
  TELEGRAM_CHANNEL = 0;
  WEBSOCKET_CHANNEL = 1;
  HTTP_API_CHANNEL = 2;
  MT5_CLIENT_CHANNEL = 3;
  EMAIL_CHANNEL = 4;
  SMS_CHANNEL = 5;
}

enum TemplateType {
  MUSTACHE = 0;
  HANDLEBARS = 1;
  JINJA2 = 2;
  CUSTOM_TEMPLATE = 3;
}

enum MappingType {
  DIRECT_MAPPING = 0;                 // Direct field copy
  COMPUTED_MAPPING = 1;               // Computed from multiple fields
  TEMPLATE_MAPPING = 2;               // Template-based mapping
  CONDITIONAL_MAPPING = 3;            // Conditional logic mapping
}

enum FunctionType {
  FORMAT_FUNCTION = 0;                // Format transformation
  CALCULATE_FUNCTION = 1;             // Mathematical calculation
  LOOKUP_FUNCTION = 2;                // Dictionary lookup
  CUSTOM_FUNCTION = 3;                // Custom script function
}

enum TransformerType {
  PROTOBUF_JSON = 0;
  JSON_XML = 1;
  BINARY_TEXT = 2;
  CUSTOM_TRANSFORM = 3;
}

enum CurrencyPosition {
  BEFORE_AMOUNT = 0;                  // $100.00
  AFTER_AMOUNT = 1;                   // 100.00 USD
}

enum NumberRounding {
  ROUND_UP = 0;
  ROUND_DOWN = 1;
  ROUND_NEAREST = 2;
  ROUND_BANKER = 3;
}

enum ValidationType {
  REQUIRED_VALIDATION = 0;
  LENGTH_VALIDATION = 1;
  PATTERN_VALIDATION = 2;
  RANGE_VALIDATION = 3;
}
```

## Formatting Pipeline

### **1. Format Detection & Selection**
```javascript
// Automatic format detection based on destination
function selectOutputFormat(destination, contentType, userPreferences) {
  // 1. Channel-based format selection
  if (destination.channel === "telegram") {
    return getFormat("telegram-message");
  }

  // 2. Content-type specific formatting
  if (contentType === "trading_signal") {
    return getFormat("trading-signal-" + destination.channel);
  }

  // 3. User preference override
  if (userPreferences.format) {
    return getFormat(userPreferences.format);
  }

  // 4. Default format fallback
  return getFormat("default-json");
}
```

### **2. Schema Transformation**
```javascript
// Transform Protocol Buffer to target format
function transformSchema(protobufMessage, targetFormat) {
  // 1. Extract field mappings
  mappings = getFieldMappings(protobufMessage.type, targetFormat);

  // 2. Apply field transformations
  transformedData = {};
  for (mapping of mappings) {
    value = extractField(protobufMessage, mapping.source_field);
    transformedValue = applyTransformation(value, mapping.transform);
    setField(transformedData, mapping.target_field, transformedValue);
  }

  // 3. Apply default values
  applyDefaults(transformedData, targetFormat.defaults);

  return transformedData;
}
```

### **3. Template Application**
```javascript
// Apply template untuk final formatting
function applyTemplate(data, templateId) {
  // 1. Load template
  template = loadTemplate(templateId);

  // 2. Prepare template context
  context = prepareTemplateContext(data);

  // 3. Apply localization
  localizedContext = applyLocalization(context, data.user_locale);

  // 4. Render template
  return renderTemplate(template, localizedContext);
}
```

## Channel-Specific Formatting

### **Telegram Message Formatting**
```javascript
// Format untuk Telegram dengan emoji dan markup
function formatTelegramMessage(tradingSignal) {
  template = `
🔔 *TRADING SIGNAL*

📈 *{{signal}} {{symbol}}*
💰 Entry: {{entry_price}}
🛑 Stop Loss: {{stop_loss}}
🎯 Take Profit: {{take_profit}}
📊 Confidence: {{confidence}}%
⏰ Time: {{timestamp}}

_{{reasoning}}_
  `;

  return applyTemplate(template, {
    signal: tradingSignal.signal === "BUY" ? "BUY" : "SELL",
    symbol: tradingSignal.symbol,
    entry_price: formatCurrency(tradingSignal.entry_price),
    stop_loss: formatCurrency(tradingSignal.stop_loss),
    take_profit: formatCurrency(tradingSignal.take_profit),
    confidence: formatPercentage(tradingSignal.confidence),
    timestamp: formatDateTime(tradingSignal.timestamp),
    reasoning: tradingSignal.reasoning
  });
}
```

### **WebSocket JSON Formatting**
```javascript
// Format untuk Frontend WebSocket
function formatWebSocketMessage(data, messageType) {
  return {
    type: messageType,
    user_id: data.user_id,
    timestamp: new Date().toISOString(),
    data: transformToWebSocketFormat(data),
    metadata: {
      correlation_id: data.correlation_id,
      source: "api-gateway",
      version: "1.0"
    }
  };
}
```

### **MT5 Binary Formatting**
```javascript
// Format untuk Client-MT5 binary Protocol Buffers
function formatMT5Command(executionCommand) {
  // 1. Create Protocol Buffer message
  pbMessage = new ExecutionCommand({
    command_id: executionCommand.command_id,
    user_id: executionCommand.user_id,
    action: transformToMT5Action(executionCommand.action),
    params: transformToMT5Params(executionCommand.params)
  });

  // 2. Serialize to binary
  binaryData = pbMessage.serializeBinary();

  // 3. Add integrity checksum
  checksum = calculateChecksum(binaryData);

  return {
    binary_data: binaryData,
    checksum: checksum,
    metadata: createMT5Metadata(executionCommand)
  };
}
```

## Performance Optimizations

### **Template Caching**
```javascript
// Intelligent template caching
const templateCache = new Map();

function getCachedTemplate(templateId) {
  if (!templateCache.has(templateId)) {
    template = loadAndCompileTemplate(templateId);
    templateCache.set(templateId, template);
  }
  return templateCache.get(templateId);
}
```

### **Format Precompilation**
- **Template Compilation**: Pre-compile templates at startup
- **Schema Mapping Cache**: Cache field mapping configurations
- **Transform Function Cache**: Cache compiled transformation functions
- **Output Validation Cache**: Cache validation rules

### **Batch Processing**
- **Bulk Transformation**: Process multiple messages in batches
- **Parallel Processing**: Use worker threads untuk heavy transformations
- **Pipeline Optimization**: Optimize transformation pipeline
- **Memory Management**: Efficient memory usage untuk large datasets

## Quality Assurance

### **Output Validation**
```javascript
// Comprehensive output validation
function validateOutput(formattedOutput, format) {
  // 1. Structure validation
  if (!validateStructure(formattedOutput, format.schema)) {
    throw new ValidationError("Invalid output structure");
  }

  // 2. Content validation
  if (!validateContent(formattedOutput, format.content_rules)) {
    throw new ValidationError("Content validation failed");
  }

  // 3. Size constraints
  if (!validateSize(formattedOutput, format.size_limits)) {
    throw new ValidationError("Output size exceeds limits");
  }

  // 4. Security validation
  if (!validateSecurity(formattedOutput, format.security_rules)) {
    throw new ValidationError("Security validation failed");
  }

  return true;
}
```

### **Error Handling**
- **Graceful Degradation**: Fallback to simpler formats on error
- **Partial Success**: Allow partial formatting success
- **Error Recovery**: Automatic recovery from formatting errors
- **Debug Information**: Detailed error information untuk troubleshooting

## Monitoring & Metrics

### **Performance Metrics**
- **Transformation Latency**: <1ms average formatting time
- **Template Render Time**: <500μs average template rendering
- **Cache Hit Rate**: >95% template cache hit rate
- **Error Rate**: <0.1% formatting error rate

### **Quality Metrics**
- **Output Validation Success**: 100% validation pass rate
- **Character Set Compliance**: UTF-8 compliance rate
- **Template Accuracy**: Template rendering accuracy
- **Localization Coverage**: Supported locale coverage