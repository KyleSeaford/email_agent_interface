# Standard library imports
import os
import base64
import logging
import asyncio
from pathlib import Path
from tempfile import SpooledTemporaryFile

# Third-party imports
import requests
from fastapi import UploadFile

# Configure logging
logger = logging.getLogger("file_utils")

# Constants
ATTACHMENTS_DIR = os.getenv("ATTACHMENTS_DIR", "attachments")

# Create attachments directory if it doesn't exist
Path(ATTACHMENTS_DIR).mkdir(parents=True, exist_ok=True)


async def save_attachment(attachment: UploadFile) -> dict:
    """Save attachment to disk and return metadata"""
    try:
        # Generate a unique filename
        filename = Path(attachment.filename)
        unique_filename = f"{filename.stem}_{os.urandom(4).hex()}{filename.suffix}"
        file_path = Path(ATTACHMENTS_DIR) / unique_filename

        # Save the file
        content = await attachment.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Get file info
        file_size = os.path.getsize(file_path)
        is_image = filename.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

        # For images, create a base64 thumbnail
        thumbnail = None
        if is_image and file_size < 5_000_000:  # Only for images under 5MB
            try:
                with open(file_path, "rb") as img_file:
                    thumbnail = base64.b64encode(img_file.read()).decode('utf-8')
            except Exception as e:
                logger.warning("Could not create thumbnail: %s", str(e))

        return {
            "filename": attachment.filename,
            "path": str(file_path),
            "size": file_size,
            "content_type": attachment.content_type,
            "is_image": is_image,
            "thumbnail": thumbnail if is_image else None
        }
    except Exception as e:
        logger.error("Error saving attachment: %s", str(e))
        return {
            "filename": attachment.filename,
            "error": str(e)
        }


async def upload_to_langflow(attachment: UploadFile, flow_id: str, api_url: str) -> dict:
    """Upload attachment directly to Langflow"""
    try:
        # Prepare the upload URL
        upload_url = f"{api_url}/api/v1/files/upload/{flow_id}"

        # Create a new file with the same filename and content
        files = {"file": (attachment.filename, await attachment.read(), attachment.content_type)}

        # Upload the file to Langflow
        logger.info("Uploading file %s to Langflow at %s", attachment.filename, upload_url)

        response = requests.post(
            upload_url,
            files=files,
            timeout=30
        )

        # Accept both 200 and 201 as success status codes
        if response.status_code in [200, 201]:
            result = response.json()
            logger.info("File uploaded successfully: %s", result)
            return {
                "filename": attachment.filename,
                "langflow_file_id": result.get("file_path"),  # Note: API returns file_path, not file_id
                "content_type": attachment.content_type,
                "uploaded": True
            }
        else:
            logger.error("Failed to upload file: %s", response.text)
            return {
                "filename": attachment.filename,
                "error": f"Upload failed with status {response.status_code}",
                "uploaded": False
            }
    except Exception as e:
        logger.error("Error uploading file to Langflow: %s", str(e))
        return {
            "filename": attachment.filename,
            "error": str(e),
            "uploaded": False
        }


async def process_attachment(attachment, attachment_key: str, i: int, flow_id: str, api_url: str) -> dict:
    """Process different types of attachments and upload to Langflow"""
    try:
        # Handle different types of attachments
        if isinstance(attachment, UploadFile):
            # Standard FastAPI UploadFile
            logger.info("Processing UploadFile attachment: %s", attachment.filename)
            file_content = await attachment.read()
            filename = attachment.filename
            content_type = attachment.content_type
        elif hasattr(attachment, 'file') and hasattr(attachment, 'filename'):
            # Another type with file-like attributes
            logger.info("Processing file-like attachment: %s", attachment.filename)
            # Check if file is a coroutine or regular file
            if hasattr(attachment.file, 'read') and callable(attachment.file.read):
                if asyncio.iscoroutinefunction(attachment.file.read):
                    file_content = await attachment.file.read()
                else:
                    file_content = attachment.file.read()
            else:
                # If file is already bytes
                file_content = attachment.file
            filename = attachment.filename
            content_type = getattr(attachment, 'content_type', 'application/octet-stream')
        elif isinstance(attachment, bytes):
            # Raw bytes
            logger.info("Processing bytes attachment from key: %s", attachment_key)
            file_content = attachment
            filename = f"attachment_{i}.bin"
            content_type = 'application/octet-stream'
        elif isinstance(attachment, str) and attachment.startswith(('http://', 'https://')):
            # URL to a file
            logger.info("Processing URL attachment: %s", attachment)
            response = requests.get(attachment, timeout=30)
            file_content = response.content
            filename = attachment.split('/')[-1] or f"attachment_{i}.bin"
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
        else:
            logger.warning("Unsupported attachment type: %s", type(attachment))
            return None

        # Create a temporary file for the attachment
        temp_file = Path(ATTACHMENTS_DIR) / f"temp_{os.urandom(4).hex()}_{filename}"
        with open(temp_file, "wb") as f:
            f.write(file_content)

        # Create a new UploadFile from the temp file
        with open(temp_file, "rb") as f:
            # Create a SpooledTemporaryFile with the content
            spooled_file = SpooledTemporaryFile()
            spooled_file.write(f.read())
            spooled_file.seek(0)

            # Create UploadFile with the correct content type from the beginning
            upload_file = UploadFile(
                file=spooled_file,
                filename=filename,
                headers={"content-type": content_type}
            )

            # Upload to Langflow
            attachment_info = await upload_to_langflow(upload_file, flow_id, api_url)

            # Save locally as backup
            attachment_info["local_path"] = str(temp_file)

        logger.info("Successfully processed attachment: %s", filename)
        return attachment_info
    except Exception as e:
        logger.error("Error processing attachment: %s", str(e))
        return {
            "filename": getattr(attachment, "filename", f"attachment_{i}"),
            "error": str(e),
            "uploaded": False
        }
