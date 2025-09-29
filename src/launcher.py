#!/usr/bin/env python3
"""
CAUSA Agent Desktop Launcher
Launches Streamlit app and opens browser automatically
"""

import os
import sys
import time
import webbrowser
import subprocess
import threading
import signal
import socket
from pathlib import Path
import requests

def find_free_port(start_port=8501):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except OSError:
                continue
    return None

def wait_for_server(port, timeout=30):
    """Wait for Streamlit server to be ready"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f'http://localhost:{port}', timeout=1)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    return False

def setup_directories():
    """Create necessary directories if they don't exist"""
    # Import path_manager here to avoid circular imports
    from path_manager import setup_environment

    # Setup complete environment
    setup_environment()
    print(f"✓ Environment setup completed")

def launch_streamlit():
    """Launch Streamlit server"""
    port = find_free_port()
    if not port:
        print("❌ No available ports found")
        return None, None

    print(f"🚀 Starting CAUSA Agent on port {port}...")

    # Set environment variables
    env = os.environ.copy()
    env['STREAMLIT_SERVER_PORT'] = str(port)
    env['STREAMLIT_SERVER_HEADLESS'] = 'true'
    env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    env['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
    env['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'false'

    # Launch Streamlit
    try:
        process = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run', 'app.py',
            '--server.port', str(port),
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false',
            '--server.enableCORS', 'false',
            '--server.enableXsrfProtection', 'false'
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return process, port
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")
        return None, None

def open_browser(port):
    """Open browser after server is ready"""
    def browser_thread():
        if wait_for_server(port):
            print(f"✓ Server ready! Opening browser...")
            webbrowser.open(f'http://localhost:{port}')
        else:
            print("❌ Server failed to start within timeout")

    thread = threading.Thread(target=browser_thread)
    thread.daemon = True
    thread.start()

def signal_handler(sig, frame, process):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down CAUSA Agent...")
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    sys.exit(0)

def main():
    """Main launcher function"""
    print("=" * 50)
    print("🦋 CAUSA - Social Media Content Agent")
    print("=" * 50)

    # Setup directories
    setup_directories()

    # Change to src directory where app.py is located
    src_dir = Path(__file__).parent
    os.chdir(src_dir)

    # Launch Streamlit
    process, port = launch_streamlit()

    if not process or not port:
        print("❌ Failed to start application")
        input("Press Enter to exit...")
        return

    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, process))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, process))

    # Open browser
    open_browser(port)

    print(f"✓ CAUSA Agent running at: http://localhost:{port}")
    print("💡 Close this window to stop the application")
    print("=" * 50)

    try:
        # Wait for process to complete
        process.wait()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None, process)

if __name__ == "__main__":
    main()
