import os
from typing import Any

from src.config import get_settings
from src.exceptions import (
    EmailDeliveryError,
    PdfGenerationError,
    StorageError,
    ValidationError,
)
from src.services.email_service import EmailService
from src.services.pdf_generator_service import PdfGeneratorService
from src.services.s3_service import S3Service
from src.utils.logger import get_logger
from src.utils.validators import validate_event_payload

logger = get_logger(__name__)


def _calculate_summary_metrics(criteria: list[dict[str, Any]]) -> dict[str, int]:
    total = len(criteria)
    has_compliance = sum(1 for c in criteria if c.get("compliance") == "Tiene")
    has_no_compliance = sum(1 for c in criteria if c.get("compliance") == "No tiene")
    verified_criteria = sum(1 for c in criteria if c.get("is_verified") is True)
    total_checker_files = sum(len(c.get("checker_files", [])) for c in criteria)

    return {
        "total_criteria": total,
        "has_compliance": has_compliance,
        "has_no_compliance": has_no_compliance,
        "verified_criteria": verified_criteria,
        "total_checker_files": total_checker_files,
    }


def _is_local_test_mode() -> bool:
    return os.getenv("LOCAL_TEST_MODE", "false").strip().lower() == "true"


def _build_base_response(request_id: str, metrics: dict[str, int]) -> dict[str, Any]:
    return {
        "statusCode": 200,
        "request_id": request_id,
        "metrics": metrics,
    }


def _handle_local_output(pdf_buffer: Any, request_id: str, metrics: dict[str, int]) -> dict[str, Any]:
    output_dir = "local_output"
    os.makedirs(output_dir, exist_ok=True)

    pdf_path = os.path.join(output_dir, f"report-{request_id}.pdf")
    with open(pdf_path, "wb") as file:
        file.write(pdf_buffer.getvalue())

    logger.info("PDF generado localmente en %s", pdf_path)

    response = _build_base_response(request_id=request_id, metrics=metrics)
    response.update(
        {
            "message": "PDF generado localmente, sin S3 ni SES",
            "local_pdf_path": pdf_path,
        }
    )
    return response


def _handle_aws_output(
    pdf_buffer: Any,
    request_id: str,
    supplier: dict[str, Any],
    requester: dict[str, Any],
    metrics: dict[str, int],
) -> dict[str, Any]:
    settings = get_settings()

    s3_service = S3Service(
        bucket_name=settings.s3_bucket_name,
        region_name=settings.aws_region,
        reports_prefix=settings.reports_prefix,
    )
    upload_result = s3_service.upload_pdf(
        supplier_id=supplier["id_supplier"],
        pdf_buffer=pdf_buffer,
    )

    email_service = EmailService(
        sender_email=settings.ses_sender_email,
        region_name=settings.aws_region,
    )
    email_response = email_service.send_report_ready_email(
        recipient_name=requester["name"],
        recipient_email=requester["email"],
        supplier_name=supplier["business_name"],
        request_id=request_id,
        report_reference=upload_result.get("presigned_url") or upload_result["s3_uri"],
    )

    logger.info(
        "Proceso completado request_id=%s, s3_uri=%s, email_message_id=%s",
        request_id,
        upload_result["s3_uri"],
        email_response.get("MessageId"),
    )

    response = _build_base_response(request_id=request_id, metrics=metrics)
    response.update(
        {
            "message": "Informe generado y notificado correctamente",
            "report": upload_result,
        }
    )
    return response


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger.info("Inicio de procesamiento de informe")

    try:
        settings = get_settings()
        execution_mode = "local" if settings.local_test_mode else "AWS"
        logger.info("Ambiente: %s", settings.app_env)
        logger.info("Lambda ejecutándose en modo %s", execution_mode)

        payload = validate_event_payload(event)

        request_id = payload["request_id"]
        supplier = payload["supplier"]
        requester = payload["requested_by"]

        metrics = _calculate_summary_metrics(payload["criteria"])
        logger.info("Métricas calculadas para request_id=%s: %s", request_id, metrics)

        pdf_service = PdfGeneratorService()
        pdf_buffer = pdf_service.generate(payload, metrics)

        if settings.local_test_mode or _is_local_test_mode():
            return _handle_local_output(
                pdf_buffer=pdf_buffer,
                request_id=request_id,
                metrics=metrics,
            )

        return _handle_aws_output(
            pdf_buffer=pdf_buffer,
            request_id=request_id,
            supplier=supplier,
            requester=requester,
            metrics=metrics,
        )

    except ValidationError as exc:
        logger.error("Error de validación: %s", exc)
        return {"statusCode": 400, "error": str(exc)}
    except (PdfGenerationError, StorageError, EmailDeliveryError) as exc:
        logger.error("Error de procesamiento: %s", exc)
        return {"statusCode": 500, "error": str(exc)}
    except Exception as exc:
        logger.exception("Error no controlado")
        return {"statusCode": 500, "error": f"Error interno no controlado: {exc}"}
