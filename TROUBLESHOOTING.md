# 🚨 Troubleshooting Guide

This guide covers common issues and their solutions when working with the Slack bot.

## 🔍 Quick Diagnostic Commands

### 1. Check Bot Status
```bash
# Test configuration
python -c "from src.config import BotConfig; print('Config:', BotConfig.validate_config())"

# Test bot initialization
python -c "from src.bot import DailyStandupBot; print('Bot init OK')"

# Check environment variables
python -c "import os; print('SLACK_BOT_TOKEN:', 'SET' if os.getenv('SLACK_BOT_TOKEN') else 'MISSING')"
```

### 2. Check Logs
```bash
# View error logs
tail -f logs/bot_errors.log

# Check Flask logs
python -m flask run --debug 2>&1 | tee flask.log

# Check system logs
journalctl -u slack-bot -f  # If using systemd
```

## 🚨 Common Issues and Solutions

### 1. Bot Not Starting

#### Issue: "SLACK_BOT_TOKEN not found"
**Symptoms**: Bot exits immediately with token error
**Solution**:
```bash
# Check .env file exists
ls -la .env

# Verify token format
echo $SLACK_BOT_TOKEN | head -c 20

# Token should start with 'xoxb-'
```

#### Issue: "SLACK_APP_TOKEN not found"
**Symptoms**: Socket Mode connection fails
**Solution**:
```bash
# Check app token in .env
echo $SLACK_APP_TOKEN | head -c 20

# App token should start with 'xapp-'
# Enable Socket Mode in Slack app settings
```

#### Issue: Import errors
**Symptoms**: ModuleNotFoundError or ImportError
**Solution**:
```bash
# Install dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"

# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 2. Bot Not Responding

#### Issue: Bot appears offline
**Symptoms**: Bot shows as offline in Slack
**Solution**:
1. **Check OAuth scopes** in Slack app settings:
   - `chat:write`
   - `channels:read`
   - `users:read`
   - `channels:history`

2. **Verify app installation**:
   - Go to Slack app settings
   - Check "Install App" status
   - Reinstall if necessary

3. **Check bot permissions**:
   - Ensure bot is added to channels
   - Check bot user permissions

#### Issue: Commands not working
**Symptoms**: Slash commands return "command not found"
**Solution**:
1. **Verify command registration**:
   ```python
   # In src/bot.py, check setup_commands method
   self.app.command("/checkin")(self.standup_handler.handle_checkin)
   ```

2. **Check command permissions**:
   - Commands must be registered with Slack
   - Verify bot has required scopes

3. **Test command manually**:
   ```python
   # Test command handler directly
   python -c "from src.handlers.standup_handlers import StandupHandler; print('Handler OK')"
   ```

### 3. Coda Integration Issues

#### Issue: "Coda not configured"
**Symptoms**: Bot can't store data in Coda
**Solution**:
```bash
# Check Coda environment variables
echo "CODA_API_TOKEN: ${CODA_API_TOKEN:+SET}"
echo "CODA_DOC_ID: ${CODA_DOC_ID:+SET}"

