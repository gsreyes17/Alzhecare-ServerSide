from uuid import uuid4
from io import BytesIO

import boto3
from PIL import Image

from app.core.config import get_settings


class S3Service:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.AWS_S3_BUCKET
        self.base_path = settings.AWS_S3_BASE_PATH.strip("/")
        self.profile_base_path = settings.AWS_S3_PROFILE_BASE_PATH.strip("/")
        self.url_ttl_seconds = settings.SIGNED_URL_EXPIRES_SECONDS
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )

    def upload_image(
        self,
        data: bytes,
        filename: str,
        content_type: str = "image/jpeg",
        folder: str | None = None,
    ) -> str:
        safe_name = filename.replace(" ", "_")
        base_folder = (folder or self.base_path).strip("/")
        key = f"{base_folder}/{uuid4()}_{safe_name}"
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return key

    def optimize_profile_image(self, raw_data: bytes, max_size: int = 640, quality: int = 82) -> bytes:
        with Image.open(BytesIO(raw_data)) as image:
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            elif image.mode == "L":
                image = image.convert("RGB")

            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            output = BytesIO()
            image.save(
                output,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )
            return output.getvalue()

    def sign_get_url(self, key: str) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=self.url_ttl_seconds,
        )


s3_service = S3Service()
