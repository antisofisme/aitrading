#!/usr/bin/env python3
"""
MCP Server Control Panel
Advanced management system for MCP servers with auto-restart functionality
"""

import json
import subprocess
import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class MCPController:
    def __init__(self):
        self.config_path = Path("/mnt/f/WINDSURF/neliti_code/.claude/mcp-settings.json")
        self.log_file = "/tmp/mcp-controller.log"
        self.setup_logging()
        self.load_config()

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self):
        """Load MCP configuration from settings file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Config file not found: {self.config_path}")
            self.config = {"mcp_servers": {}, "monitoring": {"enabled": False}}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
            self.config = {"mcp_servers": {}, "monitoring": {"enabled": False}}

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")

    def is_process_running(self, process_name: str) -> bool:
        """Check if a process is running"""
        try:
            result = subprocess.run(['pgrep', '-f', process_name], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def get_process_pid(self, process_name: str) -> Optional[int]:
        """Get PID of running process"""
        try:
            result = subprocess.run(['pgrep', '-f', process_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split('\n')[0])
        except Exception:
            pass
        return None

    def start_server(self, server_key: str) -> bool:
        """Start a specific MCP server"""
        if server_key not in self.config['mcp_servers']:
            self.logger.error(f"Unknown server: {server_key}")
            return False

        server = self.config['mcp_servers'][server_key]
        
        if self.is_process_running(server['name']):
            self.logger.info(f"{server['name']} is already running")
            return True

        self.logger.info(f"Starting {server['name']}...")
        
        try:
            # Kill any zombie processes first
            subprocess.run(['pkill', '-f', server['name']], 
                         capture_output=True, check=False)
            time.sleep(2)
            
            # Start the server
            subprocess.Popen(server['command'], shell=True, 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait and check if it started successfully
            time.sleep(self.config.get('monitoring', {}).get('restart_delay', 5))
            
            if self.is_process_running(server['name']):
                server['last_restart'] = datetime.now().isoformat()
                server['restart_count'] += 1
                self.save_config()
                self.logger.info(f"✅ {server['name']} started successfully")
                return True
            else:
                self.logger.error(f"❌ Failed to start {server['name']}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting {server['name']}: {e}")
            return False

    def stop_server(self, server_key: str) -> bool:
        """Stop a specific MCP server"""
        if server_key not in self.config['mcp_servers']:
            self.logger.error(f"Unknown server: {server_key}")
            return False

        server = self.config['mcp_servers'][server_key]
        
        if not self.is_process_running(server['name']):
            self.logger.info(f"{server['name']} is not running")
            return True

        self.logger.info(f"Stopping {server['name']}...")
        
        try:
            subprocess.run(['pkill', '-f', server['name']], check=True)
            time.sleep(2)
            
            if not self.is_process_running(server['name']):
                self.logger.info(f"✅ {server['name']} stopped successfully")
                return True
            else:
                # Force kill if still running
                subprocess.run(['pkill', '-9', '-f', server['name']], check=False)
                self.logger.info(f"✅ {server['name']} force stopped")
                return True
                
        except Exception as e:
            self.logger.error(f"Error stopping {server['name']}: {e}")
            return False

    def restart_server(self, server_key: str) -> bool:
        """Restart a specific MCP server"""
        self.logger.info(f"Restarting {server_key}...")
        if self.stop_server(server_key):
            time.sleep(2)
            return self.start_server(server_key)
        return False

    def get_server_status(self, server_key: str) -> Dict[str, Any]:
        """Get detailed status of a server"""
        if server_key not in self.config['mcp_servers']:
            return {"error": f"Unknown server: {server_key}"}

        server = self.config['mcp_servers'][server_key]
        is_running = self.is_process_running(server['name'])
        pid = self.get_process_pid(server['name']) if is_running else None
        
        return {
            "name": server['name'],
            "status": "running" if is_running else "stopped",
            "enabled": server.get('status', 'disabled') == 'enabled',
            "auto_restart": server.get('auto_restart', False),
            "pid": pid,
            "restart_count": server.get('restart_count', 0),
            "last_restart": server.get('last_restart'),
            "description": server.get('description', 'No description')
        }

    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers"""
        status = {}
        for server_key in self.config['mcp_servers']:
            status[server_key] = self.get_server_status(server_key)
        return status

    def monitor_cycle(self):
        """Run one monitoring cycle for auto-restart"""
        if not self.config.get('monitoring', {}).get('enabled', False):
            return

        self.logger.info("🔍 Running MCP monitoring cycle...")
        
        for server_key, server in self.config['mcp_servers'].items():
            if server.get('auto_restart', False) and server.get('status') == 'enabled':
                if not self.is_process_running(server['name']):
                    max_attempts = self.config.get('monitoring', {}).get('max_restart_attempts', 3)
                    if server.get('restart_count', 0) < max_attempts:
                        self.logger.warning(f"⚠️  {server['name']} not running, attempting restart...")
                        self.start_server(server_key)
                    else:
                        self.logger.error(f"❌ {server['name']} exceeded max restart attempts")

    def enable_server(self, server_key: str):
        """Enable a server for auto-restart"""
        if server_key in self.config['mcp_servers']:
            self.config['mcp_servers'][server_key]['status'] = 'enabled'
            self.config['mcp_servers'][server_key]['auto_restart'] = True
            self.save_config()
            self.logger.info(f"✅ {server_key} enabled for auto-restart")

    def disable_server(self, server_key: str):
        """Disable a server from auto-restart"""
        if server_key in self.config['mcp_servers']:
            self.config['mcp_servers'][server_key]['status'] = 'disabled'
            self.config['mcp_servers'][server_key]['auto_restart'] = False
            self.save_config()
            self.logger.info(f"🔄 {server_key} disabled from auto-restart")

