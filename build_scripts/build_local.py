#!/usr/bin/env python3
"""
Local build script for CAUSA Agent
Use this to build the desktop app locally for testing
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and handle errors"""
    print(f"🔄 Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")

    # Install Python requirements
    if not run_command([sys.executable, '-m', 'pip', 'install', '-r', 'src/requirements.txt']):
        return False

    # Install PyInstaller
    if not run_command([sys.executable, '-m', 'pip', 'install', 'pyinstaller']):
        return False

    return True

def build_app():
    """Build the application using PyInstaller"""
    print("🔨 Building application...")

    build_dir = Path('build_config')
    spec_file = build_dir / 'causa_agent.spec'

    if not spec_file.exists():
        print(f"❌ Spec file not found: {spec_file}")
        return False

    # Run PyInstaller
    if not run_command(['pyinstaller', str(spec_file), '--clean', '--noconfirm'], cwd=build_dir):
        return False

    return True

def create_distribution():
    """Create distribution package"""
    print("📦 Creating distribution package...")

    dist_dir = Path('build_config/dist')
    system = platform.system()

    if system == 'Windows':
        exe_path = dist_dir / 'CAUSA-Agent.exe'
        if exe_path.exists():
            print(f"✓ Windows executable created: {exe_path}")
            # Create zip package
            import zipfile
            with zipfile.ZipFile('CAUSA-Agent-Windows.zip', 'w') as zip_file:
                zip_file.write(exe_path, 'CAUSA-Agent.exe')
                # Add README
                zip_file.writestr('README.txt', '''CAUSA Social Media Agent

1. Extract CAUSA-Agent.exe to a folder of your choice
2. Double-click CAUSA-Agent.exe to launch
3. The app will open in your default browser
4. Go to Configuration to set up your OpenAI API key

For support: https://github.com/your-username/agipro-agent
''')
            print("✓ Created CAUSA-Agent-Windows.zip")
        else:
            print("❌ Windows executable not found")
            return False

    elif system == 'Darwin':  # macOS
        app_path = dist_dir / 'CAUSA-Agent.app'
        if app_path.exists():
            print(f"✓ macOS app bundle created: {app_path}")
            # Create DMG (requires create-dmg)
            try:
                run_command([
                    'create-dmg',
                    '--volname', 'CAUSA Agent',
                    '--window-pos', '200', '120',
                    '--window-size', '600', '300',
                    '--icon-size', '100',
                    '--app-drop-link', '425', '120',
                    'CAUSA-Agent-macOS.dmg',
                    str(dist_dir)
                ])
                print("✓ Created CAUSA-Agent-macOS.dmg")
            except:
                print("⚠️ Could not create DMG (create-dmg not installed)")
                print("   You can install it with: brew install create-dmg")
        else:
            print("❌ macOS app bundle not found")
            return False

    else:
        print(f"⚠️ Unsupported system: {system}")
        return False

    return True

def main():
    """Main build function"""
    print("🦋 CAUSA Agent - Local Build Script")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path('src/app.py').exists():
        print("❌ Please run this script from the project root directory")
        print("   (where src/app.py is located)")
        return 1

    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return 1

    # Build app
    if not build_app():
        print("❌ Failed to build application")
        return 1

    # Create distribution
    if not create_distribution():
        print("❌ Failed to create distribution")
        return 1

    print("=" * 50)
    print("✅ Build completed successfully!")
    print("\nDistribution files created:")

    system = platform.system()
    if system == 'Windows':
        print("   - CAUSA-Agent-Windows.zip")
    elif system == 'Darwin':
        print("   - CAUSA-Agent-macOS.dmg")
        print("   - build_config/dist/CAUSA-Agent.app")

    print("\n💡 Test the application before sharing:")
    if system == 'Windows':
        print("   Extract the zip and run CAUSA-Agent.exe")
    elif system == 'Darwin':
        print("   Mount the DMG and run CAUSA-Agent.app")

    return 0

if __name__ == "__main__":
    sys.exit(main())