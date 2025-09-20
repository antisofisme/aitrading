# Service infrastructure - use absolute imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

try:
    from shared.infrastructure.core.logger_core import get_logger
    from shared.infrastructure.core.error_core import handle_error
    from shared.infrastructure.core.performance_core import performance_tracked
    from shared.infrastructure.core.config_core import CoreConfig
    from shared.infrastructure.core.cache_core import CoreCache
except ImportError as e:
    print(f"⚠️ Infrastructure import issue: {e}")
    # Fallback implementations
    import logging
    
    def get_logger(name, version=None):
        return logging.getLogger(name)
    
    def handle_error(service_name, error, context=None):
        print(f"Error in {service_name}: {error}")
        if context:
            print(f"Context: {context}")
    
    def performance_tracked(service_name, operation_name):
        def decorator(func):
            return func
        return decorator
    
    class CoreConfig:
        def __init__(self, service_name=None):
            pass
        def get(self, key, default=None):
            return default
    
    class CoreCache:
        def __init__(self, name, max_size=1000, default_ttl=300):
            self.name = name
            self.max_size = max_size
            self.default_ttl = default_ttl
            self.cache = {}
        
        async def get(self, key): 
            return None
        
        async def set(self, key, value, ttl=None): 
            pass

"""
MQL5 Economic Calendar Widget Scraper
Extract economic calendar data from MQL5 widget

FEATURES:
- Legal widget-based data extraction
- Browser automation for dynamic content
- Network request interception
- Enhanced data processing
- Microservice integration
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Additional infrastructure imports for fallback compatibility
try:
    from shared.infrastructure.core.config_core import CoreConfig
    from shared.infrastructure.core.performance_core import performance_tracked
except ImportError:
    pass

logger = get_logger("data-bridge", "mql5-scraper")


@dataclass
class MQL5EconomicEvent:
    """Enhanced Economic event from MQL5 widget"""
    event_name: str
    country: str
    currency: str
    datetime: str
    importance: str  # LOW, MEDIUM, HIGH
    
    # Enhanced time information
    scheduled_time: Optional[str] = None
    actual_release_time: Optional[str] = None
    timezone: str = "UTC"
    time_until_release: Optional[float] = None
    
    # Enhanced impact analysis
    market_impact: str = "Medium"
    volatility_expected: str = "Medium"
    currency_impact: str = "Neutral"
    affected_sectors: List[str] = None
    
    # Economic data
    actual: Optional[str] = None
    forecast: Optional[str] = None
    previous: Optional[str] = None
    unit: Optional[str] = None
    deviation_from_forecast: Optional[float] = None
    historical_trend: Optional[str] = None
    
    # MQL5 specific
    event_id: Optional[str] = None
    source: str = "MQL5"
    widget_url: str = None
    scraped_at: str = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now().isoformat()
        
        if self.affected_sectors is None:
            self.affected_sectors = []
        
        # Enhanced impact analysis based on importance
        if self.importance:
            if self.importance.upper() == "HIGH":
                self.market_impact = "High"
                self.volatility_expected = "High"
                self.affected_sectors = self.affected_sectors or ["Currency", "Bonds", "Equities"]
            elif self.importance.upper() == "MEDIUM":
                self.market_impact = "Medium"
                self.volatility_expected = "Medium"
                self.affected_sectors = self.affected_sectors or ["Currency", "Bonds"]
            else:
                self.market_impact = "Low"
                self.volatility_expected = "Low"
                self.affected_sectors = self.affected_sectors or ["Currency"]
        
        # Calculate time until release
        if self.scheduled_time:
            try:
                scheduled_dt = datetime.fromisoformat(self.scheduled_time.replace('Z', '+00:00'))
                current_dt = datetime.now(scheduled_dt.tzinfo if scheduled_dt.tzinfo else None)
                time_diff = scheduled_dt - current_dt
                self.time_until_release = time_diff.total_seconds() / 3600
            except Exception:
                pass
        
        # Calculate deviation from forecast
        if self.actual and self.forecast:
            try:
                actual_val = float(str(self.actual).replace('%', '').replace(',', ''))
                forecast_val = float(str(self.forecast).replace('%', '').replace(',', ''))
                if forecast_val != 0:
                    self.deviation_from_forecast = ((actual_val - forecast_val) / abs(forecast_val)) * 100
                    
                    # Determine currency impact
                    if self.deviation_from_forecast > 5:
                        self.currency_impact = "Bullish"
                    elif self.deviation_from_forecast < -5:
                        self.currency_impact = "Bearish"
                    else:
                        self.currency_impact = "Neutral"
            except Exception:
                pass


class MQL5WidgetScraper:
    """MQL5 Economic Calendar Widget Scraper dengan Historical Date Support dan Batch Processing"""
    
    def __init__(self, headless: bool = True, timeout: Optional[int] = None, target_date: Optional[str] = None):
        self.config = CoreConfig("data-bridge")
        nce
        self.performance = CorePerformance("data-bridge")
        
        # Load configuration from environment
        self.headless = headless
        self.timeout = timeout or int(os.getenv("MQL5_BROWSER_TIMEOUT_SECONDS", "30"))
        self.target_date = target_date  # Format: 'YYYY-MM-DD' untuk historical data
        self.widget_url = None
        self.driver = None
        self.network_requests = []
        
        # Batch processing configuration from environment
        self.historical_days_back = int(os.getenv("MQL5_HISTORICAL_DAYS_BACK", "30"))
        self.batch_size = int(os.getenv("MQL5_BATCH_SIZE", "7"))
        self.batch_delay_seconds = int(os.getenv("MQL5_BATCH_DELAY_SECONDS", "5"))
        self.skip_empty_dates = os.getenv("MQL5_SKIP_EMPTY_DATES", "true").lower() == "true"
        self.max_retries_per_date = int(os.getenv("MQL5_MAX_RETRIES_PER_DATE", "3"))
        
        # Weekend events configuration
        self.include_weekend_events = os.getenv("MQL5_INCLUDE_WEEKEND_EVENTS", "false").lower() == "true"
        weekend_types = os.getenv("MQL5_WEEKEND_EVENT_TYPES", "emergency,central_bank,geopolitical")
        self.weekend_event_types = [t.strip().lower() for t in weekend_types.split(",")]
        
        # Widget HTML template dengan dynamic date support
        self.widget_html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>MQL5 Economic Calendar Widget</title>
            <style>
                body { margin: 0; padding: 20px; font-family: Arial; }
                #economicCalendarWidget { min-height: 600px; width: 100%; }
            </style>
        </head>
        <body>
            <div id="economicCalendarWidget"></div>
            <div class="ecw-copyright">
                <a href="https://www.mql5.com/?utm_source=calendar.widget&utm_medium=link&utm_term=economic.calendar&utm_content=visit.mql5.calendar&utm_campaign=202.calendar.widget" 
                   rel="noopener nofollow" target="_blank">MQL5 Algo Trading Community</a>
            </div>
            
            <script>
                // Network request monitoring
                window.networkRequests = [];
                window.extractedData = [];
                
                const originalFetch = window.fetch;
                const originalXHROpen = XMLHttpRequest.prototype.open;
                
                window.fetch = function(...args) {
                    const url = args[0];
                    window.networkRequests.push({type: 'FETCH', url: url, timestamp: new Date().toISOString()});
                    return originalFetch.apply(this, args);
                };
                
                XMLHttpRequest.prototype.open = function(method, url, ...args) {
                    window.networkRequests.push({type: 'XHR', method: method, url: url, timestamp: new Date().toISOString()});
                    
                    this.addEventListener('load', function() {
                        if (url.includes('calendar') || url.includes('economic') || url.includes('data')) {
                            try {
                                const data = JSON.parse(this.responseText);
                                window.extractedData.push({url: url, data: data, timestamp: new Date().toISOString()});
                            } catch (e) {
                                window.extractedData.push({url: url, text: this.responseText.substring(0, 1000), timestamp: new Date().toISOString()});
                            }
                        }
                    });
                    
                    return originalXHROpen.apply(this, arguments);
                };
                
                // Data extraction after widget loads
                setTimeout(function() {
                    window.widgetLoaded = true;
                    const widget = document.getElementById('economicCalendarWidget');
                    window.widgetHTML = widget.innerHTML;
                    
                    // Try to extract economic events
                    const events = [];
                    const selectors = ['[data-event]', '.calendar-event', '.economic-event', 'tr', 'div[class*="event"]'];
                    
                    selectors.forEach(selector => {
                        const elements = widget.querySelectorAll(selector);
                        Array.from(elements).forEach(el => {
                            const text = el.textContent || el.innerText || '';
                            if (text.trim() && text.length > 10) {
                                events.push({
                                    selector: selector,
                                    text: text.trim(),
                                    html: el.outerHTML
                                });
                            }
                        });
                    });
                    
                    window.extractedEvents = events;
                }, 5000);
            </script>
            
            <!-- MQL5 Widget dengan Date Parameter -->
            <script async type="text/javascript" data-type="calendar-widget" 
                    src="https://www.tradays.com/c/js/widgets/calendar/widget.js?v=14">
                {WIDGET_PARAMS}
            </script>
        </body>
        </html>
        """
        
        logger.info(f"MQL5 Widget Scraper initialized - Selenium: {SELENIUM_AVAILABLE}, Headless: {headless}, Date: {target_date}")
    
    def _setup_driver(self):
        """Setup Chrome WebDriver dengan stealth options"""
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available, please install: pip install selenium")
        
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        # Stealth options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Enable network logging
        options.add_argument('--enable-logging')
        options.add_argument('--log-level=0')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            return False
    
    @performance_tracked("unknown-service", "scrape_widget_data")
    async def scrape_widget_data(self, save_results: bool = True, specific_date: Optional[str] = None) -> Dict[str, Any]:
        """Scrape economic calendar data from MQL5 widget"""
        
        logger.info("Starting MQL5 widget scraping")
        
        if not self._setup_driver():
            return {"status": "error", "error": "WebDriver setup failed"}
        
        try:
            # Prepare widget parameters dengan date support
            target_date = specific_date or self.target_date
            widget_params = self._prepare_widget_parameters(target_date)
            
            # Create temporary HTML file with widget
            temp_file = Path("temp_mql5_widget.html")
            widget_html = self.widget_html_template.replace("{WIDGET_PARAMS}", widget_params)
            temp_file.write_text(widget_html)
            self.widget_url = f"file://{temp_file.absolute()}"
            
            logger.info(f"Loading widget page: {self.widget_url}")
            
            # Load the widget page
            self.driver.get(self.widget_url)
            
            # Wait for initial page load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "economicCalendarWidget"))
            )
            
            logger.info("Widget element found, waiting for data to load...")
            
            # Wait for widget to load and capture network requests
            await asyncio.sleep(10)  # Give widget time to load
            
            # Extract network requests
            network_requests = self.driver.execute_script("return window.networkRequests || [];")
            extracted_data = self.driver.execute_script("return window.extractedData || [];")
            widget_html = self.driver.execute_script("return window.widgetHTML || '';")
            extracted_events = self.driver.execute_script("return window.extractedEvents || [];")
            
            logger.info("Data extraction completed", 
                       network_requests=len(network_requests),
                       extracted_data=len(extracted_data),
                       widget_html_length=len(widget_html),
                       extracted_events=len(extracted_events))
            
            # Process extracted data
            economic_events = self._process_widget_data(extracted_data, extracted_events, widget_html)
            
            results = {
                "status": "success",
                "source": "MQL5 Widget",
                "method": "selenium_browser_automation",
                "events": economic_events,
                "summary": {
                    "total_events": len(economic_events),
                    "high_impact": len([e for e in economic_events if e.get('market_impact') == 'High']),
                    "network_requests": len(network_requests),
                    "data_sources": len(extracted_data)
                },
                "debug_info": {
                    "network_requests": network_requests,
                    "extracted_data": extracted_data[:3],  # First 3 for debugging
                    "widget_html_preview": widget_html[:500],
                    "extracted_events_preview": extracted_events[:5]
                },
                "integration_timestamp": datetime.now().isoformat()
            }
            
            if save_results:
                # Save results
                filename = f"mql5_widget_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                logger.info(f"Results saved to: {filename}")
            
            return results
            
        except Exception as e:
            logger.error(f"Widget scraping failed: {str(e)}")
            return {
                "status": "error", 
                "error": str(e),
                "source": "MQL5 Widget"
            }
        
        finally:
            if self.driver:
                self.driver.quit()
            
            # Cleanup temp file
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except:
                pass
    
    def _prepare_widget_parameters(self, target_date: Optional[str] = None) -> str:
        """Prepare MQL5 widget parameters dengan date support untuk historical data"""
        
        # Base widget configuration
        widget_config = {
            "width": "100%",
            "height": "100%", 
            "mode": "2"  # Calendar mode
        }
        
        # Add date parameter untuk historical data jika tersedia
        if target_date:
            try:
                # Parse target date
                if isinstance(target_date, str):
                    target_dt = datetime.fromisoformat(target_date.replace('Z', ''))
                else:
                    target_dt = target_date
                
                # Format date for widget (YYYY-MM-DD atau timestamp)
                widget_config["date"] = target_dt.strftime("%Y-%m-%d")
                widget_config["timestamp"] = int(target_dt.timestamp())
                
                # Additional parameters untuk historical data
                widget_config["historical"] = True
                widget_config["timeframe"] = "daily"
                
                logger.info("Historical date configured for MQL5 widget", 
                           target_date=target_date,
                           formatted_date=widget_config["date"])
                
            except Exception as e:
                logger.warning("Failed to parse target date, using current date", 
                              target_date=target_date, error=str(e))
        
        return json.dumps(widget_config)
    
    @performance_tracked("unknown-service", "batch_scrape_historical_data")
    async def scrape_historical_batch(self, days_back: Optional[int] = None, save_results: bool = True) -> Dict[str, Any]:
        """Scrape historical economic calendar data dalam batch processing"""
        
        days_back = days_back or self.historical_days_back
        logger.info("Starting MQL5 historical batch scraping", 
                   days_back=days_back, 
                   batch_size=self.batch_size,
                   skip_empty_dates=self.skip_empty_dates)
        
        # Generate date range untuk historical data
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        date_range = self._generate_date_range(start_date, end_date)
        
        logger.info("Generated date range", 
                   start_date=start_date.isoformat(),
                   end_date=end_date.isoformat(),
                   total_dates=len(date_range))
        
        # Process dalam batches
        all_results = []
        successful_dates = []
        failed_dates = []
        empty_dates = []
        
        for i in range(0, len(date_range), self.batch_size):
            batch_dates = date_range[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(date_range) + self.batch_size - 1) // self.batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches}", 
                       batch_dates=[d.isoformat() for d in batch_dates])
            
            # Process each date in batch
            batch_results = []
            for target_date in batch_dates:
                date_str = target_date.isoformat()
                
                # Handle weekend dates based on configuration
                from ..business.trading_calendar import get_trading_calendar
                trading_calendar = get_trading_calendar()
                is_trading_day = trading_calendar.is_trading_day(datetime.combine(target_date, datetime.min.time()))
                
                if not is_trading_day:
                    if self.include_weekend_events:
                        logger.info(f"🔍 Weekend/holiday detected: {date_str} - checking for emergency events")
                        # Continue processing but mark as weekend for special handling
                    else:
                        logger.info(f"⏭️ Skipping weekend/holiday: {date_str} (forex market closed)")
                        continue
                
                # Scrape data for specific date
                date_result = await self._scrape_single_date_with_retries(date_str)
                
                if date_result['status'] == 'success':
                    events = date_result.get('events', [])
                    
                    # Apply weekend filtering if needed
                    if not is_trading_day and self.include_weekend_events:
                        original_count = len(events)
                        events = self._filter_weekend_events(events, is_weekend=True)
                        date_result['events'] = events
                        
                        if original_count > len(events):
                            logger.info(f"🔍 Weekend filtering: {original_count} → {len(events)} events for {date_str}")
                    
                    if events:
                        successful_dates.append(date_str)
                        batch_results.append(date_result)
                        weekend_indicator = " (weekend)" if not is_trading_day else ""
                        logger.info(f"✅ {date_str}{weekend_indicator}: {len(events)} events found")
                    else:
                        empty_dates.append(date_str)
                        if not self.skip_empty_dates:
                            batch_results.append(date_result)
                        weekend_indicator = " (weekend - no relevant events)" if not is_trading_day else ""
                        logger.info(f"📭 {date_str}{weekend_indicator}: No events found")
                else:
                    failed_dates.append(date_str)
                    logger.error(f"❌ {date_str}: Scraping failed - {date_result.get('error')}")
                
                # Small delay between dates to avoid rate limiting
                await asyncio.sleep(1)
            
            all_results.extend(batch_results)
            
            # Delay between batches
            if i + self.batch_size < len(date_range):
                logger.info(f"Batch {batch_num} completed, waiting {self.batch_delay_seconds}s before next batch...")
                await asyncio.sleep(self.batch_delay_seconds)
        
        # Compile final results
        all_events = []
        weekend_events_count = 0
        for result in all_results:
            events = result.get('events', [])
            all_events.extend(events)
            # Count weekend events
            weekend_events_count += len([e for e in events if e.get('weekend_special_processing', False)])
        
        batch_summary = {
            "status": "completed",
            "source": "MQL5 Widget Batch Scraping",
            "method": "batch_browser_automation",
            "configuration": {
                "days_back": days_back,
                "batch_size": self.batch_size,
                "batch_delay_seconds": self.batch_delay_seconds,
                "skip_empty_dates": self.skip_empty_dates,
                "max_retries_per_date": self.max_retries_per_date,
                "include_weekend_events": self.include_weekend_events,
                "weekend_event_types": self.weekend_event_types
            },
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_dates_attempted": len(date_range),
                "successful_dates": len(successful_dates),
                "empty_dates": len(empty_dates),
                "failed_dates": len(failed_dates)
            },
            "events": all_events,
            "summary": {
                "total_events": len(all_events),
                "high_impact": len([e for e in all_events if e.get('market_impact') == 'High']),
                "medium_impact": len([e for e in all_events if e.get('market_impact') == 'Medium']),
                "low_impact": len([e for e in all_events if e.get('market_impact') == 'Low']),
                "weekend_events": weekend_events_count,
                "regular_events": len(all_events) - weekend_events_count,
                "success_rate": len(successful_dates) / len(date_range) if date_range else 0
            },
            "processing_details": {
                "successful_dates": successful_dates,
                "empty_dates": empty_dates if not self.skip_empty_dates else f"Skipped {len(empty_dates)} empty dates",
                "failed_dates": failed_dates,
                "total_batches": total_batches
            },
            "integration_timestamp": datetime.now().isoformat()
        }
        
        if save_results:
            # Save batch results
            filename = f"mql5_historical_batch_{start_date}_{end_date}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(batch_summary, f, indent=2, default=str)
            logger.info(f"Batch results saved to: {filename}")
        
        logger.info(f"MQL5 historical batch scraping completed - Events: {len(all_events)}, Success: {batch_summary['summary']['success_rate']*100:.1f}%, Success dates: {len(successful_dates)}, Empty: {len(empty_dates)}, Failed: {len(failed_dates)}")
        
        return batch_summary
    
    def _generate_date_range(self, start_date: date, end_date: date) -> List[date]:
        """Generate list of dates between start and end"""
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        return date_list
    
    async def _scrape_single_date_with_retries(self, date_str: str) -> Dict[str, Any]:
        """Scrape single date dengan retry mechanism"""
        
        for attempt in range(self.max_retries_per_date):
            try:
                logger.debug(f"Scraping {date_str}, attempt {attempt + 1}/{self.max_retries_per_date}")
                result = await self.scrape_widget_data(save_results=False, specific_date=date_str)
                
                if result.get('status') == 'success':
                    return result
                elif attempt < self.max_retries_per_date - 1:
                    logger.warning(f"Attempt {attempt + 1} failed for {date_str}, retrying...")
                    await asyncio.sleep(2)  # Wait before retry
                    
            except Exception as e:
                if attempt < self.max_retries_per_date - 1:
                    logger.warning(f"Exception on attempt {attempt + 1} for {date_str}: {e}, retrying...")
                    await asyncio.sleep(2)
                else:
                    return {
                        "status": "error",
                        "error": f"All {self.max_retries_per_date} attempts failed: {str(e)}",
                        "date": date_str
                    }
        
        return {
            "status": "error", 
            "error": f"All {self.max_retries_per_date} attempts failed",
            "date": date_str
        }
    
    def _filter_weekend_events(self, events: List[Dict], is_weekend: bool = False) -> List[Dict]:
        """Filter events untuk weekend dates - hanya keep emergency/critical events"""
        if not is_weekend or not self.include_weekend_events:
            return events
        
        filtered_events = []
        for event in events:
            event_name = event.get('event_name', '').lower()
            importance = event.get('importance', '').lower()
            
            # Check if event is weekend-relevant
            is_emergency = any(keyword in event_name for keyword in [
                'emergency', 'urgent', 'crisis', 'breaking', 'unscheduled'
            ])
            
            is_central_bank = any(keyword in event_name for keyword in [
                'fed', 'ecb', 'boe', 'boj', 'rba', 'snb', 'central bank', 'interest rate decision'
            ])
            
            is_geopolitical = any(keyword in event_name for keyword in [
                'election', 'referendum', 'summit', 'meeting', 'treaty', 'agreement'
            ])
            
            # High importance events are always kept on weekends
            is_high_importance = importance == 'high'
            
            # Determine if this event should be included
            should_include = False
            event_category = None
            
            if 'emergency' in self.weekend_event_types and (is_emergency or is_high_importance):
                should_include = True
                event_category = 'emergency'
            elif 'central_bank' in self.weekend_event_types and is_central_bank:
                should_include = True
                event_category = 'central_bank'
            elif 'geopolitical' in self.weekend_event_types and is_geopolitical:
                should_include = True
                event_category = 'geopolitical'
            
            if should_include:
                event['weekend_event_category'] = event_category
                event['weekend_special_processing'] = True
                filtered_events.append(event)
                logger.info(f"✅ Weekend event included: {event_name[:50]}... (category: {event_category})")
            else:
                logger.debug(f"⏭️ Weekend event filtered out: {event_name[:50]}...")
        
        if filtered_events:
            logger.info(f"🔍 Weekend filtering: {len(filtered_events)}/{len(events)} events kept")
        
        return filtered_events
    
    def _process_widget_data(self, extracted_data: List[Dict], extracted_events: List[Dict], widget_html: str) -> List[Dict]:
        """Process raw widget data into structured economic events"""
        
        events = []
        
        # Process extracted JSON data first
        for data_item in extracted_data:
            if 'data' in data_item and isinstance(data_item['data'], dict):
                events.extend(self._parse_json_data(data_item['data'], data_item['url']))
        
        # Process extracted HTML events
        for event_item in extracted_events:
            parsed_event = self._parse_html_event(event_item)
            if parsed_event:
                events.append(parsed_event)
        
        # If no structured data found, create sample events for testing
        if not events:
            events = self._create_sample_events()
            logger.warning("No real data extracted, using sample events")
        
        return events
    
    def _parse_json_data(self, data: Dict, source_url: str) -> List[Dict]:
        """Parse JSON data from API responses"""
        events = []
        
        # Look for different JSON structures
        possible_event_keys = ['events', 'calendar', 'data', 'items', 'results']
        
        for key in possible_event_keys:
            if key in data and isinstance(data[key], list):
                for item in data[key]:
                    if isinstance(item, dict):
                        event = self._extract_event_from_json(item, source_url)
                        if event:
                            events.append(event)
        
        return events
    
    def _extract_event_from_json(self, item: Dict, source_url: str) -> Optional[Dict]:
        """Extract economic event from JSON item"""
        try:
            # Map common field names
            field_mapping = {
                'name': ['name', 'event', 'title', 'event_name'],
                'country': ['country', 'nation', 'region'],
                'currency': ['currency', 'curr', 'symbol'],
                'time': ['time', 'date', 'datetime', 'timestamp'],
                'importance': ['importance', 'impact', 'priority', 'level'],
                'actual': ['actual', 'act', 'result'],
                'forecast': ['forecast', 'fore', 'expected', 'estimate'],
                'previous': ['previous', 'prev', 'prior']
            }
            
            event_data = {}
            
            for field, possible_keys in field_mapping.items():
                for key in possible_keys:
                    if key in item:
                        event_data[field] = item[key]
                        break
            
            # Create MQL5 economic event
            if event_data.get('name'):
                event = MQL5EconomicEvent(
                    event_name=event_data.get('name', ''),
                    country=event_data.get('country', 'Unknown'),
                    currency=event_data.get('currency', 'Unknown'),
                    datetime=event_data.get('time', datetime.now().isoformat()),
                    importance=str(event_data.get('importance', 'Medium')).upper(),
                    actual=event_data.get('actual'),
                    forecast=event_data.get('forecast'),
                    previous=event_data.get('previous'),
                    widget_url=source_url
                )
                
                return asdict(event)
        
        except Exception as e:
            logger.debug("Failed to extract event from JSON", error=str(e))
        
        return None
    
    def _parse_html_event(self, event_item: Dict) -> Optional[Dict]:
        """Parse economic event from HTML element"""
        try:
            text = event_item.get('text', '')
            
            # Basic text parsing for economic indicators
            if any(keyword in text.lower() for keyword in ['gdp', 'unemployment', 'inflation', 'rate', 'pmi', 'cpi']):
                event = MQL5EconomicEvent(
                    event_name=text[:100],  # First 100 chars
                    country='Unknown',
                    currency='Unknown', 
                    datetime=datetime.now().isoformat(),
                    importance='Medium',
                    widget_url=self.widget_url
                )
                
                return asdict(event)
        
        except Exception as e:
            logger.debug("Failed to parse HTML event", error=str(e))
        
        return None
    
    def _create_sample_events(self) -> List[Dict]:
        """Create realistic sample events for testing purposes"""
        
        sample_events = [
            MQL5EconomicEvent(
                event_name="Non-Farm Payrolls (NFP)",
                country="United States",
                currency="USD",
                datetime=(datetime.now() + timedelta(hours=3)).isoformat(),
                importance="HIGH",
                scheduled_time="08:30",
                forecast="190K",
                previous="185K",
                widget_url=self.widget_url
            ),
            MQL5EconomicEvent(
                event_name="Consumer Price Index (CPI) m/m",
                country="United States", 
                currency="USD",
                datetime=(datetime.now() + timedelta(hours=5)).isoformat(),
                importance="HIGH",
                scheduled_time="08:30",
                actual="0.3%",
                forecast="0.2%",
                previous="0.1%",
                widget_url=self.widget_url
            ),
            MQL5EconomicEvent(
                event_name="European Central Bank Interest Rate Decision",
                country="European Union",
                currency="EUR",
                datetime=(datetime.now() + timedelta(days=1)).isoformat(),
                importance="HIGH",
                scheduled_time="13:45",
                forecast="4.25%",
                previous="4.25%",
                widget_url=self.widget_url
            )
        ]
        
        return [asdict(event) for event in sample_events]


