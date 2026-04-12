from datetime import datetime, timezone
from io import BytesIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.exceptions import StorageError


class S3Service:
    def __init__(self, bucket_name: str, region_name: str, reports_prefix: str) -> None:
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.reports_prefix = reports_prefix.strip("/")
        self.client = boto3.client("s3", region_name=region_name)

    def _build_key(self, supplier_id: str) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{self.reports_prefix}/{supplier_id}/report-{timestamp}.pdf"

    def upload_pdf(self, *, supplier_id: str, pdf_buffer: BytesIO) -> dict[str, str]:
        key = self._build_key(supplier_id)
        try:
            self.client.upload_fileobj(
                Fileobj=pdf_buffer,
                Bucket=self.bucket_name,
                Key=key,
                ExtraArgs={"ContentType": "application/pdf"},
            )
            s3_uri = f"s3://{self.bucket_name}/{key}"
            presigned_url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=86400,
            )
            return {
                "bucket": self.bucket_name,
                "key": key,
                "s3_uri": s3_uri,
                "presigned_url": presigned_url,
            }
        except (ClientError, BotoCoreError) as exc:
            raise StorageError(f"Error al subir PDF a S3: {exc}") from exc
