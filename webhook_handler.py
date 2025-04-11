# Standard library imports
import json
import logging
import os
import sys
from email.parser import HeaderParser

# Third-party imports
from fastapi import FastAPI, Request, Form
import uvicorn
from dotenv import load_dotenv
import aiohttp
from fastapi.background import BackgroundTasks

# Local imports
from attach import process_attachment
from text_utils import clean_text

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
LANGFLOW_FLOW_ID = os.getenv("LANGFLOW_FLOW_ID")
CHAT_INPUT_ID = os.getenv("CHAT_INPUT_ID")
# Optional Langflow API Key for secured endpoints
LANGFLOW_API_KEY = os.getenv("LANGFLOW_API_KEY")

@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    to: str = Form(...),
    sender: str = Form(..., alias="from"),
    subject: str = Form(""),
    text: str = Form(""),
    headers: str = Form(""),
    attachments: int = Form(0)
):
    """Handle incoming email webhook from SendGrid"""
    try:
        # Get the form data
        form_data = await request.form()

        # Log all form keys for debugging
        logger.info("Form data keys: %s", list(form_data.keys()))
        logger.info("Received webhook with %s attachments claimed", attachments)

        # Prepare data structure
        data = {
            "to": clean_text(to),
            "sender": clean_text(sender),
            "subject": clean_text(subject),
            "text": clean_text(text)
        }

        # --- Determine Thread ID ---
        parser = HeaderParser()
        parsed_headers = parser.parsestr(headers)

        message_id = parsed_headers.get('Message-ID', '').strip('<>')
        in_reply_to = parsed_headers.get('In-Reply-To', '').strip('<>')
        references_header = parsed_headers.get('References', '')

        thread_id = None
        if references_header:
            # The first ID in References is often the root of the thread
            try:
                thread_id = references_header.split()[0].strip('<>')
            except IndexError:
                logger.warning("References header format unexpected: %s", references_header)
        elif in_reply_to:
            # Fallback to In-Reply-To if References is not present or invalid
            thread_id = in_reply_to
        elif message_id:
            # If it's a new email, use its own Message-ID as the thread ID
            thread_id = message_id

        # Final fallback if no suitable header is found
        if not thread_id:
            logger.warning("Could not determine thread ID from headers, falling back to sender.")
            thread_id = data.get('sender')

        # Ensure thread_id is never None or empty before sending
        if not thread_id:
            logger.error("Critical: Could not determine a valid thread_id. Headers: %s", headers)
            # Using a placeholder to prevent errors, but this case should be investigated
            thread_id = f"unknown_thread_{data.get('sender', 'unknown_sender')}"

        logger.info(f"Using Thread ID (Session ID): {thread_id}")
        # --- End Determine Thread ID ---

        # Process Attachments (if any)
        # if int(attachments) > 0:
        #     logger.info("Attempting to process %s attachments", attachments)
        #     attachment_data = []
        #
        #     for i in range(1, int(attachments) + 1):
        #         attachment_key = f"attachment{i}"
        #         logger.info("Looking for attachment key: %s", attachment_key)
        #         if attachment_key in form_data:
        #             attachment = form_data[attachment_key]
        #             logger.info("Found attachment with type: %s", type(attachment).__name__)
        #
        #             # Process the attachment
        #             attachment_info = await process_attachment(
        #                 attachment,
        #                 attachment_key,
        #                 i,
        #                 LANGFLOW_FLOW_ID,
        #                 LANGFLOW_API_URL
        #             )
        #
        #             if attachment_info:
        #                 attachment_data.append(attachment_info)
        #         else:
        #             logger.warning("Attachment key %s not found in form data", attachment_key)
        #
        #     if attachment_data:
        #         logger.info("Adding %s attachments to data payload", len(attachment_data))
        #         data["attachments"] = attachment_data
        #     else:
        #         logger.warning("No attachments were successfully processed")

        # Truncate very long messages if needed
        if len(data.get("text", "")) > 10000:
            data["text"] = data["text"][:10000] + "... (truncated)"

        # Log the data
        logger.info("Data keys being sent to Langflow: %s", list(data.keys()))
        logger.info("Sending to Langflow: %s", json.dumps(data, indent=2))

        # Forward to Langflow using the run API
        run_url = f"{LANGFLOW_API_URL}/api/v1/run/{LANGFLOW_ENDPOINT}?stream=false"
        logger.info("Sending to Langflow run API: %s", run_url)

        # Format the payload for Langflow run API
        run_payload = {
            "output_type": "chat",
            "input_type": "chat",
            "session_id": data['sender'],
            "tweaks": {
                CHAT_INPUT_ID: {
                    # We'll add files here if there are attachments
                }
            }
        }

        # Add file references if we have attachments
        # if "attachments" in data and data["attachments"]:
        #     for attachment in data["attachments"]:
        #         if attachment.get("uploaded") and attachment.get("langflow_file_id"):
        #             # Make sure the files parameter is correctly formatted
        #             run_payload["tweaks"][CHAT_INPUT_ID]["files"] = attachment["langflow_file_id"]
        #             logger.info("Added file reference to payload: %s", attachment["langflow_file_id"])
        #             # For now, just use the first attachment
        #             break

        # Add email metadata as context, including the thread ID
        email_context = (
            f"From: {data['sender']}\n"
            f"To: {data['to']}\n"
            f"Subject: {data['subject']}\n"
            f"Thread ID: {thread_id}\n\n"
        )
        # Only set input_value at the top level
        run_payload["input_value"] = email_context + data["text"]

        # Add headers for the request
        headers = {
            'Content-Type': 'application/json'
        }
        # Add Langflow API key header if it exists
        if LANGFLOW_API_KEY:
            headers['x-api-key'] = LANGFLOW_API_KEY
            logger.info("Adding x-api-key header to Langflow request.")

        logger.info("Sending run payload to Langflow: %s", json.dumps(run_payload, indent=2))

        # Instead of waiting for the response, add the task to background
        background_tasks.add_task(
            send_to_langflow,
            run_url,
            headers,
            run_payload
        )

        return {"status": "accepted"}

    except Exception as e:
        logger.error("Error processing webhook: %s", str(e), exc_info=True)
        return {"status": "error", "message": str(e)}

async def send_to_langflow(url, headers, payload):
    """Send request to Langflow in the background"""
    try:
        async with aiohttp.ClientSession() as session:
            logger.info("Sending run payload to Langflow: %s", json.dumps(payload, indent=2))

            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=120
            ) as response:
                response_text = await response.text()
                logger.info("Forwarded to Langflow, status: %d, response: %s", 
                           response.status, response_text)
    except Exception as e:
        logger.error("Error in background task: %s", str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check called")
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info("Starting webhook server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
