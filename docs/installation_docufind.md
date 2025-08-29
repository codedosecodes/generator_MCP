# 🛠️ DOCUFIND Installation Guide

> **Complete Step-by-Step Setup for Email & Invoice Processing**

## 📖 Table of Contents

- [System Requirements](#-system-requirements)
- [Quick Start](#-quick-start)
- [Detailed Installation](#-detailed-installation)
- [Google Cloud Setup](#-google-cloud-setup)
- [Email Configuration](#-email-configuration)
- [Verification & Testing](#-verification--testing)
- [Troubleshooting](#-troubleshooting)
- [Next Steps](#-next-steps)

## 💻 System Requirements

### Minimum Requirements
- **OS**: Windows 10, macOS 10.15, Ubuntu 18.04+
- **Python**: 3.8 or higher
- **RAM**: 2GB available memory
- **Storage**: 1GB free disk space
- **Internet**: Stable broadband connection

### Recommended Specifications
- **OS**: Windows 11, macOS 12+, Ubuntu 20.04+
- **Python**: 3.9 or 3.10
- **RAM**: 4GB+ available memory
- **Storage**: 5GB+ free disk space (for processing large volumes)
- **Internet**: High-speed broadband (for Google Drive uploads)

### Required Accounts
- ✅ **Google Account** (for Google Drive & Sheets access)
- ✅ **Email Account** with IMAP access (Gmail, Outlook, Yahoo, etc.)
- ✅ **GitHub Account** (for repository access)

## ⚡ Quick Start

### 1-Minute Installation (For Experienced Users)

```bash
# Clone repository
git clone https://github.com/yourusername/DOCUFIND.git
cd DOCUFIND

# Setup environment
python -m venv venv_find_docs
source venv_find_docs/bin/activate  # Windows: venv_find_docs\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure (edit these files with your credentials)
cp config.json.template config/config.json
cp .env.template .env

# Run
python src/find_documents_main.py
```

> ⚠️ **Quick start assumes you have Google Cloud credentials ready**. For detailed setup, continue reading.

## 📋 Detailed Installation

### Step 1: Environment Setup

#### 🐍 Python Installation

**Windows:**
```powershell
# Download Python from python.org or use Windows Store
# Verify installation
python --version
# Should show Python 3.8+ 

# Install pip if not included
python -m ensurepip --upgrade
```

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python@3.9

# Or download from python.org
# Verify installation
python3 --version
```

**Ubuntu/Linux:**
```bash
# Update package manager
sudo apt update

# Install Python 3.9+
sudo apt install python3.9 python3.9-venv python3.9-pip

# Verify installation
python3.9 --version
```

#### 📁 Project Setup

1. **Clone Repository:**
   ```bash
   git clone https://github.com/yourusername/DOCUFIND.git
   cd DOCUFIND
   ```

2. **Create Virtual Environment:**
   ```bash
   # Windows
   python -m venv venv_find_docs
   venv_find_docs\Scripts\activate
   
   # macOS/Linux  
   python3 -m venv venv_find_docs
   source venv_find_docs/bin/activate
   ```

3. **Upgrade pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

### Step 2: Install Dependencies

#### 📦 Core Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list
```

#### 🔍 Dependency Details
The following packages will be installed:

```text
# Core Google API Libraries
google-api-python-client>=2.0.0
google-auth-httplib2>=0.1.0  
google-auth-oauthlib>=0.5.0
google-auth>=2.0.0

# Email Processing
email-validator>=1.1.0
python-dotenv>=0.19.0

# Data Processing  
requests>=2.25.0
openpyxl>=3.0.0

# Utilities
python-dateutil>=2.8.0
pytz>=2021.1
```

#### ⚠️ Troubleshooting Dependencies

**Common Issues:**

1. **SSL Certificate Errors:**
   ```bash
   # macOS
   /Applications/Python\ 3.x/Install\ Certificates.command
   
   # Linux
   sudo apt-get update && sudo apt-get install ca-certificates
   ```

2. **Permission Errors (Windows):**
   ```powershell
   # Run as Administrator or use:
   pip install --user -r requirements.txt
   ```

3. **Build Tools Missing (Windows):**
   ```powershell
   # Install Microsoft C++ Build Tools
   # Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   ```

### Step 3: Configuration Files

#### 📄 Create Configuration Templates

1. **Main Configuration:**
   ```bash
   # Copy templates
   cp config.json.template config/config.json
   cp .env.template .env
   
   # Create required directories
   mkdir -p logs temp
   ```

2. **Directory Structure Verification:**
   ```
   DOCUFIND/
   ├── config/
   │   ├── config.json          ✅ Created
   │   ├── credentials.json     ❌ Will create in Google setup
   │   └── token.json          ❌ Auto-generated
   ├── logs/                   ✅ Created
   ├── temp/                   ✅ Created
   └── .env                    ✅ Created
   ```

## ☁️ Google Cloud Setup

### Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create New Project:**
   ```
   📋 Project Details:
   Project Name: DOCUFIND-Processing
   Project ID: docufind-[your-name]-[random]
   Billing Account: [Required for API usage]
   ```

3. **Enable Required APIs:**
   Navigate to **APIs & Services > Library** and enable:
   - ✅ Google Drive API
   - ✅ Google Sheets API  
   - ✅ Gmail API (optional, for advanced features)

### Step 2: Create Service Account

1. **Navigate to Credentials:**
   - Go to **APIs & Services > Credentials**
   - Click **+ CREATE CREDENTIALS > Service Account**

2. **Service Account Details:**
   ```
   📋 Account Info:
   Service Account Name: docufind-processor
   Service Account ID: docufind-processor
   Description: DOCUFIND email and document processing
   ```

3. **Grant Permissions:**
   ```
   📋 Roles to Add:
   - Editor (for Drive access)
   - Project > Editor (for general access)
   ```

4. **Create Key:**
   ```
   📋 Key Configuration:
   Key Type: JSON
   Download Location: config/credentials.json
   ```

### Step 3: Configure Drive & Sheets Access

1. **Share Google Drive Folder:**
   ```
   📋 Steps:
   1. Create folder "DOCUFIND" in your Google Drive
   2. Right-click > Share
   3. Add service account email (from credentials.json)  
   4. Grant "Editor" permissions
   ```

2. **Test API Access:**
   ```bash
   python scripts/test_google_apis.py
   ```

### Step 4: Cost Considerations

> 💡 **Google Cloud Pricing:**
> - **Drive API**: 1,000 requests/day FREE, then $0.40/1K requests
> - **Sheets API**: 100 requests/100 seconds FREE, then $4/million requests  
> - **Storage**: 15GB FREE, then $0.02/GB/month
>
> **Typical monthly cost for 1000 emails**: < $5 USD

## 📧 Email Configuration

### Gmail Setup (Recommended)

#### 1. Enable 2-Factor Authentication
```
📋 Gmail Security Setup:
1. Go to Google Account settings
2. Security > 2-Step Verification  
3. Enable 2FA (required for App Passwords)
4. Verify with phone/authenticator
```

#### 2. Create App Password
```
📋 App Password Creation:
1. Google Account > Security > 2-Step Verification
2. Scroll down to "App passwords"
3. Select App: "Mail"
4. Select Device: "Other (custom name)"
5. Name: "DOCUFIND"
6. Copy the 16-character password
```

#### 3. Configure DOCUFIND
Edit `config/config.json`:
```json
{
  "email": {
    "username": "your-email@gmail.com",
    "password": "your-16-char-app-password", 
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "use_ssl": true
  }
}
```

### Outlook/Hotmail Setup

#### 1. Enable IMAP Access
```
📋 Outlook IMAP Setup:
1. Go to Outlook.com > Settings > Mail > Sync email
2. Enable "IMAP access"  
3. Save changes
```

#### 2. Configuration
```json
{
  "email": {
    "username": "your-email@outlook.com",
    "password": "your-outlook-password",
    "imap_server": "outlook.office365.com", 
    "imap_port": 993,
    "use_ssl": true
  }
}
```

### Other Email Providers

#### Yahoo Mail
```json
{
  "email": {
    "username": "your-email@yahoo.com", 
    "password": "your-app-password",
    "imap_server": "imap.mail.yahoo.com",
    "imap_port": 993,
    "use_ssl": true
  }
}
```

#### Custom IMAP Server
```json
{
  "email": {
    "username": "your-email@company.com",
    "password": "your-password", 
    "imap_server": "mail.company.com",
    "imap_port": 993,
    "use_ssl": true
  }
}
```

### Environment Variables Setup

Edit `.env` file:
```bash
# Email Configuration
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Google Configuration  
GOOGLE_CREDENTIALS_PATH=config/credentials.json

# Processing Configuration
DEBUG_MODE=true
LOG_LEVEL=INFO

# Optional: Notification Settings
NOTIFICATION_EMAIL=admin@company.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## ✅ Verification & Testing

### Step 1: Connection Tests

#### Test Email Connection
```bash
python scripts/test_email_connection.py
```

**Expected Output:**
```
🧪 Testing Email Connection...
✅ IMAP connection successful
✅ Authentication successful  
✅ Folder access successful
📧 Found 1,234 emails in INBOX
✅ Email connection test PASSED
```

#### Test Google APIs
```bash
python scripts/test_google_connection.py
```

**Expected Output:**
```
🧪 Testing Google API Connection...
✅ Drive API authentication successful
✅ Sheets API authentication successful
✅ Test folder created: DOCUFIND_TEST
✅ Test spreadsheet created
✅ Google API test PASSED
```

### Step 2: End-to-End Test

```bash
# Run minimal test processing
python src/find_documents_main.py --test-mode --max-emails=5
```

**Expected Output:**
```
🚀 DOCUFIND Test Mode Started
📧 Searching emails (limit: 5)...
✅ Found 5 test emails
📊 Processing 1/5 (20%)...
📄 Processing attachment: invoice.pdf
💰 Extracted: $45.99 USD from TechCorp  
☁️ Uploaded to: FIND_DOCUMENTS/Test/2024/08/Email_123/
📊 Processing complete!
✅ Success rate: 100%
```

### Step 3: Configuration Validation

```bash
python scripts/validate_config.py
```

**Validation Checklist:**
```
✅ Python version: 3.9.7
✅ All dependencies installed
✅ Configuration files present
✅ Google credentials valid
✅ Email credentials valid  
✅ Directory permissions OK
✅ Internet connectivity OK
⚠️ Warning: Large attachment handling not tested
✅ System ready for production use
```

## 🔧 Troubleshooting

### Common Installation Issues

#### 1. **Python Path Issues**
```bash
# Issue: Command 'python' not found
# Solution: Use python3 or add python to PATH

# Windows
py -3 --version

# macOS/Linux  
python3 --version
which python3
```

#### 2. **Virtual Environment Problems**
```bash
# Issue: venv activation fails
# Solution: Recreate virtual environment

rm -rf venv_find_docs
python -m venv venv_find_docs
source venv_find_docs/bin/activate  # or .bat on Windows
```

#### 3. **Google API Authentication**
```bash
# Issue: "Credentials not found" error
# Check: credentials.json location
ls -la config/credentials.json

# Issue: "Access denied" error  
# Solution: Check service account permissions in Google Cloud Console
```

#### 4. **Email Connection Failures**

**Gmail Issues:**
```
❌ Error: [AUTHENTICATIONFAILED] Invalid credentials
✅ Solution: Ensure 2FA enabled and App Password used

❌ Error: [IMAP] Connection timed out
✅ Solution: Check firewall/antivirus blocking port 993
```

**Outlook Issues:**
```  
❌ Error: IMAP not enabled
✅ Solution: Enable IMAP in Outlook.com settings

❌ Error: Too many login attempts
✅ Solution: Wait 15 minutes before retrying
```

#### 5. **Permission Errors**

**Windows:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**macOS/Linux:**
```bash
# Fix directory permissions
chmod 755 config/
chmod 600 config/credentials.json
chmod 600 .env
```

### Network & Firewall Issues

#### Required Ports & Domains
```
📋 Firewall Configuration:
Outbound Ports:
- 993 (IMAP over SSL)
- 443 (HTTPS for Google APIs)  
- 80 (HTTP redirects)

Domains to Allow:
- *.googleapis.com (Google APIs)
- *.google.com (OAuth)
- imap.gmail.com (Gmail IMAP)
- outlook.office365.com (Outlook IMAP)
```

#### Corporate Network Issues
```bash
# If behind corporate proxy
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8080

# Configure pip for proxy
pip install --proxy http://proxy.company.com:8080 -r requirements.txt
```

### Performance Issues

#### Slow Processing
```
🐌 Issue: Email processing very slow
✅ Solutions:
- Reduce max_results in config.json
- Use more specific date ranges
- Check internet connection speed
- Monitor Google API quota usage
```

#### Memory Issues  
```
🧠 Issue: High memory usage
✅ Solutions:
- Process smaller batches  
- Increase virtual memory/swap
- Close other applications
- Use streaming processing mode
```

## 🎯 Advanced Installation Options

### Docker Installation (Optional)

#### Build Docker Image
```bash
# Create Dockerfile (provided in repo)
docker build -t docufind:latest .

# Run with mounted config
docker run -v $(pwd)/config:/app/config docufind:latest
```

#### Docker Compose  
```yaml
version: '3.8'
services:
  docufind:
    build: .
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - DEBUG_MODE=false
```

### Automated Installation Script

#### Windows PowerShell
```powershell  
# Download and run installation script
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/yourusername/DOCUFIND/main/scripts/install.ps1" -OutFile "install.ps1"
.\install.ps1
```

#### macOS/Linux Bash
```bash
# Download and run installation script  
curl -sSL https://raw.githubusercontent.com/yourusername/DOCUFIND/main/scripts/install.sh | bash
```

### Development Installation

#### Additional Development Tools
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/

# Code quality checks
pylint src/
mypy src/
black src/
```

## 📋 Post-Installation Checklist

### ✅ Installation Complete When:
- [ ] Python 3.8+ installed and verified
- [ ] Virtual environment created and activated  
- [ ] All dependencies installed without errors
- [ ] Google Cloud project created and APIs enabled
- [ ] Service account created and JSON key downloaded
- [ ] Email provider configured with proper credentials
- [ ] Configuration files completed
- [ ] Connection tests pass
- [ ] End-to-end test completes successfully
- [ ] Directory permissions set correctly

### 🎉 Ready for Production When:
- [ ] All tests pass
- [ ] Configuration validated
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Error handling tested
- [ ] Performance benchmarked
- [ ] Security review completed

## 🚀 Next Steps

After successful installation:

1. **📖 Read the [Configuration Guide](CONFIGURATION.md)** for advanced settings
2. **👨‍💻 Follow the [User Guide](USER_GUIDE.md)** for usage instructions  
3. **🏗️ Review [Architecture](ARCHITECTURE.md)** to understand the system
4. **🔧 Check [Troubleshooting](TROUBLESHOOTING.md)** for common issues
5. **🔌 Explore [MCP Implementation](MCP_IMPLEMENTATION.md)** for advanced features

### Initial Processing Run

```bash
# Start with a small test batch
python src/find_documents_main.py \
  --start-date "2024-08-01" \
  --end-date "2024-08-31" \
  --keywords "invoice,bill" \
  --folder-name "August_Test" \
  --max-results 10
```

---

## 🆘 Getting Help

### Support Channels
- **📖 Documentation**: [docs/](docs/)
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/yourusername/DOCUFIND/issues)  
- **💬 Discussions**: [GitHub Discussions](https://github.com/yourusername/DOCUFIND/discussions)
- **📧 Email**: support@docufind.com

### Before Requesting Help
1. ✅ Check this installation guide thoroughly
2. ✅ Run the verification tests
3. ✅ Check logs in `logs/find_documents.log`
4. ✅ Search existing GitHub issues  
5. ✅ Provide system information and error logs

---

*Installation complete? Continue with [Configuration Guide](CONFIGURATION.md) →*