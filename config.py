import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure DevOps configuration from environment variables
ORG = os.getenv("AZURE_DEVOPS_ORG")
PROJECT = os.getenv("AZURE_DEVOPS_PROJECT")
USER_EMAIL = os.getenv("AZURE_DEVOPS_USER_EMAIL")
PERSONAL_ACCESS_TOKEN = os.getenv("AZURE_DEVOPS_PAT")

# Validate that all required environment variables are set
required_vars = {
    "AZURE_DEVOPS_ORG": ORG,
    "AZURE_DEVOPS_PROJECT": PROJECT,
    "AZURE_DEVOPS_USER_EMAIL": USER_EMAIL,
    "AZURE_DEVOPS_PAT": PERSONAL_ACCESS_TOKEN
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Configuration constants
BATCH_SIZE = 50  # Number of bugs per query batch