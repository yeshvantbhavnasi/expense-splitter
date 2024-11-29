import boto3
import magic
from botocore.exceptions import ClientError
from fastapi import HTTPException
import os
from config import get_settings
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

def get_mime_type(file_data: bytes) -> str:
    """
    Get MIME type of file using python-magic
    """
    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file_data)
        logger.info(f"Detected MIME type: {mime_type}")
        return mime_type
    except Exception as e:
        logger.error(f"Failed to detect MIME type: {str(e)}")
        raise

def get_file_extension(mime_type: str) -> str:
    """
    Get file extension from MIME type
    """
    mime_to_ext = {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif',
        'application/pdf': 'pdf',
        'image/heic': 'heic',
        'image/heif': 'heif',
    }
    ext = mime_to_ext.get(mime_type, 'bin')
    logger.info(f"Using extension '{ext}' for MIME type '{mime_type}'")
    return ext

def upload_file_to_s3(file_data: bytes, content_type: str, folder: str = "receipts") -> str:
    """
    Upload a file to S3
    Returns the URL of the uploaded file
    """
    try:
        logger.info(f"Starting S3 upload to folder: {folder}")
        
        # Verify file type
        actual_mime_type = get_mime_type(file_data)
        if not actual_mime_type.startswith(('image/', 'application/pdf')):
            logger.warning(f"Invalid file type detected: {actual_mime_type}")
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only images and PDFs are allowed."
            )
        
        # Generate a unique filename with proper extension
        file_extension = get_file_extension(actual_mime_type)
        filename = f"{folder}/{uuid.uuid4()}.{file_extension}"
        logger.info(f"Generated filename: {filename}")
        
        # Upload to S3
        logger.info(f"Uploading to S3 bucket: {settings.AWS_BUCKET_NAME}")
        s3_client.put_object(
            Bucket=settings.AWS_BUCKET_NAME,
            Key=filename,
            Body=file_data,
            ContentType=actual_mime_type
        )
        
        # Generate URL
        url = f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
        logger.info(f"Upload successful. URL: {url}")
        return url
    
    except ClientError as e:
        logger.error(f"AWS S3 error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
        raise

def delete_file_from_s3(file_url: str) -> None:
    """
    Delete a file from S3 using its URL
    """
    try:
        # Extract key from URL
        key = file_url.split('.com/')[-1]
        logger.info(f"Deleting file from S3: {key}")
        
        # Delete from S3
        s3_client.delete_object(
            Bucket=settings.AWS_BUCKET_NAME,
            Key=key
        )
        logger.info("File deleted successfully")
    except ClientError as e:
        logger.error(f"AWS S3 error during deletion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during deletion: {str(e)}", exc_info=True)
        raise
