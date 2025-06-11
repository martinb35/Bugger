import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure DevOps configuration
ORG = os.getenv('AZURE_DEVOPS_ORG')
PROJECT = os.getenv('AZURE_DEVOPS_PROJECT')
USER_EMAIL = os.getenv('AZURE_DEVOPS_USER_EMAIL')

print(f"[DEBUG] Using Azure DevOps user email: {USER_EMAIL}")

AZURE_DEVOPS_PAT = os.getenv('AZURE_DEVOPS_PAT')

# AI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configuration constants
BATCH_SIZE = 50
API_VERSION = "7.0"  # Or the version your Azure DevOps client expects

# Validate required environment variables (excluding optional AI features)
required_vars = {
    'AZURE_DEVOPS_ORG': ORG,
    'AZURE_DEVOPS_PROJECT': PROJECT, 
    'AZURE_DEVOPS_USER_EMAIL': USER_EMAIL,
    'AZURE_DEVOPS_PAT': AZURE_DEVOPS_PAT
}

missing = [var for var, value in required_vars.items() if not value]

if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Optional: Set OpenAI API key if available
AI_ENABLED = False
if OPENAI_API_KEY:
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        AI_ENABLED = True
        print("AI analysis enabled with OpenAI")
    except ImportError:
        print("Warning: OpenAI package not installed. Using heuristic analysis only.")
        AI_ENABLED = False
else:
    print("No OpenAI API key found. Using heuristic analysis only.")