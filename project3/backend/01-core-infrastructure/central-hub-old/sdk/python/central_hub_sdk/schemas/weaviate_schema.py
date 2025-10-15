"""
Weaviate Schema Definitions
Vector database for ML embeddings and semantic search
"""
from typing import Dict, List, Any


def get_weaviate_schemas() -> List[Dict[str, Any]]:
    """Get all Weaviate class schemas"""
    return [
        TRADING_SIGNALS_CLASS,
        MARKET_ANALYSIS_CLASS,
        ECONOMIC_NEWS_CLASS,
    ]


# ============================================================================
# TRADING SIGNALS CLASS
# ============================================================================

TRADING_SIGNALS_CLASS = {
    "class": "TradingSignals",
    "description": "Trading signals with ML embeddings for semantic search",
    "vectorizer": "text2vec-transformers",
    "moduleConfig": {
        "text2vec-transformers": {
            "vectorizeClassName": False,
            "poolingStrategy": "masked_mean"
        }
    },
    "properties": [
        {
            "name": "symbol",
            "dataType": ["string"],
            "description": "Trading pair symbol",
            "indexFilterable": True,
            "indexSearchable": False
        },
        {
            "name": "signalType",
            "dataType": ["string"],
            "description": "Signal type: buy, sell, hold",
            "indexFilterable": True,
            "indexSearchable": False
        },
        {
            "name": "strength",
            "dataType": ["number"],
            "description": "Signal strength (0-100)",
            "indexFilterable": True,
            "indexSearchable": False
        },
        {
            "name": "strategyName",
            "dataType": ["string"],
            "description": "Strategy that generated this signal",
            "indexFilterable": True,
            "indexSearchable": True
        },
        {
            "name": "description",
            "dataType": ["text"],
            "description": "Textual description of the signal",
            "indexFilterable": False,
            "indexSearchable": True,
            "moduleConfig": {
                "text2vec-transformers": {
                    "vectorizePropertyName": False
                }
            }
        },
        {
            "name": "timestamp",
            "dataType": ["number"],
            "description": "Unix timestamp milliseconds",
            "indexFilterable": True,
            "indexSearchable": False
        },
        {
            "name": "price",
            "dataType": ["number"],
            "description": "Price at signal generation",
            "indexFilterable": True,
            "indexSearchable": False
        },
    ]
}


# ============================================================================
# MARKET ANALYSIS CLASS
# ============================================================================

MARKET_ANALYSIS_CLASS = {
    "class": "MarketAnalysis",
    "description": "Market analysis reports with embeddings",
    "vectorizer": "text2vec-transformers",
    "moduleConfig": {
        "text2vec-transformers": {
            "vectorizeClassName": False
        }
    },
    "properties": [
        {
            "name": "symbol",
            "dataType": ["string"],
            "description": "Trading pair symbol",
            "indexFilterable": True
        },
        {
            "name": "timeframe",
            "dataType": ["string"],
            "description": "Analysis timeframe",
            "indexFilterable": True
        },
        {
            "name": "analysisType",
            "dataType": ["string"],
            "description": "Type: technical, fundamental, sentiment",
            "indexFilterable": True
        },
        {
            "name": "content",
            "dataType": ["text"],
            "description": "Full analysis content",
            "indexSearchable": True,
            "moduleConfig": {
                "text2vec-transformers": {
                    "vectorizePropertyName": False
                }
            }
        },
        {
            "name": "sentiment",
            "dataType": ["string"],
            "description": "Overall sentiment: bullish, bearish, neutral",
            "indexFilterable": True
        },
        {
            "name": "confidence",
            "dataType": ["number"],
            "description": "Analysis confidence (0-1)",
            "indexFilterable": True
        },
        {
            "name": "timestamp",
            "dataType": ["number"],
            "description": "Unix timestamp milliseconds",
            "indexFilterable": True
        },
    ]
}


# ============================================================================
# ECONOMIC NEWS CLASS
# ============================================================================

ECONOMIC_NEWS_CLASS = {
    "class": "EconomicNews",
    "description": "Economic news and events with embeddings",
    "vectorizer": "text2vec-transformers",
    "moduleConfig": {
        "text2vec-transformers": {
            "vectorizeClassName": False
        }
    },
    "properties": [
        {
            "name": "title",
            "dataType": ["text"],
            "description": "News title",
            "indexSearchable": True
        },
        {
            "name": "content",
            "dataType": ["text"],
            "description": "Full news content",
            "indexSearchable": True,
            "moduleConfig": {
                "text2vec-transformers": {
                    "vectorizePropertyName": False
                }
            }
        },
        {
            "name": "source",
            "dataType": ["string"],
            "description": "News source",
            "indexFilterable": True
        },
        {
            "name": "category",
            "dataType": ["string"],
            "description": "News category",
            "indexFilterable": True
        },
        {
            "name": "sentiment",
            "dataType": ["string"],
            "description": "Sentiment: positive, negative, neutral",
            "indexFilterable": True
        },
        {
            "name": "impact",
            "dataType": ["string"],
            "description": "Expected impact: high, medium, low",
            "indexFilterable": True
        },
        {
            "name": "affectedSymbols",
            "dataType": ["string[]"],
            "description": "List of affected trading pairs",
            "indexFilterable": True
        },
        {
            "name": "publishedAt",
            "dataType": ["number"],
            "description": "Publication timestamp",
            "indexFilterable": True
        },
    ]
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_class_definition(class_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Weaviate class definition JSON

    Args:
        class_schema: Class schema dict

    Returns:
        JSON for class creation
    """
    return {
        "class": class_schema["class"],
        "description": class_schema.get("description", ""),
        "vectorizer": class_schema.get("vectorizer", "none"),
        "moduleConfig": class_schema.get("moduleConfig", {}),
        "properties": class_schema["properties"]
    }


def get_all_weaviate_json() -> List[Dict[str, Any]]:
    """
    Generate complete Weaviate schema as JSON

    Returns:
        List of class definitions
    """
    schemas = get_weaviate_schemas()
    return [generate_class_definition(schema) for schema in schemas]


def get_class_by_name(class_name: str) -> Dict[str, Any]:
    """
    Get specific class schema by name

    Args:
        class_name: Name of the class

    Returns:
        Class schema dict
    """
    schemas = get_weaviate_schemas()
    for schema in schemas:
        if schema["class"] == class_name:
            return schema
    return {}
