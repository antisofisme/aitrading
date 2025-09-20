"""
Query Builder - Database-agnostic query construction
Builds optimized queries for all 6 database types with proper escaping and validation
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import re

# Infrastructure integration
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))
from shared.infrastructure.core.logger_core import get_logger
from shared.infrastructure.core.error_core import get_error_handler


class QueryBuilder:
    """Universal query builder for all database types"""
    
    def __init__(self):
        self.logger = get_logger("database-service", "query-builder")
        self.error_handler = get_error_handler("database-service")
        
        # Query templates for different database types
        self._query_templates = self._load_query_templates()
    
    # ===== CLICKHOUSE QUERY BUILDING =====
    
    def build_recent_ticks_query(self, symbol: str, broker: str = "FBS-Demo", limit: int = 100) -> str:
        """Build HIGH-PERFORMANCE optimized query for recent ticks with indexing hints"""
        try:
            # Sanitize inputs with optimized validation
            symbol = self._sanitize_string(symbol)
            broker = self._sanitize_string(broker)
            limit = max(1, min(limit, 10000))  # Limit between 1 and 10,000
            
            # High-performance query with indexing hints and column optimization
            query = """
            SELECT 
                timestamp,
                symbol,
                bid,
                ask,
                last,
                volume,
                spread,
                primary_session,
                broker,
                account_type
            FROM ticks 
            WHERE symbol = %(symbol)s 
                AND broker = %(broker)s
                AND timestamp > NOW() - INTERVAL 1 DAY  -- Index hint: limit time range
            ORDER BY timestamp DESC 
            LIMIT %(limit)s
            SETTINGS optimize_read_in_order = 1  -- ClickHouse optimization
            """
            
            self.logger.debug(f"Built OPTIMIZED recent ticks query - symbol: {symbol}, broker: {broker}, limit: {limit}")
            
            return query.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to build recent ticks query: {e}")
            raise
    
    def build_bulk_tick_insert_query(self, tick_data: List[Dict[str, Any]]) -> str:
        """Build optimized bulk insert query for high-frequency tick data using VALUES format"""
        try:
            if not tick_data:
                raise ValueError("No tick data provided for bulk insert")
            
            # Build VALUES clause with actual data
            values_list = []
            for record in tick_data:
                # Extract and escape values in the correct column order
                timestamp = self._escape_sql_string(record.get('timestamp', 'now64()'))
                symbol = self._escape_sql_string(record.get('symbol', ''))
                bid = float(record.get('bid', 0.0))
                ask = float(record.get('ask', 0.0))
                last_price = float(record.get('last', 0.0))
                volume = float(record.get('volume', 0.0))
                spread = float(record.get('spread', ask - bid))
                primary_session = self._escape_sql_string(record.get('primary_session', 'Unknown'))
                
                # Handle active_sessions array
                active_sessions = record.get('active_sessions', [])
                if isinstance(active_sessions, list):
                    active_sessions_str = "['" + "','".join([self._escape_sql_string(s) for s in active_sessions]) + "']"
                else:
                    active_sessions_str = "[]"
                
                session_overlap = str(record.get('session_overlap', False)).lower()
                broker = self._escape_sql_string(record.get('broker', 'FBS-Demo'))
                account_type = self._escape_sql_string(record.get('account_type', 'demo'))
                
                # Build VALUES tuple
                values_tuple = f"('{timestamp}', '{symbol}', {bid}, {ask}, {last_price}, {volume}, {spread}, '{primary_session}', {active_sessions_str}, {session_overlap}, '{broker}', '{account_type}')"
                values_list.append(values_tuple)
            
            # Limit batch size for performance
            if len(values_list) > 10000:
                values_list = values_list[:10000]
                self.logger.warning(f"Limiting bulk insert to 10000 records (requested: {len(tick_data)})")
            
            values_clause = ',\\n    '.join(values_list)
            
            query = f"""INSERT INTO trading_data.ticks 
                (timestamp, symbol, bid, ask, last, volume, spread, primary_session, active_sessions, session_overlap, broker, account_type) 
                VALUES 
    {values_clause}
            SETTINGS async_insert = 1, wait_for_async_insert = 0"""
            
            self.logger.debug(f"Built VALUES bulk INSERT query for {len(values_list)} ticks")
            
            return query.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to build bulk insert VALUES query: {e}")
            raise
    
    def build_tick_aggregation_query(self, 
                                   symbol: str, 
                                   timeframe: str = "1m",
                                   start_time: datetime = None,
                                   end_time: datetime = None,
                                   broker: str = "FBS-Demo") -> str:
        """Build query for tick data aggregation"""
        try:
            symbol = self._sanitize_string(symbol)
            broker = self._sanitize_string(broker)
            
            # Default time range (last 24 hours)
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            # Convert timeframe to ClickHouse interval
            interval = self._convert_timeframe_to_interval(timeframe)
            
            query = f"""
            SELECT 
                toStartOfInterval(timestamp, INTERVAL {interval}) as period,
                symbol,
                broker,
                count() as tick_count,
                first_value(bid) as open_bid,
                max(bid) as high_bid,
                min(bid) as low_bid,
                last_value(bid) as close_bid,
                first_value(ask) as open_ask,
                max(ask) as high_ask,
                min(ask) as low_ask,
                last_value(ask) as close_ask,
                avg(bid) as avg_bid,
                avg(ask) as avg_ask,
                sum(volume) as total_volume
            FROM ticks
            WHERE symbol = '{symbol}'
                AND broker = '{broker}'
                AND timestamp >= '{start_time.isoformat()}'
                AND timestamp <= '{end_time.isoformat()}'
            GROUP BY period, symbol, broker
            ORDER BY period DESC
            """
            
            self.logger.debug(f"Built tick aggregation query - symbol: {symbol}, timeframe: {timeframe}")
            
            return query.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to build tick aggregation query: {e}")
            raise
    
    def build_symbol_statistics_query(self, symbol: str, hours: int = 24, broker: str = "FBS-Demo") -> str:
        """Build query for symbol trading statistics"""
        try:
            symbol = self._sanitize_string(symbol)
            broker = self._sanitize_string(broker)
            hours = max(1, min(hours, 168))  # Limit between 1 hour and 1 week
            
            query = f"""
            SELECT 
                symbol,
                broker,
                count() as total_ticks,
                min(timestamp) as first_tick,
                max(timestamp) as last_tick,
                min(bid) as min_bid,
                max(bid) as max_bid,
                min(ask) as min_ask,
                max(ask) as max_ask,
                avg(bid) as avg_bid,
                avg(ask) as avg_ask,
                avg(spread) as avg_spread,
                min(spread) as min_spread,
                max(spread) as max_spread,
                sum(volume) as total_volume,
                count(DISTINCT primary_session) as sessions_count
            FROM ticks
            WHERE symbol = '{symbol}'
                AND broker = '{broker}'
                AND timestamp >= now() - INTERVAL {hours} HOUR
            GROUP BY symbol, broker
            """
            
            self.logger.debug(f"Built symbol statistics query - symbol: {symbol}, hours: {hours}")
            
            return query.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to build symbol statistics query: {e}")
            raise
    
    # ===== POSTGRESQL QUERY BUILDING =====
    
    def build_user_authentication_query(self, username: str, email: str = None) -> str:
        """Build PostgreSQL query for user authentication"""
        try:
            username = self._sanitize_string(username)
            
            conditions = ["username = %(username)s"]
            if email:
                email = self._sanitize_string(email)
                conditions.append("email = %(email)s")
            
            query = f"""
            SELECT 
                user_id,
                username,
                email,
                is_active,
                created_at,
                last_login,
                role
            FROM users
            WHERE {' OR '.join(conditions)}
                AND is_active = true
            LIMIT 1
            """
            
            self.logger.debug(f"Built user authentication query - username: {username}")
            
            return query.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to build user authentication query: {e}")
            raise
    
    def build_user_sessions_query(self, user_id: int, active_only: bool = True) -> str:
        """Build query for user sessions"""
        try:
            user_id = int(user_id)
            
            conditions = ["user_id = %(user_id)s"]
            if active_only:
                conditions.append("expires_at > NOW()")
            
            query = f"""
            SELECT 
                session_id,
                user_id,
                session_token,
                created_at,
                expires_at,
                last_activity,
                ip_address,
                user_agent
            FROM user_sessions
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            """
            
            self.logger.debug(f"Built user sessions query - user_id: {user_id}, active_only: {active_only}")
            
            return query.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to build user sessions query: {e}")
            raise
    
    # ===== ARANGODB QUERY BUILDING =====
    
    def build_strategy_query(self, strategy_id: str = None, status: str = None) -> str:
        """Build AQL query for trading strategies"""
        try:
            filters = []
            
            if strategy_id:
                strategy_id = self._sanitize_string(strategy_id)
                filters.append(f"strategy._key == @strategy_id")
            
            if status:
                status = self._sanitize_string(status)
                filters.append(f"strategy.status == @status")
            
            filter_clause = ""
            if filters:
                filter_clause = f"FILTER {' AND '.join(filters)}"
            
            query = f"""
            FOR strategy IN trading_strategies
                {filter_clause}
                RETURN {{
                    id: strategy._key,
                    name: strategy.name,
                    description: strategy.description,
                    status: strategy.status,
                    created_at: strategy.created_at,
                    updated_at: strategy.updated_at,
                    parameters: strategy.parameters,
                    performance: strategy.performance
                }}
            """
            
            self.logger.debug(f"Built strategy query - strategy_id: {strategy_id}, status: {status}")
            
            return query.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to build strategy query: {e}")
            raise
    
    def build_strategy_relationships_query(self, strategy_id: str) -> str:
        """Build AQL query for strategy relationships"""
        try:
            strategy_id = self._sanitize_string(strategy_id)
            
            query = f"""
            FOR strategy IN trading_strategies
                FILTER strategy._key == '{strategy_id}'
                FOR relationship IN 1..2 OUTBOUND strategy strategy_relationships
                    RETURN {{
                        strategy_id: strategy._key,
                        related_strategy: relationship._key,
                        relationship_type: relationship.type,
                        strength: relationship.strength
                    }}
            """
            
            self.logger.debug(f"Built strategy relationships query - strategy_id: {strategy_id}")
            
            return query.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to build strategy relationships query: {e}")
            raise
    
    # ===== WEAVIATE QUERY BUILDING =====
    
    def build_vector_search_query(self, 
                                 search_text: str, 
                                 vector_class_name: str = "TradingDocument", 
                                 result_limit: int = 10,
                                 search_certainty: float = 0.7) -> Dict[str, Any]:
        """Build Weaviate GraphQL query for vector search"""
        try:
            search_text = self._sanitize_string(search_text)
            vector_class_name = self._sanitize_string(vector_class_name)
            result_limit = max(1, min(result_limit, 100))
            search_certainty = max(0.0, min(search_certainty, 1.0))
            
            # Weaviate GraphQL query structure
            query = {
                "query": f"""
                {{
                    Get {{
                        {vector_class_name}(
                            nearText: {{
                                concepts: ["{search_text}"]
                                certainty: {search_certainty}
                            }}
                            limit: {result_limit}
                        ) {{
                            content
                            title
                            category
                            timestamp
                            _additional {{
                                certainty
                                distance
                            }}
                        }}
                    }}
                }}
                """
            }
            
            self.logger.debug(f"Built vector search query - class: {vector_class_name}, limit: {result_limit}")
            
            return query
            
        except Exception as e:
            self.logger.error(f"Failed to build vector search query: {e}")
            raise
    
    def build_vector_similarity_query(self, 
                                     search_vector: List[float], 
                                     vector_class_name: str = "TradingDocument", 
                                     result_limit: int = 10) -> Dict[str, Any]:
        """Build Weaviate query for vector similarity search"""
        try:
            vector_class_name = self._sanitize_string(vector_class_name)
            result_limit = max(1, min(result_limit, 100))
            
            # Validate vector format
            if not isinstance(search_vector, list) or not all(isinstance(x, (int, float)) for x in search_vector):
                raise ValueError("Vector must be a list of numbers")
            
            query = {
                "query": f"""
                {{
                    Get {{
                        {vector_class_name}(
                            nearVector: {{
                                vector: {search_vector}
                            }}
                            limit: {result_limit}
                        ) {{
                            content
                            title
                            category
                            timestamp
                            _additional {{
                                certainty
                                distance
                                vector
                            }}
                        }}
                    }}
                }}
                """
            }
            
            self.logger.debug(f"Built vector similarity query - class: {vector_class_name}, vector_length: {len(search_vector)}")
            
            return query
            
        except Exception as e:
            self.logger.error(f"Failed to build vector similarity query: {e}")
            raise
    
    # ===== UTILITY METHODS =====
    
    # Compiled regex patterns for O(1) performance optimization
    _DANGEROUS_CHARS_PATTERN = re.compile(r"[;'\"\\`\-\-/\*\*/]")
    _SQL_INJECTION_PATTERN = re.compile(r"(union|select|insert|update|delete|drop|create|alter|exec|execute)", re.IGNORECASE)
    
    def _sanitize_string(self, value: str) -> str:
        """Sanitize string input to prevent SQL injection - PERFORMANCE OPTIMIZED"""
        if not isinstance(value, str):
            value = str(value)
        
        # Validate length first to prevent buffer overflow attacks
        if len(value) > 255:
            raise ValueError("Input string too long - potential security risk")
        
        # Use compiled regex patterns for O(1) performance
        value = self._DANGEROUS_CHARS_PATTERN.sub("", value)
        value = self._SQL_INJECTION_PATTERN.sub("", value)
        value = value.strip()
        
        return value
    
    def _escape_sql_string(self, value: str) -> str:
        """Escape SQL string values for VALUES format queries"""
        if not isinstance(value, str):
            value = str(value)
        
        # Escape single quotes by doubling them for VALUES format
        value = value.replace("'", "''")
        
        # Remove or escape other potentially dangerous characters
        value = value.replace("\\", "\\\\")  # Escape backslashes
        value = value.replace("\n", "\\n")   # Escape newlines
        value = value.replace("\r", "\\r")   # Escape carriage returns
        value = value.replace("\t", "\\t")   # Escape tabs
        
        # Limit length to prevent buffer overflow
        if len(value) > 255:
            value = value[:255]
        
        # Additional sanitization to prevent injection
        value = self._sanitize_string(value)
        
        return value
    
    def _batch_sanitize_strings(self, values: List[str]) -> List[str]:
        """Batch sanitization for O(n) instead of O(n²) performance"""
        sanitized = []
        for value in values:
            if not isinstance(value, str):
                value = str(value)
            
            if len(value) > 255:
                continue  # Skip invalid entries instead of raising
            
            value = self._DANGEROUS_CHARS_PATTERN.sub("", value)
            value = self._SQL_INJECTION_PATTERN.sub("", value)
            sanitized.append(value.strip())
        
        return sanitized
    
    def _convert_timeframe_to_interval(self, timeframe: str) -> str:
        """Convert timeframe to ClickHouse interval format"""
        timeframe_map = {
            "1m": "1 MINUTE",
            "5m": "5 MINUTE",
            "15m": "15 MINUTE",
            "30m": "30 MINUTE",
            "1h": "1 HOUR",
            "4h": "4 HOUR",
            "1d": "1 DAY",
            "1w": "1 WEEK"
        }
        
        return timeframe_map.get(timeframe.lower(), "1 MINUTE")
    
    def _load_query_templates(self) -> Dict[str, Dict[str, str]]:
        """Load query templates for different database types"""
        return {
            "clickhouse": {
                "recent_ticks": "SELECT * FROM ticks WHERE symbol = '{symbol}' ORDER BY timestamp DESC LIMIT {limit}",
                "tick_stats": "SELECT count() as total FROM ticks WHERE symbol = '{symbol}'"
            },
            "postgresql": {
                "user_by_id": "SELECT * FROM users WHERE user_id = {user_id}",
                "active_sessions": "SELECT * FROM user_sessions WHERE expires_at > NOW()"
            },
            "arangodb": {
                "all_strategies": "FOR strategy IN trading_strategies RETURN strategy",
                "strategy_by_id": "FOR strategy IN trading_strategies FILTER strategy._key == '{id}' RETURN strategy"
            }
        }
    
    def validate_query(self, sql_query: str, database_type: str) -> bool:
        """Validate query syntax and security"""
        try:
            # Basic security checks
            dangerous_patterns = [
                r"DROP\s+TABLE",
                r"DELETE\s+FROM\s+\w+\s*;",
                r"UPDATE\s+\w+\s+SET.*WHERE\s+1\s*=\s*1",
                r"UNION\s+SELECT",
                r"--\s*$",
                r"/\*.*\*/"
            ]
            
            query_upper = sql_query.upper()
            
            for pattern in dangerous_patterns:
                if re.search(pattern, query_upper, re.IGNORECASE):
                    self.logger.warning(f"Potentially dangerous query pattern detected: {pattern}")
                    return False
            
            # Database-specific validations
            if database_type == "clickhouse":
                return self._validate_clickhouse_query(sql_query)
            elif database_type == "postgresql":
                return self._validate_postgresql_query(sql_query)
            elif database_type == "arangodb":
                return self._validate_aql_query(sql_query)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Query validation failed: {e}")
            return False
    
    def _validate_clickhouse_query(self, sql_query: str) -> bool:
        """Validate ClickHouse-specific query syntax"""
        # Basic ClickHouse query validation
        if not re.search(r"SELECT|INSERT|CREATE|ALTER", sql_query, re.IGNORECASE):
            return False
        
        return True
    
    def _validate_postgresql_query(self, sql_query: str) -> bool:
        """Validate PostgreSQL-specific query syntax"""
        # Basic PostgreSQL query validation
        if not re.search(r"SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER", sql_query, re.IGNORECASE):
            return False
        
        return True
    
    def _validate_aql_query(self, aql_query: str) -> bool:
        """Validate ArangoDB AQL query syntax"""
        # Basic AQL query validation
        if not re.search(r"FOR|RETURN|FILTER|SORT|LIMIT", aql_query, re.IGNORECASE):
            return False
        
        return True