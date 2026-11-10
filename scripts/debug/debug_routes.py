import sys
import os

# Adiciona o diretório atual ao path para importação
sys.path.append(os.getcwd())

try:
    from app.main import app
    print("\n--- ROUTES ---")
    for route in app.routes:
        if hasattr(route, "path"):
            print(f"Path: {route.path} | Name: {route.name} | Methods: {route.methods if hasattr(route, 'methods') else 'N/A'}")
    print("--- END ROUTES ---\n")
except Exception as e:
    print(f"Error importing app: {e}")
