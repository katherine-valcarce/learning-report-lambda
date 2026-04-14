from __future__ import annotations

from io import BytesIO
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen
import zipfile

from src.exceptions import StorageError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CheckerFileDownloader:
    """Interfaz base para descargar archivos verificadores."""

    def download(self, file_url: str) -> bytes:
        raise NotImplementedError


class HttpCheckerFileDownloader(CheckerFileDownloader):
    """Descarga directa por HTTP(S)."""

    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds

    def download(self, file_url: str) -> bytes:
        try:
            with urlopen(file_url, timeout=self.timeout_seconds) as response:
                return response.read()
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
                    try:
                        downloaded_content = self.downloader.download(file_url)
                        zip_path = self._build_checker_zip_path(file_name)
                        zip_file.writestr(zip_path, downloaded_content)
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
            checker_files = item.get("checker_files", [])
            if not isinstance(checker_files, list):
                continue
            for checker_file in checker_files:
                if isinstance(checker_file, dict):
                    yield checker_file

    def _build_checker_zip_path(self, file_name: str) -> str:
        parsed_name = PurePosixPath(urlparse(file_name).path).name or "archivo"
        return f"verificadores/{parsed_name}"
