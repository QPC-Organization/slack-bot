# Slack Bot Project - Comprehensive Documentation

Project Overview
This is a sophisticated Slack bot designed for team management and productivity tracking. The bot handles daily standups, health checks, blocker management, and integrates with Coda for data storage and analysis.

Key Features
- *Daily Standup Management*: Automated standup prompts and response collection
- *Health Check System*: Team wellness monitoring and tracking
- *Blocker Management*: Issue tracking, escalation, and resolution workflows
- *Key Results (KR) Management*: OKR tracking and search functionality
- *Coda Integration*: Data storage and analytics
- *Role-Based Routing*: Intelligent message routing based on user roles
- *AI-Powered Features*: Mistral AI integration for enhanced functionality

Architecture Overview

Technology Stack
- *Backend*: Python 3.x with Flask
- *Slack Integration*: Slack SDK with Socket Mode support
- *Database*: Coda (primary)
- *AI Services*: Mistral AI API
- *Scheduling*: Python schedule library
- *Configuration*: Environment variables with dotenv

Project Structure
slack-bot-1/
├── src/                          # Main application code
│   ├── app.py                   # Application entry point
│   ├── bot.py                   # Core bot logic (main class)
│   ├── config.py                # Configuration management
│   ├── handlers/                # Event and command handlers
│   │   ├── blocker_handlers.py  # Blocker-related functionality
│   │   ├── health_handlers.py   # Health check management
│   │   ├── kr_handlers.py       # Key Results handling
│   │   ├── modal_handlers.py    # Modal form processing
│   │   └── submission_handlers.py # Form submissions
│   ├── coda_service.py          # Coda API integration
│   ├── org_metadata_service.py  # Organization metadata service
│   └── utilities.py             # Utility functions
├── tests/                       # Test suite
├── requirements.txt             # Python dependencies
├── package.json                 # Node.js dependencies (for some features)
└── .env                        # Environment configuration

Setup and Installation

Prerequisites
- Python 3.8+
- Node.js 16+ (for some features)
- Slack workspace with admin permissions
- Coda account and API access
- Mistral AI API key (optional but recommended)

1. Environment Setup

Create a *.env* file in the project root:

env
Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_CHANNEL_ID=C0123456789
SLACK_ESCALATION_CHANNEL=leads
SLACK_BOT_USER_ID=U0912DJRNSF

Coda Configuration
CODA_API_TOKEN=your-coda-api-token-here
CODA_DOC_ID=your-coda-doc-id-here
Health_Check=your-health-check-table-id
Blocker=your-blocker-table-id
Stand_Up=your-standup-table-id
Blocker_Resolution=your-resolution-table-id
KR_Table=your-kr-table-id
After_Health_Check=your-after-health-check-table-id
Response=your-response-table-id
ERROR_TABLE=error_logs

AI Configuration
MISTRAL_API_KEY=your-mistral-api-key-here

Timing Configuration
STANDUP_TIME=09:00
RESPONSE_DEADLINE=10:00
REMINDER_TIME=09:30
AUTO_ESCALATION_DELAY_HOURS=2

Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=3000
FLASK_DEBUG=False

2. Slack App Configuration

