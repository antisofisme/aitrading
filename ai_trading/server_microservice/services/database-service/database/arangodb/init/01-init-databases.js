// ArangoDB Initialization Script for Neliti Database Service
// Uses existing schemas from src/schemas/arangodb/trading_strategies_schemas.py

db._useDatabase('_system');

// Create main databases
try {
    db._createDatabase('neliti_graph');
    print('Database neliti_graph created successfully');
} catch (e) {
    if (e.errorNum === 1207) {
        print('Database neliti_graph already exists');
    } else {
        print('Error creating database: ' + e.message);
    }
}

try {
    db._createDatabase('trading_system');
    print('Database trading_system created successfully');
} catch (e) {
    if (e.errorNum === 1207) {
        print('Database trading_system already exists');
    } else {
        print('Error creating database: ' + e.message);
    }
}

// Switch to main database
db._useDatabase('neliti_graph');

// Create document collections (from existing schemas)
const collections = [
    'trading_strategies',
    'strategy_parameters', 
    'strategy_performance',
    'strategy_signals',
    'user_workflows',
    'workflow_executions',
    'market_analysis'
];

collections.forEach(function(collectionName) {
    try {
        db._create(collectionName);
        print('Collection ' + collectionName + ' created successfully');
    } catch (e) {
        if (e.errorNum === 1207) {
            print('Collection ' + collectionName + ' already exists');
        } else {
            print('Error creating collection ' + collectionName + ': ' + e.message);
        }
    }
});

// Create edge collections for relationships
const edgeCollections = [
    'strategy_relationships',
    'strategy_dependencies', 
    'workflow_dependencies',
    'user_strategy_assignments'
];

edgeCollections.forEach(function(collectionName) {
    try {
        db._createEdgeCollection(collectionName);
        print('Edge collection ' + collectionName + ' created successfully');
    } catch (e) {
        if (e.errorNum === 1207) {
            print('Edge collection ' + collectionName + ' already exists');
        } else {
            print('Error creating edge collection ' + collectionName + ': ' + e.message);
        }
    }
});

// Create indexes for performance
try {
    // Trading strategies indexes
    db.trading_strategies.ensureIndex({ type: "persistent", fields: ["strategy_name"] });
    db.trading_strategies.ensureIndex({ type: "persistent", fields: ["strategy_type"] });
    db.trading_strategies.ensureIndex({ type: "persistent", fields: ["created_by"] });
    db.trading_strategies.ensureIndex({ type: "persistent", fields: ["status"] });
    
    // Strategy performance indexes
    db.strategy_performance.ensureIndex({ type: "persistent", fields: ["strategy_id"] });
    db.strategy_performance.ensureIndex({ type: "persistent", fields: ["performance_date"] });
    db.strategy_performance.ensureIndex({ type: "persistent", fields: ["symbol"] });
    
    // Strategy signals indexes
    db.strategy_signals.ensureIndex({ type: "persistent", fields: ["strategy_id"] });
    db.strategy_signals.ensureIndex({ type: "persistent", fields: ["signal_timestamp"] });
    db.strategy_signals.ensureIndex({ type: "persistent", fields: ["symbol"] });
    db.strategy_signals.ensureIndex({ type: "persistent", fields: ["signal_type"] });
    
    print('Indexes created successfully');
} catch (e) {
    print('Error creating indexes: ' + e.message);
}

// Create sample trading strategy document
try {
    const sampleStrategy = {
        "_key": "momentum_strategy_v1",
        "strategy_name": "Momentum Strategy",
        "strategy_type": "momentum",
        "version": "1.0.0",
        "description": "Basic momentum trading strategy using moving averages",
        "parameters": {
            "fast_ma_period": 10,
            "slow_ma_period": 20,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30
        },
        "symbols": ["EURUSD", "GBPUSD", "USDJPY"],
        "timeframes": ["15m", "1h", "4h"],
        "risk_management": {
            "max_risk_per_trade": 0.02,
            "max_daily_risk": 0.06,
            "stop_loss_pips": 50,
            "take_profit_pips": 100
        },
        "created_by": "admin",
        "status": "active",
        "created_at": new Date().toISOString(),
        "updated_at": new Date().toISOString()
    };
    
    db.trading_strategies.save(sampleStrategy);
    print('Sample trading strategy created successfully');
} catch (e) {
    print('Error creating sample strategy: ' + e.message);
}

// Create sample strategy parameters
try {
    const sampleParameters = {
        "_key": "momentum_params_v1",
        "strategy_id": "trading_strategies/momentum_strategy_v1",
        "parameter_set": "default",
        "parameters": {
            "entry_conditions": {
                "ma_crossover": true,
                "rsi_confirmation": true,
                "volume_confirmation": false
            },
            "exit_conditions": {
                "opposite_signal": true,
                "stop_loss": true,
                "take_profit": true,
                "time_based": false
            },
            "filters": {
                "trend_filter": true,
                "volatility_filter": false,
                "news_filter": false
            }
        },
        "optimization_results": {
            "backtest_period": "2023-01-01_2024-01-01",
            "total_trades": 156,
            "win_rate": 0.65,
            "profit_factor": 1.8,
            "max_drawdown": 0.12,
            "sharpe_ratio": 1.4
        },
        "created_at": new Date().toISOString()
    };
    
    db.strategy_parameters.save(sampleParameters);
    print('Sample strategy parameters created successfully');
} catch (e) {
    print('Error creating sample parameters: ' + e.message);
}

// Create views for common queries
try {
    // Active strategies view
    db._createView("active_strategies_view", "trading_strategies", {
        "links": {}
    });
    
    // Strategy performance summary view  
    db._createView("strategy_performance_summary", "strategy_performance", {
        "links": {
            "trading_strategies": {
                "analyzers": [{
                    "name": "identity",
                    "type": "identity"
                }]
            }
        }
    });
    
    print('Views created successfully');
} catch (e) {
    print('Error creating views: ' + e.message);
}

// Create graph for strategy relationships
try {
    var graph = require("@arangodb/general-graph");
    
    graph._create("strategy_network", [
        {
            "collection": "strategy_relationships",
            "from": ["trading_strategies"],
            "to": ["trading_strategies"]
        },
        {
            "collection": "strategy_dependencies", 
            "from": ["trading_strategies"],
            "to": ["trading_strategies"]
        }
    ]);
    
    print('Strategy network graph created successfully');
} catch (e) {
    if (e.errorNum === 1925) {
        print('Graph strategy_network already exists');
    } else {
        print('Error creating graph: ' + e.message);
    }
}

print('ArangoDB initialization completed successfully - Graph database ready for trading strategies');