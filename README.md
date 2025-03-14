# Email AI Agent Webhook Handler

A FastAPI-based webhook handler that processes email notifications from GitHub and forwards them to a Langflow AI agent.

## Overview

This service acts as a bridge between GitHub email notifications and your Langflow AI agent. It:

1. Receives webhook payloads from GitHub email notifications using Composio triggers
2. Cleans and sanitizes the JSON data to ensure proper formatting
3. Extracts relevant information (sender, subject, message text, etc.)
4. Forwards the cleaned data to a Langflow endpoint for AI processing

## Features

- **JSON Repair**: Automatically fixes malformed JSON using the `json_repair` library
- **Unicode Normalization**: Ensures consistent character encoding
- **Control Character Removal**: Strips problematic control characters from text
- **Message Truncation**: Prevents oversized messages from causing issues
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/email-ai-agent-webhook.git
   cd email-ai-agent-webhook
   ```

2. Install dependencies:
   ```
   pip install fastapi uvicorn requests json-repair
   ```

3. Configure the Langflow endpoint:
   Edit `webhook_handler.py` and update the `LANGFLOW_API_URL` variable to point to your Langflow instance.

## Usage

### Running the Server

Start the webhook handler:

```
python webhook_handler.py
```

The server will run on port 8000 by default.

### Exposing to the Internet

To receive webhooks from GitHub, you'll need to expose your server to the internet. You can use ngrok for development:

```
ngrok http 8000
```

Use the ngrok URL as your webhook endpoint in your GitHub notification settings.

### Health Check

The server provides a health check endpoint at `/health` that you can use to verify it's running correctly.

## Troubleshooting

- Check the `webhook.log` file for detailed logs
- If you're having JSON parsing issues, ensure the `json_repair` library is installed
- For webhook delivery problems, verify your ngrok tunnel is active and the URL is correctly configured

## License

MIT License

Copyright (c) 2025 David Jones-Gilardi

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files.