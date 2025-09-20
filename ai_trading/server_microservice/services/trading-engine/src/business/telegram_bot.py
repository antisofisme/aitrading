"""
Telegram Bot Integration - Migrated from server_side for Trading-Engine Service
Advanced Telegram bot for trading notifications, alerts, and interactive commands
"""

import asyncio
import json
import io
import base64
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import threading
import time
import uuid
from collections import deque, defaultdict
import re

# Local infrastructure integration
from ...shared.infrastructure.core.logger_core import get_logger
from ...shared.infrastructure.core.config_core import get_config
from ...shared.infrastructure.core.error_core import get_error_handler
from ...shared.infrastructure.core.performance_core import get_performance_tracker
from ...shared.infrastructure.core.cache_core import CoreCache

# Initialize local infrastructure components
logger = get_logger("trading-engine", "telegram_bot")
config = get_config("trading-engine")
error_handler = get_error_handler("trading-engine")
performance_tracker = get_performance_tracker("trading-engine")
cache = CoreCache("trading-engine")

# Telegram bot imports with fallback
try:
    import telegram
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("⚠️ Telegram library not available, bot will run in mock mode")
    
    # Mock telegram classes for graceful degradation
    class MockUpdate:
        def __init__(self):
            self.message = None
            self.callback_query = None
            self.effective_user = None
    
    class MockContextTypes:
        class DEFAULT_TYPE:
            pass
    
    class MockInlineKeyboardButton:
        def __init__(self, text, callback_data=None):
            self.text = text
            self.callback_data = callback_data
    
    class MockInlineKeyboardMarkup:
        def __init__(self, keyboard):
            self.keyboard = keyboard
    
    class MockParseMode:
        MARKDOWN = "Markdown"
        HTML = "HTML"
    
    # Set mock objects
    Update = MockUpdate
    ContextTypes = MockContextTypes
    InlineKeyboardButton = MockInlineKeyboardButton
    InlineKeyboardMarkup = MockInlineKeyboardMarkup
    ParseMode = MockParseMode

# Visualization imports with fallback
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    import numpy as np
    import pandas as pd
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logger.warning("⚠️ Visualization libraries not available, charts disabled")
    
    # Mock visualization for graceful degradation
    import random
    import math
    
    class MockFigure:
        def __init__(self, figsize=(10, 6)):
            self.figsize = figsize
        
        def add_subplot(self, *args):
            return MockAxes()
        
        def savefig(self, buffer, *args, **kwargs):
            # Generate simple mock chart data
            buffer.write(b"mock chart data")

    class MockAxes:
        def plot(self, *args, **kwargs): pass
        def set_title(self, title): pass
        def set_xlabel(self, label): pass
        def set_ylabel(self, label): pass
        def grid(self, *args, **kwargs): pass
        def legend(self, *args, **kwargs): pass

    Figure = MockFigure
    plt = type('MockPlt', (), {
        'subplots': lambda figsize=(10, 6): (MockFigure(figsize), MockAxes()),
        'close': lambda fig: None
    })()

# Import core trading classes from local modules
try:
    from .strategy_executor import TradingSignal, StrategyPerformance
    from .risk_manager import RiskMetrics
    from .performance_analytics import PerformanceReport, TradingPerformanceAnalytics
except ImportError:
    # Fallback if imports fail
    logger.warning("⚠️ Some trading core modules not available for Telegram bot")


class AlertSeverity(Enum):
    """Alert severity levels for Telegram notifications"""
    INFO = "ℹ️"
    WARNING = "⚠️"
    ERROR = "❌"
    CRITICAL = "🚨"
    SUCCESS = "✅"
    SIGNAL = "📊"
    TRADE = "💰"
    PATTERN = "🧠"


class UserPermission(Enum):
    """User permission levels"""
    VIEWER = "viewer"           # View only
    TRADER = "trader"          # Can execute trades
    ANALYST = "analyst"        # Can run analysis
    ADMIN = "admin"           # Full access
    OWNER = "owner"           # System owner


