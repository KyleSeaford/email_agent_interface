# ✉️ Email as an AI Interface Webhook Handler 🤖 ⚡️

A FastAPI-based webhook handler that transforms email into a natural interface for AI interaction. Using [SendGrid's Inbound Parse](https://docs.sendgrid.com/for-developers/parsing-email/inbound-email), it enables users to communicate with a [Langflow](https://langflow.org) AI agent through their regular email client.

## ✨ Try It Now!

Want to interact with our AI agent? It's as simple as sending an email:

📧 **Email Address:** [`langflow@email-agent.ai`](mailto:langflow@email-agent.ai)

The service will process your email and respond with an AI-generated reply. Try asking questions, requesting analysis, or starting a conversation!

```
                    Email AI Agent Interface
                    
                         .----------.
                        /          /|
                       /  EMAIL   / |
                      /   /@\    /  |
                     .----------.   |
                     |          |   |
                     |          |  /
                     |          | /
                     .----------.
                           |
                           v
                    +--------------+
                    |   WEBHOOK    |
                    |   HANDLER    |---> [Parse]
                    |              |---> [Clean]
                    +--------------+---> [Extract]
                           |
                           v
                    +--------------+
                    |  AI AGENT    |====> Natural
                    |  PROCESSOR   |====> Language
                    |     </>      |====> Response
                    +--------------+
                           |
                           v
                    [ Smart Response ]
```

## Overview

This service acts as a bridge between [SendGrid's Inbound Parse webhook](https://docs.sendgrid.com/for-developers/parsing-email/inbound-email) and your [Langflow](https://langflow.org) AI agent. It:

1. Receives webhook payloads from SendGrid's Inbound Parse
2. Cleans and sanitizes the email data
3. Extracts relevant information (sender, subject, message text, thread IDs)
4. Forwards the cleaned data to a Langflow endpoint for AI processing
5. 🚧 **Coming Soon:** File attachment handling (images, documents, etc.) - *In Development*

## Environment Variables

The following environment variables are required:

- `LOG_LEVEL`: Logging level (default: INFO)
- `PORT`: Server port (default: 8000)
- `LANGFLOW_API_URL`: Base URL for Langflow API
- `LANGFLOW_ENDPOINT`: Specific Langflow endpoint to call
- `LANGFLOW_API_KEY`: Optional API key for secured endpoints

### Setting Up Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your specific configuration:
   ```bash
   # Server Configuration
   PORT=8000
   LOG_LEVEL=INFO

   # Langflow Configuration
   LANGFLOW_API_URL=http://localhost:3000    # Your Langflow instance URL
   LANGFLOW_ENDPOINT=your-flow-endpoint      # Your specific flow endpoint
   LANGFLOW_API_KEY=your-api-key             # Optional: Your API key
   ```

## API Endpoints

### POST /webhook

Receives incoming webhook POST requests from [SendGrid's Inbound Parse](https://docs.sendgrid.com/for-developers/parsing-email/setting-up-the-inbound-parse-webhook).

**Input Fields:**
- `to`: Recipient email address
- `sender`: Sender email address (alias: "from")
- `subject`: Email subject
- `text`: Email body text
- `headers`: Raw email headers

**Response:**
- Success: `{"status": "accepted"}`
- Error: `{"status": "error", "message": "..."}`

### GET /health

Health check endpoint to verify service status.

**Response:**
- `{"status": "healthy"}`

## Features

- **Email Thread Parsing**: Extracts and tracks email conversation threads using [email-reply-parser](https://github.com/zapier/email-reply-parser)
- **Reply Extraction**: Intelligently extracts reply content from email chains
- **Unicode Normalization**: Ensures consistent character encoding
- **Async Processing**: Background task handling using [FastAPI](https://fastapi.tiangolo.com)'s async features

## Installation

### Prerequisites

- Python 3.12+ (developed and tested with Python 3.12.5)
- pip

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/SonicDMG/email_agent_interface.git
   cd email_agent_interface
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```