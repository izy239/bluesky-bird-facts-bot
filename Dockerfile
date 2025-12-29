FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY bird_facts_bot.py .
COPY bird_facts.json .

# Create volume for persistent data (tracking posted facts)
VOLUME /app/data

# Run the bot
CMD ["python", "bird_facts_bot.py"]
