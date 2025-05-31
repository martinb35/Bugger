# Bug Analyzer Dashboard

A Gradio-based dashboard for analyzing and categorizing Azure DevOps bugs, helping you prioritize and clean up your bug backlog.

## Features

- **Questionable Bug Detection**: Identifies bugs with insufficient descriptions, broken references, or other issues that make them non-actionable
- **Smart Categorization**: Automatically groups actionable bugs by type (crashes, performance, drivers, etc.)
- **Azure DevOps Integration**: Direct query links to view bugs in Azure DevOps
- **Statistical Analysis**: Shows average bug age and time in active state
- **Batch Query Support**: Handles large bug lists by creating batched queries

## Setup

1. Create a `.env` file with your Azure DevOps credentials:
```
AZURE_DEVOPS_ORG=your-organization
AZURE_DEVOPS_PROJECT=your-project
AZURE_DEVOPS_USER_EMAIL=your-email@domain.com
AZURE_DEVOPS_PAT=your-personal-access-token
```

2. Install dependencies:
```bash
pip install gradio requests python-dotenv
```

3. Run the dashboard:
```bash
python main.py
```

## Architecture

The application is organized into modular components:

- `config.py` - Configuration and environment variables
- `azure_client.py` - Azure DevOps API interactions
- `bug_analyzer.py` - Bug statistics calculations
- `bug_categorizer.py` - Actionable bug categorization
- `report_generator.py` - Report generation logic
- `questionable_analyzer.py` - Questionable bug detection
- `main.py` - Main orchestration and Gradio UI

## Revision History

### v2.0.0 (2024-01-XX)
- **Major Refactoring**: Split monolithic main.py (400+ lines) into modular components
- **Fixed Bug Count Discrepancy**: Query links now use specific bug IDs instead of keyword searches
- **Added Batch Query Support**: Categories with >50 bugs are split into multiple queries
- **Improved Statistics**: Bug age and active duration now calculated only from actionable bugs
- **Better Organization**: Each module has single responsibility, no code duplication

### v1.0.0 (Initial Release)
- Basic bug analysis functionality
- Single file implementation
- Keyword-based categorization