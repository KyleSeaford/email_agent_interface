"""Webhook handler for processing inbound emails via SendGrid's Inbound Parse.
Receives email data (sender, recipient, subject, text, headers, attachments)
via a POST request, extracts relevant information, parses email threads,
removes quoted reply history, and forwards the cleaned data and context
to a specified Langflow flow endpoint using a background task.

Attachment handling is currently disabled due to a bug in the Langflow
ChatInput component when uploading files and using session_id at the same time.
"""

# Standard library imports
import json
import logging
import os
import sys
from email.parser import HeaderParser

# Third-party imports
import aiohttp
import uvicorn
from dotenv import load_dotenv
from email_reply_parser import EmailReplyParser
from fastapi import FastAPI, Form, Request
from fastapi.background import BackgroundTasks

# Local application imports
#from attach import process_attachment # Currently unused due to commented code
from text_utils import clean_text

# Load environment variables
load_dotenv()

# Configure logging level based on environment variable
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper()
# Map string level to logging constant, default to INFO if invalid
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL, # Use the level from env var
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webhook.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("webhook_handler")
# Log the effective logging level
logger.info("Logging level set to: %s", logging.getLevelName(LOG_LEVEL))

app = FastAPI(title="Email AI Agent Webhook Handler")

# Server Configuration
PORT = int(os.getenv('PORT', '8000'))

# Langflow API details from environment variables
LANGFLOW_API_URL = os.getenv("LANGFLOW_API_URL")
LANGFLOW_ENDPOINT = os.getenv("LANGFLOW_ENDPOINT")
#LANGFLOW_FLOW_ID = os.getenv("LANGFLOW_FLOW_ID") # Used in attachment file tweak
#CHAT_INPUT_ID = os.getenv("CHAT_INPUT_ID") # Used in attachment file tweak
# Optional Langflow API Key for secured endpoints
LANGFLOW_API_KEY = os.getenv("LANGFLOW_API_KEY")

