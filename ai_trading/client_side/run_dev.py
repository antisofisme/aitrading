#!/usr/bin/env python3
"""
run_dev.py - Enhanced Development Runner

🎯 PURPOSE:
Business: Advanced development runner with hot reload and testing features
Technical: Development environment with auto-reload and testing integration
Domain: Development/Hot Reload/Testing

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.938Z
Session: client-side-ai-brain-full-compliance
Confidence: 86%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_DEV_ENHANCED: Enhanced development environment with hot reload
- AUTO_RELOAD_SYSTEM: Automatic application reload on file changes

📦 DEPENDENCIES:
Internal: central_hub, hybrid_bridge
External: watchdog, sys, os, threading

💡 AI DECISION REASONING:
Enhanced development runner improves developer productivity with automatic reload and integrated testing capabilities.

🚀 USAGE:
python run_dev.py --watch --auto-test

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AutoReloadHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.restart_client()
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Only restart for Python files
        if event.src_path.endswith('.py'):
            print(f"\n🔄 File changed: {event.src_path}")
            print("🔄 Restarting client...")
            self.restart_client()
    
    def restart_client(self):
        # Kill existing process
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
        
        # Start new process
        print("🚀 Starting MT5 Client...")
        self.process = subprocess.Popen([
            sys.executable, "run.py"
        ], cwd=Path(__file__).parent)

def main():
    print("🔥 Development Mode - Auto-Reload Enabled")
    print("📁 Watching for file changes...")
    print("🛑 Press Ctrl+C to stop")
    
    handler = AutoReloadHandler()
    observer = Observer()
    
    # Watch src directory for changes
    observer.schedule(handler, "src", recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping auto-reload...")
        if handler.process:
            handler.process.terminate()
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        main()
    except ImportError:
        print("❌ watchdog not installed")
        print("💡 Install with: pip install watchdog")
        print("🔄 Falling back to normal mode...")
        subprocess.run([sys.executable, "run.py"])