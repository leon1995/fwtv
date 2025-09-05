import os
import dotenv

dotenv.load_dotenv()

CLIENT_ID: str = os.environ.get('FACTORIALHR_CLIENT_ID', '')
CLIENT_SECRET: str = os.environ.get('FACTORIALHR_CLIENT_SECRET', '')
REDIRECT_URI: str = os.environ.get('FACTORIALHR_REDIRECT_URI', '')
ENVIRONMENT_URL: str = os.environ.get('FACTORIALHR_ENVIRONMENT_URL', '')
API_KEY: str = os.environ.get('FACTORIALHR_API_KEY', '')
SCOPE = 'read'
