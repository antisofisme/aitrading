import { DiagramEngine } from '../core/DiagramEngine';
import {
  BatchGenerationRequest,
  BatchGenerationResult,
  DiagramType,
  AnalysisData,
  DiagramOptions,
  GenerationResult
} from '../core/types';

export class BatchProcessor {
  private engine: DiagramEngine;
  private maxConcurrent: number;
  private retryAttempts: number;

  constructor(
    engine: DiagramEngine,
    maxConcurrent: number = 5,
    retryAttempts: number = 3
  ) {
    this.engine = engine;
    this.maxConcurrent = maxConcurrent;
    this.retryAttempts = retryAttempts;
  }

  /**
   * Process multiple diagram generation requests in batches
   */
  async processBatch(requests: BatchGenerationRequest[]): Promise<BatchGenerationResult> {
    const startTime = Date.now();

    // Sort requests by priority
    const sortedRequests = this.sortByPriority(requests);

    // Process in chunks to control concurrency
    const chunks = this.chunkArray(sortedRequests, this.maxConcurrent);
    const allResults: GenerationResult[] = [];

    for (const chunk of chunks) {
      const chunkResults = await this.processChunk(chunk);
      allResults.push(...chunkResults);
    }

    const duration = Date.now() - startTime;
    const successful = allResults.filter(r => r.success).length;
    const failed = allResults.length - successful;

    return {
      requestId: this.generateRequestId(),
      results: allResults,
      summary: {
        total: requests.length,
        successful,
        failed,
        duration
      }
    };
  }

  /**
   * Process a single chunk of requests concurrently
   */
  private async processChunk(requests: BatchGenerationRequest[]): Promise<GenerationResult[]> {
    const promises = requests.map(request => this.processRequestWithRetry(request));
    const results = await Promise.allSettled(promises);

    return results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        return {
          success: false,
          error: result.reason?.message || 'Processing failed',
          diagramType: requests[index].diagramType
        };
      }
    });
  }

  /**
   * Process a single request with retry logic
   */
  private async processRequestWithRetry(request: BatchGenerationRequest): Promise<GenerationResult> {
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        const result = await this.engine.generateDiagram(
          request.analysisData,
          request.diagramType,
          request.options
        );

        if (result.success) {
          return result;
        } else {
          lastError = new Error(result.error || 'Generation failed');
        }

      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');

        // Wait before retry (exponential backoff)
        if (attempt < this.retryAttempts) {
          await this.delay(Math.pow(2, attempt) * 1000);
        }
      }
    }

    return {
      success: false,
      error: `Failed after ${this.retryAttempts} attempts: ${lastError?.message}`,
      diagramType: request.diagramType
    };
  }

  /**
   * Auto-generate diagrams from analysis data
   */
  async autoGenerateFromAnalysis(
    analysisDataList: AnalysisData[],
    options?: DiagramOptions
  ): Promise<BatchGenerationResult> {
    const requests: BatchGenerationRequest[] = [];

    for (const analysisData of analysisDataList) {
      // Auto-select diagram type
      const diagramType = await this.engine.autoSelectDiagramType(analysisData);

      // Optimize layout for the diagram
      const optimizedOptions = await this.engine.optimizeLayout(diagramType, analysisData);

      requests.push({
        id: `auto_${analysisData.id}`,
        analysisData,
        diagramType,
        options: { ...options, ...optimizedOptions },
        priority: this.calculatePriority(analysisData)
      });
    }

    return await this.processBatch(requests);
  }

  /**
   * Generate all supported diagram types for single analysis data
   */
  async generateAllTypes(
    analysisData: AnalysisData,
    options?: DiagramOptions
  ): Promise<BatchGenerationResult> {
    const supportedTypes: DiagramType[] = [
      'system-architecture',
      'component-graph',
      'sequence-diagram',
      'er-diagram',
      'user-journey'
    ];

    const requests: BatchGenerationRequest[] = supportedTypes.map(type => ({
      id: `${analysisData.id}_${type}`,
      analysisData,
      diagramType: type,
      options,
      priority: 'normal'
    }));

    return await this.processBatch(requests);
  }

  /**
   * Process diagram variations (different themes/formats)
   */
  async generateVariations(
    analysisData: AnalysisData,
    diagramType: DiagramType,
    variations: DiagramOptions[]
  ): Promise<BatchGenerationResult> {
    const requests: BatchGenerationRequest[] = variations.map((variation, index) => ({
      id: `${analysisData.id}_${diagramType}_var${index}`,
      analysisData,
      diagramType,
      options: variation,
      priority: 'low'
    }));

    return await this.processBatch(requests);
  }

  /**
   * Monitor batch processing progress
   */
  async processBatchWithProgress(
    requests: BatchGenerationRequest[],
    onProgress?: (completed: number, total: number) => void
  ): Promise<BatchGenerationResult> {
    const startTime = Date.now();
    const sortedRequests = this.sortByPriority(requests);
    const chunks = this.chunkArray(sortedRequests, this.maxConcurrent);
    const allResults: GenerationResult[] = [];

    let completed = 0;

    for (const chunk of chunks) {
      const chunkResults = await this.processChunk(chunk);
      allResults.push(...chunkResults);

      completed += chunk.length;
      if (onProgress) {
        onProgress(completed, requests.length);
      }
    }

    const duration = Date.now() - startTime;
    const successful = allResults.filter(r => r.success).length;
    const failed = allResults.length - successful;

    return {
      requestId: this.generateRequestId(),
      results: allResults,
      summary: {
        total: requests.length,
        successful,
        failed,
        duration
      }
    };
  }

  /**
   * Sort requests by priority
   */
  private sortByPriority(requests: BatchGenerationRequest[]): BatchGenerationRequest[] {
    const priorityOrder = { critical: 0, high: 1, normal: 2, low: 3 };

    return requests.sort((a, b) => {
      const aPriority = priorityOrder[a.priority || 'normal'];
      const bPriority = priorityOrder[b.priority || 'normal'];
      return aPriority - bPriority;
    });
  }

  /**
   * Chunk array into smaller arrays
   */
  private chunkArray<T>(array: T[], chunkSize: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += chunkSize) {
      chunks.push(array.slice(i, i + chunkSize));
    }
    return chunks;
  }

  /**
   * Calculate priority based on analysis data characteristics
   */
  private calculatePriority(analysisData: AnalysisData): 'low' | 'normal' | 'high' {
    // High priority for critical systems or complex data
    if (analysisData.complexity > 0.8) return 'high';
    if (analysisData.contentType.includes('critical')) return 'high';

    // Normal priority for regular content
    if (analysisData.complexity > 0.3) return 'normal';

    // Low priority for simple content
    return 'low';
  }

  /**
   * Generate unique request ID
   */
  private generateRequestId(): string {
    return `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Delay utility for retry logic
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get processing statistics
   */
  getStatistics(): {
    maxConcurrent: number;
    retryAttempts: number;
    averageProcessingTime: number;
  } {
    return {
      maxConcurrent: this.maxConcurrent,
      retryAttempts: this.retryAttempts,
      averageProcessingTime: 0 // Would be calculated from historical data
    };
  }

  /**
   * Update batch processing configuration
   */
  updateConfiguration(config: {
    maxConcurrent?: number;
    retryAttempts?: number;
  }): void {
    if (config.maxConcurrent !== undefined) {
      this.maxConcurrent = Math.max(1, config.maxConcurrent);
    }
    if (config.retryAttempts !== undefined) {
      this.retryAttempts = Math.max(0, config.retryAttempts);
    }
  }
}