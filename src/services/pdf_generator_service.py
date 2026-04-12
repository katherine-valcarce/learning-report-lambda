from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from src.exceptions import PdfGenerationError


class PdfGeneratorService:
    def __init__(self) -> None:
        self.page_width, self.page_height = LETTER
        self.margin_x = 50
        self.margin_top = 50
        self.margin_bottom = 50
        self.line_height = 14

    def generate(self, payload: dict[str, Any], metrics: dict[str, int]) -> BytesIO:
        buffer = BytesIO()
        try:
            pdf = canvas.Canvas(buffer, pagesize=LETTER)
            y = self.page_height - self.margin_top

            def ensure_space(current_y: float, needed_lines: int = 1) -> float:
                if current_y - (needed_lines * self.line_height) < self.margin_bottom:
                    pdf.showPage()
                    return self.page_height - self.margin_top
                return current_y

            def draw_title(text: str, current_y: float) -> float:
                current_y = ensure_space(current_y, 2)
                pdf.setFont("Helvetica-Bold", 15)
                pdf.drawString(self.margin_x, current_y, text)
                return current_y - (self.line_height * 1.5)

            def draw_line(label: str, value: str, current_y: float, bold_label: bool = True) -> float:
                current_y = ensure_space(current_y)
                if bold_label:
                    pdf.setFont("Helvetica-Bold", 10)
                    pdf.drawString(self.margin_x, current_y, f"{label}:")
                    pdf.setFont("Helvetica", 10)
                    pdf.drawString(self.margin_x + 130, current_y, value)
                else:
                    pdf.setFont("Helvetica", 10)
                    pdf.drawString(self.margin_x, current_y, f"{label}: {value}")
                return current_y - self.line_height

            generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

            y = draw_title("Informe de cumplimiento del proveedor", y)
            y = draw_line("Fecha de generación", generated_at, y)
            y = draw_line("ID de solicitud", str(payload["request_id"]), y)

            y -= 8
            y = draw_title("Solicitado por", y)
            y = draw_line("Nombre", payload["requested_by"]["name"], y)
            y = draw_line("Email", payload["requested_by"]["email"], y)

            supplier = payload["supplier"]
            y -= 8
            y = draw_title("Datos del proveedor", y)
            y = draw_line("Razón social", supplier.get("business_name", ""), y)
            y = draw_line("RUT", supplier.get("rut", ""), y)
            y = draw_line("Industria", supplier.get("industry", ""), y)
            y = draw_line("Nombre de marca", supplier.get("brand_name", ""), y)
            y = draw_line("Sitio web", supplier.get("link", ""), y)
            y = draw_line("Slug", supplier.get("slug", ""), y)

            y -= 8
            y = draw_title("Resumen ejecutivo", y)
            y = draw_line("Total de criterios", str(metrics["total_criteria"]), y)
            y = draw_line("Cumplen (Tiene)", str(metrics["has_compliance"]), y)
            y = draw_line("No cumplen (No tiene)", str(metrics["has_no_compliance"]), y)
            y = draw_line("Criterios verificados", str(metrics["verified_criteria"]), y)
            y = draw_line("Total de archivos verificadores", str(metrics["total_checker_files"]), y)

            y -= 8
            y = draw_title("Detalle de criterios", y)

            for idx, item in enumerate(payload["criteria"], start=1):
                checker_files = item.get("checker_files", [])
                file_names = [f.get("file_name", "") for f in checker_files if isinstance(f, dict)]

                y = ensure_space(y, 7 + len(file_names))
                pdf.setFont("Helvetica-Bold", 11)
                pdf.drawString(self.margin_x, y, f"Criterio #{idx}")
                y -= self.line_height

                y = draw_line("Tipo", str(item.get("type", "")), y)
                y = draw_line("Título", str(item.get("title", "")), y)
                y = draw_line("Cumplimiento", str(item.get("compliance", "")), y)
                y = draw_line("Verificado", "Sí" if item.get("is_verified") else "No", y)
                y = draw_line("Archivos verificadores", str(len(checker_files)), y)

                if file_names:
                    y = draw_line("Nombres de archivos", "", y)
                    for file_name in file_names:
                        y = ensure_space(y)
                        pdf.setFont("Helvetica", 10)
                        pdf.drawString(self.margin_x + 20, y, f"• {file_name}")
                        y -= self.line_height

                y -= 6

            pdf.save()
            buffer.seek(0)
            return buffer
        except Exception as exc:
            raise PdfGenerationError(f"No fue posible generar el PDF: {exc}") from exc
