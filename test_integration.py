"""Integration tests for the webhook handler, focusing on Langflow connectivity."""

# Standard library imports
import os
import sys

# Third-party imports
import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
# Use override=True because LANGFLOW variables might already be set in the shell environment
# pointing to production, and we want the test to use the .env values for local testing.
load_dotenv(override=True)

# Local application imports
# Import the function to test
try:
    # Assuming webhook_handler.py is in the parent directory relative to tests
    # If tests/ is a subdir, this works. If same dir, direct import works.
    from webhook_handler import send_to_langflow
except ImportError:
    # Handle path if test file is in a different relative location
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from webhook_handler import send_to_langflow

# --- Prerequisites --- >
# Ensure these are set correctly in your .env or environment
LANGFLOW_API_URL = os.getenv("LANGFLOW_API_URL")
LANGFLOW_ENDPOINT = os.getenv("LANGFLOW_ENDPOINT")
LANGFLOW_API_KEY = os.getenv("LANGFLOW_API_KEY") # Optional key
# < --- Prerequisites ---

# --- Sample Data --- >
# Use data similar to what your unit tests verify the webhook creates
SAMPLE_HEADERS = {'Content-Type': 'application/json'}
if LANGFLOW_API_KEY:
    SAMPLE_HEADERS['x-api-key'] = LANGFLOW_API_KEY

# Construct a realistic payload based on webhook logic output
SAMPLE_RUN_PAYLOAD = {
    "output_type": "chat",
    "input_type": "chat",
    "session_id": "test_integration_user@example.com", # Unique session for test
    "tweaks": {"null": {}}, # Adjust if your flow uses specific tweaks
    "input_value": ("From: integration_test@example.com\n"
                   "To: test@agent.com\n"
                   "Subject: Integration Test Call\n"
                   "Thread ID: <integration.test.123@id>\n\n"
                   "This is a message sent directly from an integration test.")
}

# Only construct RUN_URL if base URL and endpoint are defined
RUN_URL = None
if LANGFLOW_API_URL and LANGFLOW_ENDPOINT:
    RUN_URL = f"{LANGFLOW_API_URL}/api/v1/run/{LANGFLOW_ENDPOINT}?stream=false"
# < --- Sample Data ---


@pytest.mark.asyncio # Mark as async test
# Skip test if Langflow URL or endpoint isn't configured
@pytest.mark.skipif(not RUN_URL, reason="LANGFLOW_API_URL or LANGFLOW_ENDPOINT not set in environment")
async def test_send_to_langflow_integration():
    """
    Integration test: Checks if send_to_langflow can successfully POST
    to the configured Langflow run endpoint.

    Requires a running Langflow instance and correct .env variables.

    NOTE: This test currently only checks if the POST *completes* without error.
          It does NOT verify the Langflow flow's output or success status.
          Modify send_to_langflow to return status code for stronger assertion.
    """

    print(f"\nAttempting integration test POST to Langflow URL: {RUN_URL}") # Debug print
    print(f"Using Headers: {SAMPLE_HEADERS}")
    # Consider masking API key in logs if sensitive
    # print(f"Using Payload: {SAMPLE_RUN_PAYLOAD}") # Be careful logging full payloads

    try:
        # Call the actual function making the HTTP request
        await send_to_langflow(RUN_URL, SAMPLE_HEADERS, SAMPLE_RUN_PAYLOAD)

        # If the await completes without raising an exception, the network call
        # was likely made successfully (though Langflow might have returned 4xx/5xx).
        # This is a basic connectivity and payload format check.
        print("send_to_langflow completed without raising an exception.")
        assert True # Indicates the call finished

    except Exception as e:
        # Fail the test if any exception occurs during the call
        pytest.fail(f"send_to_langflow raised an exception during integration test: {e}")
