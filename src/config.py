import os
import base64
import mimetypes
from dataclasses import dataclass

from src.exceptions import ValidationError


@dataclass(frozen=True)
class Settings:
    app_env: str
    s3_bucket_name: str
    ses_sender_email: str
    aws_region: str
    reports_prefix: str
    platform_url: str
    email_logo_url: str
    local_test_mode: bool


_REQUIRED_ENV_VARS = ("S3_BUCKET_NAME", "SES_SENDER_EMAIL", "AWS_REGION")


def _get_bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() == "true"


def _build_logo_src() -> str:
    logo_path = (os.getenv("EMAIL_LOGO_PATH") or "").strip()
    if logo_path:
        try:
            with open(logo_path, "rb") as logo_file:
                encoded = base64.b64encode(logo_file.read()).decode("ascii")
        except OSError as exc:
            raise ValidationError(
                f"No se pudo leer EMAIL_LOGO_PATH='{logo_path}': {exc}"
            ) from exc
        mime_type = mimetypes.guess_type(logo_path)[0] or "image/png"
        return f"data:{mime_type};base64,{encoded}"

    return (os.getenv("EMAIL_LOGO_URL") or "https://i.imgur.com/St19Vpz.png").strip()


def get_settings() -> Settings:
    app_env = (os.getenv("APP_ENV") or "dev").strip().lower() or "dev"
    local_test_mode = _get_bool_env("LOCAL_TEST_MODE", default="false")
    aws_region = (os.getenv("AWS_REGION") or "").strip()
    s3_bucket_name = (os.getenv("S3_BUCKET_NAME") or "").strip()
    ses_sender_email = (os.getenv("SES_SENDER_EMAIL") or "").strip()

    reports_prefix = (os.getenv("REPORTS_PREFIX") or "reports").strip().strip("/")
    if not reports_prefix:
        reports_prefix = "reports"

    platform_url = (os.getenv("PLATFORM_URL") or "").strip()
    email_logo_url = _build_logo_src()

    if not local_test_mode:
        missing = [key for key in _REQUIRED_ENV_VARS if not os.getenv(key, "").strip()]
        if missing:
            raise ValidationError(
                "Faltan variables de entorno obligatorias: " + ", ".join(missing)
            )

    return Settings(
        app_env=app_env,
        s3_bucket_name=s3_bucket_name,
        ses_sender_email=ses_sender_email,
        aws_region=aws_region,
        reports_prefix=reports_prefix,
        platform_url=platform_url,
        email_logo_url=email_logo_url,
        local_test_mode=local_test_mode,
    )
