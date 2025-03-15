# Standard library imports
import json
import logging
import os
import sys
import unicodedata

# Third-party imports
from fastapi import FastAPI, Request
import requests
import uvicorn
from dotenv import load_dotenv
from json_repair import repair_json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webhook.log"),  # Log to a file
        logging.StreamHandler(sys.stdout)    # Also log to console
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
CONTROL_CHAR_TABLE = str.maketrans("", "", "".join(chr(i) for i in range(32)) + chr(127))

def clean_json_data(data):
    """Clean JSON data to ensure it can be properly serialized"""
    if isinstance(data, dict):
        return {k: clean_json_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_json_data(item) for item in data]
    elif isinstance(data, str):
        # Remove control characters
        cleaned = data.translate(CONTROL_CHAR_TABLE)
        # Normalize Unicode
        cleaned = unicodedata.normalize("NFC", cleaned)
        return cleaned
    else:
        return data

@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming webhook from Gmail"""
    try:
        # Get raw request body and try to repair if needed
        raw_body = await request.body()
        raw_text = raw_body.decode('utf-8')

        # Find the JSON object boundaries
        start = raw_text.find("{") if raw_text.find("{") < raw_text.find("[") or raw_text.find("[") == -1 else raw_text.find("[")
        end = raw_text.rfind("}") if raw_text.rfind("}") > raw_text.rfind("]") or raw_text.rfind("]") == -1 else raw_text.rfind("]")
        if start != -1 and end != -1 and end > start:
            raw_text = raw_text[start:end+1]

        try:
            # First try standard parsing
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            # If that fails, try to repair the JSON
            logger.info("Attempting to repair malformed JSON")
            repaired_text = repair_json(raw_text)
            payload = json.loads(repaired_text)
            logger.info("JSON successfully repaired")
        
        # Log the full payload for testing
        logger.info("Received webhook: %s", json.dumps(payload, indent=2))

        # Handle both list and dictionary payloads
        if isinstance(payload, list):
            # For list payloads, process each item individually
            logger.info("Processing list payload with %d items", len(payload))
            results = []
            for item in payload:
                result = process_webhook_item(item)
                if result:
                    results.append(result)
            return {"status": "success", "message": f"Processed {len(results)} webhook items"}
        else:
            # For dictionary payloads, process as before
            result = process_webhook_item(payload)
            return {"status": "success", "message": "Webhook received and processed"}

    except Exception as e:
        logger.error("Error processing webhook: %s", str(e), exc_info=True)
        return {"status": "error", "message": str(e)}

def process_webhook_item(data):
    """Process a single webhook item"""
    try:
        # Extract the data from the payload
        if isinstance(data, dict):
            # Create a filtered payload
            filtered_data = {
                "to": data.get("to") or data.get("email"),
                "sender": data.get("from") or data.get("smtp-id"),
                "subject": data.get("subject") or data.get("category", [""])[0],
                "messageText": data.get("text", "") or f"Event: {data.get('event', 'unknown')}",
                "messageTimestamp": data.get("messageTimestamp") or data.get("timestamp"),
                "threadId": data.get("threadId") or data.get("sg_message_id"),
                "messageId": data.get("messageId") or data.get("sg_event_id")
            }

            # Add any additional fields that might be useful
            if "event" in data:
                filtered_data["event"] = data.get("event")
            if "reason" in data:
                filtered_data["reason"] = data.get("reason")
            if "status" in data:
                filtered_data["status"] = data.get("status")

            # Clean the filtered data to ensure it can be properly serialized
            filtered_data = clean_json_data(filtered_data)
            
            # Truncate very long messages if needed
            if len(filtered_data.get("messageText", "")) > 10000:
                filtered_data["messageText"] = filtered_data["messageText"][:10000] + "... (truncated)"

            # Log the full filtered data for testing
            logger.info("Sending to Langflow: %s", json.dumps(filtered_data, indent=2))

            response = requests.post(
                f"{LANGFLOW_API_URL}/api/v1/webhook/{LANGFLOW_ENDPOINT}",
                json=filtered_data,
                timeout=10
            )

            logger.info("Forwarded to Langflow, status: %d, response: %s", response.status_code, response.text)
            return {"status": "success"}
        else:
            logger.warning("Received non-dictionary item: %s", data)
            return None
    except Exception as e:
        logger.error("Error processing webhook item: %s", str(e), exc_info=True)
        return None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check called")
    return {"status": "healthy"}

# Main entry point
if __name__ == "__main__":
    logger.info("Starting webhook server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
