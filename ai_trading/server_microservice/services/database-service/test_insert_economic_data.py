#!/usr/bin/env python3
"""
Test script to insert economic calendar data into the newly created table
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add src path to sys.path for proper imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.business.database_manager import DatabaseManager


async def test_insert_economic_data():
    """Test inserting economic calendar data"""
    print("🚀 Testing economic data insertion...")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.initialize()
        print("✅ Database manager initialized")
        
        # Sample economic event data
        economic_event = {
            "timestamp": datetime.now(timezone.utc),
            "event_name": "Non-Farm Payrolls",
            "country": "United States",
            "currency": "USD",
            "importance": "High",
            "scheduled_time": datetime.now(timezone.utc),
            "timezone": "New York",
            "actual": "250000",
            "forecast": "200000", 
            "previous": "180000",
            "unit": "jobs",
            "deviation_from_forecast": 50000.0,
            "market_impact": "High",
            "volatility_expected": "High",
            "currency_impact": "Positive",
            "affected_sectors": "All major sectors",
            "ai_predicted_value": 245000.0,
            "ai_prediction_confidence": 0.85,
            "ai_prediction_model": "ensemble",
            "ai_sentiment_score": 0.72,
            "volatility_impact_score": 8.5,
            "currency_pair_impacts": "EURUSD:-0.8%, GBPUSD:-0.6%",
            "sector_rotation_prediction": "Technology up, Utilities down",
            "central_bank_reaction_probability": 0.15,
            "historical_pattern_match": 0.78,
            "seasonal_adjustment": 1.02,
            "surprise_index": 2.5,
            "consensus_accuracy": 0.68,
            "bond_impact_prediction": "10Y yields up 5-10 bps",
            "equity_impact_prediction": "S&P500 up 0.3-0.8%",
            "commodity_impact_prediction": "Gold down $10-15",
            "immediate_impact_window": "0-15 minutes",
            "delayed_impact_window": "15-60 minutes", 
            "impact_duration_minutes": 45,
            "market_conditions_at_release": "Normal volatility, good liquidity",
            "liquidity_conditions": "Normal",
            "concurrent_events": "ECB speech at 16:00",
            "event_id": "NFP_2025_01",
            "source": "MQL5",
            "widget_url": "https://www.mql5.com/en/economic-calendar"
        }
        
        print(f"📊 Sample economic event: {economic_event['event_name']} ({economic_event['country']})")
        
        # Insert data using raw SQL (since we're in default database, not trading_data)
        insert_query = """
        INSERT INTO default.economic_calendar (
            timestamp, event_name, country, currency, importance, scheduled_time, 
            timezone, actual, forecast, previous, unit, deviation_from_forecast,
            market_impact, volatility_expected, currency_impact, affected_sectors,
            ai_predicted_value, ai_prediction_confidence, ai_prediction_model, ai_sentiment_score,
            volatility_impact_score, currency_pair_impacts, sector_rotation_prediction,
            central_bank_reaction_probability, historical_pattern_match, seasonal_adjustment,
            surprise_index, consensus_accuracy, bond_impact_prediction, equity_impact_prediction,
            commodity_impact_prediction, immediate_impact_window, delayed_impact_window,
            impact_duration_minutes, market_conditions_at_release, liquidity_conditions,
            concurrent_events, event_id, source, widget_url
        ) VALUES (
            now64(), %(event_name)s, %(country)s, %(currency)s, %(importance)s, now64(),
            %(timezone)s, %(actual)s, %(forecast)s, %(previous)s, %(unit)s, %(deviation_from_forecast)s,
            %(market_impact)s, %(volatility_expected)s, %(currency_impact)s, %(affected_sectors)s,
            %(ai_predicted_value)s, %(ai_prediction_confidence)s, %(ai_prediction_model)s, %(ai_sentiment_score)s,
            %(volatility_impact_score)s, %(currency_pair_impacts)s, %(sector_rotation_prediction)s,
            %(central_bank_reaction_probability)s, %(historical_pattern_match)s, %(seasonal_adjustment)s,
            %(surprise_index)s, %(consensus_accuracy)s, %(bond_impact_prediction)s, %(equity_impact_prediction)s,
            %(commodity_impact_prediction)s, %(immediate_impact_window)s, %(delayed_impact_window)s,
            %(impact_duration_minutes)s, %(market_conditions_at_release)s, %(liquidity_conditions)s,
            %(concurrent_events)s, %(event_id)s, %(source)s, %(widget_url)s
        )"""
        
        # Execute insert (using default database directly)
        print("💾 Inserting economic event data...")
        
        # Use httpx directly for parameterized query
        import httpx
        
        # Build query with actual values (ClickHouse format)
        insert_values = {
            'event_name': f"'{economic_event['event_name']}'",
            'country': f"'{economic_event['country']}'", 
            'currency': f"'{economic_event['currency']}'",
            'importance': f"'{economic_event['importance']}'",
            'timezone': f"'{economic_event['timezone']}'",
            'actual': f"'{economic_event['actual']}'",
            'forecast': f"'{economic_event['forecast']}'",
            'previous': f"'{economic_event['previous']}'",
            'unit': f"'{economic_event['unit']}'",
            'deviation_from_forecast': str(economic_event['deviation_from_forecast']),
            'market_impact': f"'{economic_event['market_impact']}'",
            'volatility_expected': f"'{economic_event['volatility_expected']}'",
            'currency_impact': f"'{economic_event['currency_impact']}'",
            'affected_sectors': f"'{economic_event['affected_sectors']}'",
            'ai_predicted_value': str(economic_event['ai_predicted_value']),
            'ai_prediction_confidence': str(economic_event['ai_prediction_confidence']),
            'ai_prediction_model': f"'{economic_event['ai_prediction_model']}'",
            'ai_sentiment_score': str(economic_event['ai_sentiment_score']),
            'volatility_impact_score': str(economic_event['volatility_impact_score']),
            'currency_pair_impacts': f"'{economic_event['currency_pair_impacts']}'",
            'sector_rotation_prediction': f"'{economic_event['sector_rotation_prediction']}'",
            'central_bank_reaction_probability': str(economic_event['central_bank_reaction_probability']),
            'historical_pattern_match': str(economic_event['historical_pattern_match']),
            'seasonal_adjustment': str(economic_event['seasonal_adjustment']),
            'surprise_index': str(economic_event['surprise_index']),
            'consensus_accuracy': str(economic_event['consensus_accuracy']),
            'bond_impact_prediction': f"'{economic_event['bond_impact_prediction']}'",
            'equity_impact_prediction': f"'{economic_event['equity_impact_prediction']}'",
            'commodity_impact_prediction': f"'{economic_event['commodity_impact_prediction']}'",
            'immediate_impact_window': f"'{economic_event['immediate_impact_window']}'",
            'delayed_impact_window': f"'{economic_event['delayed_impact_window']}'",
            'impact_duration_minutes': str(economic_event['impact_duration_minutes']),
            'market_conditions_at_release': f"'{economic_event['market_conditions_at_release']}'",
            'liquidity_conditions': f"'{economic_event['liquidity_conditions']}'",
            'concurrent_events': f"'{economic_event['concurrent_events']}'",
            'event_id': f"'{economic_event['event_id']}'",
            'source': f"'{economic_event['source']}'",
            'widget_url': f"'{economic_event['widget_url']}'"
        }
        
        # Simple INSERT query with values
        simple_insert = f"""
        INSERT INTO default.economic_calendar VALUES (
            now64(), {insert_values['event_name']}, {insert_values['country']}, {insert_values['currency']},
            {insert_values['importance']}, now64(), NULL, {insert_values['timezone']},
            {insert_values['actual']}, {insert_values['forecast']}, {insert_values['previous']}, {insert_values['unit']},
            {insert_values['deviation_from_forecast']}, {insert_values['market_impact']}, {insert_values['volatility_expected']},
            {insert_values['currency_impact']}, {insert_values['affected_sectors']}, {insert_values['ai_predicted_value']},
            {insert_values['ai_prediction_confidence']}, {insert_values['ai_prediction_model']}, {insert_values['ai_sentiment_score']},
            {insert_values['volatility_impact_score']}, {insert_values['currency_pair_impacts']}, {insert_values['sector_rotation_prediction']},
            {insert_values['central_bank_reaction_probability']}, {insert_values['historical_pattern_match']}, {insert_values['seasonal_adjustment']},
            {insert_values['surprise_index']}, {insert_values['consensus_accuracy']}, {insert_values['bond_impact_prediction']},
            {insert_values['equity_impact_prediction']}, {insert_values['commodity_impact_prediction']}, {insert_values['immediate_impact_window']},
            {insert_values['delayed_impact_window']}, {insert_values['impact_duration_minutes']}, {insert_values['market_conditions_at_release']},
            {insert_values['liquidity_conditions']}, {insert_values['concurrent_events']}, {insert_values['event_id']},
            {insert_values['source']}, {insert_values['widget_url']}, now64()
        )"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8123/",
                params={"query": simple_insert},
                auth=("default", "")
            )
            response.raise_for_status()
            print("✅ Economic event inserted successfully!")
        
        # Verify data was inserted
        print("\n🔍 Verifying inserted data...")
        verify_query = "SELECT event_name, country, currency, importance, ai_predicted_value, ai_prediction_confidence FROM default.economic_calendar ORDER BY timestamp DESC LIMIT 1"
        
        result = await db_manager.execute_clickhouse_query(
            query=verify_query,
            database="default"
        )
        
        if result:
            print("✅ Data verification successful!")
            for key, value in result[0].items():
                print(f"  📊 {key}: {value}")
        else:
            print("❌ No data found in verification query")
        
        # Check total count
        print("\n📊 Checking total economic events...")
        count_query = "SELECT COUNT(*) as total FROM default.economic_calendar"
        count_result = await db_manager.execute_clickhouse_query(
            query=count_query,
            database="default"
        )
        
        if count_result:
            total = count_result[0].get("total", 0)
            print(f"📈 Total economic events in database: {total}")
        
        # Cleanup
        await db_manager.shutdown()
        print("\n🎉 Economic data insertion test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in economic data test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("📅 Economic Calendar Data Insertion Test")
    print("=" * 50)
    asyncio.run(test_insert_economic_data())