# Test Coda connection
python -c "
from src.coda_service import CodaService
coda = CodaService()
print('Coda configured:', coda.is_configured())
"
```

#### Issue: "Failed to store response"
**Symptoms**: Data not being saved to Coda
**Solution**:
1. **Verify API token permissions**:
   - Check token has write access to doc
   - Verify token hasn't expired

2. **Check table IDs**:
   ```bash
   # Verify table IDs in .env
   grep -E "^(Health_Check|Blocker|Stand_Up)=" .env
   ```

3. **Test Coda API directly**:
   ```python
   import requests
   
   headers = {"Authorization": f"Bearer {os.getenv('CODA_API_TOKEN')}"}
   response = requests.get(f"https://coda.io/apis/v1/docs/{os.getenv('CODA_DOC_ID')}", headers=headers)
   print("Coda API status:", response.status_code)
   ```

#### Issue: Table schema mismatch
**Symptoms**: Data format errors when writing to Coda
**Solution**:
1. **Check table structure**:
   ```python
   # Get table schema
   from src.coda_service import CodaService
   coda = CodaService()
   schema = coda.get_table_schema(table_id)
   print("Table schema:", schema)
   ```

2. **Verify column names** match expected format
3. **Check data types** are compatible

### 4. Socket Mode Issues

#### Issue: "Socket Mode connection failed"
**Symptoms**: Bot can't establish WebSocket connection
**Solution**:
1. **Check app token**:
   ```bash
   echo $SLACK_APP_TOKEN | head -c 20
   # Should start with 'xapp-'
   ```

2. **Verify Socket Mode enabled**:
   - Go to Slack app settings
   - Check "Socket Mode" is enabled
   - Generate new app-level token if needed

3. **Check network connectivity**:
   ```bash
   # Test connection to Slack
   curl -I https://slack.com/api/apps.connections.open
   ```

4. **Fallback to webhook mode**:
   ```python
   # In src/bot.py, modify initialization
   bot = DailyStandupBot(socket_mode=False)  # Disable Socket Mode
   ```

#### Issue: Connection drops frequently
**Symptoms**: Bot disconnects and reconnects repeatedly
**Solution**:
1. **Check network stability**
2. **Implement reconnection logic**:
   ```python
   # Add reconnection handling
   import asyncio
   
   async def maintain_connection(self):
       while True:
           try:
               await self.socket_client.connect()
               await asyncio.sleep(30)  # Keep alive
           except Exception as e:
               logger.error(f"Connection lost: {e}")
               await asyncio.sleep(5)  # Wait before retry
   ```

### 5. Performance Issues

#### Issue: Slow response times
**Symptoms**: Bot takes >5 seconds to respond
**Solution**:
1. **Check API rate limits**:
   ```python
   # Monitor Slack API calls
   from slack_sdk.web import WebClient
   client = WebClient(token=token)
   response = client.auth_test()
   print("API response time:", response.get('response_metadata', {}).get('next_cursor'))
   ```

2. **Optimize database queries**:
   ```python
   # Use batch operations
   await coda.batch_add_rows(table_id, rows)
   
   # Cache frequently accessed data
   from functools import lru_cache
   @lru_cache(maxsize=128)
   def get_user_info(user_id):
       # Expensive operation
       pass
   ```

3. **Check system resources**:
   ```bash
   # Monitor CPU and memory
   top -p $(pgrep -f "python.*app.py")
   
   # Check disk I/O
   iostat -x 1
   ```

#### Issue: High memory usage
**Symptoms**: Bot consumes excessive memory
**Solution**:
1. **Check for memory leaks**:
   ```python
   import gc
   import sys
   
   def check_memory():
       gc.collect()
       print("Memory usage:", sys.getsizeof(globals()))
   ```

2. **Limit data caching**:
   ```python
   # Clear old data periodically
   self.standup_responses.clear()  # Clear old responses
   self.tracked_blockers.clear()   # Clear resolved blockers
   ```

### 6. Authentication Issues

#### Issue: "Invalid signing secret"
**Symptoms**: Slack rejects bot requests
**Solution**:
1. **Verify signing secret**:
   ```bash
   echo $SLACK_SIGNING_SECRET | head -c 20
   # Should match app settings exactly
   ```

2. **Check app configuration**:
   - Go to Slack app settings
   - Copy signing secret from "Basic Information"
   - Update `.env` file

3. **Test signature validation**:
   ```python
   from slack_sdk.signature import SignatureVerifier
   
   verifier = SignatureVerifier(signing_secret)
   is_valid = verifier.is_valid(request_body, headers)
   print("Signature valid:", is_valid)
   ```

#### Issue: Token expired
**Symptoms**: API calls return 401 errors
**Solution**:
1. **Check token expiration**:
   ```python
   from slack_sdk.web import WebClient
   
   client = WebClient(token=token)
   try:
       response = client.auth_test()
       print("Token valid for user:", response['user'])
   except Exception as e:
       print("Token error:", e)
   ```

2. **Regenerate tokens**:
   - Go to Slack app OAuth settings
   - Revoke old tokens
   - Generate new tokens
   - Update `.env` file

### 7. Database Issues

#### Issue: MongoDB connection failed
**Symptoms**: Fallback storage not working
**Solution**:
1. **Check MongoDB URI**:
   ```bash
   echo $MONGODB_URI | head -c 20
   # Should be valid MongoDB connection string
   ```

2. **Test MongoDB connection**:
   ```python
   from pymongo import MongoClient
   
   try:
       client = MongoClient(os.getenv('MONGODB_URI'))
       db = client[os.getenv('MONGODB_DB_NAME')]
       print("MongoDB connected:", db.name)
   except Exception as e:
       print("MongoDB error:", e)
   ```

3. **Check MongoDB service**:
   ```bash
   # If running locally
   sudo systemctl status mongod
   
   # Check MongoDB logs
   tail -f /var/log/mongodb/mongod.log
   ```

## 🔧 Advanced Troubleshooting

### 1. Enable Debug Mode
```python
# In .env
FLASK_DEBUG=True
LOG_LEVEL=DEBUG