class CommandCategory(Enum):
    """Command categories for better organization"""
    GENERAL = "📋 General"
    TRADING = "💰 Trading"
    ANALYSIS = "📊 Analysis"
    PERFORMANCE = "📈 Performance"
    SETTINGS = "⚙️ Settings"
    ADMIN = "👑 Admin"


@dataclass
class TelegramBotConfig:
    """Telegram bot configuration"""
    # Bot Settings
    bot_token: str
    webhook_url: Optional[str] = None
    polling_mode: bool = True
    
    # User Management
    authorized_users: List[int] = None  # User IDs
    user_permissions: Dict[int, UserPermission] = None
    admin_users: List[int] = None
    
    # Alert Settings
    enable_alerts: bool = True
    alert_frequency_minutes: int = 5
    max_alerts_per_hour: int = 20
    alert_priority_threshold: AlertSeverity = AlertSeverity.WARNING
    
    # Trading Integration
    enable_trading_commands: bool = True
    require_confirmation: bool = True
    max_position_size: float = 1.0
    
    # Visualization Settings
    enable_charts: bool = True
    chart_width: int = 1200
    chart_height: int = 800
    chart_dpi: int = 100
    
    # Language and Formatting
    language: str = "en"
    timezone: str = "UTC"
    number_format: str = "%.4f"
    
    # Performance Settings
    command_timeout_seconds: int = 30
    max_concurrent_requests: int = 10
    enable_caching: bool = True


@dataclass
class UserSession:
    """User session data"""
    user_id: int
    username: str
    first_name: str
    last_name: Optional[str]
    permission_level: UserPermission
    
    # Session State
    last_activity: datetime
    current_menu: Optional[str] = None
    awaiting_input: Optional[str] = None
    session_data: Dict[str, Any] = None
    
    # Usage Statistics
    commands_used: int = 0
    alerts_received: int = 0
    trades_executed: int = 0


@dataclass
class TradingAlert:
    """Trading alert for Telegram notification"""
    alert_id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    
    # Alert Context
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    signal_type: Optional[str] = None
    confidence: Optional[float] = None
    
    # Action Buttons
    action_buttons: List[Dict[str, str]] = None
    expires_at: Optional[datetime] = None
    
    # Visualization
    chart_data: Optional[bytes] = None
    chart_caption: Optional[str] = None


