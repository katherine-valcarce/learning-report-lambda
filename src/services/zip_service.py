from __future__ import annotations

import mimetypes
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen
import zipfile

from src.exceptions import StorageError
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class DownloadedCheckerFile:
    content: bytes
    content_type: str | None = None


class CheckerFileDownloader:
    """Interfaz base para descargar archivos verificadores."""

    def download(self, file_url: str) -> DownloadedCheckerFile:
        raise NotImplementedError


class HttpCheckerFileDownloader(CheckerFileDownloader):
    """Descarga directa por HTTP(S)."""

    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds

    def download(self, file_url: str) -> DownloadedCheckerFile:
        try:
            with urlopen(file_url, timeout=self.timeout_seconds) as response:
                content_type = response.headers.get_content_type()
                return DownloadedCheckerFile(
                    content=response.read(),
                    content_type=content_type if content_type and content_type != "application/octet-stream" else None,
                )
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"No se pudo descargar archivo verificador desde {file_url}: {exc}") from exc


class ZipService:
    def __init__(self, downloader: CheckerFileDownloader | None = None) -> None:
        self.downloader = downloader or HttpCheckerFileDownloader()

    def generate_report_package(
        self,
        *,
        pdf_buffer: BytesIO,
        criteria: list[dict[str, Any]],
        pdf_name: str = "informe.pdf",
    ) -> BytesIO:
        zip_buffer = BytesIO()
        downloaded_count = 0
        failed_count = 0

        try:
            with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr(pdf_name, pdf_buffer.getvalue())

                for checker_file in self._iter_checker_files(criteria):
                    file_name = checker_file["file_name"].strip()
                    file_url = checker_file["file_url"].strip()
                    checker_type = checker_file["checker_type"].strip()
                    try:
                        downloaded_file = self.downloader.download(file_url)
                        zip_path = self._build_checker_zip_path(
                            checker_type=checker_type,
                            file_name=file_name,
                            file_url=file_url,
                            content_type=downloaded_file.content_type,
                        )
                        zip_file.writestr(zip_path, downloaded_file.content)
                        downloaded_count += 1
                    except StorageError as exc:
                        failed_count += 1
                        logger.warning(
                            "No se pudo descargar checker_file file_name=%s file_url=%s error=%s",
                            file_name,
                            file_url,
                            exc,
                        )

            logger.info(
                "ZIP generado con verificadores descargados=%s fallidos=%s",
                downloaded_count,
                failed_count,
            )

            zip_buffer.seek(0)
            return zip_buffer
        except StorageError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"No se pudo generar el ZIP final: {exc}") from exc

    def _iter_checker_files(self, criteria: list[dict[str, Any]]):
        for item in criteria:
            checker_type = self._normalize_checker_type(item.get("type", ""))
            checker_files = item.get("checker_files", [])
            if not isinstance(checker_files, list):
                continue
            for checker_file in checker_files:
                if isinstance(checker_file, dict):
                    enriched_file = dict(checker_file)
                    enriched_file["checker_type"] = checker_type
                    yield enriched_file

    def _build_checker_zip_path(
        self,
        *,
        checker_type: str,
        file_name: str,
        file_url: str,
        content_type: str | None,
    ) -> str:
        parsed_name = PurePosixPath(urlparse(file_name).path).name or "archivo"
        final_name = self._ensure_extension(
            parsed_name=parsed_name,
            file_url=file_url,
            content_type=content_type,
        )
        return f"verificadores/{checker_type}/{final_name}"

    def _normalize_checker_type(self, raw_type: Any) -> str:
        candidate = str(raw_type or "").strip().lower()
        mapping = {
            "ambiental": "Ambiental",
            "social": "Social",
            "gobernanza": "Gobernanza",
            "governance": "Gobernanza",
            "environmental": "Ambiental",
        }
        return mapping.get(candidate, "Otros")

    def _ensure_extension(
        self,
        *,
        parsed_name: str,
        file_url: str,
        content_type: str | None,
    ) -> str:
        if PurePosixPath(parsed_name).suffix:
            return parsed_name

        extension = self._detect_extension_from_url(file_url)
        if not extension and content_type:
            extension = mimetypes.guess_extension(content_type, strict=False)

        if not extension:
            extension = ".bin"
        elif not extension.startswith("."):
            extension = f".{extension}"

        return f"{parsed_name}{extension}"

    def _detect_extension_from_url(self, file_url: str) -> str | None:
        parsed = urlparse(file_url)
        path_suffix = PurePosixPath(parsed.path).suffix
        if path_suffix:
            return path_suffix

        data_url_match = re.match(r"^data:([^;,]+)", file_url, re.IGNORECASE)
        if data_url_match:
            mime_type = data_url_match.group(1).strip().lower()
            return mimetypes.guess_extension(mime_type, strict=False)

        return None
