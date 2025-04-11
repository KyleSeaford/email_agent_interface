"""Tests for the SendGrid inbound email webhook handler."""
# test_webhook.py
# Standard library imports
import sys
import os
from unittest.mock import patch, MagicMock # Import mock utilities

# Third-party imports
# import pytest # Removed - Not explicitly used in the code
from fastapi.testclient import TestClient

# Local application imports
# Import the FastAPI app instance from your webhook_handler file
# Adjust the import path if your file structure is different
try:
    # Try direct import first
    from webhook_handler import app # Removed send_to_langflow as it's only used for patching path
except ImportError:
    # Handle potential path issues if test file is in a different location
    # Ensure this path manipulation is correct for your structure
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from webhook_handler import app # Removed send_to_langflow here too


# Create a TestClient instance
client = TestClient(app)

# --- Test Data Payloads (mimicking curl examples) ---

INITIAL_EMAIL_PAYLOAD = {
    "to": "travel-agent@yourdomain.com",
    "from": "traveler@example.com",
    "subject": "Orlando Day Trip - Lake Eola Ideas?",
    "text": (
        "Hi there! Planning a one-day trip to Orlando soon and want to focus "
        "on the Lake Eola area. Could you suggest a possible itinerary? "
        "Looking for things to do, maybe a nice lunch spot? Thanks!"
    ),
    "headers": (
        'Received: by 1.2.3.4 with HTTP; Mon, 05 Aug 2024 09:00:00 -0400\r\n'
        'Date: Mon, 05 Aug 2024 09:00:00 -0400\r\n'
        'Message-ID: <orlando.request.abc@example.com>\r\n'
        'From: Traveler <traveler@example.com>\r\n'
        'To: Travel Agent <travel-agent@yourdomain.com>\r\n'
        'Subject: Orlando Day Trip - Lake Eola Ideas?\r\n'
        'Content-Type: text/plain; charset="UTF-8"\r\n'
        '\r\n'
    ),
    "attachments": "0"
}

FIRST_REPLY_PAYLOAD = {
    "to": "travel-agent@yourdomain.com",
    "from": "traveler@example.com",
    "subject": "Re: Orlando Day Trip - Lake Eola Ideas?",
    "text": (
        "Thanks for the suggestions! The swan boats sound fun, and the farmer's "
        "market on Sunday is a possibility if my trip aligns. For lunch, I "
        "prefer something casual with outdoor seating if possible. Any specific "
        "recommendations near the park?\n\n"
        "On Mon, Aug 5, 2024 at 10:30 AM Travel Agent <travel-agent@yourdomain.com> wrote:\n"
        ">\n> Hi Traveler,\n>\n"
        "> Great choice! For Lake Eola, you could start with a walk around the lake...\n>\n"
        "> Let me know if you'd like more details!\n>\n"
        "> Best,\n> Travel Agent"
    ),
    "headers": (
        'Received: by 5.6.7.8 with HTTP; Mon, 05 Aug 2024 11:00:00 -0400\r\n'
        'Date: Mon, 05 Aug 2024 11:00:00 -0400\r\n'
        'Message-ID: <traveler.reply1.ghi@example.com>\r\n'
        'In-Reply-To: <agent.lakeeola.reply1.def@yourdomain.com>\r\n'
        'References: <orlando.request.abc@example.com> <agent.lakeeola.reply1.def@yourdomain.com>\r\n'
        'From: Traveler <traveler@example.com>\r\n'
        'To: Travel Agent <travel-agent@yourdomain.com>\r\n'
        'Subject: Re: Orlando Day Trip - Lake Eola Ideas?\r\n'
        'Content-Type: text/plain; charset="UTF-8"\r\n'
        '\r\n'
    ),
    "attachments": "0"
}

SECOND_REPLY_PAYLOAD = {
    "to": "travel-agent@yourdomain.com",
    "from": "traveler@example.com",
    "subject": "Re: Orlando Day Trip - Lake Eola Ideas?",
    "text": (
        "Perfect, that casual spot sounds great! One last thing - what's usually "
        "the best time of day to do the swan boats to avoid crowds or long waits?\n\n"
        "On Mon, Aug 5, 2024 at 11:45 AM Travel Agent <travel-agent@yourdomain.com> wrote:\n"
        ">\n> For casual with outdoor seating near Lake Eola, check out Relax Grill. "
        "It's right on the lake.\n>\n"
        "> > On Mon, Aug 5, 2024 at 11:00 AM Traveler <traveler@example.com> wrote:\n"
        "> >\n> > Thanks for the suggestions! ... Any specific recommendations near the park?\n"
        "> >\n> > > On Mon, Aug 5, 2024 at 10:30 AM Travel Agent <travel-agent@yourdomain.com> wrote:\n"
        "> > > ...\n> \n"
        "> Hope this helps!\n> Travel Agent"
    ),
    "headers": (
        'Received: by 9.10.11.12 with HTTP; Mon, 05 Aug 2024 12:00:00 -0400\r\n'
        'Date: Mon, 05 Aug 2024 12:00:00 -0400\r\n'
        'Message-ID: <traveler.reply2.mno@example.com>\r\n'
        'In-Reply-To: <agent.lakeeola.reply2.jkl@yourdomain.com>\r\n'
        'References: <orlando.request.abc@example.com> <agent.lakeeola.reply1.def@yourdomain.com> <agent.lakeeola.reply2.jkl@yourdomain.com>\r\n'
        'From: Traveler <traveler@example.com>\r\n'
        'To: Travel Agent <travel-agent@yourdomain.com>\r\n'
        'Subject: Re: Orlando Day Trip - Lake Eola Ideas?\r\n'
        'Content-Type: text/plain; charset="UTF-8"\r\n'
        '\r\n'
    ),
    "attachments": "0"
}