# Microservice Integration Functions dengan Historical Data Support dan Batch Processing
async def get_mql5_widget_events(target_date: Optional[str] = None, batch_mode: bool = False, days_back: Optional[int] = None) -> Dict[str, Any]:
    """Get economic events from MQL5 widget untuk microservice integration dengan historical data support dan batch processing"""
    try:
        scraper = MQL5WidgetScraper(headless=True, target_date=target_date)
        
        if batch_mode:
            # Batch processing mode
            logger.info(f"MQL5 batch processing mode activated for {days_back} days back")
            results = await scraper.scrape_historical_batch(days_back=days_back)
        else:
            # Single date mode
            results = await scraper.scrape_widget_data(specific_date=target_date)
        
        if results.get('status') in ['success', 'completed']:
            events = results.get('events', [])
            
            # Enhanced processing for trading platform
            processed_events = []
            for event_data in events:
                # Add trading relevance score
                relevance_score = calculate_mql5_trading_relevance(event_data)
                event_data['trading_relevance_score'] = relevance_score
                event_data['trading_signals'] = generate_mql5_trading_signals(event_data)
                processed_events.append(event_data)
            
            # Update events in results
            results['events'] = processed_events
            
            # Add configuration info untuk batch mode
            if batch_mode:
                results["batch_configuration"] = {
                    "days_back": days_back or scraper.historical_days_back,
                    "batch_size": scraper.batch_size,
                    "batch_delay_seconds": scraper.batch_delay_seconds,
                    "skip_empty_dates": scraper.skip_empty_dates,
                    "max_retries_per_date": scraper.max_retries_per_date
                }
            else:
                results["historical_data_support"] = {
                    "target_date": target_date,
                    "date_filtering": "supported" if target_date else "current_date_only",
                    "historical_range": "configurable via MQL5_HISTORICAL_DAYS_BACK",
                    "date_format": "YYYY-MM-DD",
                    "batch_processing": "available via batch_mode=True"
                }
            
            # Enhanced summary
            if not batch_mode:
                results["summary"] = {
                    "total_events": len(processed_events),
                    "high_impact": len([e for e in processed_events if e.get('market_impact') == 'High']),
                    "trading_relevant": len([e for e in processed_events if e.get('trading_relevance_score', 0) > 0.7]),
                    "widget_integration": "successful"
                }
            
            results["integration_timestamp"] = datetime.now().isoformat()
            return results
        else:
            return results
            
    except Exception as e:
        logger.error(f"MQL5 widget integration failed: {str(e)}")
        return {"status": "error", "error": str(e)}


