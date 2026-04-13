import re
from typing import Any

from src.exceptions import ValidationError

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_VALID_COMPLIANCE = {"Tiene", "No tiene"}
_VALID_COUNTRY_CODES = {"CHL", "PER", "ARG"}


def _required_str(data: dict[str, Any], field: str, label: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label} es obligatorio y debe ser string no vacío")
    return value.strip()


def validate_event_payload(event: Any) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise ValidationError("El payload debe ser un objeto JSON")

    _required_str(event, "request_id", "request_id")

    requested_by = event.get("requested_by")
    if not isinstance(requested_by, dict):
        raise ValidationError("requested_by es obligatorio y debe ser objeto")

    _required_str(requested_by, "name", "requested_by.name")
    email = _required_str(requested_by, "email", "requested_by.email")
    if not _EMAIL_REGEX.match(email):
        raise ValidationError("requested_by.email no tiene formato válido")

    supplier = event.get("supplier")
    if not isinstance(supplier, dict):
        raise ValidationError("supplier es obligatorio y debe ser objeto")

    _required_str(supplier, "id_supplier", "supplier.id_supplier")
    _required_str(supplier, "business_name", "supplier.business_name")
    raw_country = supplier.get("country")
    if raw_country is None:
        country = "CHL"
    elif not isinstance(raw_country, str) or not raw_country.strip():
        raise ValidationError("supplier.country debe ser string no vacío cuando se envía")
    else:
        country = raw_country.strip().upper()

    if country not in _VALID_COUNTRY_CODES:
        raise ValidationError("supplier.country debe ser código ISO3 válido: CHL, PER o ARG")
    supplier["country"] = country

    criteria = event.get("criteria")
    if not isinstance(criteria, list):
        raise ValidationError("criteria debe ser una lista")

    for idx, item in enumerate(criteria):
        if not isinstance(item, dict):
            raise ValidationError(f"criteria[{idx}] debe ser un objeto")

        for field in ("id_supplier_criteria", "type", "title", "compliance", "is_verified", "checker_files"):
            if field not in item:
                raise ValidationError(f"criteria[{idx}].{field} es obligatorio")

        if not isinstance(item["id_supplier_criteria"], int):
            raise ValidationError(f"criteria[{idx}].id_supplier_criteria debe ser entero")

        if not isinstance(item["type"], str) or not item["type"].strip():
            raise ValidationError(f"criteria[{idx}].type debe ser string no vacío")

        if not isinstance(item["title"], str) or not item["title"].strip():
            raise ValidationError(f"criteria[{idx}].title debe ser string no vacío")

        if item["compliance"] not in _VALID_COMPLIANCE:
            raise ValidationError(
                f"criteria[{idx}].compliance debe ser 'Tiene' o 'No tiene'"
            )

        if not isinstance(item["is_verified"], bool):
            raise ValidationError(f"criteria[{idx}].is_verified debe ser booleano")

        checker_files = item["checker_files"]
        if not isinstance(checker_files, list):
            raise ValidationError(f"criteria[{idx}].checker_files debe ser lista")

        for file_idx, file_item in enumerate(checker_files):
            if not isinstance(file_item, dict):
                raise ValidationError(
                    f"criteria[{idx}].checker_files[{file_idx}] debe ser objeto"
                )
            if "file_name" not in file_item or "file_url" not in file_item:
                raise ValidationError(
                    f"criteria[{idx}].checker_files[{file_idx}] debe incluir file_name y file_url"
                )
            if not isinstance(file_item["file_name"], str) or not file_item["file_name"].strip():
                raise ValidationError(
                    f"criteria[{idx}].checker_files[{file_idx}].file_name debe ser string no vacío"
                )
            if not isinstance(file_item["file_url"], str) or not file_item["file_url"].strip():
                raise ValidationError(
                    f"criteria[{idx}].checker_files[{file_idx}].file_url debe ser string no vacío"
                )

    indicators = event.get("indicators")
    if indicators is not None:
        if not isinstance(indicators, dict):
            raise ValidationError("indicators debe ser un objeto")

        required_fields = ("reported_compliance_level", "verified_compliance_level")
        for field in required_fields:
            if field not in indicators:
                raise ValidationError(f"indicators.{field} es obligatorio cuando indicators está presente")

            value = indicators[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValidationError(f"indicators.{field} debe ser numérico")

            if value < 0 or value > 100:
                raise ValidationError(f"indicators.{field} debe estar entre 0 y 100")

    return event
