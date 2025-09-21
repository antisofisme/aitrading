/**
 * Trading Pattern Parser - Specialized parser for trading system patterns
 * Identifies trading strategies, risk management components, market data flows
 */

import {
  Parser,
  CodeElement,
  Relationship,
  ParserContext,
  Logger,
  ElementType,
  RelationshipType,
  TradingPattern,
  DataFlowPath
} from '../types';

export class TradingPatternParser implements Parser {
  name = 'trading-pattern';
  supportedExtensions = ['.ts', '.js', '.tsx', '.jsx'];

  // Trading pattern definitions
  private readonly tradingPatterns = {
    strategies: [
      /MovingAverage.*Strategy/i,
      /RSI.*Strategy/i,
      /MACD.*Strategy/i,
      /Bollinger.*Strategy/i,
      /Momentum.*Strategy/i,
      /Mean.*Reversion/i,
      /Trend.*Following/i,
      /Arbitrage.*Strategy/i,
      /Market.*Making/i,
      /Grid.*Trading/i,
      /Scalping.*Strategy/i,
      /Swing.*Trading/i,
      /Algorithm.*Trading/i,
      /Quantitative.*Strategy/i,
      /High.*Frequency.*Trading/i
    ],
    riskManagement: [
      /Risk.*Manager/i,
      /Position.*Sizer/i,
      /Stop.*Loss/i,
      /Take.*Profit/i,
      /Risk.*Calculator/i,
      /Portfolio.*Risk/i,
      /Exposure.*Monitor/i,
      /Drawdown.*Control/i,
      /Value.*at.*Risk/i,
      /Risk.*Metrics/i,
      /Risk.*Assessment/i,
      /Risk.*Monitor/i
    ],
    dataFlow: [
      /Market.*Data/i,
      /Price.*Feed/i,
      /Order.*Book/i,
      /Trade.*Feed/i,
      /Real.*Time.*Data/i,
      /Historical.*Data/i,
      /Data.*Stream/i,
      /Tick.*Data/i,
      /Bar.*Data/i,
      /Quote.*Data/i,
      /News.*Feed/i,
      /Economic.*Data/i
    ],
    execution: [
      /Order.*Manager/i,
      /Trade.*Executor/i,
      /Execution.*Engine/i,
      /Order.*Router/i,
      /Fill.*Manager/i,
      /Broker.*Interface/i,
      /Exchange.*API/i,
      /Order.*Gateway/i,
      /Trade.*Gateway/i,
      /Execution.*Venue/i
    ],
    notifications: [
      /Alert.*Manager/i,
      /Notification.*Service/i,
      /Signal.*Generator/i,
      /Alert.*Handler/i,
      /Message.*Queue/i,
      /Event.*Publisher/i,
      /Webhook.*Handler/i,
      /Email.*Notification/i,
      /SMS.*Alert/i,
      /Push.*Notification/i
    ],
    analytics: [
      /Performance.*Analytics/i,
      /Trade.*Analytics/i,
      /Portfolio.*Analytics/i,
      /Risk.*Analytics/i,
      /P&L.*Calculator/i,
      /Metrics.*Calculator/i,
      /Benchmark.*Comparison/i,
      /Sharpe.*Ratio/i,
      /Return.*Calculator/i,
      /Volatility.*Calculator/i
    ]
  };

  constructor(private logger: Logger) {}

  canParse(filePath: string): boolean {
    return this.supportedExtensions.some(ext => filePath.endsWith(ext)) &&
           this.containsTradingPatterns(filePath);
  }

  async parse(context: ParserContext): Promise<CodeElement[]> {
    const elements: CodeElement[] = [];

    try {
      // Analyze content for trading patterns
      const tradingElements = this.extractTradingElements(context);
      elements.push(...tradingElements);

      // Extract data flow elements
      const dataFlowElements = this.extractDataFlowElements(context);
      elements.push(...dataFlowElements);

      // Extract API endpoints related to trading
      const apiElements = this.extractTradingAPIElements(context);
      elements.push(...apiElements);

      // Extract configuration elements
      const configElements = this.extractTradingConfigElements(context);
      elements.push(...configElements);

      this.logger.debug(`Extracted ${elements.length} trading pattern elements from ${context.filePath}`);

    } catch (error) {
      this.logger.error(`Failed to parse trading patterns in ${context.filePath}:`, error);
    }

    return elements;
  }

