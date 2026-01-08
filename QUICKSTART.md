# Quick Start Guide

Get your Slack summarizer running in 15 minutes!

## Prerequisites Checklist

- [ ] Slack workspace admin access
- [ ] GitHub account
- [ ] OpenAI API key

## 5-Minute Setup

### 1. Create Slack App (5 min)

```
1. Visit: https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "Daily Summary Bot"
4. Select your workspace
```

### 2. Add Permissions (2 min)

Go to **OAuth & Permissions** and add:

**User Token Scopes:**
```
channels:history, channels:read, channels:write
groups:history, groups:read, groups:write
im:history, im:read, im:write
mpim:history, mpim:read, mpim:write
users:read
```

**Bot Token Scopes:**
```
chat:write, users:read
```

### 3. Install & Get Tokens (1 min)

```
1. Click "Install to Workspace" → "Allow"
2. Copy User OAuth Token (xoxp-...)
3. Copy Bot OAuth Token (xoxb-...)
4. Get your User ID from Slack profile → Copy member ID
```

### 4. GitHub Setup (5 min)

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/slack-daily-summary.git
cd slack-daily-summary

# Copy project files here

# Commit and push
git add .
git commit -m "Initial commit"
git push origin main
```

### 5. Add GitHub Secrets (2 min)

Go to **Settings → Secrets and variables → Actions**:

| Secret | Value |
|--------|-------|
| `SLACK_USER_TOKEN` | xoxp-... |
| `SLACK_BOT_TOKEN` | xoxb-... |
| `SLACK_USER_ID` | U... |
| `OPENAI_API_KEY` | sk-... |

### 6. Test It! (1 min)

```
1. Go to Actions tab
2. Select "Daily Slack Summary"
3. Click "Run workflow"
4. Wait ~2 minutes
5. Check Slack for your summary! 🎉
```

## Local Testing (Optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Test connection
python test_connection.py

# Run manual summary
python -m src.main
```

## What's Next?

- **Wait for 9 AM EST** tomorrow for your first automatic summary
- **Check Actions tab** to see the workflow history
- **Customize** the schedule in `.github/workflows/daily-summary.yml`

## Common Issues

**No summary received?**
- Check Actions logs for errors
- Verify all 4 secrets are set correctly
- Ensure Slack app has all required scopes

**"missing_scope" error?**
- Add the missing scope in Slack app settings
- **Reinstall the app** to workspace (required!)

**Need help?**
- See [README.md](README.md) for full troubleshooting guide
- Check [test_connection.py](test_connection.py) output
- Review GitHub Actions logs

---

**Done! Your automated summaries start tomorrow at 9 AM EST** ⏰
