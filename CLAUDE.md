# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Discord bot collection with multiple specialized bot implementations. The project contains several standalone bot scripts that demonstrate different Discord.py capabilities:

- `bot.py` - Main bot with scheduled messages, slash commands, and reaction handling
- `sample01_get_room_contents.py` - Channel message history export bot
- `sample02_get_room_log.py` - Real-time message logging bot  
- `sample03_get_guild_members.py` - Guild member list export bot

## Setup and Development

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.template .env
# Edit .env to add your Discord bot token
```

### Running Bots
Each bot is standalone and can be run independently:
```bash
python bot.py                        # Main bot with scheduled features
python sample01_get_room_contents.py # Message history export
python sample02_get_room_log.py      # Real-time logging
python sample03_get_guild_members.py # Member list export
```

## Architecture

### Common Bot Structure
All bots follow a consistent pattern:
- Use `discord.py==2.3.2` with modern async/await syntax
- Load Discord token from `.env` file via `python-dotenv`
- Configure intents based on required permissions
- Use `on_raw_reaction_add` for reliable reaction handling across message history
- Implement error handling with user-friendly Discord messages

### File Encoding Requirements
**CRITICAL: Always specify UTF-8 encoding to prevent character corruption with Japanese text**

All file operations MUST use explicit UTF-8 encoding:
```python
# Reading files
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Writing text files  
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)

# Writing CSV files
with open(filepath, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)

# Appending to files
with open(filepath, 'a', encoding='utf-8') as f:
    f.write(text)
```

This repository frequently handles Japanese text, and omitting `encoding='utf-8'` will cause character corruption issues. Always include this parameter in any file I/O operations.

### Key Components

**Intents Configuration:**
- `message_content = True` - Required for reading message text content
- `reactions = True` - For reaction-based triggers
- `members = True` - Only in sample03 for member list access

**Reaction-Based Triggers:**
All sample bots use 👍 (thumbs up) reactions as triggers to avoid accidental activation.

**File Generation Pattern:**
Bots that export data follow this pattern:
1. Generate temporary files in `/tmp/` directory
2. Create timestamped filenames
3. Check Discord file size limits (25MB)
4. Upload as Discord attachments
5. Clean up temporary files

### Specific Bot Features

**bot.py (Main Bot):**
- Scheduled tasks using `@tasks.loop(time=time(hour=6, minute=0))`
- Slash command synchronization for both global and guild-specific commands
- Command tree clearing and re-syncing on startup

**sample01_get_room_contents.py:**
- Batch message fetching (100 messages per batch with 2-second delays)
- Retrieves up to 2000 historical messages
- Exports to text format

**sample02_get_room_log.py:**
- Real-time message logging to persistent file (`room_log.txt`)
- Logs all messages including bot messages in target channel
- Appends to existing log file across bot restarts

**sample03_get_guild_members.py:**
- Requires `Server Members Intent` privilege in Discord Developer Portal
- Exports member data to CSV format with detailed information
- Handles large member lists with file size checking

## Discord Developer Portal Requirements

### Required Bot Permissions:
- Send Messages
- Read Message History
- Use Slash Commands
- Add Reactions

### Required Privileged Intents:
- Message Content Intent (for all bots)
- Server Members Intent (only for sample03)

### Hardcoded IDs in Code:
- Target Guild ID: `1394139562028306644`
- Target Channel ID: `1394203406574424104` (varies by bot)

When working with this codebase, be aware that these IDs are specific to the development Discord server and may need updating for different deployments.