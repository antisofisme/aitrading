"""
run_bridge.py - Bridge Runner Utility

🎯 PURPOSE:
Business: Utility script for running the trading bridge with specific configurations
Technical: Configuration-specific bridge runner with environment setup
Domain: CLI Utility/Bridge Runner/Configuration

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.947Z
Session: client-side-ai-brain-full-compliance
Confidence: 87%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_CLI_UTILITY: CLI utility with configuration management

📦 DEPENDENCIES:
Internal: bridge_app, config_manager
External: argparse, sys, os

💡 AI DECISION REASONING:
Bridge runner utility provides flexible configuration options for different deployment scenarios.

🚀 USAGE:
python run_bridge.py --env=production --symbols=EURUSD,GBPUSD

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import asyncio
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
import psutil
import signal
from loguru import logger

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from bridge_app import MT5Bridge
from libs.config import get_settings, validate_mt5_path


class BridgeRunner:
    """
    Production ready MT5 Bridge runner
    Handles monitoring, restart, and health checks
    """
    
    def __init__(self):
        self.bridge: Optional[MT5Bridge] = None
        self.running = False
        self.start_time = None
        self.restart_count = 0
        self.max_restarts = 5
        
    async def start(self):
        """Start MT5 Bridge with monitoring"""
        try:
            logger.info("🚀 Starting MT5 Bridge Runner")
            
            # Validate configuration
            if not await self._validate_setup():
                return False
            
            # Display startup info
            self._display_startup_info()
            
            # Start main loop
            await self._run_with_monitoring()
            
        except KeyboardInterrupt:
            logger.info("👋 Shutdown requested by user")
        except Exception as e:
            logger.error(f"Runner error: {e}")
        finally:
            await self._cleanup()
    
    async def _validate_setup(self) -> bool:
        """Validate MT5 Bridge setup"""
        try:
            logger.info("🔍 Validating setup...")
            
            # Load settings
            settings = get_mt5_settings()
            
            # Check MT5 path
            if not validate_mt5_path(settings.mt5_path):
                logger.error(f"❌ MT5 not found at: {settings.mt5_path}")
                logger.info("Please check MT5_PATH in .env file")
                return False
            
            # Check required settings
            if not settings.mt5_login or not settings.mt5_password or not settings.mt5_server:
                logger.error("❌ Missing MT5 credentials in .env file")
                logger.info("Please configure MT5_LOGIN, MT5_PASSWORD, MT5_SERVER")
                return False
            
            logger.success("✅ Setup validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Setup validation error: {e}")
            return False
    
    def _display_startup_info(self):
        """Display startup information"""
        settings = get_mt5_settings()
        
        print("\n" + "="*60)
        print("🚀 MT5 BRIDGE - AI TRADING CONNECTOR")
        print("="*60)
        print(f"📅 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📈 MT5 Server: {settings.mt5_server}")
        print(f"🔗 Backend URL: {settings.backend_ws_url}")
        print(f"💰 Trading: {'✅ ENABLED' if settings.trading_enabled else '❌ DISABLED'}")
        print(f"🛡️  Risk Limit: {settings.max_risk_percent}% per trade")
        print(f"📊 Daily Limit: {settings.max_daily_trades} trades")
        print(f"🔒 Emergency Stop: {'🚨 ACTIVE' if settings.emergency_stop else '✅ READY'}")
        print("="*60)
        print("📋 Commands:")
        print("   Ctrl+C : Graceful shutdown")
        print("   Check logs: tail -f mt5_bridge.log")
        print("="*60 + "\n")
    
    async def _run_with_monitoring(self):
        """Run bridge with health monitoring"""
        self.running = True
        self.start_time = time.time()
        
        while self.running and self.restart_count < self.max_restarts:
            try:
                logger.info(f"🔄 Starting MT5 Bridge (Attempt {self.restart_count + 1})")
                
                # Create and start bridge
                self.bridge = MT5Bridge()
                await self.bridge.start()
                
            except Exception as e:
                self.restart_count += 1
                logger.error(f"Bridge crashed: {e}")
                
                if self.restart_count < self.max_restarts:
                    wait_time = min(30, 5 * self.restart_count)
                    logger.warning(f"⏳ Restarting in {wait_time} seconds... ({self.restart_count}/{self.max_restarts})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.critical("❌ Max restart attempts reached, stopping")
                    break
            
            finally:
                if self.bridge:
                    await self.bridge.stop()
                    self.bridge = None
    
    async def _cleanup(self):
        """Cleanup resources"""
        try:
            self.running = False
            
            if self.bridge:
                await self.bridge.stop()
            
            # Calculate uptime
            if self.start_time:
                uptime = time.time() - self.start_time
                logger.info(f"⏱️  Total uptime: {uptime:.1f} seconds")
            
            logger.info("🧹 Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


class HealthChecker:
    """System health checker"""
    
    @staticmethod
    def check_system_resources() -> dict:
        """Check system resources"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
                "status": "healthy" if cpu_percent < 80 and memory.percent < 85 else "warning"
            }
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def check_mt5_process() -> dict:
        """Check if MT5 is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if 'terminal64' in proc.info['name'].lower():
                    return {
                        "running": True,
                        "pid": proc.info['pid'],
                        "status": "found"
                    }
            
            return {
                "running": False,
                "status": "not_found"
            }
        except Exception as e:
            return {
                "running": False,
                "status": "error",
                "message": str(e)
            }


async def main():
    """Main entry point"""
    try:
        # Setup logging for runner
        logger.remove()
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>Runner</cyan> | <level>{message}</level>",
            colorize=True
        )
        
        # Check system health
        health = HealthChecker.check_system_resources()
        logger.info(f"💻 System Health: {health['status']}")
        logger.info(f"   CPU: {health['cpu_percent']:.1f}%")
        logger.info(f"   Memory: {health['memory_percent']:.1f}%")
        logger.info(f"   Free Disk: {health['disk_free_gb']:.1f}GB")
        
        # Check MT5 process
        mt5_status = HealthChecker.check_mt5_process()
        if mt5_status['running']:
            logger.success(f"✅ MT5 Terminal detected (PID: {mt5_status['pid']})")
        else:
            logger.warning("⚠️  MT5 Terminal not detected - Make sure MT5 is running")
        
        # Start runner
        runner = BridgeRunner()
        await runner.start()
        
    except Exception as e:
        logger.error(f"Main error: {e}")
    finally:
        logger.info("👋 MT5 Bridge Runner finished")


if __name__ == "__main__":
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Run application
    asyncio.run(main())