  async extractRelationships(context: ParserContext, elements: CodeElement[]): Promise<Relationship[]> {
    const relationships: Relationship[] = [];

    try {
      // Extract strategy usage relationships
      relationships.push(...this.extractStrategyRelationships(context, elements));

      // Extract risk monitoring relationships
      relationships.push(...this.extractRiskRelationships(context, elements));

      // Extract data flow relationships
      relationships.push(...this.extractDataFlowRelationships(context, elements));

      // Extract execution flow relationships
      relationships.push(...this.extractExecutionRelationships(context, elements));

      // Extract notification relationships
      relationships.push(...this.extractNotificationRelationships(context, elements));

      this.logger.debug(`Extracted ${relationships.length} trading relationships from ${context.filePath}`);

    } catch (error) {
      this.logger.error(`Failed to extract trading relationships from ${context.filePath}:`, error);
    }

    return relationships;
  }

  private containsTradingPatterns(filePath: string): boolean {
    const fileName = filePath.toLowerCase();
    const tradingKeywords = [
      'trading', 'strategy', 'risk', 'order', 'market', 'portfolio',
      'execution', 'broker', 'exchange', 'price', 'signal', 'algorithm'
    ];

    return tradingKeywords.some(keyword => fileName.includes(keyword));
  }

  private extractTradingElements(context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];
    const content = context.content;
    const lines = content.split('\n');

    // Extract class-based trading components
    const classMatches = content.match(/class\s+(\w+)[^{]*{[^}]*}/gs) || [];

    classMatches.forEach((classMatch, index) => {
      const classNameMatch = classMatch.match(/class\s+(\w+)/);
      if (!classNameMatch) return;

      const className = classNameMatch[1];
      const elementType = this.determineTradingElementType(className, classMatch);

      if (elementType) {
        const startLine = this.findLineNumber(content, classMatch);

        const element: CodeElement = {
          id: this.generateId(context.filePath, className),
          name: className,
          type: elementType,
          filePath: context.filePath,
          startLine,
          endLine: startLine + classMatch.split('\n').length - 1,
          metadata: {
            tradingCategory: this.getTradingCategory(className, classMatch),
            methods: this.extractMethods(classMatch),
            dependencies: this.extractDependencies(classMatch),
            configuration: this.extractConfiguration(classMatch),
            patterns: this.identifyPatterns(className, classMatch),
            complexity: this.calculateTradingComplexity(classMatch),
            riskLevel: this.assessRiskLevel(className, classMatch)
          }
        };

        elements.push(element);
      }
    });

    // Extract function-based trading components
    const functionMatches = content.match(/(?:export\s+)?(?:async\s+)?function\s+(\w+)[^{]*{[^}]*}/gs) || [];

    functionMatches.forEach(functionMatch => {
      const functionNameMatch = functionMatch.match(/function\s+(\w+)/);
      if (!functionNameMatch) return;

      const functionName = functionNameMatch[1];

      if (this.isTradingFunction(functionName, functionMatch)) {
        const startLine = this.findLineNumber(content, functionMatch);

        const element: CodeElement = {
          id: this.generateId(context.filePath, functionName),
          name: functionName,
          type: ElementType.FUNCTION,
          filePath: context.filePath,
          startLine,
          endLine: startLine + functionMatch.split('\n').length - 1,
          metadata: {
            tradingCategory: this.getTradingCategory(functionName, functionMatch),
            parameters: this.extractFunctionParameters(functionMatch),
            returns: this.extractReturnType(functionMatch),
            patterns: this.identifyPatterns(functionName, functionMatch),
            complexity: this.calculateTradingComplexity(functionMatch)
          }
        };

        elements.push(element);
      }
    });

