#!/usr/bin/env python3

import subprocess
import time
from typing import Dict, Tuple

# Test email configurations for different agent types
TEST_EMAILS = [
    {
        "from": "david.gilardi+deal@datastax.com",
        "to": "deals@email-agent.ai",
        "subject": "Test Email from Terminal",
        "body": "what are the latest deals on the nintendo switch?"
    },
    {
        "from": "david.gilardi+travel@datastax.com",
        "to": "travel@email-agent.ai",
        "subject": "Test Email from Terminal",
        "body": (
            "Let's plan a fun cocktail dinner in Orlando, FL for tonight at 8PM. "
            "Just pick a place for me. Include a map link to the location."
        )
    },
    {
        "from": "david.gilardi+financial@datastax.com",
        "to": "financial@email-agent.ai",
        "subject": "Test Email from Terminal",
        "body": "What is the current financial situation for Nvidia today?"
    },
    {
        "from": "david.gilardi+research@datastax.com",
        "to": "research@email-agent.ai",
        "subject": "Test Email from Terminal",
        "body": (
            "Research the effectiveness of different prompt engineering techniques in controlling "
            "AI hallucinations, with focus on real-world applications and empirical studies."
        )
    }
]

def send_test_email(email_config: Dict[str, str]) -> Tuple[bool, str]:
    """
    Send a test email using sendmail.
    
    Args:
        email_config (Dict[str, str]): Email configuration with from, to, subject, and body
            
    Returns:
        Tuple[bool, str]: (Success status, Error message if any)
    """
    try:
        # Format the email content
        email_content = (
            f"From: {email_config['from']}\n"
            f"To: {email_config['to']}\n"
            f"Subject: {email_config['subject']}\n"
            f"\n"
            f"{email_config['body']}"
        )

        # Write content to a temporary file to avoid shell quoting issues
        with open('temp_email.txt', 'w', encoding='utf-8') as f:
            f.write(email_content)

        # Use cat to read the file and pipe to sendmail
        result = subprocess.run(
            'cat temp_email.txt | sendmail -t',
            shell=True,
            text=True,
            capture_output=True,
            check=False
        )

        # Clean up temp file
        subprocess.run(['rm', 'temp_email.txt'], check=False)

        if result.returncode == 0:
            print(f"Successfully sent email to {email_config['to']}")
            return True, ""
        else:
            error_msg = f"Failed to send email: {result.stderr}"
            print(error_msg)
            return False, result.stderr

    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        print(error_msg)
        return False, str(e)

def send_all_test_emails() -> None:
    """Send all configured test emails and print results."""
    print("\nSending test emails to verify end-to-end functionality...")
    print("=" * 50)

    success_count = 0
    for email in TEST_EMAILS:
        success, _ = send_test_email(email)
        if success:
            success_count += 1
        time.sleep(2)  # Wait 2 seconds between emails

    print("\nSummary:")
    print(f"Successfully sent {success_count} out of {len(TEST_EMAILS)} test emails")
    print("=" * 50)

def send_single_test_email(email_type: str) -> None:
    """Send a single test email based on the email type (e.g., 'travel', 'deal')."""
    matching_email = next((email for email in TEST_EMAILS if f"+{email_type}" in email["from"]), None)
    if matching_email:
        print(f"\nSending test email for {email_type} agent...")
        print("=" * 50)
        success, _ = send_test_email(matching_email)
        print("=" * 50)
    else:
        print(f"No test email found for type: {email_type}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        send_single_test_email(sys.argv[1])
    else:
        send_all_test_emails()
