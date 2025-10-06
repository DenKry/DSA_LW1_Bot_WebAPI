
from dotenv import load_dotenv; load_dotenv()
import os

DIRECTLINE_SECRET = os.getenv("DIRECTLINE_SECRET")
MICROSOFT_APP_ID = os.getenv("MICROSOFT_APP_ID")
DIRECTLINE_BASE = os.getenv("DIRECTLINE_BASE", "https://directline.botframework.com/v3/directline")