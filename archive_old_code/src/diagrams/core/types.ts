export type DiagramType =
  | 'system-architecture'
  | 'sequence-diagram'
  | 'er-diagram'
  | 'component-graph'
  | 'user-journey'
  | 'trading-workflow'
  | 'data-flow'
  | 'state-diagram'
  | 'class-diagram'
  | 'gantt-chart';

export type OutputFormat = 'svg' | 'png' | 'pdf' | 'html' | 'json';

export type ThemeName =
  | 'default'
  | 'dark'
  | 'neutral'
  | 'forest'
  | 'base'
  | 'trading-light'
  | 'trading-dark'
  | 'professional'
  | 'minimal';

export interface DiagramConfig {
  defaultTheme?: ThemeName;
  themes?: Record<string, ThemeConfig>;
  outputDirectory?: string;
  cacheEnabled?: boolean;
  maxConcurrentGenerations?: number;
}

export interface ThemeConfig {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  text: string;
  border: string;
  success: string;
  warning: string;
  error: string;
  fontFamily?: string;
  fontSize?: number;
}

export interface DiagramOptions {
  theme?: ThemeName;
  formats?: OutputFormat[];
  layout?: LayoutOptions;
  colorScheme?: Record<string, string>;
  interactive?: boolean;
  animations?: boolean;
  responsive?: boolean;
  title?: string;
  subtitle?: string;
  watermark?: string;
}

export interface LayoutOptions {
  direction?: 'TB' | 'BT' | 'LR' | 'RL';
  spacing?: 'compact' | 'normal' | 'wide';
  grouping?: 'none' | 'clustered' | 'hierarchical';
  alignment?: 'left' | 'center' | 'right';
  maxWidth?: number;
  maxHeight?: number;
}

export interface AnalysisData {
  id: string;
  contentType: string;
  structure: string[];
  complexity: number;
  nodes?: DiagramNode[];
  relationships?: DiagramRelationship[];
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface DiagramNode {
  id: string;
  label: string;
  type: string;
  properties?: Record<string, any>;
  position?: { x: number; y: number };
  style?: NodeStyle;
}

export interface DiagramRelationship {
  id: string;
  source: string;
  target: string;
  type: string;
  label?: string;
  properties?: Record<string, any>;
  style?: EdgeStyle;
}

export interface NodeStyle {
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  shape?: 'rect' | 'circle' | 'diamond' | 'hexagon' | 'cylinder' | 'actor';
  fontSize?: number;
  fontWeight?: 'normal' | 'bold';
  fontColor?: string;
}

export interface EdgeStyle {
  stroke?: string;
  strokeWidth?: number;
  strokeDasharray?: string;
  fill?: string;
  fontSize?: number;
  fontColor?: string;
}

export interface GenerationResult {
  success: boolean;
  diagramType: DiagramType;
  mermaidCode?: string;
  outputs?: Record<OutputFormat, string | Buffer>;
  error?: string;
  metadata?: {
    generatedAt: string;
    performance?: Record<string, number>;
    [key: string]: any;
  };
}

export interface TemplateContext {
  nodes: DiagramNode[];
  relationships: DiagramRelationship[];
  metadata: Record<string, any>;
  options: DiagramOptions;
}

export interface MermaidTemplate {
  type: DiagramType;
  template: string;
  variables: string[];
  validation?: (context: TemplateContext) => boolean;
  preprocessing?: (context: TemplateContext) => TemplateContext;
}

export interface MCPDiagramResult {
  type: DiagramType;
  mermaidCode: string;
  outputs: Record<OutputFormat, string | Buffer>;
  metadata: Record<string, any>;
}

export interface FileWatcherConfig {
  filePath: string;
  diagramType: DiagramType;
  options?: DiagramOptions;
  autoRegenerate?: boolean;
  debounceMs?: number;
}

export interface GenerationMetrics {
  totalGenerated: number;
  successRate: number;
  averageGenerationTime: number;
  errorCounts: Record<string, number>;
  formatDistribution: Record<OutputFormat, number>;
}

export interface DiagramValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

export interface AutoLayoutResult {
  optimizedOptions: DiagramOptions;
  reasoning: string;
  expectedPerformance: {
    renderTime: number;
    memoryUsage: number;
    readability: number;
  };
}

export interface BatchGenerationRequest {
  id: string;
  analysisData: AnalysisData;
  diagramType: DiagramType;
  options?: DiagramOptions;
  priority?: 'low' | 'normal' | 'high';
}

export interface BatchGenerationResult {
  requestId: string;
  results: GenerationResult[];
  summary: {
    total: number;
    successful: number;
    failed: number;
    duration: number;
  };
}

// Event types for hooks integration
export interface DiagramEvent {
  type: 'generation-start' | 'generation-complete' | 'generation-error' | 'file-change';
  diagramType: DiagramType;
  data: any;
  timestamp: string;
}

export interface HookConfiguration {
  preGeneration?: (event: DiagramEvent) => Promise<void>;
  postGeneration?: (event: DiagramEvent) => Promise<void>;
  onError?: (event: DiagramEvent) => Promise<void>;
  onFileChange?: (event: DiagramEvent) => Promise<void>;
}