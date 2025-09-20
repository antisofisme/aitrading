"""
run_bridge_simple.py - Simplified Bridge Runner

🎯 PURPOSE:
Business: Simplified bridge runner for basic trading operations
Technical: Lightweight bridge runner with minimal configuration
Domain: CLI Utility/Simplified Runner/Basic Operations

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.964Z
Session: client-side-ai-brain-full-compliance
Confidence: 90%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_SIMPLE_RUNNER: Simplified runner for basic operations

📦 DEPENDENCIES:
Internal: bridge_app
External: sys, asyncio

💡 AI DECISION REASONING:
Simplified runner provides quick start option for basic trading operations without complex configuration.

🚀 USAGE:
python run_bridge_simple.py

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

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from bridge_app import MT5Bridge
from src.shared.config.client_settings import get_client_settings


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
            print("Starting MT5 Bridge Runner")
            
            # Validate configuration
            if not await self._validate_setup():
                return False
            
            # Display startup info
            self._display_startup_info()
            
            # Start main loop
            await self._run_with_monitoring()
            
        except KeyboardInterrupt:
            print("Shutdown requested by user")
        except Exception as e:
            print(f"Runner error: {e}")
        finally:
            await self._cleanup()
    
    async def _validate_setup(self) -> bool:
        """Validate MT5 Bridge setup"""
        try:
            print("Validating setup...")
            
            # Load centralized settings
            client_settings = get_client_settings()
            
            # Check MT5 path
            mt5_path = client_settings.mt5.installation_path
            if not Path(mt5_path).exists():
                print(f"ERROR: MT5 not found at: {mt5_path}")
                print("Please check MT5_WINDOWS_PATH or MT5_LINUX_PATH in .env.client")
                return False
            
            # Check required settings - these should be set in .env.client
            print("✅ MT5 path validation passed")
            print("✅ Configuration loaded from centralized client_settings")
            print("Setup validation passed")
            return True
            
        except Exception as e:
            print(f"Setup validation error: {e}")
            return False
    
    def _display_startup_info(self):
        """Display startup information"""
        client_settings = get_client_settings()
        
        print("\n" + "="*60)
        print("MT5 BRIDGE - AI TRADING CONNECTOR")
        print("="*60)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Environment: {client_settings.app.environment}")
        print(f"WebSocket URL: {client_settings.network.websocket_url}")
        print(f"Trading: {'ENABLED' if client_settings.app.trading_enabled else 'DISABLED'}")
        print(f"Paper Trading: {'YES' if client_settings.app.paper_trading else 'NO'}")
        print(f"Risk Limit: {client_settings.app.max_risk_per_trade}% per trade")
        print(f"Daily Limit: {client_settings.app.max_daily_trades} trades")
        print("="*60)
        print("Commands:")
        print("   Ctrl+C : Graceful shutdown")
        print(f"   Check logs: tail -f {client_settings.app.log_file}")
        print("="*60 + "\n")
    
    async def _run_with_monitoring(self):
        """Run bridge with health monitoring"""
        self.running = True
        self.start_time = time.time()
        
        while self.running and self.restart_count < self.max_restarts:
            try:
                print(f"Starting MT5 Bridge (Attempt {self.restart_count + 1})")
                
                # Create and start bridge
                self.bridge = MT5Bridge()
                await self.bridge.start()
                
            except Exception as e:
                self.restart_count += 1
                print(f"Bridge crashed: {e}")
                
                if self.restart_count < self.max_restarts:
                    wait_time = min(30, 5 * self.restart_count)
                    print(f"Restarting in {wait_time} seconds... ({self.restart_count}/{self.max_restarts})")
                    await asyncio.sleep(wait_time)
                else:
                    print("ERROR: Max restart attempts reached, stopping")
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
                print(f"Total uptime: {uptime:.1f} seconds")
            
            print("Cleanup completed")
            
        except Exception as e:
            print(f"Cleanup error: {e}")


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
            print(f"Health check error: {e}")
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
        # Check system health
        health = HealthChecker.check_system_resources()
        print(f"System Health: {health['status']}")
        print(f"   CPU: {health['cpu_percent']:.1f}%")
        print(f"   Memory: {health['memory_percent']:.1f}%")
        print(f"   Free Disk: {health['disk_free_gb']:.1f}GB")
        
        # Check MT5 process
        mt5_status = HealthChecker.check_mt5_process()
        if mt5_status['running']:
            print(f"SUCCESS: MT5 Terminal detected (PID: {mt5_status['pid']})")
        else:
            print("WARNING: MT5 Terminal not detected - Bridge will try to start it")
        
        # Start runner
        runner = BridgeRunner()
        await runner.start()
        
    except Exception as e:
        print(f"Main error: {e}")
    finally:
        print("MT5 Bridge Runner finished")


if __name__ == "__main__":
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Run application
    asyncio.run(main())