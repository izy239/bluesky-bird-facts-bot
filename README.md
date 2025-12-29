# 🐦 Bluesky Bird Facts Bot

A Docker-based bot that posts interesting bird facts to Bluesky once daily.

## Features

- Posts a unique bird fact every day at 6 AM ET
- Includes Creative Commons licensed bird photos from Flickr
- Credits photographers in each post
- Adds descriptive alt text for accessibility
- Clickable hashtags (#birdfacts #Birds #Nature)
- Tracks posted facts to avoid repetition
- Automatically resets when all facts have been shared
- Runs in Docker for easy deployment
- Includes 365 fascinating bird facts

## Prerequisites

- Docker and Docker Compose installed
- A Bluesky account
- A Bluesky App Password (see instructions below)
- (Optional) A Flickr API key for including images in posts

## Setup Instructions

### 1. Get Your Bluesky App Password

1. Log into Bluesky
2. Go to Settings → App Passwords
3. Create a new App Password
4. Save this password securely (you'll need it in step 3)

### 2. Get Your Flickr API Key (Optional but Recommended)

Images make posts much more engaging! To add bird photos to your posts:

1. Go to https://www.flickr.com/services/apps/create/apply/
2. Sign in with a Flickr/Yahoo account (or create one)
3. Apply for a non-commercial API key
4. Fill out the form:
   - App name: "Bird Facts Bot" (or similar)
   - Purpose: "Educational bot posting bird facts with photos"
5. Copy your API Key (not the Secret)

**Note:** Without a Flickr API key, the bot will still work but posts won't include images.

### 3. Clone and Configure

```bash
# Create a directory for the bot
mkdir bird-facts-bot
cd bird-facts-bot

# Copy all files to this directory
# (bird_facts_bot.py, bird_facts.json, Dockerfile, docker-compose.yml, requirements.txt)

# Create .env file from example
cp .env.example .env

# Create data directory for persistence
mkdir data
```

### 4. Add Your Credentials

Edit the `.env` file and add your credentials:

```
BLUESKY_USERNAME=yourhandle.bsky.social
BLUESKY_PASSWORD=your-app-password-here
FLICKR_API_KEY=your-flickr-api-key-here
```

**Note:** The `FLICKR_API_KEY` is optional. If you don't include it, posts will still work but won't have images.

### 5. Build and Run

```bash
# Build the Docker image
docker-compose build

# Test the bot (posts immediately)
docker-compose run --rm bird-facts-bot

# Start the scheduler (runs daily at 9 AM)
docker-compose up -d scheduler
```

## Usage

### Manual Post
To manually post a bird fact immediately:
```bash
docker-compose run --rm bird-facts-bot
```

### Check Logs
To see the scheduler logs:
```bash
docker-compose logs -f scheduler
```

### Stop the Scheduler
```bash
docker-compose down
```

## Customization

### Change Posting Time
Edit `docker-compose.yml` and modify the schedule line:
```yaml
ofelia.job-run.bird-facts.schedule: "0 0 9 * * *"
```

Format: `seconds minutes hours day month weekday`
- Daily at 9 AM: `0 0 9 * * *`
- Daily at 6 PM: `0 0 18 * * *`
- Twice daily (9 AM and 6 PM): `0 0 9,18 * * *`

### Add More Bird Facts
Edit `bird_facts.json` and add facts to the `facts` array:
```json
{
  "facts": [
    "Your new bird fact here...",
    "Another interesting fact..."
  ]
}
```

### Change Post Format
Edit `bird_facts_bot.py` and modify the `post_text` formatting in the `main()` function.

## File Structure

```
bird-facts-bot/
├── bird_facts_bot.py      # Main bot script
├── bird_facts.json        # Collection of bird facts
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Python dependencies
├── .env                   # Your credentials (don't commit!)
├── .env.example          # Example credentials file
├── data/                 # Persistent data (tracks posted facts)
│   └── posted_facts.json # Auto-generated tracking file
└── README.md             # This file
```

## Troubleshooting

### Bot doesn't post
1. Check credentials in `.env` file
2. Verify your App Password is correct
3. Check logs: `docker-compose logs bird-facts-bot`

### Want to reset fact rotation
Delete `data/posted_facts.json` to start over:
```bash
rm data/posted_facts.json
```

### Scheduler not running
1. Ensure Docker daemon is running
2. Check scheduler logs: `docker-compose logs scheduler`
3. Verify the cron schedule format is correct

## Security Notes

- Never commit your `.env` file to version control
- Use App Passwords, not your main Bluesky password
- Keep your credentials secure

## License

Feel free to use and modify this bot for your own purposes!

## Contributing

Want to add more bird facts? Edit `bird_facts.json` and add them to the array. Pull requests welcome!
