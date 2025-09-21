/**
 * Core type definitions for the AI Trading System Analysis Engine
 */

export interface CodeElement {
  id: string;
  name: string;
  type: ElementType;
  filePath: string;
  startLine: number;
  endLine: number;
  metadata: Record<string, any>;
}

export enum ElementType {
  CLASS = 'class',
  INTERFACE = 'interface',
  FUNCTION = 'function',
  METHOD = 'method',
  PROPERTY = 'property',
  VARIABLE = 'variable',
  IMPORT = 'import',
  EXPORT = 'export',
  MODULE = 'module',
  ENUM = 'enum',
  TYPE_ALIAS = 'type_alias',
  DECORATOR = 'decorator',
  API_ENDPOINT = 'api_endpoint',
  DATABASE_ENTITY = 'database_entity',
  TRADING_STRATEGY = 'trading_strategy',
  RISK_COMPONENT = 'risk_component',
  NOTIFICATION_HANDLER = 'notification_handler'
}

export interface Relationship {
  id: string;
  sourceId: string;
  targetId: string;
  type: RelationshipType;
  weight: number;
  metadata: RelationshipMetadata;
}

export enum RelationshipType {
  INHERITS = 'inherits',
  IMPLEMENTS = 'implements',
  DEPENDS_ON = 'depends_on',
  CALLS = 'calls',
  IMPORTS = 'imports',
  EXPORTS = 'exports',
  COMPOSITION = 'composition',
  AGGREGATION = 'aggregation',
  ASSOCIATION = 'association',
  DATA_FLOW = 'data_flow',
  API_CALL = 'api_call',
  DATABASE_RELATION = 'database_relation',
  EVENT_EMISSION = 'event_emission',
  EVENT_SUBSCRIPTION = 'event_subscription',
  STRATEGY_USAGE = 'strategy_usage',
  RISK_MONITORING = 'risk_monitoring'
}

export interface RelationshipMetadata {
  description?: string;
  confidence: number;
  frequency?: number;
  direction: 'unidirectional' | 'bidirectional';
  category: 'structural' | 'behavioral' | 'data' | 'trading';
  tags: string[];
}

export interface AnalysisGraph {
  elements: Map<string, CodeElement>;
  relationships: Map<string, Relationship>;
  metadata: GraphMetadata;
}

export interface GraphMetadata {
  projectName: string;
  analysisDate: Date;
  version: string;
  filePaths: string[];
  statistics: GraphStatistics;
  tradingSystemMetrics: TradingSystemMetrics;
}

export interface GraphStatistics {
  totalElements: number;
  totalRelationships: number;
  elementsByType: Record<ElementType, number>;
  relationshipsByType: Record<RelationshipType, number>;
  cyclomaticComplexity: number;
  cohesion: number;
  coupling: number;
}

export interface TradingSystemMetrics {
  strategyCount: number;
  riskComponentCount: number;
  apiEndpointCount: number;
  dataSourceCount: number;
  notificationHandlerCount: number;
  complexityScore: number;
  riskScore: number;
}

export interface DiagramConfig {
  type: DiagramType;
  title: string;
  direction?: 'TB' | 'TD' | 'BT' | 'RL' | 'LR';
  theme?: 'default' | 'dark' | 'forest' | 'neutral';
  filters: DiagramFilter[];
  groupBy?: GroupingStrategy;
  showMetrics?: boolean;
}

export enum DiagramType {
  CLASS_DIAGRAM = 'classDiagram',
  FLOW_CHART = 'flowchart',
  SEQUENCE_DIAGRAM = 'sequenceDiagram',
  ER_DIAGRAM = 'erDiagram',
  STATE_DIAGRAM = 'stateDiagram',
  GITGRAPH = 'gitgraph',
  MINDMAP = 'mindmap',
  TIMELINE = 'timeline',
  TRADING_FLOW = 'tradingFlow',
  RISK_DIAGRAM = 'riskDiagram',
  DATA_FLOW = 'dataFlow'
}

export interface DiagramFilter {
  elementTypes?: ElementType[];
  relationshipTypes?: RelationshipType[];
  filePatterns?: string[];
  complexity?: { min?: number; max?: number };
  tags?: string[];
}

export enum GroupingStrategy {
  BY_MODULE = 'by_module',
  BY_LAYER = 'by_layer',
  BY_FEATURE = 'by_feature',
  BY_COMPLEXITY = 'by_complexity',
  BY_TRADING_COMPONENT = 'by_trading_component'
}

export interface AnalysisConfig {
  include: string[];
  exclude: string[];
  parsers: ParserConfig[];
  analyzers: AnalyzerConfig[];
  cache: CacheConfig;
  hooks: HooksConfig;
  output: OutputConfig;
}

export interface ParserConfig {
  name: string;
  enabled: boolean;
  filePatterns: string[];
  options: Record<string, any>;
}

export interface AnalyzerConfig {
  name: string;
  enabled: boolean;
  priority: number;
  options: Record<string, any>;
}

export interface CacheConfig {
  enabled: boolean;
  ttl: number;
  strategy: 'memory' | 'file' | 'claude-flow';
  namespace: string;
}

export interface HooksConfig {
  enabled: boolean;
  events: string[];
  incremental: boolean;
  notificationThreshold: number;
}

export interface OutputConfig {
  formats: ('json' | 'yaml' | 'mermaid' | 'dot')[];
  directory: string;
  includeMetadata: boolean;
  compress: boolean;
}

export interface AnalysisResult {
  graph: AnalysisGraph;
  diagrams: GeneratedDiagram[];
  metrics: AnalysisMetrics;
  recommendations: Recommendation[];
  timestamp: Date;
}

export interface GeneratedDiagram {
  id: string;
  type: DiagramType;
  title: string;
  content: string;
  metadata: DiagramMetadata;
}

export interface DiagramMetadata {
  elementCount: number;
  relationshipCount: number;
  complexity: number;
  renderTime: number;
  estimatedSize: string;
}

export interface AnalysisMetrics {
  parseTime: number;
  analysisTime: number;
  diagramGenerationTime: number;
  cacheHitRate: number;
  memoryUsage: number;
  filesProcessed: number;
  errorsCount: number;
  warningsCount: number;
}

export interface Recommendation {
  id: string;
  type: 'performance' | 'structure' | 'complexity' | 'security' | 'trading';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  affectedElements: string[];
  suggestedActions: string[];
  confidence: number;
}

export interface ParserContext {
  filePath: string;
  content: string;
  ast: any;
  sourceFile: any;
  metadata: Record<string, any>;
}

export interface AnalyzerContext {
  graph: AnalysisGraph;
  config: AnalysisConfig;
  cache: Map<string, any>;
  logger: Logger;
}

export interface Logger {
  debug(message: string, ...args: any[]): void;
  info(message: string, ...args: any[]): void;
  warn(message: string, ...args: any[]): void;
  error(message: string, ...args: any[]): void;
}

export interface TradingPattern {
  name: string;
  type: 'strategy' | 'indicator' | 'signal' | 'risk_management';
  confidence: number;
  elements: string[];
  description: string;
}

export interface DataFlowPath {
  id: string;
  source: string;
  target: string;
  path: string[];
  type: 'market_data' | 'order_flow' | 'risk_data' | 'notification';
  latency?: number;
  volume?: number;
}

export interface CacheEntry<T = any> {
  key: string;
  value: T;
  timestamp: Date;
  ttl: number;
  hits: number;
  metadata?: Record<string, any>;
}