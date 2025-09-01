from dotenv import load_dotenv
import os
from estatecore_backend import create_app

# Load environment variables from .env file
load_dotenv()

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # Default to 5000 if not in .env
    app.run(host="0.0.0.0", port=port)