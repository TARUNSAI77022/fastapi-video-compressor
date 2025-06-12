import boto3
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

S3_BUCKET = os.getenv("S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

if not all([S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION]):
    raise RuntimeError("Missing required AWS environment variables")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def upload_to_s3(local_path: str, s3_key: str, original_filename: str = None):
    try:
        content_type = 'video/x-matroska' if s3_key.endswith('.mkv') else 'image/webp'
        
        extra_args = {
            'ACL': 'bucket-owner-full-control',
            'ContentType': content_type
        }

        if original_filename:
            extra_args['Metadata'] = {
                'original-name': original_filename
            }

        logger.info(f"Uploading {local_path} to S3 bucket {S3_BUCKET} as {s3_key}")
        s3.upload_file(
            Filename=local_path,
            Bucket=S3_BUCKET,
            Key=s3_key,
            ExtraArgs=extra_args
        )
        logger.info(f"Successfully uploaded {s3_key} to S3")
    except Exception as e:
        logger.error(f"Failed to upload {local_path} to S3: {e}")
        raise