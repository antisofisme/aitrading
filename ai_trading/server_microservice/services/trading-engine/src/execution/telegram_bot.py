"""
Advanced Telegram Bot for Trading - MICROSERVICE VERSION
Phase 5: Advanced Intelligence & Infrastructure Enhancement
Advanced Telegram bot with trading commands, real-time alerts, and visualization integration
"""

import asyncio
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import threading
import time
import uuid
import io
import base64
from collections import deque, defaultdict
import re

# MICROSERVICE INFRASTRUCTURE INTEGRATION
from ...shared.infrastructure.logging.base_logger import BaseLogger
from ...shared.infrastructure.config.base_config import BaseConfig
from ...shared.infrastructure.error_handling.base_error_handler import BaseErrorHandler
from ...shared.infrastructure.base.base_performance import BasePerformance as BasePerformanceTracker
from ...shared.infrastructure.events.base_event_publisher import BaseEventPublisher

# Enhanced logger with microservice infrastructure
telegram_logger = BaseLogger("trading.telegram_bot", {
    "component": "trading",
    "service": "telegram_bot", 
    "feature": "notification_system"
})

# Maintain backward compatibility
logger = telegram_logger

# Telegram bot imports
try:
    import telegram
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    telegram_logger.warning("python-telegram-bot not available. Telegram notifications disabled.")

# Telegram bot performance metrics
telegram_metrics = {
    "messages_sent": 0,
    "commands_processed": 0,
    "alerts_sent": 0,
    "users_served": 0,
    "errors_encountered": 0,
    "uptime_seconds": 0,
    "avg_response_time_ms": 0,
    "events_published": 0
}


class AlertType(Enum):
    """Telegram alert types"""
    TRADE_SIGNAL = "trade_signal"
    TRADE_EXECUTED = "trade_executed"
    RISK_WARNING = "risk_warning"
    PERFORMANCE_UPDATE = "performance_update"
    SYSTEM_STATUS = "system_status"
    ERROR_ALERT = "error_alert"
    DAILY_SUMMARY = "daily_summary"


class CommandType(Enum):
    """Telegram command types"""
    STATUS = "status"
    PERFORMANCE = "performance"
    POSITIONS = "positions"
    BALANCE = "balance"
    STOP_TRADING = "stop_trading"
    START_TRADING = "start_trading"
    RISK_STATUS = "risk_status"
    HELP = "help"


@dataclass
class TelegramAlert:
    """Telegram alert message"""
    alert_id: str
    alert_type: AlertType
    title: str
    message: str
    priority: str = "normal"  # low, normal, high, critical
    timestamp: datetime = None
    chat_id: Optional[str] = None
    parse_mode: str = "HTML"
    
    def __post_init__(self):
        if self.alert_id is None:
            self.alert_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class TelegramUser:
    """Telegram user information"""
    user_id: str
    username: str
    chat_id: str
    is_authorized: bool = False
    subscription_types: List[AlertType] = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.subscription_types is None:
            self.subscription_types = list(AlertType)
        if self.last_activity is None:
            self.last_activity = datetime.now()


