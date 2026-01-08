# Slack Daily Unread Messages Summarizer

Automatically fetch your unread Slack messages daily, generate AI-powered summaries, and receive them as a DM. Runs at 9 AM EST via GitHub Actions—no servers required!

## Features

- 📬 **Automated Daily Summaries** - Runs every day at 9 AM EST
- 🤖 **AI-Powered** - Uses OpenAI GPT-4o-mini for concise, actionable summaries
- ✅ **Auto-Mark as Read** - Automatically marks messages as read after summarizing
- 🔗 **Clickable Links** - Direct links to conversations and messages
- 📊 **Comprehensive Coverage** - Fetches from public channels, private channels, DMs, and threads
- 🚀 **Simple Setup** - No servers to manage, runs entirely on GitHub Actions (free tier)
- 💰 **Cost-Effective** - ~$0.03-$0.06 per month for OpenAI API

## Prerequisites

Before you begin, you'll need:

1. **Slack Workspace** - Admin access to install a custom app
2. **GitHub Account** - To host the code and run automation
3. **OpenAI API Key** - Get one from [platform.openai.com](https://platform.openai.com/)

## Setup Guide

### Step 1: Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From scratch"**
3. Name it **"Daily Summary Bot"** and select your workspace

### Step 2: Configure OAuth Scopes

1. In your app settings, go to **"OAuth & Permissions"**

2. **Add User Token Scopes** (required for reading your unreads):
   - `channels:history` - Read public channel messages
   - `channels:read` - List public channels
   - `channels:write` - Mark public channels as read
   - `groups:history` - Read private channel messages
   - `groups:read` - List private channels
   - `groups:write` - Mark private channels as read
   - `im:history` - Read DM messages
   - `im:read` - List DMs
   - `im:write` - Mark DMs as read
   - `mpim:history` - Read group DM messages
   - `mpim:read` - List group DMs
   - `mpim:write` - Mark group DMs as read
   - `users:read` - Get user information

3. **Add Bot Token Scopes** (required for sending summaries):
   - `chat:write` - Send messages
   - `users:read` - Get user information

### Step 3: Install App to Workspace

1. Scroll up to **"OAuth Tokens for Your Workspace"**
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. Copy the **User OAuth Token** (starts with `xoxp-`)
5. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

### Step 4: Get Your Slack User ID

1. In Slack, click your profile picture
2. Click **"Profile"**
3. Click the **⋮** (three dots) → **"Copy member ID"**
4. Save this ID (starts with `U`, e.g., `U01234ABCDE`)

### Step 5: Create GitHub Repository

1. Create a new **public** repository on GitHub (e.g., `slack-daily-summary`)
2. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/YOUR_USERNAME/slack-daily-summary.git
   cd slack-daily-summary
   ```

3. Copy all the project files into this directory

4. Push to GitHub:
   ```bash
   git add .
   git commit -m "Initial commit: Slack summarizer"
   git push origin main
   ```

### Step 6: Add GitHub Secrets

1. In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** and add each of these:

| Secret Name | Value | Example |
|------------|-------|---------|
| `SLACK_USER_TOKEN` | User OAuth token from Step 3 | `xoxp-123...` |
| `SLACK_BOT_TOKEN` | Bot OAuth token from Step 3 | `xoxb-456...` |
| `SLACK_USER_ID` | Your member ID from Step 4 | `U01234ABCDE` |
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-proj-...` |

### Step 7: Test the Setup

#### Local Testing (Optional but Recommended)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create `.env` file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and fill in your credentials

4. Test connectivity:
   ```bash
   python test_connection.py
   ```

5. Run a test summary:
   ```bash
   python -m src.main
   ```

#### GitHub Actions Testing

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select **"Daily Slack Summary"** workflow
4. Click **"Run workflow"** → **"Run workflow"**
5. Wait a few minutes and check:
   - Workflow completes successfully (green checkmark)
   - You receive a summary DM in Slack

### Step 8: Verify Scheduled Runs

The workflow is configured to run automatically at 9 AM EST daily. After the first scheduled run:

1. Check the **Actions** tab for automatic runs
2. Verify you receive summaries in Slack
3. Check that messages are marked as read

## Usage

Once set up, the system runs automatically. No manual intervention needed!

### What You'll Receive

Every day at 9 AM EST, you'll get a Slack DM with:

- **Header** - Date and summary title
- **Per-Channel Summaries** - AI-generated overview of key points
- **View Messages Button** - Quick link to each conversation
- **Footer** - Total message and conversation counts

### Message Handling

- **All messages are automatically marked as read** after summary generation
- **To keep messages unread**: Click "View Messages" to open the conversation, then interact with it in Slack

## Project Structure

```
slack-reader/
├── src/
│   ├── config.py              # Configuration and environment variables
│   ├── slack_client.py        # Slack API wrapper with rate limiting
│   ├── message_fetcher.py     # Fetch unread messages
│   ├── message_processor.py   # Enrich and organize messages
│   ├── summarizer.py          # OpenAI integration
│   ├── mark_as_read.py        # Mark messages as read
│   ├── interaction_handler.py # Format Slack Block Kit messages
│   └── main.py                # Main orchestration
├── tests/                     # Test suite
├── .github/workflows/         # GitHub Actions automation
├── requirements.txt           # Python dependencies
├── test_connection.py         # Connection testing script
└── README.md                  # This file
```

## Configuration

### Environment Variables

All configuration is done via environment variables (GitHub Secrets for production, `.env` for local):

- `SLACK_USER_TOKEN` - Required
- `SLACK_BOT_TOKEN` - Required
- `SLACK_USER_ID` - Required
- `OPENAI_API_KEY` - Required
- `OPENAI_MODEL` - Optional (default: `gpt-4o-mini`)
- `LOG_LEVEL` - Optional (default: `INFO`)

### Customize Schedule

To change the run time, edit [.github/workflows/daily-summary.yml](.github/workflows/daily-summary.yml):

```yaml
schedule:
  - cron: '0 13 * * *'  # Change time here (UTC)
```

**Time Conversion**:
- 9 AM EST = 14:00 UTC
- 9 AM EDT = 13:00 UTC
- Use [crontab.guru](https://crontab.guru/) to help with cron syntax

### Customize Limits

Edit [src/config.py](src/config.py) to adjust:

- `MAX_MESSAGES_PER_CHANNEL` - Max messages to fetch per channel (default: 50)
- `MAX_THREAD_REPLIES` - Max replies to fetch per thread (default: 10)
- `MAX_MESSAGE_LENGTH` - Max chars per message for AI (default: 500)

## Testing

### Run Tests Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Test Connection

```bash
python test_connection.py
```

This verifies:
- Slack user token works
- Slack bot token works
- OpenAI API key works
- Can detect unread messages

## Troubleshooting

### No Summary Received

1. **Check GitHub Actions logs**:
   - Go to Actions tab → Latest run → View logs
   - Look for errors in the "Run summarizer" step

2. **Verify secrets are set**:
   - Settings → Secrets → Actions
   - Ensure all 4 secrets exist

3. **Check Slack app permissions**:
   - Go to api.slack.com/apps → Your app → OAuth & Permissions
   - Verify all scopes from Step 2 are added

### Error: "missing_scope"

Your Slack app is missing required permissions. Go to:
1. api.slack.com/apps → Your app
2. OAuth & Permissions
3. Add missing scopes listed in error
4. **Reinstall the app** to workspace (required after scope changes)

### Error: "invalid_auth"

Your tokens are invalid or expired:
1. Check that secrets match exactly (no extra spaces)
2. User tokens can expire - reinstall the app if needed
3. Verify token format: User = `xoxp-`, Bot = `xoxb-`

### Messages Not Marked as Read

1. Verify user token has `:write` scopes (channels:write, groups:write, etc.)
2. Check GitHub Actions logs for "Mark as read" errors
3. Reinstall Slack app if you added `:write` scopes after initial install

### OpenAI Rate Limit

Free tier: 3 requests/min, 200/day. Upgrade at platform.openai.com for higher limits.

### GitHub Actions Not Running

1. Ensure workflow file is in `.github/workflows/`
2. Check Actions tab → Enable workflows if disabled
3. Verify cron syntax is correct
4. Public repos: GitHub Actions is free
5. Private repos: Check you have available minutes

## Cost Breakdown

### Free
- **Slack API** - Completely free
- **GitHub Actions** - Free (up to 2000 minutes/month on public repos)

### Paid
- **OpenAI API** - ~$0.001-$0.002 per run = **$0.03-$0.06/month**
  - Model: gpt-4o-mini ($0.15 per 1M input tokens)
  - Typical usage: 2,000-5,000 tokens per day

**Total Monthly Cost: ~$0.03-$0.06** 🎉

## Security

- **Never commit** tokens or API keys to the repository
- Use **GitHub Secrets** for all credentials (encrypted at rest)
- `.env` file is in `.gitignore` (safe for local testing)
- Slack messages are sent to OpenAI but **not stored**
- Processing happens in-memory only

## Future Enhancements

Potential improvements (not currently implemented):

1. **Interactive "Keep Unread" buttons** - Requires webhook server
2. **Custom summary preferences** - Per-channel summary styles
3. **Priority channels** - Flag certain channels for detailed summaries
4. **Action item extraction** - Identify and highlight TODOs
5. **Multi-user support** - Deploy for entire team
6. **Analytics** - Track message volume trends

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure tests pass: `pytest tests/ -v`
6. Submit a pull request

## License

MIT License - Feel free to use and modify as needed.

## Support

Having issues?

1. Check [Troubleshooting](#troubleshooting) section above
2. Review GitHub Actions logs for errors
3. Run `python test_connection.py` locally
4. Open an issue on GitHub with:
   - Error message
   - Steps to reproduce
   - GitHub Actions logs (remove sensitive data)

## Acknowledgments

- Built with [Slack SDK for Python](https://slack.dev/python-slack-sdk/)
- AI summaries powered by [OpenAI](https://openai.com/)
- Automation via [GitHub Actions](https://github.com/features/actions)

---

**Enjoy your automated Slack summaries!** 🎉
