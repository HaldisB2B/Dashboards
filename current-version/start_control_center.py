#!/usr/bin/env python3
"""
Service Control Center Server
Your centralized localhost dashboard at http://localhost:9000/
"""

import http.server
import socketserver
import webbrowser
import threading
import time
import json
import subprocess
import os
import signal
import sys
import urllib.request
import urllib.error
from pathlib import Path

PORT = 9000
SERVICES_CONFIG_FILE = "/Users/peter/services_config.json"

class ServiceControlHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for service control endpoints"""
    
    def do_GET(self):
        if self.path == '/api/services':
            self.send_json_response(self.get_services_status())
        elif self.path == '/api/models':
            self.send_json_response(self.get_ollama_models())
        elif self.path.startswith('/api/start/'):
            service_name = self.path.split('/')[-1]
            result = self.start_service(service_name)
            self.send_json_response(result)
        elif self.path.startswith('/api/stop/'):
            service_name = self.path.split('/')[-1]
            result = self.stop_service(service_name)
            self.send_json_response(result)
        else:
            # Serve static files
            super().do_GET()
    
    def send_json_response(self, data):
        """Send JSON response with CORS headers"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_services_status(self):
        """Get status of all services"""
        services = {
            'ollama': {
                'name': 'Ollama AI Models',
                'port': 11434,
                'url': 'http://localhost:11434/api/tags',
                'type': 'api'
            },
            'brain_button': {
                'name': 'Brain Button Interface',
                'port': 3001,
                'url': 'http://localhost:3001/',
                'type': 'web'
            },
            'other_project': {
                'name': 'Your Other Project',
                'port': 5173,
                'url': 'http://localhost:5173/',
                'type': 'web'
            }
        }
        
        for service_name, config in services.items():
            try:
                req = urllib.request.Request(config['url'])
                with urllib.request.urlopen(req, timeout=2) as response:
                    config['status'] = 'running' if response.status == 200 else 'error'
            except:
                config['status'] = 'stopped'
        
        return services
    
    def get_ollama_models(self):
        """Get Ollama models"""
        try:
            req = urllib.request.Request('http://localhost:11434/api/tags')
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = response.read().decode('utf-8')
                    return json.loads(data)
        except:
            pass
        return {'models': []}
    
    def start_service(self, service_name):
        """Start a service"""
        try:
            if service_name == 'ollama':
                # Start Ollama in background
                subprocess.Popen(['ollama', 'serve'], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                return {'success': True, 'message': 'Ollama starting...'}
            elif service_name == 'brain_button':
                # Start Brain Button server
                subprocess.Popen(['python3', '/Users/peter/start_brain_button_server.py'],
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                return {'success': True, 'message': 'Brain Button starting...'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
        
        return {'success': False, 'message': 'Unknown service'}
    
    def stop_service(self, service_name):
        """Stop a service"""
        try:
            if service_name == 'ollama':
                os.system('pkill -f "ollama serve"')
                return {'success': True, 'message': 'Ollama stopped'}
            elif service_name == 'brain_button':
                os.system('pkill -f "start_brain_button_server.py"')
                return {'success': True, 'message': 'Brain Button stopped'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
        
        return {'success': False, 'message': 'Unknown service'}

def save_pid():
    """Save process ID for later cleanup"""
    with open('/tmp/control_center.pid', 'w') as f:
        f.write(str(os.getpid()))

def cleanup_on_exit():
    """Cleanup function"""
    print(f"\n🛑 Service Control Center shutting down...")
    try:
        os.remove('/tmp/control_center.pid')
    except:
        pass

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    cleanup_on_exit()
    sys.exit(0)

def start_server():
    """Start the control center server"""
    # Change to the directory containing our HTML files
    web_dir = Path("/Users/peter")
    os.chdir(web_dir)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Save PID
    save_pid()
    
    # Start server
    with socketserver.TCPServer(("", PORT), ServiceControlHandler) as httpd:
        print(f"🎛️  Service Control Center running at: http://localhost:{PORT}/")
        print(f"📊 Dashboard: http://localhost:{PORT}/service_dashboard_themed.html")
        print(f"🔧 API Endpoints: /api/services, /api/models, /api/start/<service>, /api/stop/<service>")
        print(f"🎨 Professional Theme: Light Blue with Deep Blue Dark Mode")
        print(f"🛑 Press Ctrl+C to stop")
        print("=" * 70)
        
        # Auto-open browser after a short delay
        def open_browser():
            time.sleep(2)
            webbrowser.open(f'http://localhost:{PORT}/service_dashboard_themed.html')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            cleanup_on_exit()

if __name__ == "__main__":
    print("🎛️  Starting Service Control Center")
    print("=" * 50)
    print("🌐 Your centralized localhost dashboard")
    print("📍 Fixed Address: http://localhost:9000/")
    print("=" * 50)
    
    # Check if port is already in use
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', PORT))
            if result == 0:
                print(f"❌ Port {PORT} is already in use!")
                print("Another Control Center might be running.")
                sys.exit(1)
    except:
        pass
    
    start_server()