class TradingTelegramBot:
    """
    Advanced Telegram bot for trading notifications and commands with microservice infrastructure
    """
    
    def __init__(self, bot_token: str, authorized_users: List[str] = None):
        """Initialize Telegram bot with microservice infrastructure"""
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot library not available")
        
        self.bot_token = bot_token
        self.authorized_users = set(authorized_users or [])
        
        # Microservice Infrastructure Components
        self.logger = BaseLogger("trading_telegram_bot")
        self.config_manager = BaseConfig()
        self.error_handler = BaseErrorHandler("telegram_bot")
        self.performance_tracker = BasePerformanceTracker("telegram_bot")
        self.event_publisher = BaseEventPublisher("telegram_bot")
        
        # Bot state
        self.application = None
        self.bot = None
        self.is_running = False
        self.start_time = datetime.now()
        
        # User management
        self.registered_users = {}
        self.user_subscriptions = defaultdict(set)
        
        # Alert queue and history
        self.alert_queue = deque()
        self.alert_history = deque(maxlen=1000)
        
        # Performance tracking
        self.messages_sent = 0
        self.commands_processed = 0
        self.alerts_sent = 0
        
        self.logger.info("TradingTelegramBot initialized successfully")


    async def initialize(self):
        """Initialize Telegram bot application"""
        try:
            self.logger.info("Initializing Telegram bot")
            
            # Create application
            self.application = Application.builder().token(self.bot_token).build()
            self.bot = self.application.bot
            
            # Register command handlers
            await self._register_handlers()
            
            # Test bot connection
            bot_info = await self.bot.get_me()
            self.logger.info(f"Connected to Telegram bot: {bot_info.username}")
            
            # Load configuration
            bot_config = self.config_manager.get_config("telegram", {
                "update_frequency": "hourly",
                "max_retries": 3,
                "timeout": 30
            })
            
            self.logger.info("Telegram bot initialized successfully")
            
            # Publish initialization event
            await self.event_publisher.publish_event({
                "event_type": "telegram_bot_initialized",
                "bot_username": bot_info.username,
                "authorized_users_count": len(self.authorized_users),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "initialize_telegram_bot")
            self.logger.error(f"Failed to initialize Telegram bot: {error_response}")
            raise


    async def _register_handlers(self):
        """Register command and message handlers"""
        try:
            # Command handlers
            self.application.add_handler(CommandHandler("start", self._handle_start))
            self.application.add_handler(CommandHandler("help", self._handle_help))
            self.application.add_handler(CommandHandler("status", self._handle_status))
            self.application.add_handler(CommandHandler("performance", self._handle_performance))
            self.application.add_handler(CommandHandler("positions", self._handle_positions))
            self.application.add_handler(CommandHandler("balance", self._handle_balance))
            self.application.add_handler(CommandHandler("risk", self._handle_risk_status))
            self.application.add_handler(CommandHandler("stop", self._handle_stop_trading))
            self.application.add_handler(CommandHandler("subscribe", self._handle_subscribe))
            self.application.add_handler(CommandHandler("unsubscribe", self._handle_unsubscribe))
            
            # Callback query handler
            self.application.add_handler(CallbackQueryHandler(self._handle_callback))
            
            # Message handler for text messages
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            
            self.logger.info("Telegram handlers registered successfully")
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "register_telegram_handlers")
            self.logger.error(f"Failed to register handlers: {error_response}")
            raise


    async def start_bot(self):
        """Start the Telegram bot"""
        try:
            if self.is_running:
                self.logger.warning("Telegram bot is already running")
                return
            
            if not self.application:
                await self.initialize()
            
            self.logger.info("Starting Telegram bot...")
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            
            self.is_running = True
            self.start_time = datetime.now()
            
            # Start alert processing
            asyncio.create_task(self._process_alert_queue())
            
            self.logger.info("Telegram bot started successfully")
            
            # Publish start event
            await self.event_publisher.publish_event({
                "event_type": "telegram_bot_started",
                "start_time": self.start_time.isoformat(),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "start_telegram_bot")
            self.logger.error(f"Failed to start Telegram bot: {error_response}")
            raise


    async def stop_bot(self):
        """Stop the Telegram bot"""
        try:
            if not self.is_running:
                self.logger.warning("Telegram bot is not running")
                return
            
            self.logger.info("Stopping Telegram bot...")
            
            self.is_running = False
            
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
            
            self.logger.info("Telegram bot stopped successfully")
            
            # Publish stop event
            await self.event_publisher.publish_event({
                "event_type": "telegram_bot_stopped",
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "stop_telegram_bot")
            self.logger.error(f"Failed to stop Telegram bot: {error_response}")


    async def send_alert(self, alert: TelegramAlert, chat_id: Optional[str] = None):
        """Send alert to Telegram"""
        try:
            if not self.is_running or not self.bot:
                self.logger.warning("Telegram bot not running, queueing alert")
                self.alert_queue.append(alert)
                return
            
            # Determine recipients
            recipients = []
            if chat_id:
                recipients.append(chat_id)
            else:
                # Send to all subscribed users
                for user_id, user in self.registered_users.items():
                    if alert.alert_type in user.subscription_types:
                        recipients.append(user.chat_id)
            
            # Send message to each recipient
            for recipient_chat_id in recipients:
                try:
                    # Format message based on alert type
                    formatted_message = self._format_alert_message(alert)
                    
                    await self.bot.send_message(
                        chat_id=recipient_chat_id,
                        text=formatted_message,
                        parse_mode=alert.parse_mode
                    )
                    
                    self.messages_sent += 1
                    telegram_metrics["messages_sent"] += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to send message to {recipient_chat_id}: {e}")
                    continue
            
            # Store in history
            self.alert_history.append(alert)
            self.alerts_sent += 1
            telegram_metrics["alerts_sent"] += 1
            
            self.logger.info(f"Alert sent to {len(recipients)} recipients: {alert.title}")
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "send_telegram_alert")
            self.logger.error(f"Failed to send alert: {error_response}")


    def _format_alert_message(self, alert: TelegramAlert) -> str:
        """Format alert message for Telegram"""
        try:
            priority_emoji = {
                "low": "🔵",
                "normal": "🟡", 
                "high": "🟠",
                "critical": "🔴"
            }
            
            type_emoji = {
                AlertType.TRADE_SIGNAL: "📈",
                AlertType.TRADE_EXECUTED: "✅",
                AlertType.RISK_WARNING: "⚠️",
                AlertType.PERFORMANCE_UPDATE: "📊",
                AlertType.SYSTEM_STATUS: "🖥️",
                AlertType.ERROR_ALERT: "❌",
                AlertType.DAILY_SUMMARY: "📋"
            }
            
            emoji = type_emoji.get(alert.alert_type, "📢")
            priority = priority_emoji.get(alert.priority, "🟡")
            
            formatted = f"{emoji} {priority} <b>{alert.title}</b>\n\n"
            formatted += f"{alert.message}\n\n"
            formatted += f"<i>Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</i>"
            
            return formatted
            
        except Exception as e:
            self.logger.error(f"Failed to format alert message: {e}")
            return f"Alert: {alert.title}\n{alert.message}"


    async def _process_alert_queue(self):
        """Process queued alerts"""
        while self.is_running:
            try:
                if self.alert_queue and self.bot:
                    alert = self.alert_queue.popleft()
                    await self.send_alert(alert)
                
                await asyncio.sleep(1)  # Process every second
                
            except Exception as e:
                error_response = self.error_handler.handle_error(e, "process_alert_queue")
                self.logger.error(f"Alert queue processing error: {error_response}")
                await asyncio.sleep(5)  # Wait longer on error


    # Command handlers
    async def _handle_start(self, update: Update, context):
        """Handle /start command"""
        try:
            user = update.effective_user
            chat_id = str(update.effective_chat.id)
            
            # Check authorization
            if str(user.id) not in self.authorized_users and user.username not in self.authorized_users:
                await update.message.reply_text("❌ Unauthorized access. Contact administrator.")
                return
            
            # Register user
            telegram_user = TelegramUser(
                user_id=str(user.id),
                username=user.username or "Unknown",
                chat_id=chat_id,
                is_authorized=True
            )
            
            self.registered_users[str(user.id)] = telegram_user
            
            welcome_message = (
                "🤖 <b>Welcome to Trading Bot</b>\n\n"
                "Available commands:\n"
                "/status - Trading system status\n"
                "/performance - Performance metrics\n"
                "/positions - Current positions\n"
                "/balance - Account balance\n"
                "/risk - Risk status\n"
                "/stop - Stop trading\n"
                "/subscribe - Subscribe to alerts\n"
                "/help - Show this help\n\n"
                "You are now subscribed to all alerts."
            )
            
            await update.message.reply_text(welcome_message, parse_mode="HTML")
            
            self.commands_processed += 1
            telegram_metrics["commands_processed"] += 1
            
            self.logger.info(f"User {user.username} started bot")
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "handle_start_command")
            await update.message.reply_text(f"Error: {error_response}")


    async def _handle_help(self, update: Update, context):
        """Handle /help command"""
        try:
            if not self._is_authorized(update.effective_user):
                await update.message.reply_text("❌ Unauthorized access.")
                return
            
            help_message = (
                "🤖 <b>Trading Bot Commands</b>\n\n"
                "<b>Status Commands:</b>\n"
                "/status - System status\n"
                "/performance - Performance metrics\n"
                "/positions - Current positions\n"
                "/balance - Account balance\n"
                "/risk - Risk assessment\n\n"
                "<b>Control Commands:</b>\n"
                "/stop - Emergency stop trading\n"
                "/subscribe [type] - Subscribe to alerts\n"
                "/unsubscribe [type] - Unsubscribe from alerts\n\n"
                "<b>Alert Types:</b>\n"
                "• trade_signal - Trading signals\n"
                "• trade_executed - Executed trades\n"
                "• risk_warning - Risk warnings\n"
                "• performance_update - Performance updates\n"
                "• system_status - System status\n"
                "• daily_summary - Daily summaries"
            )
            
            await update.message.reply_text(help_message, parse_mode="HTML")
            
            self.commands_processed += 1
            telegram_metrics["commands_processed"] += 1
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "handle_help_command")
            await update.message.reply_text(f"Error: {error_response}")


    async def _handle_status(self, update: Update, context):
        """Handle /status command"""
        try:
            if not self._is_authorized(update.effective_user):
                await update.message.reply_text("❌ Unauthorized access.")
                return
            
            # Get system status (placeholder)
            uptime = datetime.now() - self.start_time
            
            status_message = (
                "📊 <b>Trading System Status</b>\n\n"
                f"🟢 <b>Bot Status:</b> Running\n"
                f"⏱️ <b>Uptime:</b> {uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m\n"
                f"📨 <b>Messages Sent:</b> {self.messages_sent}\n"
                f"🚨 <b>Alerts Sent:</b> {self.alerts_sent}\n"
                f"👥 <b>Active Users:</b> {len(self.registered_users)}\n"
                f"📈 <b>Trading Mode:</b> Active\n"
                f"💰 <b>Account Status:</b> Connected\n\n"
                f"<i>Last Updated: {datetime.now().strftime('%H:%M:%S')}</i>"
            )
            
            await update.message.reply_text(status_message, parse_mode="HTML")
            
            self.commands_processed += 1
            telegram_metrics["commands_processed"] += 1
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "handle_status_command")
            await update.message.reply_text(f"Error: {error_response}")


    async def _handle_performance(self, update: Update, context):
        """Handle /performance command"""
        try:
            if not self._is_authorized(update.effective_user):
                await update.message.reply_text("❌ Unauthorized access.")
                return
            
            # Get performance data (placeholder)
            performance_message = (
                "📈 <b>Performance Summary</b>\n\n"
                f"💰 <b>Total P&L:</b> +$1,234.56\n"
                f"📊 <b>Win Rate:</b> 68.5%\n"
                f"📉 <b>Max Drawdown:</b> -5.2%\n"
                f"📈 <b>Sharpe Ratio:</b> 1.45\n"
                f"🎯 <b>Total Trades:</b> 156\n"
                f"✅ <b>Winning Trades:</b> 107\n"
                f"❌ <b>Losing Trades:</b> 49\n"
                f"⏱️ <b>Avg Trade Duration:</b> 2h 15m\n\n"
                f"<i>Period: Last 30 Days</i>"
            )
            
            await update.message.reply_text(performance_message, parse_mode="HTML")
            
            self.commands_processed += 1
            telegram_metrics["commands_processed"] += 1
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "handle_performance_command")
            await update.message.reply_text(f"Error: {error_response}")


    async def _handle_positions(self, update: Update, context):
        """Handle /positions command"""
        try:
            if not self._is_authorized(update.effective_user):
                await update.message.reply_text("❌ Unauthorized access.")
                return
            
            # Get positions data (placeholder)
            positions_message = (
                "📋 <b>Current Positions</b>\n\n"
                "📈 <b>EURUSD</b>\n"
                "  • Direction: Long\n"
                "  • Size: 0.50 lots\n"
                "  • Entry: 1.0850\n"
                "  • Current: 1.0875\n"
                "  • P&L: +$125.00\n\n"
                "📉 <b>GBPUSD</b>\n"
                "  • Direction: Short\n"
                "  • Size: 0.30 lots\n"
                "  • Entry: 1.2650\n"
                "  • Current: 1.2635\n"
                "  • P&L: +$45.00\n\n"
                f"💰 <b>Total Unrealized P&L:</b> +$170.00\n"
                f"📊 <b>Total Exposure:</b> $80,000"
            )
            
            await update.message.reply_text(positions_message, parse_mode="HTML")
            
            self.commands_processed += 1
            telegram_metrics["commands_processed"] += 1
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "handle_positions_command")
            await update.message.reply_text(f"Error: {error_response}")


    async def _handle_balance(self, update: Update, context):
        """Handle /balance command"""
        try:
            if not self._is_authorized(update.effective_user):
                await update.message.reply_text("❌ Unauthorized access.")
                return
            
            # Get balance data (placeholder)
            balance_message = (
                "💰 <b>Account Balance</b>\n\n"
                f"💵 <b>Balance:</b> $10,500.00\n"
                f"💎 <b>Equity:</b> $10,670.00\n"
                f"📊 <b>Margin Used:</b> $2,100.00\n"
                f"🆓 <b>Free Margin:</b> $8,570.00\n"
                f"📈 <b>Margin Level:</b> 508.1%\n\n"
                f"📋 <b>Today's Summary:</b>\n"
                f"  • Realized P&L: +$45.00\n"
                f"  • Unrealized P&L: +$170.00\n"
                f"  • Trades: 3\n"
                f"  • Win Rate: 100%"
            )
            
            await update.message.reply_text(balance_message, parse_mode="HTML")
            
            self.commands_processed += 1
            telegram_metrics["commands_processed"] += 1
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "handle_balance_command")
            await update.message.reply_text(f"Error: {error_response}")


    async def _handle_risk_status(self, update: Update, context):
        """Handle /risk command"""
        try:
            if not self._is_authorized(update.effective_user):
                await update.message.reply_text("❌ Unauthorized access.")
                return
            
            # Get risk data (placeholder)
            risk_message = (
                "🛡️ <b>Risk Assessment</b>\n\n"
                f"📊 <b>Risk Level:</b> 🟢 Low\n"
                f"📉 <b>Current Drawdown:</b> -2.1%\n"
                f"⚠️ <b>Max Drawdown:</b> -5.2%\n"
                f"💰 <b>Portfolio VaR (95%):</b> $850.00\n"
                f"📈 <b>Sharpe Ratio:</b> 1.45\n"
                f"🎯 <b>Position Correlation:</b> 0.35\n\n"
                f"🔧 <b>Risk Controls:</b>\n"
                f"  • Stop Loss: ✅ Active\n"
                f"  • Position Sizing: ✅ Active\n"
                f"  • Correlation Limits: ✅ Active\n"
                f"  • Drawdown Protection: ✅ Active"
            )
            
            await update.message.reply_text(risk_message, parse_mode="HTML")
            
            self.commands_processed += 1
            telegram_metrics["commands_processed"] += 1
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "handle_risk_command")
            await update.message.reply_text(f"Error: {error_response}")


    async def _handle_stop_trading(self, update: Update, context):
        """Handle /stop command"""
        try:
            if not self._is_authorized(update.effective_user):
                await update.message.reply_text("❌ Unauthorized access.")
                return
            
            # Create confirmation keyboard
            keyboard = [
                [InlineKeyboardButton("🛑 CONFIRM STOP", callback_data="confirm_stop")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_stop")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            warning_message = (
                "⚠️ <b>Emergency Stop Trading</b>\n\n"
                "This will:\n"
                "• Stop all automated trading\n"
                "• Close pending orders\n"
                "• Maintain existing positions\n\n"
                "Are you sure you want to proceed?"
            )
            
            await update.message.reply_text(
                warning_message,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            
            self.commands_processed += 1
            telegram_metrics["commands_processed"] += 1
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "handle_stop_command")
            await update.message.reply_text(f"Error: {error_response}")


    async def _handle_subscribe(self, update: Update, context):
        """Handle /subscribe command"""
        try:
            if not self._is_authorized(update.effective_user):
                await update.message.reply_text("❌ Unauthorized access.")
                return
            
            user_id = str(update.effective_user.id)
            
            if context.args:
                alert_type_str = context.args[0].lower()
                try:
                    alert_type = AlertType(alert_type_str)
                    
                    if user_id in self.registered_users:
                        self.registered_users[user_id].subscription_types.append(alert_type)
                        await update.message.reply_text(f"✅ Subscribed to {alert_type.value} alerts")
                    else:
                        await update.message.reply_text("❌ User not registered")
                        
                except ValueError:
                    await update.message.reply_text(f"❌ Invalid alert type: {alert_type_str}")
            else:
                # Show subscription options
                keyboard = []
                for alert_type in AlertType:
                    keyboard.append([InlineKeyboardButton(
                        f"Subscribe to {alert_type.value.replace('_', ' ').title()}",
                        callback_data=f"subscribe_{alert_type.value}"
                    )])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "📢 <b>Choose Alert Types:</b>",
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            
            self.commands_processed += 1
            telegram_metrics["commands_processed"] += 1
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "handle_subscribe_command")
            await update.message.reply_text(f"Error: {error_response}")


    async def _handle_unsubscribe(self, update: Update, context):
        """Handle /unsubscribe command"""
        try:
            if not self._is_authorized(update.effective_user):
                await update.message.reply_text("❌ Unauthorized access.")
                return
            
            user_id = str(update.effective_user.id)
            
            if context.args:
                alert_type_str = context.args[0].lower()
                try:
                    alert_type = AlertType(alert_type_str)
                    
                    if user_id in self.registered_users:
                        user = self.registered_users[user_id]
                        if alert_type in user.subscription_types:
                            user.subscription_types.remove(alert_type)
                            await update.message.reply_text(f"❌ Unsubscribed from {alert_type.value} alerts")
                        else:
                            await update.message.reply_text(f"ℹ️ Not subscribed to {alert_type.value} alerts")
                    else:
                        await update.message.reply_text("❌ User not registered")
                        
                except ValueError:
                    await update.message.reply_text(f"❌ Invalid alert type: {alert_type_str}")
            else:
                await update.message.reply_text("Usage: /unsubscribe <alert_type>")
            
            self.commands_processed += 1
            telegram_metrics["commands_processed"] += 1
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "handle_unsubscribe_command")
            await update.message.reply_text(f"Error: {error_response}")


    async def _handle_callback(self, update: Update, context):
        """Handle callback queries from inline keyboards"""
        try:
            query = update.callback_query
            await query.answer()
            
            if not self._is_authorized(query.from_user):
                await query.edit_message_text("❌ Unauthorized access.")
                return
            
            data = query.data
            
            if data == "confirm_stop":
                # Handle emergency stop confirmation
                await query.edit_message_text(
                    "🛑 <b>Trading Stopped</b>\n\nAutomated trading has been stopped.\nUse /start command to resume.",
                    parse_mode="HTML"
                )
                
                # Publish emergency stop event
                await self.event_publisher.publish_event({
                    "event_type": "emergency_stop_triggered",
                    "triggered_by": query.from_user.username,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif data == "cancel_stop":
                await query.edit_message_text("✅ Emergency stop cancelled.")
                
            elif data.startswith("subscribe_"):
                alert_type_str = data.replace("subscribe_", "")
                try:
                    alert_type = AlertType(alert_type_str)
                    user_id = str(query.from_user.id)
                    
                    if user_id in self.registered_users:
                        if alert_type not in self.registered_users[user_id].subscription_types:
                            self.registered_users[user_id].subscription_types.append(alert_type)
                        
                        await query.edit_message_text(f"✅ Subscribed to {alert_type.value} alerts")
                    else:
                        await query.edit_message_text("❌ User not registered")
                        
                except ValueError:
                    await query.edit_message_text(f"❌ Invalid alert type: {alert_type_str}")
            
            self.commands_processed += 1
            telegram_metrics["commands_processed"] += 1
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "handle_callback")
            await query.edit_message_text(f"Error: {error_response}")


    async def _handle_message(self, update: Update, context):
        """Handle text messages"""
        try:
            if not self._is_authorized(update.effective_user):
                await update.message.reply_text("❌ Unauthorized access.")
                return
            
            message_text = update.message.text.lower()
            
            if "status" in message_text:
                await self._handle_status(update, context)
            elif "performance" in message_text:
                await self._handle_performance(update, context)
            elif "help" in message_text:
                await self._handle_help(update, context)
            else:
                await update.message.reply_text(
                    "🤖 I understand you want information. Use /help to see available commands."
                )
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "handle_message")
            await update.message.reply_text(f"Error: {error_response}")


    def _is_authorized(self, user) -> bool:
        """Check if user is authorized"""
        return (str(user.id) in self.authorized_users or 
                user.username in self.authorized_users)


    def get_bot_status(self) -> Dict[str, Any]:
        """Get bot status information"""
        uptime = datetime.now() - self.start_time
        
        return {
            "is_running": self.is_running,
            "uptime_seconds": uptime.total_seconds(),
            "registered_users": len(self.registered_users),
            "messages_sent": self.messages_sent,
            "commands_processed": self.commands_processed,
            "alerts_sent": self.alerts_sent,
            "alert_queue_size": len(self.alert_queue),
            "alert_history_size": len(self.alert_history),
            "metrics": telegram_metrics.copy(),
            "last_updated": datetime.now().isoformat()
        }


    # Convenience methods for sending specific alerts
    async def send_trade_signal_alert(self, symbol: str, direction: str, 
                                    confidence: float, entry_price: float):
        """Send trade signal alert"""
        alert = TelegramAlert(
            alert_id=str(uuid.uuid4()),
            alert_type=AlertType.TRADE_SIGNAL,
            title=f"🚨 Trading Signal: {symbol}",
            message=(
                f"<b>Symbol:</b> {symbol}\n"
                f"<b>Direction:</b> {direction.upper()}\n"
                f"<b>Entry Price:</b> {entry_price}\n"
                f"<b>Confidence:</b> {confidence:.1%}"
            ),
            priority="high"
        )
        await self.send_alert(alert)


    async def send_risk_warning(self, message: str, risk_level: str = "high"):
        """Send risk warning alert"""
        alert = TelegramAlert(
            alert_id=str(uuid.uuid4()),
            alert_type=AlertType.RISK_WARNING,
            title="⚠️ Risk Warning",
            message=message,
            priority="critical" if risk_level == "critical" else "high"
        )
        await self.send_alert(alert)


    async def send_daily_summary(self, pnl: float, trades: int, win_rate: float):
        """Send daily summary alert"""
        alert = TelegramAlert(
            alert_id=str(uuid.uuid4()),
            alert_type=AlertType.DAILY_SUMMARY,
            title="📋 Daily Trading Summary",
            message=(
                f"<b>Daily P&L:</b> ${pnl:+.2f}\n"
                f"<b>Total Trades:</b> {trades}\n"
                f"<b>Win Rate:</b> {win_rate:.1%}\n"
                f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}"
            ),
            priority="normal"
        )
        await self.send_alert(alert)


# Factory function
def create_telegram_bot(bot_token: str, authorized_users: List[str] = None) -> TradingTelegramBot:
    """Factory function to create Telegram bot"""
    try:
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot library not available")
        
        bot = TradingTelegramBot(bot_token, authorized_users)
        telegram_logger.info("Telegram bot created successfully")
        return bot
        
    except Exception as e:
        telegram_logger.error(f"Failed to create Telegram bot: {e}")
        raise