@app.post("/webhook")
async def webhook(
    request: Request, # Keep request for potential future use (e.g., raw body)
    background_tasks: BackgroundTasks,
    to: str = Form(...),
    sender: str = Form(..., alias="from"),
    subject: str = Form(""),
    text: str = Form(""),
    headers: str = Form(""), # Raw headers string from SendGrid
    #attachments: int = Form(0) # Number of attachments claimed by SendGrid
):
    """Handle incoming email webhook from SendGrid Inbound Parse."""
    try:
        # Log basic info
        form_data = await request.form()
        logger.info("Received webhook from: %s to: %s", sender, to)
        logger.debug("Form data keys: %s", list(form_data.keys()))

        # Prepare initial data structure
        data = {
            "to": clean_text(to),
            "sender": clean_text(sender),
            "subject": clean_text(subject),
            # Keep original text for parsing reply
            "text": text
        }

        # --- Header Parsing (using email.parser) --- >
        message_id = None
        in_reply_to = None
        references_header = None
        if headers:
            try:
                parser = HeaderParser()
                # headersonly=True might be safer if body could be mixed in
                parsed_headers = parser.parsestr(headers, headersonly=True)

                message_id = parsed_headers.get('Message-ID', '').strip('<>')
                in_reply_to = parsed_headers.get('In-Reply-To', '').strip('<>')
                references_header = parsed_headers.get('References', '')
            except Exception as e:  # noqa: E722
                logger.error("HeaderParser failed to parse headers: %s", e,
                             exc_info=True)

        # Ensure None if empty after stripping/getting
        message_id = message_id if message_id else None
        in_reply_to = in_reply_to if in_reply_to else None
        references_header = references_header if references_header else None

        logger.debug("HeaderParser Extracted Message-ID: '%s'", message_id)
        logger.debug("HeaderParser Extracted In-Reply-To: '%s'", in_reply_to)
        logger.debug("HeaderParser Extracted References Header: '%s'", references_header)
        # < --- End Header Parsing Logic ---

        # --- Extract Reply Only --- >
        cleaned_full_text = clean_text(data["text"])
        reply_text = EmailReplyParser.read(data["text"]).reply

        if not reply_text:
            logger.warning("Could not extract reply, falling back to full text.")
            reply_text = cleaned_full_text # Use cleaned full text as fallback
        else:
             # Clean the extracted reply
            reply_text = clean_text(reply_text)
            # Use lazy formatting for log message (changed message slightly)
            logger.info("Extracted reply text (length: %d)", len(reply_text))
        # < --- End Extract Reply Only ---

        # --- Determine Thread ID --- >
        thread_id = None
        if references_header:
            try:
                ref_ids = [ref.strip('<>') for ref in references_header.split() if ref.strip()]
                if ref_ids:
                    thread_id = ref_ids[0]
                else:
                    logger.warning("References header found but no IDs: %s",
                                 references_header)
            except Exception as e:  # noqa: E722
                logger.warning("Error parsing References header '%s': %s", references_header, e)
        elif in_reply_to:
            thread_id = in_reply_to
        elif message_id:
            thread_id = message_id

        # Final fallback if no suitable header is found
        if not thread_id:
            logger.warning("Could not determine thread ID, falling back to sender.")
            # Use cleaned sender from data dict
            thread_id = data['sender']

        # Ensure thread_id is never None or empty before sending
        if not thread_id:
            logger.error("Critical: Could not determine valid thread_id. Headers: %s",
                          headers)
            # Use placeholder to prevent errors, needs investigation
            thread_id = f"unknown_thread_{data.get('sender', 'unknown')}"

        logger.info("Using Thread ID: %s", thread_id)
        # < --- End Determine Thread ID ---

        # --- Attachment Processing (Currently Disabled) --- >
        # TODO: Re-enable and test attachment handling
        # if int(attachments) > 0:
        #     logger.info("Attempting to process %s attachments", attachments)
        #     attachment_data = []
        #     for i in range(1, int(attachments) + 1):
        #         attachment_key = f"attachment{i}"
        #         if attachment_key in form_data:
        #             attachment = form_data[attachment_key]
        #             attachment_info = await process_attachment(
        #                 attachment,
        #                 attachment_key,
        #                 i,
        #                 LANGFLOW_FLOW_ID,
        #                 LANGFLOW_API_URL
        #             )
        #             if attachment_info:
        #                 attachment_data.append(attachment_info)
        #         else:
        #             logger.warning("Attach key %s not found", attachment_key)
        #     if attachment_data:
        #         logger.info("Adding %s attachments to data", len(attachment_data))
        #         data["attachments"] = attachment_data # Add to main data? Or payload?
        #     else:
        #         logger.warning("No attachments processed successfully")
        # < --- End Attachment Processing ---

        # --- Prepare Langflow Payload --- >
        # Truncate very long replies if needed (adjust limit as necessary)
        MAX_REPLY_LENGTH = 15000 # Example limit
        if len(reply_text) > MAX_REPLY_LENGTH:
            reply_text = reply_text[:MAX_REPLY_LENGTH] + "... (truncated)"
            logger.warning("Truncated long reply text to %d chars.", MAX_REPLY_LENGTH)

        run_url = f"{LANGFLOW_API_URL}/api/v1/run/{LANGFLOW_ENDPOINT}?stream=false"
        logger.info("Target Langflow run API: %s", run_url)

        # Format the payload for the Langflow run API
        langflow_payload = {
            "output_type": "chat",
            "input_type": "chat",
            "session_id": data['sender'], # Use sender email as session ID
            "tweaks": {
                 # Add tweaks here if needed, e.g., for specific components
                 # Example: "Component-Name": {"parameter": value}
                 # TODO: Check if CHAT_INPUT_ID tweak is still needed for files
            },
        }

        # Add file references tweak if attachments were processed and uploaded
        # Example assumes attachment_data contains Langflow file IDs
        # if "attachments" in data and data["attachments"]:
        #     processed_files = []
        #     for attachment in data["attachments"]:
        #         if attachment.get("uploaded") and attachment.get("langflow_file_id"):
        #             processed_files.append(attachment["langflow_file_id"])
        #     if processed_files:
        #         # Ensure CHAT_INPUT_ID is correctly set from env
        #         if CHAT_INPUT_ID:
        #              langflow_payload["tweaks"][CHAT_INPUT_ID] = {"files": processed_files}
        #              logger.info("Added file references to payload tweaks.")
        #         else:
        #              logger.warning("CHAT_INPUT_ID not set, cannot add file tweaks.")

        # Construct the context string
        email_context = (
            f"From: {data['sender']}\n"
            f"To: {data['to']}\n"
            f"Subject: {data['subject']}\n"
            f"Thread ID: {thread_id}\n\n"
        )

        # Set the main input value for Langflow
        langflow_payload["input_value"] = email_context + reply_text

        # Prepare headers for the Langflow request
        langflow_headers = {
            'Content-Type': 'application/json'
        }
        if LANGFLOW_API_KEY:
            langflow_headers['x-api-key'] = LANGFLOW_API_KEY
            # Downgrade to DEBUG
            logger.debug("Adding x-api-key header to Langflow request.")

        # < --- End Prepare Langflow Payload ---

        # --- Schedule Background Task --- >
        logger.info("Scheduling background task to send data to Langflow.")
        background_tasks.add_task(
            send_to_langflow,
            run_url,
            langflow_headers,
            langflow_payload
        )
        # < --- End Schedule Background Task ---

        # Respond immediately to SendGrid
        return {"status": "accepted"}

    except Exception as e:  # noqa: E722
        # Log any unexpected errors during webhook processing
        logger.error("Unhandled error processing webhook: %s", e, exc_info=True)
        # Return an error status, but avoid leaking internal details
        return {"status": "error", "message": "Internal server error"}

async def send_to_langflow(url: str, headers: dict, payload: dict):
    """Send request to Langflow API in the background."""
    try:
        async with aiohttp.ClientSession() as session:
            logger.debug("Sending run payload to Langflow: %s",
                        json.dumps(payload, indent=2))
            timeout = aiohttp.ClientTimeout(total=120)
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout
            ) as response:
                response_text = await response.text()
                # Truncate potentially long response text for INFO log
                truncated_response = (
                    response_text[:500] + '...' if len(response_text) > 500 
                    else response_text
                )

                logger.info("Forwarded to Langflow, status: %d, response: %s",
                           response.status, truncated_response)
                response.raise_for_status() # Raise exception for bad status codes
    except aiohttp.ClientError as e:
        logger.error("HTTP Client Error sending to Langflow: %s", e)
    except Exception as e:  # noqa: E722
        logger.error("Error in background task sending to Langflow: %s", e,
                     exc_info=True)

@app.get("/health")
async def health_check():
    """Health check endpoint to verify service is running."""
    logger.info("Health check called")
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info("Starting webhook server on port %d...", PORT)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
