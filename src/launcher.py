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
import requests

from path_manager import path_manager, setup_environment

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    import io
    # Check if stdout/stderr exist (they're None in GUI mode on Windows)
    if sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    elif sys.stdout is None:
        # Open devnull as stdout in GUI mode to prevent errors
        sys.stdout = open(os.devnull, 'w', encoding='utf-8')

    if sys.stderr is not None and hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    elif sys.stderr is None:
        # Open devnull as stderr in GUI mode to prevent errors
        sys.stderr = open(os.devnull, 'w', encoding='utf-8')

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
    env['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'

    src_dir = path_manager.get_path('src')
    app_path = src_dir / 'app.py'
    working_dir = path_manager.get_base_dir()
    cwd = str(working_dir) if working_dir else None

    # Launch Streamlit
    try:
        process = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run', str(app_path),
            '--server.port', str(port),
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false',
            '--server.enableCORS', 'false',
            '--server.enableXsrfProtection', 'false'
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)

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
