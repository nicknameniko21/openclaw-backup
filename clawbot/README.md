# ClawBot - Setup Instructions

## What is ClawBot?
A marketing automation system that runs on Google Colab and appears as human social media activity.

## Features
- Human-like browser automation (Playwright)
- Random delays, scrolling, typing patterns
- Multi-platform: Twitter/X, LinkedIn
- Auto-engagement: likes, comments, posts
- AI-generated contextual responses
- Anti-detection (hides automation flags)

## Setup Steps

### 1. Open Google Colab
- Go to https://colab.research.google.com
- Create new notebook
- Set runtime to GPU (for faster processing)

### 2. Upload ClawBot
- Copy contents of `colab_bot.py`
- Paste into first cell
- Run cell (installs dependencies)

### 3. Configure Credentials
Edit this section in the code:
```python
CREDENTIALS = {
    'username': 'YOUR_USERNAME',  # Your real account
    'password': 'YOUR_PASSWORD'
}
```

### 4. Run Bot
- Execute all cells
- Bot will:
  - Login to platform
  - Scroll like human (random intervals)
  - Like posts matching keywords
  - Comment occasionally (30% chance)
  - Post original content
  - Take random breaks

### 5. Scale (Multiple Bots)
Create multiple Colab instances:
- Instance 1: Twitter account A
- Instance 2: Twitter account B
- Instance 3: LinkedIn account
- etc.

Each runs independently, appears as separate user.

## Safety / Anti-Detection
- Random delays between actions
- Human-like mouse movements (Playwright)
- Realistic typing speed
- Varied session duration
- Natural break patterns

## Warning
- Use real accounts (not fake ones)
- Don't exceed platform rate limits
- Start slow (1-2 hours/day)
- Gradually increase activity

## Customization
Edit these in the code:
- `keywords`: What content to engage with
- `human_delay`: Speed of actions
- `templates`: What posts to create
- `duration_hours`: How long to run

---
Ready to upload to Colab.
