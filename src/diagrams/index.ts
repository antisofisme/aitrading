// Core exports
export { DiagramEngine } from './core/DiagramEngine';
export * from './core/types';

// Template exports
export { DiagramTemplate } from './templates/DiagramTemplate';
export { SystemArchitectureTemplate } from './templates/SystemArchitectureTemplate';
export { TradingWorkflowTemplate } from './templates/TradingWorkflowTemplate';
export { ERDiagramTemplate } from './templates/ERDiagramTemplate';
export { ComponentGraphTemplate } from './templates/ComponentGraphTemplate';
export { UserJourneyTemplate } from './templates/UserJourneyTemplate';

// Generator exports
export { DiagramGenerator } from './generators/DiagramGenerator';

// Format exports
export { OutputFormatter } from './formats/OutputFormatter';

// Theme exports
export { ThemeManager } from './themes/ThemeManager';

// MCP exports
export { MCPIntegration } from './mcp/MCPIntegration';

// Utility exports
export { BatchProcessor } from './utils/BatchProcessor';
export { FileWatcher } from './utils/FileWatcher';

// Factory function for easy initialization
export function createDiagramEngine(config?: any) {
  return new DiagramEngine(config);
}

// Factory function for complete diagram solution
export async function createDiagramSolution(config?: any) {
  const engine = new DiagramEngine(config);
  const batchProcessor = new BatchProcessor(engine);
  const mcpIntegration = new MCPIntegration();
  const fileWatcher = new FileWatcher(engine, mcpIntegration);

  await mcpIntegration.initialize();

  return {
    engine,
    batchProcessor,
    mcpIntegration,
    fileWatcher
  };
}