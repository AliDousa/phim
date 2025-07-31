import sys

# Add the backend directory to Python path
sys.path.insert(0, '/app')

def main():
    """Runs a basic health check on the Flask application."""
    try:
        from src.main import create_app
        app = create_app('production')

        with app.test_client() as client:
            # Creating an app_context is a good test of initialization
            with app.app_context():
                print("Application context created successfully.")

        print("Health check passed.")
        sys.exit(0)
    except Exception as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()