# In code
import logging
logging.basicConfig(level=logging.DEBUG)

# For Slack SDK
import os
os.environ['SLACK_LOG_LEVEL'] = 'DEBUG'
```

### 2. Network Diagnostics
```bash
# Check DNS resolution
nslookup slack.com

# Test connectivity
ping slack.com

# Check firewall rules
sudo ufw status  # Ubuntu
sudo iptables -L  # CentOS/RHEL
```

### 3. System Resource Monitoring
```bash
# Monitor system resources
htop

# Check disk space
df -h

# Monitor network connections
netstat -tulpn | grep python
```

### 4. Slack API Testing
```bash
# Test Slack API directly
curl -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
     "https://slack.com/api/auth.test"

# Test bot info
curl -H "Authorization: Bearer $SLACK_BOT_USER_ID" \
     "https://slack.com/api/users.info?user=$SLACK_BOT_USER_ID"
```

## 📊 Monitoring and Alerting

### 1. Health Check Endpoint
```python
# Add health check endpoint
@app.route('/health')
def health_check():
    checks = {
        'slack_connection': check_slack_connection(),
        'coda_connection': check_coda_connection(),
        'database_health': check_database_health(),
        'bot_status': get_bot_status()
    }
    return jsonify(checks)
```

### 2. Automated Monitoring
```bash
# Set up cron job for health checks
*/5 * * * * curl -f http://localhost:3000/health || echo "Bot unhealthy"

# Monitor logs for errors
tail -f logs/bot_errors.log | grep -i error | mail -s "Bot Error Alert" admin@company.com
```

### 3. Performance Metrics
```python
# Track response times
import time

def track_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        log_performance_metric(func.__name__, duration)
        return result
    return wrapper
```

## 🆘 Emergency Procedures

### 1. Bot Unresponsive
1. **Check bot status**: `curl http://localhost:3000/health`
2. **Restart bot**: `pm2 restart slack-bot` or `sudo systemctl restart slack-bot`
3. **Check logs**: `tail -f logs/bot_errors.log`
4. **Verify Slack app**: Check app status in Slack workspace

### 2. Data Loss
1. **Check Coda tables**: Verify data integrity
2. **Check MongoDB**: Review fallback storage
3. **Restore from backup**: Use Coda version history
4. **Investigate cause**: Check error logs and API responses

### 3. Security Breach
1. **Revoke tokens**: Regenerate all Slack and Coda tokens
2. **Check logs**: Review access patterns
3. **Update credentials**: Change all passwords and API keys
4. **Audit permissions**: Review bot and app permissions

## 📞 Getting Help

### 1. Self-Service Resources
- **Documentation**: [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)
- **Development Guide**: [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)
- **Code Comments**: Inline documentation in source code
- **Test Files**: Examples of proper usage

### 2. External Resources
- **Slack API Docs**: [api.slack.com](https://api.slack.com/)
- **Coda API Docs**: [coda.io/developers](https://coda.io/developers)
- **Python Documentation**: [docs.python.org](https://docs.python.org/)
- **Flask Documentation**: [flask.palletsprojects.com](https://flask.palletsprojects.com/)

### 3. Community Support
- **GitHub Issues**: Report bugs and request features
- **Slack Community**: Join developer communities
- **Stack Overflow**: Search for similar issues
- **Python Discord**: Get help from Python developers

---

## 📝 Issue Reporting Template

When reporting issues, include:

```
**Environment:**
- OS: [Windows/macOS/Linux]
- Python Version: [3.8/3.9/3.10]
- Bot Version: [commit hash or version]

**Issue Description:**
[Describe what happened and what you expected]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Error Messages:**
[Copy full error messages and stack traces]

**Logs:**
[Relevant log entries]

**Additional Context:**
[Any other relevant information]
```

---

*This troubleshooting guide covers the most common issues. For specific problems, check the logs and refer to the development guide for advanced debugging techniques.*
