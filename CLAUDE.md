# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive Discord bot sample code collection designed for learning discord.py development. The repository contains 11 specialized bot implementations demonstrating different Discord.py capabilities and integration patterns.

### Sample Categories

**Basic Discord Features:**
- `bot.py` - Main bot with scheduled messages, slash commands, and reaction handling
- `sample01_get_room_contents.py` - Channel message history export bot
- `sample02_get_room_log.py` - Real-time message logging bot  
- `sample03_get_guild_members.py` - Guild member list export bot
- `sample04_grant_role.py` - Role management bot

**AI Integration Examples:**
- `sample05_chatgpt.py` - ChatGPT text integration bot
- `sample06_chatgpt_voice.py` - ChatGPT voice message integration bot
- `sample07_chatgpt_image.py` - ChatGPT image analysis bot
- `sample08_meeting_log.py` - Meeting log generation bot

**Database-Driven Applications:**
- `sample09_memo.py` - Message copying/memo bot
- `sample10_task.py` - Task management bot with Supabase backend
- `sample11_point_system.py` - Point system bot with Supabase backend

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.template .env
# Edit .env to add required API keys and database credentials
```

### Running Individual Bots
Each bot is standalone and can be run independently:
```bash
python bot.py                        # Main bot with scheduled features
python sample01_get_room_contents.py # Message history export
python sample02_get_room_log.py      # Real-time logging
python sample03_get_guild_members.py # Member list export
python sample04_grant_role.py        # Role management
python sample05_chatgpt.py           # ChatGPT text integration
python sample06_chatgpt_voice.py     # ChatGPT voice integration
python sample07_chatgpt_image.py     # ChatGPT image integration
python sample08_meeting_log.py       # Meeting log generation
python sample09_memo.py              # Message copying/memo
python sample10_task.py              # Task management with DB
python sample11_point_system.py      # Point system with DB
```

### Database Setup for samples 10 & 11
For bots using Supabase PostgreSQL backend, execute schema files in Supabase SQL Editor:
- `sample10_task_schema.sql` - Task management tables
- `sample11_point_system_schema.sql` - Point system tables

## Architecture Overview

### Sample Code Structure
This is a **learning-focused sample collection** where each bot demonstrates specific discord.py patterns:

**Educational Design Principles:**
- Each sample is self-contained and independent
- Progressive complexity from basic message handling to database integration
- Consistent coding patterns across all samples for easy understanding
- Real-world applicable examples (task management, point systems, AI integration)

### Common Bot Architecture Pattern
All bots follow a consistent educational structure:
- Use `discord.py==2.3.2` with modern async/await syntax
- Load Discord token from `.env` file via `python-dotenv`
- Configure intents based on required permissions
- Use `on_raw_reaction_add` for reliable reaction handling across message history
- Implement comprehensive error handling with user-friendly Discord messages

### Database Architecture (Educational Examples)
Two advanced samples demonstrate database integration patterns:

**sample10_task.py (Task Management System):**
- `TaskManager` class demonstrating database connection management
- `tasks` table: id, title, completed, timestamps
- Reaction-based UI pattern: 👍 (create), ❤️ (list), ✅ (toggle completion)
- UPSERT patterns for data consistency
- Educational focus: CRUD operations, database transactions

**sample11_point_system.py (Point System):**
- `PointSystem` class with robust connection management
- `user_points` table: user_id, points, timestamps
- `point_grants` table: message_id, giver_user_id, receiver_user_id (prevents duplicates)
- Reaction-based UI: 👍 (grant points), ❤️ (check points)
- Educational focus: duplicate prevention, member info retrieval, transaction handling

### AI Integration Patterns (Educational Examples)
Samples 05-08 demonstrate external API integration:
- OpenAI API integration with proper error handling
- Async/await patterns for API calls
- Environment variable management for API keys
- Different input types: text, voice, images

### Critical Implementation Patterns

**Member Information Retrieval (Handles All User Types):**
```python
try:
    user = await guild.fetch_member(user_id)
except discord.NotFound:
    user = None
except discord.Forbidden:
    user = guild.get_member(user_id)  # Fallback for permissions
```

**File Encoding for Japanese Text (Critical):**
```python
# Always specify UTF-8 encoding to prevent character corruption
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(japanese_text)
```

**Database Connection Management Pattern:**
```python
class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.connection = None
    
    def connect(self):
        try:
            self.connection = psycopg2.connect(**self.config)
            return True
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            return False
```

### Sample-Specific Learning Objectives

**Basic Samples (01-04):**
- Message history retrieval and file generation
- Real-time event handling and logging
- Guild member management and CSV export
- Role management and permissions

**AI Integration Samples (05-08):**
- External API integration patterns
- Error handling for third-party services
- Different media type processing (text, voice, images)
- Response formatting and user interaction

**Advanced Database Samples (10-11):**
- Database schema design and migration
- CRUD operation implementation
- Transaction management and rollback
- Duplicate prevention strategies
- Complex user interaction flows

## Environment Configuration

### Required Environment Variables
```env
# Discord Bot (all samples)
DISCORD_TOKEN=your_discord_bot_token

# OpenAI API (samples 05-08)
OPENAI_API_KEY=your_openai_api_key

# Supabase PostgreSQL (samples 10-11)
SUPABASE_HOST=your-project.supabase.co
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=your-password
SUPABASE_PORT=5432
```

### Discord Developer Portal Configuration

**Required Bot Permissions:**
- Send Messages
- Read Message History
- Use Slash Commands
- Add Reactions
- Attach Files
- Embed Links

**Required Privileged Intents:**
- Message Content Intent (all bots)
- Server Members Intent (sample03 only)

### Development Server Configuration
**Hardcoded IDs for Educational Purposes:**
- Target Guild ID: `1394139562028306644`
- Target Channel ID: `1394203406574424104` (varies by sample)

When using these samples, update these IDs to match your development Discord server.

## Sample Code Educational Value

### Learning Progression
1. **Basic Bot (bot.py)** - Start here for fundamental Discord.py concepts
2. **Data Export (samples 01-03)** - Learn message/member data handling
3. **AI Integration (samples 05-08)** - External API patterns
4. **Database Integration (samples 10-11)** - Advanced data persistence

### Key Educational Concepts Demonstrated
- **Async/await patterns** for Discord.py
- **Event-driven programming** with Discord events
- **Error handling strategies** for bot reliability
- **Database design** for Discord applications
- **API integration patterns** for external services
- **User experience design** through reaction-based interfaces

### Code Quality Standards for Samples
- Comprehensive error handling and logging
- Clear variable naming and function documentation
- Consistent code structure across all samples
- UTF-8 encoding for Japanese text support
- Environment variable security practices
- Database connection management best practices