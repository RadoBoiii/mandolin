#!/usr/bin/env python3
"""
PA Form Automation Web Application
Run this script to start the web server
"""

import os
import sys
from app import app

def main():
    # Set environment variables if not already set
    if not os.getenv('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("Please set it before running the application:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print()
    
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('output/filled_forms', exist_ok=True)
    os.makedirs('output/reports', exist_ok=True)
    
    print("Starting PA Form Automation Web Application...")
    print("Open your browser and go to: http://localhost:5001")
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)

if __name__ == '__main__':
    main() 