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

    def _build_base_folder(self, supplier_id: str, user_id: str) -> str:
        return f"{self.reports_prefix}/{supplier_id}/{user_id}"

    def _build_file_keys(self, supplier_id: str, user_id: str) -> tuple[str, str]:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        base_folder = self._build_base_folder(supplier_id, user_id)
        pdf_key = f"{base_folder}/report-{timestamp}.pdf"
        zip_key = f"{base_folder}/report-package-{timestamp}.zip"
        return pdf_key, zip_key

    def _upload_file(self, file_buffer: BytesIO, key: str, content_type: str) -> dict[str, str]:
        file_buffer.seek(0)
        self.client.upload_fileobj(
            Fileobj=file_buffer,
            Bucket=self.bucket_name,
            Key=key,
            ExtraArgs={"ContentType": content_type},
        )
        return {
            "bucket": self.bucket_name,
            "key": key,
            "s3_uri": f"s3://{self.bucket_name}/{key}",
            "presigned_url": self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=86400,
            ),
        }

    def upload_report_assets(
        self,
        *,
        supplier_id: str,
        user_id: str,
        pdf_buffer: BytesIO,
        zip_buffer: BytesIO,
    ) -> dict[str, dict[str, str] | str]:
        pdf_key, zip_key = self._build_file_keys(supplier_id=supplier_id, user_id=user_id)

        try:
            pdf_result = self._upload_file(pdf_buffer, pdf_key, "application/pdf")
            zip_result = self._upload_file(zip_buffer, zip_key, "application/zip")
            pdf_reference = pdf_result.get("presigned_url") or pdf_result["s3_uri"]
            zip_reference = zip_result.get("presigned_url") or zip_result["s3_uri"]
            return {
                "folder": self._build_base_folder(supplier_id=supplier_id, user_id=user_id),
                "pdf": pdf_result,
                "zip": zip_result,
                "pdf_reference": pdf_reference,
                "zip_reference": zip_reference,
            }
        except (ClientError, BotoCoreError) as exc:
            raise StorageError(f"Error al subir activos del informe a S3: {exc}") from exc