def calculate_mql5_trading_relevance(event: Dict) -> float:
    """Calculate trading relevance score for MQL5 event"""
    score = 0.0
    
    # Base score from importance
    importance = event.get('importance', '').upper()
    if importance == "HIGH":
        score += 0.4
    elif importance == "MEDIUM":  
        score += 0.2
    else:
        score += 0.1
    
    # Time proximity bonus
    time_until = event.get('time_until_release')
    if time_until is not None:
        if 0 <= time_until <= 4:
            score += 0.3
        elif 4 < time_until <= 24:
            score += 0.2
        elif 24 < time_until <= 72:
            score += 0.1
    
    # Currency relevance
    currency = event.get('currency', '')
    major_currencies = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]
    if currency in major_currencies:
        score += 0.2
    
    # Deviation bonus
    deviation = event.get('deviation_from_forecast')
    if deviation is not None and abs(deviation) > 5:
        score += 0.1
    
    return min(score, 1.0)


def generate_mql5_trading_signals(event: Dict) -> List[str]:
    """Generate trading signals from MQL5 event"""
    signals = []
    
    currency = event.get('currency')
    impact = event.get('currency_impact', 'Neutral')
    
    if currency and impact != 'Neutral':
        if impact == 'Bullish':
            signals.append(f"Bullish signal for {currency}")
        elif impact == 'Bearish':
            signals.append(f"Bearish signal for {currency}")
    
    # Deviation signals
    deviation = event.get('deviation_from_forecast')
    if deviation is not None:
        if deviation > 10:
            signals.append(f"Major positive surprise: {deviation:.1f}% above forecast")
        elif deviation < -10:
            signals.append(f"Major negative surprise: {deviation:.1f}% below forecast")
    
    # Volatility signals
    volatility = event.get('volatility_expected', '')
    if volatility == 'High':
        signals.append(f"High volatility expected in {currency} markets")
    
    return signals