def main():
    import sys
    
    controller = MCPController()
    
    if len(sys.argv) < 2:
        print("Usage: python3 mcp-control.py <command> [server_name]")
        print("\nCommands:")
        print("  status [server]    - Show server status")
        print("  start <server>     - Start a server")
        print("  stop <server>      - Stop a server")
        print("  restart <server>   - Restart a server")
        print("  enable <server>    - Enable auto-restart")
        print("  disable <server>   - Disable auto-restart")
        print("  monitor            - Run one monitoring cycle")
        print("  daemon             - Run continuous monitoring")
        print("  list               - List all servers")
        return

    command = sys.argv[1]
    server = sys.argv[2] if len(sys.argv) > 2 else None

    if command == "status":
        if server:
            status = controller.get_server_status(server)
            print(f"\n=== {server.upper()} Status ===")
            for key, value in status.items():
                print(f"{key}: {value}")
        else:
            all_status = controller.get_all_status()
            print("\n=== MCP Servers Status ===")
            for server_key, status in all_status.items():
                status_icon = "✅" if status['status'] == 'running' else "❌"
                auto_restart = "🔄" if status['auto_restart'] else "⏸️"
                print(f"{status_icon} {auto_restart} {server_key}: {status['status']} (PID: {status['pid']})")
    
    elif command == "start" and server:
        controller.start_server(server)
    
    elif command == "stop" and server:
        controller.stop_server(server)
    
    elif command == "restart" and server:
        controller.restart_server(server)
        
    elif command == "enable" and server:
        controller.enable_server(server)
        
    elif command == "disable" and server:
        controller.disable_server(server)
    
    elif command == "monitor":
        controller.monitor_cycle()
        
    elif command == "daemon":
        print("🚀 Starting MCP monitoring daemon...")
        try:
            while True:
                controller.monitor_cycle()
                time.sleep(controller.config.get('monitoring', {}).get('check_interval', 60))
        except KeyboardInterrupt:
            print("\n🛑 MCP monitoring daemon stopped")
            
    elif command == "list":
        all_status = controller.get_all_status()
        print("\n=== Available MCP Servers ===")
        for server_key, status in all_status.items():
            print(f"• {server_key}: {status['description']}")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()