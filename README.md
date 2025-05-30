# Bugger - We Use Machines

A smart bug tracking dashboard that connects to Azure DevOps and categorizes your active bugs into meaningful groups.

## 🚀 Features

- 🎯 **Smart Categorization**: Automatically groups bugs by type (crashes, performance, drivers, etc.)
- 🔒 **Secure**: Uses environment variables for credential management
- 🌐 **Web Interface**: Clean Gradio-based dashboard
- 🔗 **Direct Links**: Click-through to Azure DevOps queries
- 📊 **Analytics**: Bug age and activity statistics
- 🚀 **Progress Tracking**: Real-time progress during data fetch

## 📋 Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/azure-devops-bug-tracker.git
   cd azure-devops-bug-tracker
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your Azure DevOps credentials:
   - **PAT**: Get from Azure DevOps → User Settings → Personal Access Tokens
   - **ORG**: Your Azure DevOps organization name
   - **PROJECT**: Your project name
   - **EMAIL**: Your Azure DevOps email

4. **Run the application:**
   ```bash
   python main.py
   ```

## 🤖 Bugger - We Use Machines

This tool leverages machine learning patterns and automated categorization to help you efficiently manage and understand your bug backlog. Because we believe in using machines to solve human problems!

## 🔧 How It Works

The dashboard fetches your active bugs from Azure DevOps and intelligently categorizes them:

- **BSoD/Crashes**: System crashes and blue screen errors
- **Boot/Startup**: Issues preventing system startup
- **Performance/Hangs**: Performance and responsiveness issues
- **Driver Issues**: Hardware driver problems
- **Memory Issues**: Memory leaks and allocation failures
- **Security/Access**: Security vulnerabilities and access control
- **File System**: File system corruption and storage issues

## 🛡️ Security

- PAT tokens are stored in environment variables only
- `.env` file is excluded from git commits
- No credentials are hardcoded in source code

## 🤝 Contributing

Feel free to submit issues and enhancement requests!