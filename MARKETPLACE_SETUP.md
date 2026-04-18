# Facebook Marketplace Monitor - Setup Guide

## What You Need to Do

### Step 1: Install ChromeDriver
1. **Check your Chrome version:**
   - Open Chrome
   - Click menu (⋮) → Settings
   - Click "About Chrome"
   - Note your version number (e.g., "Version 123.0.6312.86")

2. **Download matching ChromeDriver:**
   - Go to: https://chromedriver.chromium.org/
   - Click "Downloads"
   - Find your Chrome version
   - Download the Windows version
   - Extract the `chromedriver.exe` file

3. **Place ChromeDriver:**
   - Move `chromedriver.exe` to: `C:\Users\Owner\Downloads\`
   - (Or update the path in `marketplace_scraper.py` line ~99 if you put it elsewhere)

### Step 2: Install Python Dependencies
Run these commands in PowerShell/Command Prompt:

```powershell
pip install selenium requests
```

### Step 3: Set Up Telegram Notifications
1. **Get your Telegram Bot Token:**
   - Open Telegram
   - Search for "BotFather"
   - Send `/newbot`
   - Follow prompts to create a bot
   - Copy the API token (looks like: `123456789:ABCdefGHIjklmnoPQRstuvWXYZ`)

2. **Get your Chat ID:**
   - Create a private group or use your personal chat
   - Send a message to the bot
   - Go to: `https://api.telegram.org/bot{TOKEN}/getUpdates` (replace {TOKEN})
   - Find your chat_id in the response

3. **Set Environment Variables:**
   - Open PowerShell as Admin
   - Run:
   ```powershell
   [System.Environment]::SetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "your_token_here", "User")
   [System.Environment]::SetEnvironmentVariable("TELEGRAM_CHAT_ID", "your_chat_id_here", "User")
   ```
   - Restart PowerShell for changes to take effect

### Step 4: Test the Monitor
Run the script manually first:

```powershell
python C:\Users\Owner\.openclaw\workspace-openclaw-ai\marketplace_scraper.py
```

**Expected output:**
- Chrome browser opens (or runs in background)
- Script checks each Ohio location
- Logs results to console and `marketplace_monitor.log`
- Sends Telegram notification with any new matches

### Step 5: Schedule to Run Every 4 Hours (8 AM - 8 PM)
We need to create a Windows Task Scheduler job.

#### Option A: Using Task Scheduler (Recommended)
1. **Open Task Scheduler:**
   - Press `Win + R`
   - Type `taskschd.msc`
   - Press Enter

2. **Create new task:**
   - Right-click "Task Scheduler Library"
   - Click "Create Basic Task"
   - Name: "Marketplace Monitor"
   - Description: "Check Facebook Marketplace every 4 hours"
   - Click "Next"

3. **Set trigger:**
   - Choose "Daily"
   - Set start time: 8:00 AM
   - Check "Repeat task every: 4 hours"
   - Click "Next"

4. **Set action:**
   - Choose "Start a program"
   - Program: `C:\Program Files\Python311\python.exe` (adjust Python path)
   - Arguments: `C:\Users\Owner\.openclaw\workspace-openclaw-ai\marketplace_scraper.py`
   - Start in: `C:\Users\Owner\.openclaw\workspace-openclaw-ai\`
   - Click "Next"

5. **Finish:**
   - Check "Open the Properties dialog"
   - Click "Finish"
   - In Properties:
     - Go to "Conditions" tab
     - Uncheck "Stop if on battery power"
     - Go to "Settings" tab
     - Check "Run task as soon as possible after a scheduled start is missed"
   - Click OK

#### Option B: Using Windows PowerShell (Advanced)
```powershell
# Create trigger for 8 AM
$trigger = New-ScheduledTaskTrigger -At 08:00 -RepetitionInterval (New-TimeSpan -Hours 4) -RepetitionDuration (New-TimeSpan -Hours 12) -Daily

# Create action
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\Users\Owner\.openclaw\workspace-openclaw-ai\marketplace_scraper.py"

# Register task
Register-ScheduledTask -TaskName "Marketplace Monitor" -Trigger $trigger -Action $action -RunLevel Highest
```

## How It Works

1. **Every 4 hours** (8 AM, 12 PM, 4 PM, 8 PM), the monitor runs
2. **Visits Facebook Marketplace** for each Ohio location
3. **Scrapes listings** matching your criteria:
   - Brands: Toyota, Honda, Lexus
   - Years: 2010-2015
   - Price: Under $12,500
4. **Tracks seen listings** in `marketplace_listings.json` (doesn't notify about duplicates)
5. **Sends Telegram notification** with new matches (photo, price, link, location)
6. **Logs all activity** to `marketplace_monitor.log`

## Troubleshooting

### "ChromeDriver not found"
- Make sure you downloaded the correct version matching your Chrome
- Verify the path: `C:\Users\Owner\Downloads\chromedriver.exe`
- Update the path in `marketplace_scraper.py` line 99 if needed

### "Selenium not installed"
```powershell
pip install selenium --upgrade
```

### "Telegram notification failed"
- Verify environment variables are set correctly
- Test with: `echo $env:TELEGRAM_BOT_TOKEN`
- Make sure you've sent a message to the bot first

### Task Scheduler "Last Run Result: 0x1"
- Usually means Python path is wrong
- Verify Python location: `where python`
- Update the task with correct path

### Script runs but finds no listings
- Facebook Marketplace HTML changes frequently
- CSS selectors in script may need updating
- Check `marketplace_monitor.log` for details
- Open browser manually and verify selectors still work

## Files Created

- **marketplace_scraper.py** — Main monitoring script
- **marketplace_config.json** — Your search criteria
- **marketplace_listings.json** — Database of seen listings (auto-created)
- **marketplace_monitor.log** — Activity log (auto-created)
- **MARKETPLACE_SETUP.md** — This file

## Next Steps

1. **Download ChromeDriver** (matching your Chrome version)
2. **Install dependencies** (`pip install selenium requests`)
3. **Set environment variables** (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
4. **Test manually** by running the script
5. **Schedule in Task Scheduler** (every 4 hours, 8 AM-8 PM)
6. **Monitor the log** for any issues

## Support

If you run into issues:
- Check `marketplace_monitor.log` for error messages
- Verify ChromeDriver matches your Chrome version
- Make sure Telegram credentials are correct
- Test the script manually first before scheduling

Good luck finding those cars! 🚗