# --- Test Functions ---

# Use patch to replace 'send_to_langflow' during the test
# Note: The patch path 'webhook_handler.send_to_langflow' refers to the function
# within the webhook_handler module, so we don't need to import it directly here.
@patch('webhook_handler.send_to_langflow', new_callable=MagicMock)
def test_initial_email(mock_send_task):
    """Tests the first email in a thread."""
    response = client.post("/webhook", data=INITIAL_EMAIL_PAYLOAD)

    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}

    # Check that the background task was called once
    mock_send_task.assert_called_once()

    # Get the arguments the mock was called with
    call_args, call_kwargs = mock_send_task.call_args
    sent_payload = call_args[2] # Payload is the 3rd positional arg (url, headers, payload)

    # Assertions on the payload sent to Langflow
    assert sent_payload["session_id"] == "traveler@example.com"
    # Check for thread ID WITHOUT angle brackets
    assert "Thread ID: orlando.request.abc@example.com" in sent_payload["input_value"]
    # For initial email, the full text should be present (after context)
    assert "Hi there! Planning a one-day trip" in sent_payload["input_value"]

@patch('webhook_handler.send_to_langflow', new_callable=MagicMock)
def test_first_reply_email(mock_send_task):
    """Tests the first reply, checking for reply extraction and correct thread ID."""
    response = client.post("/webhook", data=FIRST_REPLY_PAYLOAD)

    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}
    mock_send_task.assert_called_once()
    call_args, call_kwargs = mock_send_task.call_args
    sent_payload = call_args[2]

    assert sent_payload["session_id"] == "traveler@example.com"
    # Thread ID should be the original message ID from References
    # Check for thread ID WITHOUT angle brackets
    assert "Thread ID: orlando.request.abc@example.com" in sent_payload["input_value"]
    # Check that ONLY the reply delta is in the input value
    expected_reply = (
        "Thanks for the suggestions! The swan boats sound fun, and the farmer's "
        "market on Sunday is a possibility if my trip aligns. For lunch, I "
        "prefer something casual with outdoor seating if possible. Any specific "
        "recommendations near the park?"
    )
    # Check if the extracted reply ends up in the payload (ignore context for this check)
    assert expected_reply in sent_payload["input_value"]
    # Check that the quoted part is NOT in the payload
    assert "On Mon, Aug 5, 2024 at 10:30 AM" not in sent_payload["input_value"]
    assert "> Hi Traveler," not in sent_payload["input_value"]

@patch('webhook_handler.send_to_langflow', new_callable=MagicMock)
def test_second_reply_email(mock_send_task):
    """Tests a subsequent reply with deeper history."""
    response = client.post("/webhook", data=SECOND_REPLY_PAYLOAD)

    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}
    mock_send_task.assert_called_once()
    call_args, call_kwargs = mock_send_task.call_args
    sent_payload = call_args[2]

    assert sent_payload["session_id"] == "traveler@example.com"
    # Thread ID should still be the original message ID
    # Check for thread ID WITHOUT angle brackets
    assert "Thread ID: orlando.request.abc@example.com" in sent_payload["input_value"]
    # Check that only the newest reply delta is present
    expected_reply = (
        "Perfect, that casual spot sounds great! One last thing - what's usually "
        "the best time of day to do the swan boats to avoid crowds or long waits?"
    )
    assert expected_reply in sent_payload["input_value"]
    # Check that the previous reply and agent's response are NOT included
    assert "On Mon, Aug 5, 2024 at 11:45 AM" not in sent_payload["input_value"]
    assert "> For casual with outdoor seating" not in sent_payload["input_value"]
    assert "> > Thanks for the suggestions!" not in sent_payload["input_value"]

# TODO: Add more tests? (e.g., test case where email parser fails,
#  test with attachments if re-enabled)