    return elements;
  }

  private extractDataFlowElements(context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];
    const content = context.content;

    // Look for data stream patterns
    const dataStreamPatterns = [
      /market.*data.*stream/i,
      /price.*feed/i,
      /order.*book.*stream/i,
      /trade.*feed/i,
      /real.*time.*data/i
    ];

    dataStreamPatterns.forEach(pattern => {
      const matches = content.match(new RegExp(pattern.source, 'gi')) || [];

      matches.forEach(match => {
        const startLine = this.findLineNumber(content, match);

        const element: CodeElement = {
          id: this.generateId(context.filePath, `data-flow-${match.replace(/\s+/g, '-')}`),
          name: match,
          type: ElementType.VARIABLE, // Could be refined to DATA_STREAM
          filePath: context.filePath,
          startLine,
          endLine: startLine,
          metadata: {
            dataFlowType: 'stream',
            category: 'data',
            tradingCategory: 'market_data'
          }
        };

        elements.push(element);
      });
    });

    return elements;
  }

  private extractTradingAPIElements(context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];
    const content = context.content;

    // Look for API endpoint patterns
    const apiPatterns = [
      /\/api\/.*trade/i,
      /\/api\/.*order/i,
      /\/api\/.*market/i,
      /\/api\/.*portfolio/i,
      /\/api\/.*risk/i,
      /\/api\/.*strategy/i
    ];

    apiPatterns.forEach(pattern => {
      const matches = content.match(new RegExp(pattern.source, 'gi')) || [];

      matches.forEach(match => {
        const startLine = this.findLineNumber(content, match);

        const element: CodeElement = {
          id: this.generateId(context.filePath, `api-${match.replace(/[\/\s]+/g, '-')}`),
          name: match,
          type: ElementType.API_ENDPOINT,
          filePath: context.filePath,
          startLine,
          endLine: startLine,
          metadata: {
            endpoint: match,
            method: this.extractHTTPMethod(content, match),
            tradingCategory: 'api'
          }
        };

        elements.push(element);
      });
    });

    return elements;
  }

  private extractTradingConfigElements(context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];
    const content = context.content;

    // Look for configuration objects
    const configPatterns = [
      /tradingConfig/i,
      /strategyConfig/i,
      /riskConfig/i,
      /brokerConfig/i,
      /exchangeConfig/i
    ];

    configPatterns.forEach(pattern => {
      const matches = content.match(new RegExp(`(${pattern.source})\\s*[=:].*?{[^}]*}`, 'gis')) || [];

      matches.forEach(match => {
        const configName = match.match(pattern)?.[0] || 'config';
        const startLine = this.findLineNumber(content, match);

        const element: CodeElement = {
          id: this.generateId(context.filePath, configName),
          name: configName,
          type: ElementType.VARIABLE,
          filePath: context.filePath,
          startLine,
          endLine: startLine + match.split('\n').length - 1,
          metadata: {
            configType: 'trading',
            category: 'configuration',
            tradingCategory: 'config'
          }
        };

        elements.push(element);
      });
    });

    return elements;
  }

  private extractStrategyRelationships(context: ParserContext, elements: CodeElement[]): Relationship[] {
    const relationships: Relationship[] = [];
    const content = context.content;

    const strategyElements = elements.filter(e =>
      e.type === ElementType.TRADING_STRATEGY ||
      (e.metadata.tradingCategory === 'strategy')
    );

    strategyElements.forEach(strategy => {
      // Find elements that use this strategy
      const usagePattern = new RegExp(`(\\w+).*${strategy.name}`, 'gi');
      const matches = content.match(usagePattern) || [];

      matches.forEach(match => {
        const userElement = elements.find(e => match.includes(e.name) && e.id !== strategy.id);

        if (userElement) {
          const relationship: Relationship = {
            id: `${userElement.id}-uses-strategy-${strategy.id}`,
            sourceId: userElement.id,
            targetId: strategy.id,
            type: RelationshipType.STRATEGY_USAGE,
            weight: 1,
            metadata: {
              confidence: 0.8,
              direction: 'unidirectional',
              category: 'trading',
              tags: ['strategy', 'usage']
            }
          };

          relationships.push(relationship);
        }
      });
    });

    return relationships;
  }

  private extractRiskRelationships(context: ParserContext, elements: CodeElement[]): Relationship[] {
    const relationships: Relationship[] = [];
    const content = context.content;

    const riskElements = elements.filter(e =>
      e.type === ElementType.RISK_COMPONENT ||
      (e.metadata.tradingCategory === 'risk')
    );

    riskElements.forEach(riskComponent => {
      // Find elements monitored by this risk component
      const monitoringPattern = new RegExp(`${riskComponent.name}.*monitor|monitor.*${riskComponent.name}`, 'gi');
      const matches = content.match(monitoringPattern) || [];

      elements.forEach(element => {
        if (element.id !== riskComponent.id &&
            (element.metadata.tradingCategory === 'strategy' ||
             element.metadata.tradingCategory === 'execution')) {

          const relationship: Relationship = {
            id: `${riskComponent.id}-monitors-${element.id}`,
            sourceId: riskComponent.id,
            targetId: element.id,
            type: RelationshipType.RISK_MONITORING,
            weight: 1,
            metadata: {
              confidence: 0.7,
              direction: 'unidirectional',
              category: 'trading',
              tags: ['risk', 'monitoring']
            }
          };

          relationships.push(relationship);
        }
      });
    });

    return relationships;
  }

  private extractDataFlowRelationships(context: ParserContext, elements: CodeElement[]): Relationship[] {
    const relationships: Relationship[] = [];
    const content = context.content;

    // Find data flow from market data to strategies
    const dataElements = elements.filter(e =>
      e.metadata.tradingCategory === 'market_data' ||
      e.metadata.dataFlowType === 'stream'
    );

    const strategyElements = elements.filter(e =>
      e.metadata.tradingCategory === 'strategy'
    );

    dataElements.forEach(dataElement => {
      strategyElements.forEach(strategy => {
        // Check if strategy uses this data source
        const dataUsagePattern = new RegExp(`${strategy.name}.*${dataElement.name}|${dataElement.name}.*${strategy.name}`, 'gi');

        if (dataUsagePattern.test(content)) {
          const relationship: Relationship = {
            id: `${dataElement.id}-feeds-${strategy.id}`,
            sourceId: dataElement.id,
            targetId: strategy.id,
            type: RelationshipType.DATA_FLOW,
            weight: 1,
            metadata: {
              confidence: 0.6,
              direction: 'unidirectional',
              category: 'data',
              tags: ['data-flow', 'market-data']
            }
          };

          relationships.push(relationship);
        }
      });
    });

    return relationships;
  }

  private extractExecutionRelationships(context: ParserContext, elements: CodeElement[]): Relationship[] {
    const relationships: Relationship[] = [];

    const strategyElements = elements.filter(e =>
      e.metadata.tradingCategory === 'strategy'
    );

    const executionElements = elements.filter(e =>
      e.metadata.tradingCategory === 'execution'
    );

    // Strategies typically use execution components
    strategyElements.forEach(strategy => {
      executionElements.forEach(executor => {
        const relationship: Relationship = {
          id: `${strategy.id}-executes-via-${executor.id}`,
          sourceId: strategy.id,
          targetId: executor.id,
          type: RelationshipType.DEPENDS_ON,
          weight: 1,
          metadata: {
            confidence: 0.7,
            direction: 'unidirectional',
            category: 'trading',
            tags: ['execution', 'strategy-execution']
          }
        };

        relationships.push(relationship);
      });
    });

    return relationships;
  }

  private extractNotificationRelationships(context: ParserContext, elements: CodeElement[]): Relationship[] {
    const relationships: Relationship[] = [];

    const notificationElements = elements.filter(e =>
      e.metadata.tradingCategory === 'notification'
    );

    const tradingElements = elements.filter(e =>
      ['strategy', 'risk', 'execution'].includes(e.metadata.tradingCategory)
    );

    // Trading components emit notifications
    tradingElements.forEach(tradingElement => {
      notificationElements.forEach(notifier => {
        const relationship: Relationship = {
          id: `${tradingElement.id}-notifies-${notifier.id}`,
          sourceId: tradingElement.id,
          targetId: notifier.id,
          type: RelationshipType.EVENT_EMISSION,
          weight: 1,
          metadata: {
            confidence: 0.6,
            direction: 'unidirectional',
            category: 'behavioral',
            tags: ['notification', 'event']
          }
        };

        relationships.push(relationship);
      });
    });

    return relationships;
  }

  // Helper methods

  private determineTradingElementType(name: string, content: string): ElementType | null {
    for (const [category, patterns] of Object.entries(this.tradingPatterns)) {
      if (patterns.some(pattern => pattern.test(name) || pattern.test(content))) {
        switch (category) {
          case 'strategies':
            return ElementType.TRADING_STRATEGY;
          case 'riskManagement':
            return ElementType.RISK_COMPONENT;
          case 'notifications':
            return ElementType.NOTIFICATION_HANDLER;
          default:
            return ElementType.CLASS;
        }
      }
    }
    return null;
  }

  private getTradingCategory(name: string, content: string): string {
    for (const [category, patterns] of Object.entries(this.tradingPatterns)) {
      if (patterns.some(pattern => pattern.test(name) || pattern.test(content))) {
        return category.replace(/([A-Z])/g, '_$1').toLowerCase().replace(/^_/, '');
      }
    }
    return 'general';
  }

  private isTradingFunction(name: string, content: string): boolean {
    const tradingFunctionPatterns = [
      /calculate.*price/i,
      /execute.*trade/i,
      /place.*order/i,
      /cancel.*order/i,
      /update.*position/i,
      /calculate.*risk/i,
      /validate.*order/i,
      /get.*market.*data/i,
      /process.*signal/i,
      /send.*notification/i
    ];

    return tradingFunctionPatterns.some(pattern =>
      pattern.test(name) || pattern.test(content)
    );
  }

  private generateId(filePath: string, name: string): string {
    const fileName = filePath.split('/').pop()?.replace(/\.[^/.]+$/, '') || 'unknown';
    return `trading:${fileName}:${name}`;
  }

  private findLineNumber(content: string, searchText: string): number {
    const lines = content.split('\n');
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes(searchText.split('\n')[0])) {
        return i + 1;
      }
    }
    return 1;
  }

  private extractMethods(classContent: string): string[] {
    const methodMatches = classContent.match(/(?:async\s+)?(\w+)\s*\([^)]*\)\s*{/g) || [];
    return methodMatches.map(match => {
      const methodName = match.match(/(\w+)\s*\(/)?.[1];
      return methodName || 'unknown';
    });
  }

  private extractDependencies(content: string): string[] {
    const importMatches = content.match(/import.*from\s+['"]([^'"]+)['"]/g) || [];
    return importMatches.map(match => {
      const dep = match.match(/from\s+['"]([^'"]+)['"]/)?.[1];
      return dep || 'unknown';
    });
  }

  private extractConfiguration(content: string): Record<string, any> {
    const config: Record<string, any> = {};

    // Extract configuration-like patterns
    const configMatches = content.match(/(\w+):\s*([^,}\n]+)/g) || [];
    configMatches.forEach(match => {
      const [key, value] = match.split(':').map(s => s.trim());
      if (key && value) {
        config[key] = value;
      }
    });

    return config;
  }

  private identifyPatterns(name: string, content: string): TradingPattern[] {
    const patterns: TradingPattern[] = [];

    // Identify specific trading patterns
    if (/moving.*average/i.test(name) || /moving.*average/i.test(content)) {
      patterns.push({
        name: 'Moving Average',
        type: 'indicator',
        confidence: 0.9,
        elements: [name],
        description: 'Moving average based analysis'
      });
    }

    if (/rsi/i.test(name) || /relative.*strength/i.test(content)) {
      patterns.push({
        name: 'RSI',
        type: 'indicator',
        confidence: 0.9,
        elements: [name],
        description: 'Relative Strength Index analysis'
      });
    }

    if (/stop.*loss/i.test(name) || /stop.*loss/i.test(content)) {
      patterns.push({
        name: 'Stop Loss',
        type: 'risk_management',
        confidence: 0.95,
        elements: [name],
        description: 'Stop loss risk management'
      });
    }

    return patterns;
  }

  private calculateTradingComplexity(content: string): number {
    let complexity = 1;

    // Add complexity for decision points
    const decisionPatterns = [
      /if.*price/gi,
      /if.*volume/gi,
      /if.*signal/gi,
      /switch.*strategy/gi,
      /for.*position/gi,
      /while.*trading/gi
    ];

    decisionPatterns.forEach(pattern => {
      const matches = content.match(pattern) || [];
      complexity += matches.length;
    });

    // Add complexity for mathematical operations
    const mathOperations = content.match(/[+\-*\/]/g) || [];
    complexity += mathOperations.length * 0.1;

    // Add complexity for API calls
    const apiCalls = content.match(/fetch|axios|http/gi) || [];
    complexity += apiCalls.length * 0.5;

    return Math.round(complexity * 10) / 10;
  }

  private assessRiskLevel(name: string, content: string): string {
    let riskScore = 0;

    // High risk patterns
    if (/margin|leverage|derivative/i.test(name) || /margin|leverage|derivative/i.test(content)) {
      riskScore += 3;
    }

    // Medium risk patterns
    if (/high.*frequency|scalping/i.test(name) || /high.*frequency|scalping/i.test(content)) {
      riskScore += 2;
    }

    // Low risk patterns
    if (/diversif|hedge|risk.*management/i.test(name) || /diversif|hedge|risk.*management/i.test(content)) {
      riskScore -= 1;
    }

    if (riskScore >= 3) return 'high';
    if (riskScore >= 1) return 'medium';
    return 'low';
  }

  private extractFunctionParameters(functionContent: string): string[] {
    const paramMatch = functionContent.match(/function\s+\w+\s*\(([^)]*)\)/);
    if (!paramMatch || !paramMatch[1]) return [];

    return paramMatch[1]
      .split(',')
      .map(param => param.trim())
      .filter(param => param.length > 0);
  }

  private extractReturnType(functionContent: string): string | null {
    const returnMatch = functionContent.match(/:\s*(\w+)\s*{/);
    return returnMatch ? returnMatch[1] : null;
  }

  private extractHTTPMethod(content: string, endpoint: string): string {
    const methodPattern = new RegExp(`(get|post|put|delete|patch).*${endpoint.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`, 'i');
    const match = content.match(methodPattern);
    return match ? match[1].toUpperCase() : 'GET';
  }
}