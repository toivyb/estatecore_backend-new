from dotenv import load_dotenv
import os
from estatecore_backend import create_app

# Load environment variables from .env file (only in development)
if os.path.exists('.env'):
    load_dotenv()

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)