class TelegramTradingBot:
    """
    Telegram Trading Bot for Trading-Engine Service
    
    Responsibilities:
    - Real-time trading notifications and alerts
    - Interactive trading commands and menus
    - Performance reporting and analytics
    - User management and permissions
    - Chart generation and visualization
    """
    
    def __init__(self, config: TelegramBotConfig):
        """Initialize Telegram Trading Bot with local infrastructure"""
        self.config = config
        self.logger = get_logger("trading-engine", "telegram_bot")
        
        # Bot Application
        self.application: Optional[Application] = None
        self.is_running = False
        
        # User Management
        self.user_sessions: Dict[int, UserSession] = {}
        self.authorized_users = set(config.authorized_users or [])
        self.user_permissions = config.user_permissions or {}
        
        # Alert System
        self.alert_queue: deque = deque(maxlen=1000)
        self.user_alert_counts: Dict[int, int] = defaultdict(int)
        self.last_alert_reset = datetime.now()
        
        # Performance Monitoring
        self.metrics = {
            "messages_sent": 0,
            "commands_processed": 0,
            "alerts_sent": 0,
            "errors_encountered": 0,
            "avg_response_time_ms": 0.0
        }
        
        # Command handlers
        self.command_stats: Dict[str, int] = defaultdict(int)
        self.response_times: Dict[str, List[float]] = defaultdict(list)
        
        # Threading
        self.alert_thread: Optional[threading.Thread] = None
        self.bot_lock = threading.Lock()
        
        self.logger.info("📱 Telegram Trading Bot initialized")
    
    async def initialize(self) -> bool:
        """Initialize the Telegram bot"""
        try:
            if not TELEGRAM_AVAILABLE:
                self.logger.error("❌ Telegram library not available for bot initialization")
                return False
            
            if not self.config.bot_token:
                self.logger.error("❌ Bot token not provided for initialization")
                return False
            
            # Create application
            self.application = Application.builder().token(self.config.bot_token).build()
            
            # Register command handlers
            await self._register_command_handlers()
            
            # Register callback handlers
            await self._register_callback_handlers()
            
            # Start alert system if enabled
            if self.config.enable_alerts:
                await self._start_alert_system()
            
            self.logger.info("🚀 Telegram Trading Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Telegram bot: {e}")
            return False
    
    async def start_bot(self) -> None:
        """Start the Telegram bot"""
        try:
            if not self.application:
                raise RuntimeError("Bot not initialized")
            
            self.is_running = True
            
            if self.config.polling_mode:
                self.logger.info("🤖 Starting Telegram bot in polling mode")
                await self.application.run_polling(
                    timeout=30,
                    pool_timeout=10
                )
            else:
                self.logger.info("🤖 Starting Telegram bot in webhook mode")
                await self.application.run_webhook(
                    webhook_url=self.config.webhook_url,
                    listen="0.0.0.0",
                    port=8443
                )
            
        except Exception as e:
            self.is_running = False
            self.logger.error(f"❌ Failed to start Telegram bot: {e}")
    
    async def stop_bot(self) -> None:
        """Stop the Telegram bot"""
        try:
            self.is_running = False
            
            if self.application:
                await self.application.stop()
            
            # Stop alert system
            if self.alert_thread and self.alert_thread.is_alive():
                self.alert_thread.join(timeout=5)
            
            self.logger.info("🛑 Telegram bot stopped gracefully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to stop Telegram bot: {e}")
    
    async def send_alert(self, alert: TradingAlert, target_users: Optional[List[int]] = None) -> None:
        """Send trading alert to users"""
        try:
            if not self.is_running or not self.application:
                self.logger.warning("Alert skipped: bot not running")
                return
            
            # Determine target users
            if target_users is None:
                target_users = list(self.authorized_users)
            
            # Format alert message
            message = self._format_alert_message(alert)
            
            # Create inline keyboard if action buttons exist
            reply_markup = None
            if alert.action_buttons:
                keyboard = []
                for button in alert.action_buttons:
                    keyboard.append([InlineKeyboardButton(
                        button.get('text', 'Action'),
                        callback_data=button.get('callback_data', 'no_action')
                    )])
                reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send to target users
            for user_id in target_users:
                try:
                    # Check alert rate limits
                    if not self._check_alert_rate_limit(user_id):
                        continue
                    
                    # Send chart if available
                    if alert.chart_data and VISUALIZATION_AVAILABLE:
                        await self.application.bot.send_photo(
                            chat_id=user_id,
                            photo=io.BytesIO(alert.chart_data),
                            caption=message,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=reply_markup
                        )
                    else:
                        await self.application.bot.send_message(
                            chat_id=user_id,
                            text=message,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=reply_markup,
                            disable_web_page_preview=True
                        )
                    
                    # Update user stats
                    if user_id in self.user_sessions:
                        self.user_sessions[user_id].alerts_received += 1
                    
                    self.user_alert_counts[user_id] += 1
                    self.metrics["alerts_sent"] += 1
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to send alert to user {user_id}: {e}")
            
            # Store alert in queue
            self.alert_queue.append(alert)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send alert: {e}")
            self.metrics["errors_encountered"] += 1
    
    async def send_trading_notification(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        symbol: Optional[str] = None,
        action_buttons: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """Send trading notification (convenience method)"""
        alert = TradingAlert(
            alert_id=str(uuid.uuid4()),
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(),
            symbol=symbol,
            action_buttons=action_buttons
        )
        
        await self.send_alert(alert)
    
    async def send_performance_report(self, report_data: Dict[str, Any], user_id: Optional[int] = None) -> None:
        """Send performance report to user(s)"""
        try:
            # Format performance report
            message = self._format_performance_report(report_data)
            
            # Determine target users
            target_users = [user_id] if user_id else list(self.authorized_users)
            
            for uid in target_users:
                try:
                    await self.application.bot.send_message(
                        chat_id=uid,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True
                    )
                    
                    self.metrics["messages_sent"] += 1
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to send performance report to user {uid}: {e}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send performance report: {e}")
    
    # Command Handler Registration
    async def _register_command_handlers(self) -> None:
        """Register all command handlers"""
        try:
            # General Commands
            self.application.add_handler(CommandHandler("start", self._handle_start))
            self.application.add_handler(CommandHandler("help", self._handle_help))
            self.application.add_handler(CommandHandler("menu", self._handle_menu))
            self.application.add_handler(CommandHandler("status", self._handle_status))
            
            # Trading Commands
            self.application.add_handler(CommandHandler("balance", self._handle_balance))
            self.application.add_handler(CommandHandler("positions", self._handle_positions))
            self.application.add_handler(CommandHandler("signals", self._handle_signals))
            self.application.add_handler(CommandHandler("performance", self._handle_performance))
            
            # Analysis Commands
            self.application.add_handler(CommandHandler("analyze", self._handle_analyze))
            self.application.add_handler(CommandHandler("chart", self._handle_chart))
            
            # Settings Commands
            self.application.add_handler(CommandHandler("alerts", self._handle_alert_settings))
            self.application.add_handler(CommandHandler("settings", self._handle_settings))
            
            # Message handlers
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            
            self.logger.info("✅ Command handlers registered")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to register command handlers: {e}")
    
    async def _register_callback_handlers(self) -> None:
        """Register callback query handlers"""
        try:
            self.application.add_handler(CallbackQueryHandler(self._handle_callback_query))
            self.logger.info("✅ Callback handlers registered")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to register callback handlers: {e}")
    
    # Command Handler Implementations
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        start_time = time.time()
        
        try:
            user = update.effective_user
            
            # Check authorization
            if not self._is_user_authorized(user.id):
                await update.message.reply_text(
                    "❌ You are not authorized to use this bot.\n"
                    "Please contact the administrator for access."
                )
                return
            
            # Create or update user session
            await self._create_user_session(user)
            
            welcome_message = (
                f"🤖 *Welcome to Trading Engine Bot*\n\n"
                f"Hello {user.first_name}! 👋\n\n"
                f"🎯 *Your Access Level:* {self.user_permissions.get(user.id, UserPermission.VIEWER).value.title()}\n\n"
                f"📋 *Available Features:*\n"
                f"• 💰 Trading Status & Signals\n"
                f"• 📊 Real-time Performance Analytics\n"
                f"• 📈 Interactive Charts\n"
                f"• ⚠️ Smart Alerts & Notifications\n"
                f"• 🎯 Strategy Management\n\n"
                f"Type /help for command list or /menu for interactive menu.\n\n"
                f"🚀 *Ready to manage your trading strategies!*"
            )
            
            await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
            
            self.command_stats["start"] += 1
            self.metrics["commands_processed"] += 1
            
        except Exception as e:
            self.logger.error(f"❌ Failed to handle /start command: {e}")
            await update.message.reply_text("❌ Error processing command")
        
        finally:
            # Record response time
            response_time = (time.time() - start_time) * 1000
            self.response_times["start"].append(response_time)
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        try:
            user_id = update.effective_user.id
            permission = self.user_permissions.get(user_id, UserPermission.VIEWER)
            
            help_text = "📋 *Available Commands*\n\n"
            
            # General Commands
            help_text += "🔹 *General Commands:*\n"
            help_text += "• `/start` - Start the bot\n"
            help_text += "• `/help` - Show this help\n"
            help_text += "• `/menu` - Interactive menu\n"
            help_text += "• `/status` - System status\n\n"
            
            # Trading Commands
            help_text += "🔹 *Trading Commands:*\n"
            help_text += "• `/balance` - Account balance\n"
            help_text += "• `/positions` - Current positions\n"
            help_text += "• `/signals` - Trading signals\n"
            help_text += "• `/performance` - Performance metrics\n\n"
            
            # Analysis Commands
            help_text += "🔹 *Analysis Commands:*\n"
            help_text += "• `/analyze <symbol>` - Market analysis\n"
            help_text += "• `/chart <symbol>` - Price chart\n\n"
            
            # Settings Commands
            help_text += "🔹 *Settings Commands:*\n"
            help_text += "• `/alerts` - Alert settings\n"
            help_text += "• `/settings` - Bot settings\n\n"
            
            help_text += "💡 *Tip:* Use /menu for an interactive interface!"
            
            await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
            
            self.command_stats["help"] += 1
            self.metrics["commands_processed"] += 1
            
        except Exception as e:
            self.logger.error(f"❌ Failed to handle /help command: {e}")
            await update.message.reply_text("❌ Error processing command")
    
    async def _handle_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /menu command - show interactive menu"""
        try:
            user_id = update.effective_user.id
            permission = self.user_permissions.get(user_id, UserPermission.VIEWER)
            
            keyboard = []
            
            # General options
            keyboard.append([
                InlineKeyboardButton("📊 System Status", callback_data="menu_status"),
                InlineKeyboardButton("📈 Performance", callback_data="menu_performance")
            ])
            
            # Trading options
            keyboard.append([
                InlineKeyboardButton("💰 Balance", callback_data="menu_balance"),
                InlineKeyboardButton("🎯 Signals", callback_data="menu_signals")
            ])
            
            # Analysis options
            keyboard.append([
                InlineKeyboardButton("📊 Analysis", callback_data="menu_analysis"),
                InlineKeyboardButton("📈 Charts", callback_data="menu_charts")
            ])
            
            # Settings
            keyboard.append([
                InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings"),
                InlineKeyboardButton("🔔 Alerts", callback_data="menu_alerts")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            menu_text = (
                "🎛️ *Trading Engine Control Panel*\n\n"
                "Select an option to get started:\n\n"
                f"👤 User: {update.effective_user.first_name}\n"
                f"🔐 Access: {permission.value.title()}\n"
                f"🕐 Time: {datetime.now().strftime('%H:%M:%S UTC')}"
            )
            
            await update.message.reply_text(
                menu_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
            self.command_stats["menu"] += 1
            self.metrics["commands_processed"] += 1
            
        except Exception as e:
            self.logger.error(f"❌ Failed to handle /menu command: {e}")
            await update.message.reply_text("❌ Error processing command")
    
    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command"""
        try:
            status_text = "🔍 *Trading Engine Status*\n\n"
            
            # System status
            status_text += f"🤖 Bot Status: {'✅ Running' if self.is_running else '❌ Stopped'}\n"
            status_text += f"📱 Telegram Available: {'✅ Yes' if TELEGRAM_AVAILABLE else '❌ No'}\n"
            status_text += f"📊 Charts Available: {'✅ Yes' if VISUALIZATION_AVAILABLE else '❌ No'}\n"
            
            # Bot statistics
            status_text += f"\n📊 *Bot Statistics:*\n"
            status_text += f"• Active Users: {len(self.user_sessions)}\n"
            status_text += f"• Commands Processed: {self.metrics['commands_processed']}\n"
            status_text += f"• Alerts Sent: {self.metrics['alerts_sent']}\n"
            status_text += f"• Messages Sent: {self.metrics['messages_sent']}\n"
            
            # Performance metrics
            if self.response_times:
                avg_response = sum(sum(times) for times in self.response_times.values()) / sum(len(times) for times in self.response_times.values())
                status_text += f"• Avg Response Time: {avg_response:.1f}ms\n"
            
            await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)
            
            self.command_stats["status"] += 1
            self.metrics["commands_processed"] += 1
            
        except Exception as e:
            self.logger.error(f"❌ Failed to handle /status command: {e}")
            await update.message.reply_text("❌ Error processing command")
    
    async def _handle_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /performance command"""
        try:
            # Get performance data (placeholder)
            performance_text = "📈 *Trading Performance Summary*\n\n"
            performance_text += "📊 *Key Metrics:*\n"
            performance_text += "• Total Return: +12.5%\n"
            performance_text += "• Win Rate: 68.2%\n"
            performance_text += "• Sharpe Ratio: 1.85\n"
            performance_text += "• Max Drawdown: -3.2%\n"
            performance_text += "• Total Trades: 145\n\n"
            
            performance_text += "🎯 *Recent Performance:*\n"
            performance_text += "• Last 7 days: +2.1%\n"
            performance_text += "• Last 30 days: +7.8%\n"
            performance_text += "• This month: +5.4%\n\n"
            
            performance_text += "💡 Use /chart for visual performance analysis"
            
            await update.message.reply_text(performance_text, parse_mode=ParseMode.MARKDOWN)
            
            self.command_stats["performance"] += 1
            self.metrics["commands_processed"] += 1
            
        except Exception as e:
            self.logger.error(f"❌ Failed to handle /performance command: {e}")
            await update.message.reply_text("❌ Error processing command")
    
    async def _handle_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /chart command"""
        try:
            if not VISUALIZATION_AVAILABLE:
                await update.message.reply_text("❌ Chart generation not available")
                return
            
            # Parse symbol from command
            symbol = "EURUSD"  # Default
            if context.args:
                symbol = context.args[0].upper()
            
            # Generate chart
            chart_data = await self._generate_performance_chart(symbol)
            
            if chart_data:
                await update.message.reply_photo(
                    photo=io.BytesIO(chart_data),
                    caption=f"📊 *{symbol} Performance Chart*\n\nGenerated at {datetime.now().strftime('%H:%M:%S UTC')}",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(f"❌ Could not generate chart for {symbol}")
            
            self.command_stats["chart"] += 1
            self.metrics["commands_processed"] += 1
            
        except Exception as e:
            self.logger.error(f"❌ Failed to handle /chart command: {e}")
            await update.message.reply_text("❌ Error processing command")
    
    # Helper Methods
    def _is_user_authorized(self, user_id: int) -> bool:
        """Check if user is authorized"""
        return user_id in self.authorized_users or len(self.authorized_users) == 0
    
    def _check_trading_permission(self, user_id: int) -> bool:
        """Check if user has trading permission"""
        permission = self.user_permissions.get(user_id, UserPermission.VIEWER)
        return permission in [UserPermission.TRADER, UserPermission.ADMIN, UserPermission.OWNER]
    
    async def _create_user_session(self, user) -> None:
        """Create or update user session"""
        try:
            permission = self.user_permissions.get(user.id, UserPermission.VIEWER)
            
            if user.id in self.user_sessions:
                # Update existing session
                session = self.user_sessions[user.id]
                session.last_activity = datetime.now()
                session.commands_used += 1
            else:
                # Create new session
                session = UserSession(
                    user_id=user.id,
                    username=user.username or "",
                    first_name=user.first_name or "",
                    last_name=user.last_name,
                    permission_level=permission,
                    last_activity=datetime.now(),
                    session_data={}
                )
                self.user_sessions[user.id] = session
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create user session: {e}")
    
    def _format_alert_message(self, alert: TradingAlert) -> str:
        """Format alert message for Telegram"""
        try:
            # Severity emoji
            severity_emoji = alert.severity.value
            
            # Base message
            message = f"{severity_emoji} *{alert.title}*\n\n"
            message += f"{alert.message}\n\n"
            
            # Add context if available
            if alert.symbol:
                message += f"📊 Symbol: `{alert.symbol}`\n"
            
            if alert.timeframe:
                message += f"⏱️ Timeframe: `{alert.timeframe}`\n"
            
            if alert.confidence:
                message += f"🎯 Confidence: `{alert.confidence:.1%}`\n"
            
            # Add timestamp
            message += f"🕐 Time: `{alert.timestamp.strftime('%H:%M:%S UTC')}`\n"
            
            # Add expiration if set
            if alert.expires_at:
                message += f"⏰ Expires: `{alert.expires_at.strftime('%H:%M:%S UTC')}`\n"
            
            return message
            
        except Exception as e:
            self.logger.error(f"❌ Failed to format alert message: {e}")
            return f"{alert.severity.value} {alert.title}\n{alert.message}"
    
    def _format_performance_report(self, report_data: Dict[str, Any]) -> str:
        """Format performance report for Telegram"""
        try:
            message = "📊 *Performance Report*\n\n"
            
            # Add report data
            for key, value in report_data.items():
                if isinstance(value, float):
                    message += f"• {key}: {value:.2f}\n"
                else:
                    message += f"• {key}: {value}\n"
            
            message += f"\n🕐 Generated: {datetime.now().strftime('%H:%M:%S UTC')}"
            
            return message
            
        except Exception as e:
            self.logger.error(f"❌ Failed to format performance report: {e}")
            return "📊 Performance Report\n\nError formatting report data"
    
    def _check_alert_rate_limit(self, user_id: int) -> bool:
        """Check if user hasn't exceeded alert rate limit"""
        try:
            # Reset hourly counters
            now = datetime.now()
            if (now - self.last_alert_reset).total_seconds() >= 3600:
                self.user_alert_counts.clear()
                self.last_alert_reset = now
            
            # Check user's alert count
            user_count = self.user_alert_counts.get(user_id, 0)
            return user_count < self.config.max_alerts_per_hour
            
        except Exception as e:
            self.logger.error(f"❌ Failed to check alert rate limit: {e}")
            return True
    
    async def _generate_performance_chart(self, symbol: str) -> Optional[bytes]:
        """Generate performance chart"""
        try:
            if not VISUALIZATION_AVAILABLE:
                return None
            
            # Generate sample performance data
            import random
            dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
            returns = [random.uniform(-0.02, 0.03) for _ in range(30)]
            cumulative_returns = []
            cum_return = 1.0
            for ret in returns:
                cum_return *= (1 + ret)
                cumulative_returns.append((cum_return - 1) * 100)
            
            # Create chart
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.plot(dates, cumulative_returns, linewidth=2, color='blue', label=f'{symbol} Performance')
            ax.set_title(f'{symbol} Performance Chart', fontsize=16, fontweight='bold')
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Cumulative Return (%)', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # Save to bytes
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=self.config.chart_dpi, bbox_inches='tight')
            buffer.seek(0)
            chart_data = buffer.getvalue()
            plt.close(fig)
            
            return chart_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate performance chart: {e}")
            return None
    
    # Placeholder implementations for other handlers
    async def _handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        if callback_data.startswith("menu_"):
            action = callback_data.replace("menu_", "")
            await self._handle_menu_action(action, query, context)
    
    async def _handle_menu_action(self, action: str, query, context) -> None:
        """Handle menu action callbacks"""
        try:
            if action == "status":
                await query.edit_message_text("📊 System Status: All systems operational")
            elif action == "performance":
                await query.edit_message_text("📈 Performance: Total return +12.5%, Win rate 68.2%")
            elif action == "balance":
                await query.edit_message_text("💰 Account Balance: $10,000.00 (Available: $8,500.00)")
            elif action == "signals":
                await query.edit_message_text("🎯 Active Signals: 3 pending, 2 executed today")
            else:
                await query.edit_message_text(f"🔄 Processing {action}...")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to handle menu action: {e}")
    
    # Additional placeholder methods
    async def _start_alert_system(self): pass
    async def _handle_message(self, update, context): pass
    async def _handle_balance(self, update, context): pass
    async def _handle_positions(self, update, context): pass
    async def _handle_signals(self, update, context): pass
    async def _handle_analyze(self, update, context): pass
    async def _handle_alert_settings(self, update, context): pass
    async def _handle_settings(self, update, context): pass
    
    async def get_bot_metrics(self) -> Dict[str, Any]:
        """Get bot performance metrics"""
        return {
            "metrics": self.metrics,
            "is_running": self.is_running,
            "active_users": len(self.user_sessions),
            "authorized_users": len(self.authorized_users),
            "total_alerts": len(self.alert_queue),
            "command_stats": dict(self.command_stats),
            "telegram_available": TELEGRAM_AVAILABLE,
            "visualization_available": VISUALIZATION_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Save bot state to cache
            bot_state = {
                "metrics": self.metrics,
                "command_stats": dict(self.command_stats),
                "user_sessions_count": len(self.user_sessions),
                "alerts_sent": self.metrics["alerts_sent"]
            }
            await cache.set("telegram_bot_state", bot_state, ttl=86400)
            
            self.logger.info("🧹 Telegram Bot cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Telegram Bot cleanup failed: {e}")


# Export main classes for the Trading-Engine service
__all__ = [
    "TelegramTradingBot",
    "TelegramBotConfig",
    "TradingAlert",
    "UserSession",
    "UserPermission",
    "AlertSeverity",
    "CommandCategory"
]