import os
from dataclasses import dataclass

from src.exceptions import ValidationError


@dataclass(frozen=True)
class Settings:
    s3_bucket_name: str
    ses_sender_email: str
    aws_region: str
    reports_prefix: str = "reports"


_REQUIRED_ENV_VARS = ("S3_BUCKET_NAME", "SES_SENDER_EMAIL", "AWS_REGION")


def get_settings() -> Settings:
    missing = [key for key in _REQUIRED_ENV_VARS if not os.getenv(key)]
    if missing:
        raise ValidationError(
            "Faltan variables de entorno obligatorias: " + ", ".join(missing)
        )

    reports_prefix = (os.getenv("REPORTS_PREFIX") or "reports").strip().strip("/")
    if not reports_prefix:
        reports_prefix = "reports"

    return Settings(
        s3_bucket_name=os.environ["S3_BUCKET_NAME"],
        ses_sender_email=os.environ["SES_SENDER_EMAIL"],
        aws_region=os.environ["AWS_REGION"],
        reports_prefix=reports_prefix,
    )
