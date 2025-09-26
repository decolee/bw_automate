#!/usr/bin/env python3
"""
BW_AUTOMATE Server Launcher
Production-ready launcher with Apple-inspired CLI
"""

import os
import sys
import subprocess
import argparse
import logging
import signal
import time
from pathlib import Path

# ANSI color codes for beautiful CLI output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    """Print beautiful Apple-inspired banner"""
    banner = f"""
{Colors.BLUE}{Colors.BOLD}
╭─────────────────────────────────────────────────────────────╮
│                                                             │
│   {Colors.WHITE}██████╗ ██╗    ██╗     █████╗ ██╗   ██╗████████╗ ██████╗{Colors.BLUE}   │
│   {Colors.WHITE}██╔══██╗██║    ██║    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗{Colors.BLUE}  │
│   {Colors.WHITE}██████╔╝██║ █╗ ██║    ███████║██║   ██║   ██║   ██║   ██║{Colors.BLUE}  │
│   {Colors.WHITE}██╔══██╗██║███╗██║    ██╔══██║██║   ██║   ██║   ██║   ██║{Colors.BLUE}  │
│   {Colors.WHITE}██████╔╝╚███╔███╔╝    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝{Colors.BLUE}  │
│   {Colors.WHITE}╚═════╝  ╚══╝╚══╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝{Colors.BLUE}   │
│                                                             │
│   {Colors.CYAN}Professional Python Code Analysis Platform{Colors.BLUE}            │
│   {Colors.WHITE}Enterprise-grade • Security-focused • Performance-optimized{Colors.BLUE} │
│                                                             │
╰─────────────────────────────────────────────────────────────╯
{Colors.END}"""
    print(banner)

def check_dependencies():
    """Check if required dependencies are installed"""
    print(f"{Colors.YELLOW}🔍 Checking dependencies...{Colors.END}")
    
    required_packages = [
        'flask', 'flask-cors', 'framer-motion', 'react'
    ]
    
    missing_packages = []
    
    # Check Python packages
    try:
        import flask
        import flask_cors
        print(f"  {Colors.GREEN}✓{Colors.END} Flask backend dependencies")
    except ImportError as e:
        missing_packages.append('Flask backend')
        print(f"  {Colors.RED}✗{Colors.END} Flask backend: {e}")
    
    # Check if frontend is built
    frontend_build = Path('frontend/build')
    if frontend_build.exists():
        print(f"  {Colors.GREEN}✓{Colors.END} Frontend build")
    else:
        print(f"  {Colors.YELLOW}⚠{Colors.END} Frontend not built - building now...")
        build_frontend()
    
    return len(missing_packages) == 0

def build_frontend():
    """Build the React frontend"""
    print(f"{Colors.CYAN}🔨 Building frontend...{Colors.END}")
    
    frontend_dir = Path('frontend')
    if not frontend_dir.exists():
        print(f"{Colors.RED}✗ Frontend directory not found{Colors.END}")
        return False
    
    os.chdir(frontend_dir)
    
    try:
        # Install dependencies
        print(f"  {Colors.YELLOW}Installing npm dependencies...{Colors.END}")
        subprocess.run(['npm', 'install'], check=True, capture_output=True)
        
        # Build
        print(f"  {Colors.YELLOW}Building React app...{Colors.END}")
        subprocess.run(['npm', 'run', 'build'], check=True, capture_output=True)
        
        print(f"  {Colors.GREEN}✓ Frontend built successfully{Colors.END}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  {Colors.RED}✗ Frontend build failed: {e}{Colors.END}")
        return False
    except FileNotFoundError:
        print(f"  {Colors.RED}✗ npm not found. Please install Node.js and npm{Colors.END}")
        return False
    finally:
        os.chdir('..')

def install_dependencies():
    """Install missing dependencies"""
    print(f"{Colors.CYAN}📦 Installing dependencies...{Colors.END}")
    
    try:
        # Install Python dependencies
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', 
            'flask', 'flask-cors', 'pathlib'
        ], check=True)
        
        print(f"  {Colors.GREEN}✓ Python dependencies installed{Colors.END}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  {Colors.RED}✗ Failed to install dependencies: {e}{Colors.END}")
        return False

def start_server(host='127.0.0.1', port=8000, debug=False):
    """Start the BW_AUTOMATE server"""
    print(f"{Colors.GREEN}🚀 Starting BW_AUTOMATE Server...{Colors.END}")
    print(f"  {Colors.CYAN}Host:{Colors.END} {host}")
    print(f"  {Colors.CYAN}Port:{Colors.END} {port}")
    print(f"  {Colors.CYAN}Debug:{Colors.END} {debug}")
    print(f"  {Colors.CYAN}URL:{Colors.END} http://{host}:{port}")
    print()
    
    # Set environment variables
    env = os.environ.copy()
    env['HOST'] = host
    env['PORT'] = str(port)
    env['DEBUG'] = str(debug).lower()
    
    try:
        # Start server
        subprocess.run([sys.executable, 'backend_server.py'], env=env)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹  Server stopped by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}✗ Server error: {e}{Colors.END}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='BW_AUTOMATE - Professional Python Code Analysis Platform',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Colors.CYAN}Examples:{Colors.END}
  python run_server.py                    # Start with default settings
  python run_server.py --host 0.0.0.0    # Allow external connections
  python run_server.py --debug           # Enable debug mode
  python run_server.py --build-only      # Only build frontend
        """
    )
    
    parser.add_argument(
        '--host', 
        default='127.0.0.1',
        help='Host address (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port', 
        type=int, 
        default=8000,
        help='Port number (default: 8000)'
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug mode'
    )
    
    parser.add_argument(
        '--build-only', 
        action='store_true',
        help='Only build frontend, don\'t start server'
    )
    
    parser.add_argument(
        '--install-deps', 
        action='store_true',
        help='Install missing dependencies'
    )
    
    parser.add_argument(
        '--no-banner', 
        action='store_true',
        help='Don\'t show banner'
    )
    
    args = parser.parse_args()
    
    # Show banner
    if not args.no_banner:
        print_banner()
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_dependencies():
            sys.exit(1)
        print()
    
    # Check dependencies
    if not check_dependencies():
        print(f"\n{Colors.RED}✗ Missing dependencies. Run with --install-deps to install them.{Colors.END}")
        sys.exit(1)
    
    print(f"{Colors.GREEN}✓ All dependencies satisfied{Colors.END}\n")
    
    # Build frontend only
    if args.build_only:
        if build_frontend():
            print(f"{Colors.GREEN}✓ Frontend build completed{Colors.END}")
        else:
            print(f"{Colors.RED}✗ Frontend build failed{Colors.END}")
            sys.exit(1)
        return
    
    # Start server
    start_server(args.host, args.port, args.debug)

if __name__ == '__main__':
    main()