1. *Create Slack App*:
   - Go to [api.slack.com/apps](https://api.slack.com/apps)
   - Click "Create New App" → "From scratch"
   - Name your app and select workspace

2. **Configure OAuth Scopes**:
   - *chat:write* - Send messages
   - *channels:read* - Read channel information
   - *users:read* - Read user information
   - *channels:history* - Read channel messages
   - *reactions:read* - Read reactions
   - *reactions:write* - Add reactions

3. *Enable Socket Mode*:
   - Go to "Socket Mode" in the sidebar
   - Enable Socket Mode
   - Generate app-level token

4. *Install App to Workspace*:
   - Go to "OAuth & Permissions"
   - Click "Install to Workspace"
   - Copy Bot User OAuth Token

3. Coda Setup

1. *Create Tables*:
   - Health Check table
   - Blocker table
   - Stand Up table
   - Blocker Resolution table
   - KR Table
   - After Health Check table
   - Response table
   - Error logs table

2. *Get API Token*:
   - Go to [coda.io/account](https://coda.io/account)
   - Generate API token

3. *Get Table IDs*:
   - Open table in Coda
   - Copy ID from URL or use API to list tables

4. Install Dependencies

bash
Python dependencies
pip install -r requirements.txt

Node.js dependencies (if needed)
npm install

Running the Bot

### Development Mode
bash
# Run the bot directly (recommended)
python -m src.app

# Alternative: Run with Flask development server
python -m flask run

# Alternative: Run the app.py file directly
python src/app.py

Production Mode
bash
# Run the bot (recommended)
python -m src.app

# Alternative: Run the app.py file directly
python src/app.py

Socket Mode vs Webhook Mode
- *Socket Mode* (Recommended): Uses WebSocket connection, more reliable
- *Webhook Mode*: Traditional HTTP webhook approach

Core Functionality

1. Daily Standup Management

The bot automatically sends standup prompts and collects responses:

- *Automatic Timing*: Configurable standup time (default: 9:00 AM)
- *Response Collection*: Thread-based response gathering
- *Progress Tracking*: Monitors who has responded
- *Escalation*: Automatic escalation for blockers or delays

*Commands*:
- */checkin* or *!checkin* - Start standup check-in
- */standup* - Manual standup trigger

2. Health Check System

Monitors team wellness and engagement:

- *Daily Health Checks*: Automated wellness prompts
- *Response Tracking*: Monitors participation
- *Escalation*: Alerts for concerning responses
- *Analytics*: Coda-based reporting

*Commands*
- */health* - Start health check
- */health-status* - Check current health status

3. Blocker Management

Comprehensive issue tracking and resolution:

- *Blocker Reporting*: Easy blocker submission
- *Escalation Workflow*: Automatic escalation to leads
- *Resolution Tracking*: Follow-up until resolution
- *Analytics*: Blocker patterns and resolution times

*Commands*:
- */blocked* or *!blocked* - Report a blocker
- */blocker-status* - Check blocker status
- */resolve-blocker* - Mark blocker as resolved

4. Key Results (KR) Management

OKR tracking and search functionality:

- *KR Search*: Find relevant Key Results
- *Sprint Planning*: KR assignment and tracking
- *Progress Updates*: KR status tracking
- *Integration*: Links to blocker and standup systems

*Commands*:
- */kr [search]* or *!kr [search]* - Search for KRs
- */kr* or *!kr* - Get KR help


5. Role-Based Routing

Intelligent message routing based on user roles:

- *Department Detection*: Automatic department identification
- *SME Routing*: Subject Matter Expert assignment
- *Escalation Paths*: Role-based escalation workflows
- *Dynamic Channels*: Context-aware channel selection

Configuration and Customization

Timing Configuration
python
# In config.py or .env
STANDUP_TIME = "09:00"           # Daily standup time
RESPONSE_DEADLINE = "10:00"      # Response deadline
REMINDER_TIME = "09:30"          # Reminder time
AUTO_ESCALATION_DELAY_HOURS = 2  # Escalation delay


Message Templates
Customize bot messages in *config.py*:
- *STANDUP_MESSAGE_TEMPLATE*
- *FOLLOWUP_MESSAGE_TEMPLATE*
- *ESCALATION_MESSAGE_TEMPLATE*

Channel Configuration
- *SLACK_CHANNEL_ID*: Default channel
- *SLACK_ESCALATION_CHANNEL*: Escalation channel
- Role-based channels in *org_metadata_service.py*

Testing
Running Tests
bash
Run all tests
python -m pytest

Run specific test file
python -m pytest tests/test_bot_core.py

Run with coverage
python -m pytest --cov=src


Test Structure
- *test_bot_core.py*: Core bot functionality
- *test_slack_integration.py*: Slack API integration
- *test_aggression.py*: Aggression detection
- *conftest.py*: Test configuration and fixtures

Monitoring and Logging

Log Files
- *logs/bot_errors.log*: Error logging
- Coda error table: Structured error tracking

Health Monitoring
- Bot status checks
- API connectivity monitoring
- Response time tracking
- Error rate monitoring

Security Considerations

Environment Variables
- Never commit *.env* files
- Use secure token storage
- Rotate tokens regularly

Slack Security
- Validate signing secrets
- Verify request authenticity
- Implement rate limiting

API Security
- Secure Coda API tokens
- Implement request validation
- Monitor API usage

Troubleshooting
Common Issues

1. *"Coda not configured"*
   - Check environment variables
   - Verify API token permissions
   - Confirm table IDs

2. *"Missing signing secret"*
   - Add *SLACK_SIGNING_SECRET* to *.env*
   - Verify Slack app configuration

3. *Socket Mode connection issues*
   - Check *SLACK_APP_TOKEN*
   - Verify Socket Mode is enabled
   - Check network connectivity

4. *Bot not responding*
   - Verify bot is installed in the workspace
   - Check OAuth scopes
   - Review error logs

Debug Mode
python
Enable debug logging
FLASK_DEBUG = True

Check bot status
python -c "from src.bot import DailyStandupBot; print(DailyStandupBot().config.validate_config())"

Deployment
Local Development
bash
# Run the bot (recommended)
python -m src.app

# Development server with Flask
python -m flask run --debug

# Direct execution of app.py
python src/app.py

Production Deployment
1. *Environment Setup*: Configure production *.env*
2. *Process Management*: Use PM2 or systemd
3. *Monitoring*: Set up health checks
4. *Logging*: Configure production logging
5. *Backup*: Regular Coda data backups

Docker Deployment
dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "src/app.py"]

SSH Access and Server Management

For server access and deployment management, use the following SSH connection:

```bash
ssh -i "file path" ubuntu@ip
```

**Important Notes:**
- Keep the PEM file secure and never share it
- The server is configured for Ubuntu
- Contact the project mentor for additional server access details and deployment information
- Do not share sensitive server credentials or internal network information

API Reference

Core Classes

DailyStandupBot
Main bot class handling all functionality:
python
bot = DailyStandupBot(socket_mode=True, app_token="xapp-...")
bot.run()

CodaService
Coda integration service:
python
coda = CodaService()
coda.add_response(user_id, response, timestamp)

OrgMetadataService
Organization metadata and routing:
python
org_service = OrgMetadataService(client)
department = org_service.get_user_department(user_id)

Key Methods

Standup Management
- *send_daily_standup()*: Send standup prompt
- *process_standup_response()*: Handle responses
- *escalate_blocker()*: Escalate issues

Health Check Management
- *send_health_check()*: Send health prompt
- *process_health_response()*: Handle responses
- *escalate_health_issue()*: Escalate concerns

Blocker Management
- *report_blocker()*: Report new blocker
- *track_blocker()*: Track blocker status
- *resolve_blocker()*: Mark as resolved

Contributing

Development Workflow
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

Code Standards
- Follow PEP 8 for Python
- Add type hints where possible
- Include docstrings for functions
- Write tests for new features

Testing Requirements
- Maintain test coverage >80%
- All new features must have tests
- Integration tests for Slack features

Support and Maintenance
Regular Maintenance
- *Daily*: Monitor bot status and error logs
- *Weekly*: Review Coda data and analytics
- *Monthly*: Update dependencies and security patches
- *Quarterly*: Review and optimize bot performance

Emergency Procedures
1. Check bot status and logs
2. Verify Slack app configuration
3. Check Coda API connectivity
4. Restart the bot if necessary
5. Escalate to the development team

Contact Information
- *Primary Developer*: [Your Name]
- *Slack Channel*: #bot-support
- *Documentation*: This file and README.md
- *Code Repository*: [Repository URL]
- *Project Mentor*: Contact the mentor for additional server access details, deployment information, and advanced configuration options

Future Enhancements

Planned Features
- *Advanced Analytics*: Enhanced reporting and insights
- *Mobile App*: Companion mobile application
- *Integration APIs*: Webhook endpoints for external systems
- *Machine Learning*: Predictive analytics and recommendations

Technical Improvements
- *Performance Optimization*: Response time improvements
- *Scalability*: Multi-workspace support
- *Security*: Enhanced authentication and authorization
- *Monitoring*: Advanced health monitoring and alerting

Quick Start Checklist

- [ ] Set up environment variables in *.env*
- [ ] Configure Slack app with required scopes
- [ ] Set up Coda tables and get API tokens
- [ ] Install Python dependencies
- [ ] Test bot connectivity
- [ ] Configure timing and channels
- [ ] Test core functionality
- [ ] Set up monitoring and logging
- [ ] Deploy to production environment

---

*This documentation was created to help developers quickly understand and work with the Slack bot project. For additional questions or support, refer to the contact information above or check the project repository. For server access details and advanced deployment information, contact the project mentor.*
