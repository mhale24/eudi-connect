#!/usr/bin/env python3
"""
Direct test of FastAPI app without Docker to isolate issues
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

try:
    # Try to import and run the app directly
    from eudi_connect.main import app
    print("✓ Successfully imported FastAPI app")
    
    # Test if we can create the app instance
    print(f"✓ App instance created: {type(app)}")
    
    # Try to get the routes
    routes = [route.path for route in app.routes]
    print(f"✓ Found {len(routes)} routes: {routes[:5]}...")
    
    # Try to start uvicorn directly
    import uvicorn
    print("✓ Starting uvicorn server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"✗ Runtime error: {e}")
    import traceback
    traceback.print_exc()