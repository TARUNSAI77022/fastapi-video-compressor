from .celery_app import celery
from .s3_utils import upload_to_s3
import subprocess
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@celery.task(bind=True, name="compress_and_upload", autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def compress_and_upload(self, input_path, output_path, s3_key, original_filename=None):
    try:
        logger.info(f"[{self.request.id}] Starting compression for file: {input_path}")

        if not os.path.exists(input_path):
            logger.error(f"[{self.request.id}] Input file does not exist: {input_path}")
            return

        ext = input_path.split('.')[-1].lower()
        output_ext = output_path.split('.')[-1].lower()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Upload original file to S3 (optional)
        if original_filename:
            original_s3_key = f"original/{os.path.basename(input_path)}"
            upload_to_s3(input_path, original_s3_key, original_filename=original_filename)
            logger.info(f"[{self.request.id}] Uploaded original file to S3 as {original_s3_key}")

        # Run compression only if needed
        if ext in ['mp4', 'mov', 'avi', 'mkv']:
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-i", input_path,
                "-map", "0:v:0",           # Main video stream
                "-map", "0:a?",            # All audio streams (optional)
                "-map", "0:s?",            # All subtitle streams (optional)
                "-map", "0:t?",            # All attachments (optional)
                "-c:v:0", "libx265",
                "-preset", "slow",
                "-crf", "23",
                "-c:a", "copy",
                "-c:s", "copy",
                "-c:t", "copy",
                "-map_metadata", "0",
                "-map_chapters", "0",
                output_path
            ]
        elif ext in ['jpg', 'jpeg', 'png']:
            ffmpeg_cmd = [
                "convert",
                input_path,
                "-strip", "-interlace", "Plane",
                "-quality", "80%",
                output_path
            ]
        else:
            logger.warning(f"[{self.request.id}] Unsupported format: {ext}")
            return

        logger.info(f"[{self.request.id}] Running command: {' '.join(ffmpeg_cmd)}")
        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        logger.info(f"[{self.request.id}] stdout:\n{result.stdout}")
        logger.error(f"[{self.request.id}] stderr:\n{result.stderr}")

        if result.returncode != 0:
            logger.error(f"[{self.request.id}] Compression failed with code {result.returncode}")
            return

        if not os.path.exists(output_path):
            logger.error(f"[{self.request.id}] Output file was not created: {output_path}")
            return

        # Upload compressed file
        upload_to_s3(output_path, s3_key, original_filename=original_filename)
        logger.info(f"[{self.request.id}] Successfully uploaded to S3 as {s3_key}")

    except Exception as e:
        logger.exception(f"[{self.request.id}] Compression task failed: {str(e)}")
        raise

    finally:
        for path in [input_path, output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    logger.info(f"[{self.request.id}] Removed temporary file: {path}")
                except Exception as e:
                    logger.warning(f"[{self.request.id}] Could not delete {path}: {e}")
