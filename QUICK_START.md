# 🚀 Quick Start Guide

Get your Slack bot up and running in 10 minutes!

## ⚡ Prerequisites Check

- [ ] Python 3.8+ installed
- [ ] Slack workspace admin access
- [ ] Coda account
- [ ] Git repository cloned

## 🔧 Step 1: Environment Setup (2 min)

1. **Copy environment template:**
   ```bash
   cp env_template.txt .env
   ```

2. **Fill in your values in `.env`:**
   ```env
   SLACK_BOT_TOKEN=xoxb-your-token
   SLACK_SIGNING_SECRET=your-secret
   SLACK_APP_TOKEN=xapp-your-token
   SLACK_CHANNEL_ID=C0123456789
   CODA_API_TOKEN=your-coda-token
   CODA_DOC_ID=your-doc-id
   ```

## 🤖 Step 2: Slack App Setup (3 min)

1. **Go to [api.slack.com/apps](https://api.slack.com/apps)**
2. **Create New App** → "From scratch"
3. **Name it** (e.g., "Team Standup Bot")
4. **Enable Socket Mode** in sidebar
5. **Add OAuth Scopes:**
   - `chat:write`
   - `channels:read`
   - `users:read`
   - `channels:history`
   - `reactions:read`
   - `reactions:write`
6. **Install to Workspace**
7. **Copy tokens** to your `.env` file

## 📊 Step 3: Coda Setup (2 min)

1. **Create a new Coda doc**
2. **Create these tables:**
   - Health Check
   - Blocker
   - Stand Up
   - Blocker Resolution
   - KR Table
3. **Get API token** from [coda.io/account](https://coda.io/account)
4. **Copy table IDs** to `.env`

## 📦 Step 4: Install Dependencies (1 min)

```bash
pip install -r requirements.txt
```

## 🧪 Step 5: Test & Run (2 min)

1. **Test configuration:**
   ```bash
   python -c "from src.config import BotConfig; print('✅ Config OK')"
   ```

2. **Run the bot:**
   ```bash
   python src/app.py
   ```

3. **Check Slack** - bot should appear online!

## 🎯 Test Commands

Try these in Slack:
- `/help` - Show available commands
- `/checkin` - Start standup
- `/health` - Start health check

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| "Coda not configured" | Check `.env` file |
| "Missing signing secret" | Add `SLACK_SIGNING_SECRET` |
| Bot not responding | Verify OAuth scopes |
| Connection failed | Check `SLACK_APP_TOKEN` |

## 📚 Next Steps

- Read [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) for full details
- Customize timing in `config.py`
- Set up monitoring and logging
- Configure role-based routing

---

**Need help?** Check the logs or refer to the full documentation!
