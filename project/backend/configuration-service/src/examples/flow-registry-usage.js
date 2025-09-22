/**
 * FlowRegistry Usage Examples
 *
 * Comprehensive examples showing how to use the FlowRegistry service
 * for LangGraph workflows, AI Brain validation, and Chain mappings.
 */

const FlowRegistryClient = require('../client/FlowRegistryClient');
const LangGraphIntegration = require('../client/integrations/LangGraphIntegration');

// Example configurations
const examples = {
  // Example 1: LangGraph Workflow Registration
  async langGraphWorkflowExample() {
    console.log('\n=== LangGraph Workflow Example ===');

    const client = new FlowRegistryClient({
      baseURL: 'http://localhost:8012',
      token: 'your-jwt-token' // Optional
    });

    // Define a LangGraph workflow
    const workflowDefinition = {
      name: 'ai_trading_analysis',
      description: 'AI-powered trading analysis workflow',
      version: '1.0.0',
      nodes: [
        {
          id: 'data_ingestion',
          name: 'Data Ingestion',
          type: 'data_source',
          config: {
            sources: ['market_data', 'news_feeds', 'social_sentiment'],
            refresh_interval: 60
          },
          position: { x: 100, y: 100 }
        },
        {
          id: 'technical_analysis',
          name: 'Technical Analysis',
          type: 'analyzer',
          config: {
            indicators: ['RSI', 'MACD', 'Bollinger_Bands'],
            timeframes: ['1h', '4h', '1d']
          },
          position: { x: 300, y: 100 }
        },
        {
          id: 'sentiment_analysis',
          name: 'Sentiment Analysis',
          type: 'nlp_processor',
          config: {
            models: ['bert_financial', 'finbert'],
            confidence_threshold: 0.8
          },
          position: { x: 300, y: 300 }
        },
        {
          id: 'decision_engine',
          name: 'Decision Engine',
          type: 'ml_model',
          config: {
            model_type: 'ensemble',
            risk_tolerance: 'medium',
            position_sizing: 'kelly_criterion'
          },
          position: { x: 500, y: 200 }
        }
      ],
      edges: [
        {
          id: 'data_to_technical',
          source: 'data_ingestion',
          target: 'technical_analysis',
          condition: 'data_available'
        },
        {
          id: 'data_to_sentiment',
          source: 'data_ingestion',
          target: 'sentiment_analysis',
          condition: 'news_available'
        },
        {
          id: 'technical_to_decision',
          source: 'technical_analysis',
          target: 'decision_engine'
        },
        {
          id: 'sentiment_to_decision',
          source: 'sentiment_analysis',
          target: 'decision_engine'
        }
      ],
      parameters: {
        symbol: {
          type: 'string',
          required: true,
          description: 'Trading symbol to analyze'
        },
        timeframe: {
          type: 'string',
          required: false,
          default: '1h',
          description: 'Analysis timeframe'
        },
        risk_level: {
          type: 'number',
          required: false,
          default: 0.5,
          description: 'Risk tolerance level (0-1)'
        }
      },
      required_credentials: [
        {
          key: 'market_data_api_key',
          type: 'api_key',
          required: true,
          scope: 'market_data'
        },
        {
          key: 'news_api_token',
          type: 'token',
          required: true,
          scope: 'news_feeds'
        }
      ],
      createdBy: 'ai_trading_team'
    };

    try {
      // Register the workflow
      const result = await client.registerLangGraphWorkflow(workflowDefinition);
      console.log('✅ Workflow registered:', result.data.id);

      // Execute the workflow
      const execution = await client.executeFlow(result.data.id, {
        parameters: {
          symbol: 'BTCUSD',
          timeframe: '4h',
          risk_level: 0.7
        },
        triggeredBy: 'example_script'
      });

      console.log('✅ Execution started:', execution.executionId);

      // Simulate execution completion
      setTimeout(async () => {
        await client.updateExecutionStatus(
          execution.executionId,
          'completed',
          {
            recommendation: 'BUY',
            confidence: 0.85,
            position_size: 0.1,
            stop_loss: 42000,
            take_profit: 48000
          }
        );
        console.log('✅ Execution completed with results');
      }, 2000);

      return result.data.id;
    } catch (error) {
      console.error('❌ LangGraph example failed:', error.message);
      throw error;
    }
  },

  // Example 2: AI Brain Validation Flow
  async aiBrainValidationExample() {
    console.log('\n=== AI Brain Validation Example ===');

    const client = new FlowRegistryClient({
      baseURL: 'http://localhost:8012'
    });

    // Define AI Brain validation flow
    const validationDefinition = {
      name: 'trading_model_validation',
      description: 'Validate AI trading model architecture and performance',
      version: '1.0.0',
      validation_rules: [
        {
          id: 'model_accuracy_check',
          name: 'Model Accuracy Validation',
          type: 'performance_validator',
          config: {
            min_accuracy: 0.75,
            validation_dataset: 'test_2024_q1',
            metrics: ['accuracy', 'precision', 'recall', 'f1_score']
          }
        },
        {
          id: 'bias_detection',
          name: 'Bias Detection',
          type: 'fairness_validator',
          config: {
            protected_attributes: ['symbol_type', 'market_cap'],
            bias_threshold: 0.1,
            statistical_tests: ['demographic_parity', 'equalized_odds']
          }
        },
        {
          id: 'robustness_test',
          name: 'Robustness Testing',
          type: 'adversarial_validator',
          config: {
            attack_methods: ['fgsm', 'pgd', 'c&w'],
            epsilon_values: [0.01, 0.05, 0.1],
            success_threshold: 0.9
          }
        }
      ],
      parameters: [
        {
          name: 'model_id',
          type: 'string',
          required: true,
          description: 'ID of the model to validate'
        },
        {
          name: 'validation_mode',
          type: 'string',
          required: false,
          default: 'comprehensive',
          description: 'Validation mode: quick, standard, comprehensive'
        }
      ],
      createdBy: 'ai_validation_team'
    };

    try {
      // Register validation flow
      const result = await client.registerAIBrainValidationFlow(validationDefinition);
      console.log('✅ Validation flow registered:', result.data.id);

      // Execute validation
      const execution = await client.executeFlow(result.data.id, {
        parameters: {
          model_id: 'trading_model_v2.3',
          validation_mode: 'comprehensive'
        },
        triggeredBy: 'model_deployment_pipeline'
      });

      console.log('✅ Validation started:', execution.executionId);

      // Validate the flow definition
      const validation = await client.validateFlow(result.data.id);
      console.log('✅ Flow validation:', validation.isValid ? 'PASSED' : 'FAILED');
      if (!validation.isValid) {
        console.log('⚠️ Validation errors:', validation.errors);
      }

      return result.data.id;
    } catch (error) {
      console.error('❌ AI Brain validation example failed:', error.message);
      throw error;
    }
  },

  // Example 3: Chain Mapping Flow
  async chainMappingExample() {
    console.log('\n=== Chain Mapping Example ===');

    const client = new FlowRegistryClient({
      baseURL: 'http://localhost:8012'
    });

    // Define chain mapping flow
    const chainDefinition = {
      id: 'defi_arbitrage_chain',
      name: 'DeFi Arbitrage Chain',
      description: 'Multi-chain arbitrage opportunity detection and execution',
      version: '1.0.0',
      nodes: [
        {
          id: 'ethereum_scanner',
          name: 'Ethereum Price Scanner',
          type: 'price_oracle',
          config: {
            chain: 'ethereum',
            dexes: ['uniswap_v3', 'sushiswap', 'curve'],
            tokens: ['USDC', 'USDT', 'DAI', 'WETH']
          }
        },
        {
          id: 'bsc_scanner',
          name: 'BSC Price Scanner',
          type: 'price_oracle',
          config: {
            chain: 'binance_smart_chain',
            dexes: ['pancakeswap', 'biswap', 'apeswap'],
            tokens: ['BUSD', 'USDT', 'BNB', 'WETH']
          }
        },
        {
          id: 'arbitrage_detector',
          name: 'Arbitrage Opportunity Detector',
          type: 'opportunity_analyzer',
          config: {
            min_profit_threshold: 0.005, // 0.5%
            max_slippage: 0.01, // 1%
            gas_cost_consideration: true
          }
        },
        {
          id: 'execution_engine',
          name: 'Trade Execution Engine',
          type: 'transaction_executor',
          config: {
            execution_mode: 'atomic',
            max_gas_price: 100, // gwei
            slippage_protection: true
          }
        }
      ],
      edges: [
        {
          id: 'eth_to_detector',
          source: 'ethereum_scanner',
          target: 'arbitrage_detector'
        },
        {
          id: 'bsc_to_detector',
          source: 'bsc_scanner',
          target: 'arbitrage_detector'
        },
        {
          id: 'detector_to_execution',
          source: 'arbitrage_detector',
          target: 'execution_engine',
          condition: 'opportunity_found'
        }
      ],
      dependencies: [
        {
          flowId: 'ethereum_bridge_monitor',
          type: 'prerequisite',
          condition: 'bridge_healthy',
          timeout: 30000
        },
        {
          flowId: 'gas_price_monitor',
          type: 'parallel',
          condition: 'gas_acceptable'
        }
      ],
      parameters: [
        {
          name: 'token_pair',
          type: 'string',
          required: true,
          description: 'Token pair to monitor (e.g., USDC/USDT)'
        },
        {
          name: 'amount',
          type: 'number',
          required: true,
          description: 'Amount to arbitrage in USD'
        },
        {
          name: 'auto_execute',
          type: 'boolean',
          required: false,
          default: false,
          description: 'Automatically execute profitable opportunities'
        }
      ],
      credentials: [
        {
          key: 'ethereum_private_key',
          type: 'secret',
          required: true,
          scope: 'ethereum_execution'
        },
        {
          key: 'bsc_private_key',
          type: 'secret',
          required: true,
          scope: 'bsc_execution'
        },
        {
          key: 'infura_api_key',
          type: 'api_key',
          required: true,
          scope: 'ethereum_rpc'
        }
      ],
      createdBy: 'defi_arbitrage_team'
    };

    try {
      // Register chain mapping flow
      const result = await client.registerChainMappingFlow(chainDefinition);
      console.log('✅ Chain mapping registered:', result.data.id);

      // Add dependencies
      await client.addFlowDependency(result.data.id, {
        dependsOnFlowId: 'risk_management_flow',
        dependencyType: 'prerequisite',
        condition: 'risk_approved'
      });

      console.log('✅ Dependencies added');

      // Get dependency graph
      const depGraph = await client.getDependencyGraph(result.data.id, true);
      console.log('✅ Dependency graph:', {
        dependencies: depGraph.dependencies.length,
        dependents: depGraph.dependents.length
      });

      return result.data.id;
    } catch (error) {
      console.error('❌ Chain mapping example failed:', error.message);
      throw error;
    }
  },

  // Example 4: LangGraph Integration Usage
  async langGraphIntegrationExample() {
    console.log('\n=== LangGraph Integration Example ===');

    const integration = new LangGraphIntegration({
      baseURL: 'http://localhost:8012'
    });

    // Simple workflow definition
    const simpleWorkflow = {
      name: 'sentiment_based_trading',
      description: 'Trading decisions based on market sentiment',
      nodes: [
        {
          id: 'sentiment_collector',
          name: 'Sentiment Collector',
          type: 'data_collector',
          config: {
            sources: ['twitter', 'reddit', 'news'],
            keywords: ['bitcoin', 'ethereum', 'crypto']
          }
        },
        {
          id: 'sentiment_analyzer',
          name: 'Sentiment Analyzer',
          type: 'nlp_model',
          config: {
            model: 'finbert',
            batch_size: 32
          }
        },
        {
          id: 'trading_decision',
          name: 'Trading Decision',
          type: 'decision_model',
          config: {
            strategy: 'sentiment_momentum',
            risk_threshold: 0.3
          }
        }
      ],
      edges: [
        { source: 'sentiment_collector', target: 'sentiment_analyzer' },
        { source: 'sentiment_analyzer', target: 'trading_decision' }
      ],
      parameters: {
        symbol: { type: 'string', required: true },
        sentiment_weight: { type: 'number', default: 0.7 }
      },
      createdBy: 'sentiment_trading_team'
    };

    try {
      // Register workflow using integration
      const result = await integration.registerWorkflow(simpleWorkflow);
      console.log('✅ Workflow registered via integration:', result.data.id);

      // Execute with callback handling
      const execution = await integration.executeWorkflow(
        'sentiment_based_trading',
        { symbol: 'BTCUSD', sentiment_weight: 0.8 },
        {
          triggeredBy: 'integration_example',
          onComplete: (result) => {
            console.log('🎉 Workflow completed:', result.result);
          },
          onError: (error) => {
            console.error('💥 Workflow failed:', error.error);
          }
        }
      );

      console.log('✅ Execution started with callbacks:', execution.executionId);

      // Simulate completion
      setTimeout(() => {
        integration.updateExecutionStatus(
          execution.executionId,
          'completed',
          {
            action: 'BUY',
            sentiment_score: 0.75,
            confidence: 0.82
          }
        );
      }, 3000);

      // Get workflow statistics
      const stats = await integration.getWorkflowStatistics('sentiment_based_trading');
      console.log('📊 Workflow statistics:', stats);

      return result.data.id;
    } catch (error) {
      console.error('❌ Integration example failed:', error.message);
      throw error;
    } finally {
      integration.close();
    }
  },

  // Example 5: Monitoring and Statistics
  async monitoringExample() {
    console.log('\n=== Monitoring and Statistics Example ===');

    const client = new FlowRegistryClient({
      baseURL: 'http://localhost:8012'
    });

    try {
      // Get global statistics
      const globalStats = await client.getFlowStatistics();
      console.log('📊 Global statistics:', {
        totalFlows: globalStats.flows.total_flows,
        activeFlows: globalStats.flows.active_flows,
        totalExecutions: globalStats.executions.total_executions,
        successRate: globalStats.overallSuccessRate
      });

      // List all flows with filtering
      const langGraphFlows = await client.listFlows({
        type: 'langgraph_workflow',
        status: 'active',
        limit: 10
      });

      console.log('🔍 LangGraph workflows:', langGraphFlows.data.flows.length);

      // Health check
      const health = await client.healthCheck();
      console.log('🏥 Service health:', health.status);

      // Get flow types
      const types = await client.getFlowTypes();
      console.log('📋 Available flow types:', types.types);

      return true;
    } catch (error) {
      console.error('❌ Monitoring example failed:', error.message);
      throw error;
    }
  }
};

// Run all examples
async function runAllExamples() {
  console.log('🚀 Starting FlowRegistry Examples\n');

  try {
    await examples.langGraphWorkflowExample();
    await examples.aiBrainValidationExample();
    await examples.chainMappingExample();
    await examples.langGraphIntegrationExample();
    await examples.monitoringExample();

    console.log('\n✅ All examples completed successfully!');
  } catch (error) {
    console.error('\n❌ Examples failed:', error.message);
    process.exit(1);
  }
}

// Export for use in other files
module.exports = {
  examples,
  runAllExamples
};

// Run examples if called directly
if (require.main === module) {
  runAllExamples();
}