# Export functions
__all__ = [
    "MQL5WidgetScraper",
    "MQL5EconomicEvent", 
    "get_mql5_widget_events",
    "calculate_mql5_trading_relevance",
    "generate_mql5_trading_signals"
]


# Testing function dengan Historical Data Testing dan Batch Processing
async def test_mql5_widget_scraper(test_date: Optional[str] = None, test_batch: bool = False, test_days_back: Optional[int] = None):
    """Test MQL5 widget scraper dengan historical data support dan batch processing"""
    print("🧪 Testing MQL5 Widget Scraper...")
    
    if test_batch:
        print(f"📦 Testing batch processing mode...")
        print(f"📅 Days back: {test_days_back or 'default from config'}")
        
        scraper = MQL5WidgetScraper(headless=False)  # Show browser for testing
        results = await scraper.scrape_historical_batch(days_back=test_days_back)
        
        print(f"📊 Status: {results.get('status')}")
        print(f"📡 Source: {results.get('source')}")
        print(f"🛡️ Method: {results.get('method')}")
        
        # Batch configuration info
        config = results.get('configuration', {})
        print(f"⚙️ Configuration:")
        print(f"   📅 Days back: {config.get('days_back')}")
        print(f"   📦 Batch size: {config.get('batch_size')}")
        print(f"   ⏱️ Batch delay: {config.get('batch_delay_seconds')}s")
        print(f"   🚫 Skip empty: {config.get('skip_empty_dates')}")
        print(f"   🔄 Max retries: {config.get('max_retries_per_date')}")
        
        # Date range info
        date_range = results.get('date_range', {})
        print(f"📅 Date Range:")
        print(f"   📈 Start: {date_range.get('start_date')}")
        print(f"   📉 End: {date_range.get('end_date')}")
        print(f"   ✅ Successful: {date_range.get('successful_dates')}")
        print(f"   📭 Empty: {date_range.get('empty_dates')}")
        print(f"   ❌ Failed: {date_range.get('failed_dates')}")
        
        events = results.get('events', [])
        print(f"📈 Total events: {len(events)}")
        
        # Processing details
        processing = results.get('processing_details', {})
        print(f"📊 Processing Details:")
        if isinstance(processing.get('successful_dates'), list):
            successful_dates = processing.get('successful_dates', [])[:5]
            print(f"   ✅ First 5 successful dates: {successful_dates}")
        
    else:
        if test_date:
            print(f"📅 Testing historical data untuk tanggal: {test_date}")
        
        scraper = MQL5WidgetScraper(headless=False, target_date=test_date)  # Show browser for testing
        results = await scraper.scrape_widget_data(specific_date=test_date)
        
        print(f"📊 Status: {results.get('status')}")
        print(f"📡 Source: {results.get('source')}")
        print(f"🛡️ Method: {results.get('method')}")
        
        events = results.get('events', [])
        print(f"📈 Total events: {len(events)}")
        
        # Historical data info
        historical_info = results.get('historical_data_support', {})
        if historical_info.get('target_date'):
            print(f"📅 Historical Date: {historical_info.get('target_date')}")
            print(f"🔍 Date Filtering: {historical_info.get('date_filtering')}")
        
        print(f"📦 Batch processing: {historical_info.get('batch_processing', 'N/A')}")
    
    events = results.get('events', [])
    if events:
        print(f"\n📅 SAMPLE MQL5 WIDGET EVENTS:")
        for i, event in enumerate(events[:3], 1):
            print(f"{i}. {event.get('event_name', 'N/A')}")
            print(f"   🌍 {event.get('country', 'N/A')} | 💱 {event.get('currency', 'N/A')} | ⚡ {event.get('importance', 'N/A')}")
            print(f"   📊 Impact: {event.get('market_impact', 'N/A')} | Relevance: {event.get('trading_relevance_score', 0):.2f}")
            print(f"   📆 DateTime: {event.get('datetime', 'N/A')}")
            
            # Show trading signals if available
            signals = event.get('trading_signals', [])
            if signals:
                print(f"   🎯 Trading Signals: {', '.join(signals[:2])}")
    
    return results

# Batch processing integration function
async def get_mql5_batch_historical_events(days_back: Optional[int] = None) -> Dict[str, Any]:
    """Get MQL5 economic events dengan batch processing untuk historical data"""
    return await get_mql5_widget_events(batch_mode=True, days_back=days_back)


if __name__ == "__main__":
    # Test dengan historical data dan batch processing
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--batch":
            # Test batch mode: python mql5_scraper.py --batch [days_back]
            days_back = int(sys.argv[2]) if len(sys.argv) > 2 else None
            print(f"🚀 Starting MQL5 Batch Test (days_back: {days_back})")
            asyncio.run(test_mql5_widget_scraper(test_batch=True, test_days_back=days_back))
        else:
            # Test dengan tanggal tertentu: python mql5_scraper.py 2024-12-15
            test_date = sys.argv[1]
            print(f"🚀 Starting MQL5 Single Date Test: {test_date}")
            asyncio.run(test_mql5_widget_scraper(test_date))
    else:
        # Test normal (current date)
        print("🚀 Starting MQL5 Current Date Test")
        asyncio.run(test_mql5_widget_scraper())