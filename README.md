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
   ```cmd
   git clone https://github.com/YOUR_USERNAME/bugger.git
   cd bugger
   ```

2. **Install dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

3. **Create a Personal Access Token (PAT):**
   
   To access Azure DevOps APIs, you need a Personal Access Token:
   
   - Go to [Azure DevOps](https://microsoft.visualstudio.com)
   - Sign in to your account
   - Click on your profile picture (top-right corner) → **Personal Access Tokens**
   - Click **+ New Token**
   - Fill in the form:
     - **Name**: `Bugger Dashboard` (or any descriptive name)
     - **Organization**: Select your organization
     - **Expiration**: Choose 90 days, 1 year, or custom
     - **Scopes**: Select **Custom defined**, then check:
       - ✅ **Work Items (Read)** - Required to fetch bug data
   - Click **Create**
   - **Important**: Copy the token immediately - you won't see it again!

4. **Configure environment variables:**
   ```cmd
   copy .env.example .env
   ```
   
   Edit `.env` with your Azure DevOps credentials:
   - **PAT**: Paste the Personal Access Token you just created
   - **ORG**: Your Azure DevOps organization name (from the URL: `https://microsoft.visualstudio.com/YOUR_ORG/`)
   - **PROJECT**: Your project name
   - **EMAIL**: Your Azure DevOps email address

5. **Run the application:**
   ```cmd
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
- **Never share your PAT token** - treat it like a password

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📝 Revision History

### [1.1.0] - 2023-10-08

#### Added
- Detailed steps for creating a Personal Access Token (PAT) in Azure DevOps
- Comprehensive setup guide with CMD commands
- Security guidelines and best practices for PAT usage
- Documentation on bug categorization patterns
- Revision of command examples to use CMD syntax

#### Changed
- Updated all command examples to use CMD syntax

#### Fixed
- Minor typos and formatting issues in the README

### [1.0.0] - 2023-09-15

- Initial release of Bugger - We Use Machines