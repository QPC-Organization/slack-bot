import os
from dotenv import load_dotenv
from .bot import DailyStandupBot

load_dotenv('.env')

# Initialize bot with Socket Mode
slack_token = os.environ.get("SLACK_BOT_TOKEN")
app_token = os.environ.get("SLACK_APP_TOKEN")
coda_doc_id = os.environ.get("CODA_DOC_ID")
coda_api_token = os.environ.get("CODA_API_TOKEN")

if not app_token:
    print("❌ ERROR: SLACK_APP_TOKEN not found! Socket Mode cannot work.")
    exit(1)

if not slack_token:
    print("❌ ERROR: SLACK_BOT_TOKEN not found!")
    exit(1)

bot = DailyStandupBot(
    slack_token=slack_token,
    app_token=app_token,
    coda_doc_id=coda_doc_id,
    coda_api_token=coda_api_token
)

def main():
    """Main function to run the bot in Socket Mode."""
    print("🤖 Starting Daily Standup Bot in Socket Mode...")
    
    # Run the bot (Socket Mode will handle events)
    bot.run()

if __name__ == "__main__":
    main() 