# Standard library imports
import json
import logging
import os
import sys
import unicodedata

# Third-party imports
from fastapi import FastAPI, Request, Form, File, UploadFile
import requests
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webhook.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("webhook_handler")

app = FastAPI(title="Email AI Agent Webhook Handler")

# Server Configuration
PORT = int(os.getenv('PORT', '8000'))

# Langflow API details from environment variables
LANGFLOW_API_URL = os.getenv("LANGFLOW_API_URL")
LANGFLOW_ENDPOINT = os.getenv("LANGFLOW_ENDPOINT")

# Create a translation table that maps control characters to None
CONTROL_CHAR_TABLE = str.maketrans("", "", "".join(chr(i) for i in range(32) if i not in [9, 10, 13]) + chr(127))

def clean_text(text):
    """Clean text to ensure it can be properly serialized"""
    if not isinstance(text, str):
        return text

    # Remove control characters except tabs
    cleaned = text.translate(CONTROL_CHAR_TABLE)

    # Replace newlines and carriage returns with spaces
    cleaned = cleaned.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')

    # Replace multiple spaces with a single space
    cleaned = ' '.join(cleaned.split())

    # Normalize Unicode
    cleaned = unicodedata.normalize("NFC", cleaned)
    return cleaned

@app.post("/webhook")
async def webhook(
    request: Request,
    to: str = Form(...),
    sender: str = Form(..., alias="from"),
    subject: str = Form(""),
    text: str = Form(""),
    attachments: int = Form(0),
    attachment1: UploadFile = File(None)
):
    """Handle incoming email webhook from SendGrid"""
    try:
        # Log raw request for debugging
        form_data = await request.form()
        logger.info("Received webhook: %s", json.dumps(dict(form_data), indent=2))

        # Prepare data structure
        data = {
            "to": clean_text(to),
            "sender": clean_text(sender),
            "subject": clean_text(subject),
            "text": clean_text(text)
        }

        # Process Attachments (if any)
        if attachments > 0 and attachment1:
            attachment_name = attachment1.filename
            logger.info("Received attachment: %s", attachment_name)
            data["attachment"] = clean_text(attachment_name)  # Store attachment name

        # Truncate very long messages if needed
        if len(data.get("text", "")) > 10000:
            data["text"] = data["text"][:10000] + "... (truncated)"

        # Log the data
        logger.info("Sending to Langflow: %s", json.dumps(data, indent=2))

        # Forward to Langflow
        response = requests.post(
            f"{LANGFLOW_API_URL}/api/v1/webhook/{LANGFLOW_ENDPOINT}",
            json=data,
            timeout=10
        )

        logger.info("Forwarded to Langflow, status: %d, response: %s", response.status_code, response.text)
        return {"status": "success"}

    except Exception as e:
        logger.error("Error processing webhook: %s", str(e), exc_info=True)
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check called")
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info("Starting webhook server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
