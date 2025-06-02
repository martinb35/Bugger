import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure DevOps configuration
ORG = os.getenv('AZURE_DEVOPS_ORG')
PROJECT = os.getenv('AZURE_DEVOPS_PROJECT')
USER_EMAIL = os.getenv('AZURE_DEVOPS_USER_EMAIL')
AZURE_DEVOPS_PAT = os.getenv('AZURE_DEVOPS_PAT')

# Configuration constants
BATCH_SIZE = 50

# Validate required environment variables
if not all([ORG, PROJECT, USER_EMAIL, AZURE_DEVOPS_PAT]):
    missing = []
    if not ORG:
        missing.append('AZURE_DEVOPS_ORG')
    if not PROJECT:
        missing.append('AZURE_DEVOPS_PROJECT')
    if not USER_EMAIL:
        missing.append('AZURE_DEVOPS_USER_EMAIL')
    if not AZURE_DEVOPS_PAT:
        missing.append('AZURE_DEVOPS_PAT')
    
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")