from flask import Flask
from workflows_cdk import Router
from google.oauth2.service_account import Credentials
import gspread

# Create Flask app
app = Flask(__name__)
router = Router(app)

if __name__ == "__main__":
    router.run_app(app)