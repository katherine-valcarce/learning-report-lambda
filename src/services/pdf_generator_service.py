from datetime import datetime, timezone
from io import BytesIO
from math import cos, radians, sin
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Circle, Drawing, String
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from src.exceptions import PdfGenerationError


class PdfGeneratorService:
    def __init__(self) -> None:
        self.page_width, self.page_height = LETTER
        self.margin_x = 48
        self.margin_top = 52
        self.margin_bottom = 44
        self.line_height = 14

        # Paleta sobria y profesional
        self.palette = {
            "navy": colors.HexColor("#0F2D4E"),
            "navy_soft": colors.HexColor("#1D4A7A"),
            "gray_900": colors.HexColor("#1F2937"),
            "gray_700": colors.HexColor("#4B5563"),
            "gray_500": colors.HexColor("#6B7280"),
            "gray_200": colors.HexColor("#E5E7EB"),
            "gray_100": colors.HexColor("#F3F4F6"),
            "green": colors.HexColor("#2E7D32"),
            "green_soft": colors.HexColor("#EAF6EC"),
            "red": colors.HexColor("#B91C1C"),
            "red_soft": colors.HexColor("#FDECEC"),
            "amber": colors.HexColor("#B7791F"),
            "amber_soft": colors.HexColor("#FFF8E1"),
        }

    def generate(self, payload: dict[str, Any], metrics: dict[str, int]) -> BytesIO:
        buffer = BytesIO()

        try:
            pdf = canvas.Canvas(buffer, pagesize=LETTER)
            y = self.page_height - self.margin_top

            def new_page() -> float:
                nonlocal page_counter
                draw_footer(page_counter)
                page_counter += 1
                pdf.showPage()
                return self.page_height - self.margin_top

            def ensure_space(current_y: float, needed_height: float = 0) -> float:
                if current_y - needed_height < self.margin_bottom:
                    return new_page()
                return current_y

            def draw_footer(page_number: int) -> None:
                footer_y = self.margin_bottom - 22
                pdf.setStrokeColor(self.palette["gray_200"])
                pdf.line(self.margin_x, footer_y + 10, self.page_width - self.margin_x, footer_y + 10)
                pdf.setFillColor(self.palette["gray_500"])
                pdf.setFont("Helvetica", 8)
                pdf.drawString(self.margin_x, footer_y, "Informe de cumplimiento de proveedor")
                page_label = f"Página {page_number}"
                label_w = stringWidth(page_label, "Helvetica", 8)
                pdf.drawString(self.page_width - self.margin_x - label_w, footer_y, page_label)

            page_counter = 1

            def safe_value(value: Any) -> str:
                if value is None:
                    return ""
                if isinstance(value, bool):
                    return "Sí" if value else "No"
                return str(value)

            def safe_optional_value(value: Any) -> str:
                text = safe_value(value).strip()
                return text if text else "Sin información disponible"

            def draw_wrapped_text(
                text: str,
                x: float,
                current_y: float,
                max_width: float,
                font_name: str = "Helvetica",
                font_size: int = 10,
                color: colors.Color = colors.black,
                leading: float = 13,
            ) -> float:
                words = text.split()
                if not words:
                    return current_y - leading

                lines: list[str] = []
                line = ""
                for word in words:
                    candidate = f"{line} {word}".strip()
                    if stringWidth(candidate, font_name, font_size) <= max_width:
                        line = candidate
                    else:
                        if line:
                            lines.append(line)
                        line = word
                if line:
                    lines.append(line)

                pdf.setFont(font_name, font_size)
                pdf.setFillColor(color)
                for line_text in lines:
                    pdf.drawString(x, current_y, line_text)
                    current_y -= leading
                return current_y

            def draw_header_band(current_y: float) -> float:
                band_h = 86
                current_y = ensure_space(current_y, band_h)

                top = current_y
                left = self.margin_x
                width = self.page_width - (self.margin_x * 2)

                pdf.setFillColor(self.palette["navy"])
                pdf.roundRect(left, top - band_h, width, band_h, 8, fill=1, stroke=0)

                generated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

                pdf.setFillColor(colors.white)
                pdf.setFont("Helvetica-Bold", 17)
                pdf.drawString(left + 16, top - 28, "Informe de Cumplimiento ASG")

                pdf.setFont("Helvetica", 10)
                pdf.drawString(left + 16, top - 46, f"Solicitud: {safe_value(payload.get('request_id'))}")
                pdf.drawString(left + 16, top - 61, f"Generado: {generated_at}")

                pdf.setFillColor(self.palette["gray_200"])
                pdf.setFont("Helvetica-Bold", 9)
                pdf.drawRightString(left + width - 16, top - 46, "Evaluación de Proveedor")

                return top - band_h - 28

            def draw_section_title(title: str, current_y: float) -> float:
                current_y = ensure_space(current_y, 28)
                pdf.setFillColor(self.palette["navy_soft"])
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(self.margin_x, current_y, title)

                pdf.setStrokeColor(self.palette["gray_200"])
                pdf.setLineWidth(1)
                pdf.line(self.margin_x, current_y - 5, self.page_width - self.margin_x, current_y - 5)
                return current_y - 24

            def draw_key_values(items: list[tuple[str, str]], current_y: float) -> float:
                card_h = max(56, (len(items) * 16) + 16)
                current_y = ensure_space(current_y, card_h + 6)

                card_w = self.page_width - (self.margin_x * 2)
                top = current_y
                left = self.margin_x

                pdf.setFillColor(self.palette["gray_100"])
                pdf.setStrokeColor(self.palette["gray_200"])
                pdf.roundRect(left, top - card_h, card_w, card_h, 6, fill=1, stroke=1)

                row_y = top - 18
                for label, value in items:
                    pdf.setFillColor(self.palette["gray_700"])
                    pdf.setFont("Helvetica-Bold", 9)
                    pdf.drawString(left + 14, row_y, label.upper())

                    pdf.setFillColor(self.palette["gray_900"])
                    pdf.setFont("Helvetica", 10)
                    row_y = draw_wrapped_text(value, left + 150, row_y, card_w - 165)
                    row_y -= 2

                return top - card_h - 10

            def draw_metric_box(
                x: float,
                top: float,
                width: float,
                height: float,
                title: str,
                value: str,
                tone: str = "neutral",
            ) -> None:
                if tone == "positive":
                    fill = self.palette["green_soft"]
                    border = self.palette["green"]
                    label_color = self.palette["green"]
                else:
                    fill = self.palette["gray_100"]
                    border = self.palette["gray_200"]
                    label_color = self.palette["gray_700"]

                pdf.setFillColor(fill)
                pdf.setStrokeColor(border)
                pdf.roundRect(x, top - height, width, height, 6, fill=1, stroke=1)

                pdf.setFillColor(label_color)
                pdf.setFont("Helvetica-Bold", 8)
                pdf.drawString(x + 10, top - 16, title.upper())

                pdf.setFillColor(self.palette["gray_900"])
                pdf.setFont("Helvetica-Bold", 15)
                pdf.drawString(x + 10, top - 36, value)

            def draw_summary_metrics(current_y: float) -> float:
                box_h = 48
                gap = 10
                total_w = self.page_width - (self.margin_x * 2)
                box_w = (total_w - (gap * 2)) / 3
                chart_h = 158
                needed_h = (box_h * 2) + gap + 16 + chart_h
                current_y = ensure_space(current_y, needed_h)

                left = self.margin_x
                top = current_y

                values = [
                    ("Total criterios", safe_value(metrics.get("total_criteria", 0)), "neutral"),
                    ("Tienen", safe_value(metrics.get("has_compliance", 0)), "positive"),
                    ("No tienen", safe_value(metrics.get("has_no_compliance", 0)), "neutral"),
                    ("Verificados", safe_value(metrics.get("verified_criteria", 0)), "positive"),
                    (
                        "Archivos verificadores",
                        safe_value(metrics.get("total_checker_files", 0)),
                        "neutral",
                    ),
                    (
                        "Tasa verificación",
                        f"{round((metrics.get('verified_criteria', 0) / max(metrics.get('total_criteria', 1), 1)) * 100)}%",
                        "positive",
                    ),
                ]

                for idx, (title, value, tone) in enumerate(values):
                    row = idx // 3
                    col = idx % 3
                    x = left + (col * (box_w + gap))
                    box_top = top - (row * (box_h + gap))
                    draw_metric_box(x, box_top, box_w, box_h, title, value, tone)

                chart_top = top - ((box_h * 2) + gap) - 18
                indicators = payload.get("indicators")
                if isinstance(indicators, dict):
                    reported_value = indicators.get("reported_compliance_level")
                    verified_value = indicators.get("verified_compliance_level")
                else:
                    reported_value = None
                    verified_value = None

                has_indicator_values = isinstance(reported_value, (int, float)) and isinstance(verified_value, (int, float))

                if has_indicator_values:
                    reported_value = max(0, min(100, float(reported_value)))
                    verified_value = max(0, min(100, float(verified_value)))
                    # Layout de 2 columnas: gráfico de anillos a la izquierda y leyenda a la derecha
                    chart_column_w = total_w * 0.5
                    drawing = Drawing(chart_column_w, chart_h)

                    ring_center_x = chart_column_w * 0.47
                    ring_center_y = chart_h * 0.52
                    outer_size = 124
                    inner_ring_size = 86
                    center_radius = 30
                    ring_bg = colors.HexColor("#E5E7EB")

                    # Anillo exterior: cumplimiento verificado
                    outer_pie = Pie()
                    outer_pie.x = ring_center_x - (outer_size / 2)
                    outer_pie.y = ring_center_y - (outer_size / 2)
                    outer_pie.width = outer_size
                    outer_pie.height = outer_size
                    outer_pie.slices.strokeWidth = 0
                    outer_pie.data = [verified_value, max(0.0, 100.0 - verified_value)]
                    outer_pie.slices[0].fillColor = colors.HexColor("#059669")
                    outer_pie.slices[1].fillColor = ring_bg
                    outer_pie.labels = ["", ""]
                    drawing.add(outer_pie)

                    # Ahuecado del anillo exterior para dejarlo más delgado
                    drawing.add(
                        Circle(
                            ring_center_x,
                            ring_center_y,
                            (outer_size / 2) - 14,
                            fillColor=colors.white,
                            strokeColor=colors.white,
                            strokeWidth=0,
                        )
                    )

                    # Anillo interior: cumplimiento informado
                    inner_pie = Pie()
                    inner_pie.x = ring_center_x - (inner_ring_size / 2)
                    inner_pie.y = ring_center_y - (inner_ring_size / 2)
                    inner_pie.width = inner_ring_size
                    inner_pie.height = inner_ring_size
                    inner_pie.slices.strokeWidth = 0
                    inner_pie.data = [reported_value, max(0.0, 100.0 - reported_value)]
                    inner_pie.slices[0].fillColor = colors.HexColor("#3b82f6")
                    inner_pie.slices[1].fillColor = ring_bg
                    inner_pie.labels = ["", ""]
                    drawing.add(inner_pie)

                    # Centro blanco limpio (sin borde ni texto)
                    drawing.add(
                        Circle(
                            ring_center_x,
                            ring_center_y,
                            center_radius,
                            fillColor=colors.white,
                            strokeColor=colors.white,
                            strokeWidth=0,
                        )
                    )

                    # Porcentajes sobre los anillos (sin cajas, sobrio y legible)
                    outer_label_angle = 34  # cerca del arco superior derecho del anillo exterior
                    inner_label_angle = 216  # cerca del arco inferior izquierdo del anillo interior
                    outer_label_radius = (outer_size / 2) - 7
                    inner_label_radius = (inner_ring_size / 2) - 6

                    outer_label_x = ring_center_x + (outer_label_radius * cos(radians(outer_label_angle)))
                    outer_label_y = ring_center_y + (outer_label_radius * sin(radians(outer_label_angle)))
                    inner_label_x = ring_center_x + (inner_label_radius * cos(radians(inner_label_angle)))
                    inner_label_y = ring_center_y + (inner_label_radius * sin(radians(inner_label_angle)))

                    drawing.add(
                        String(
                            outer_label_x,
                            outer_label_y,
                            f"{verified_value:.0f}%",
                            fontName="Helvetica-Bold",
                            fontSize=9,
                            fillColor=colors.HexColor("#047857"),
                            textAnchor="middle",
                        )
                    )
                    drawing.add(
                        String(
                            inner_label_x,
                            inner_label_y,
                            f"{reported_value:.0f}%",
                            fontName="Helvetica-Bold",
                            fontSize=9,
                            fillColor=colors.HexColor("#1d4ed8"),
                            textAnchor="middle",
                        )
                    )

                    renderPDF.draw(drawing, pdf, self.margin_x, chart_top - chart_h)

                    legend_x = self.margin_x + chart_column_w + 12
                    legend_block_h = 70
                    legend_y = chart_top - ((chart_h - legend_block_h) / 2)

                    pdf.setFillColor(self.palette["gray_900"])
                    pdf.setFont("Helvetica-Bold", 11)
                    pdf.drawString(legend_x, legend_y, "Indicadores de cumplimiento")

                    legend_items = [
                        ("Cumplimiento informado", f"{reported_value:.0f}%", colors.HexColor("#3b82f6")),
                        ("Cumplimiento verificado", f"{verified_value:.0f}%", colors.HexColor("#059669")),
                    ]
                    row_y = legend_y - 24
                    for label, value, color in legend_items:
                        pdf.setFillColor(color)
                        pdf.circle(legend_x + 4, row_y + 3, 4, stroke=0, fill=1)
                        pdf.setFillColor(self.palette["gray_700"])
                        pdf.setFont("Helvetica", 10)
                        pdf.drawString(legend_x + 14, row_y, label)
                        pdf.setFillColor(self.palette["gray_900"])
                        pdf.setFont("Helvetica-Bold", 10)
                        pdf.drawRightString(self.page_width - self.margin_x, row_y, value)
                        row_y -= 22
                else:
                    pdf.setFillColor(self.palette["gray_700"])
                    pdf.setFont("Helvetica", 10)
                    pdf.drawString(self.margin_x, chart_top - 28, "Sin información disponible")

                return top - needed_h - 4

            def draw_status_pill(x: float, y_top: float, label: str, kind: str) -> None:
                if kind == "ok":
                    fill = self.palette["green_soft"]
                    text_color = self.palette["green"]
                elif kind == "warning":
                    fill = self.palette["amber_soft"]
                    text_color = self.palette["amber"]
                else:
                    fill = self.palette["red_soft"]
                    text_color = self.palette["red"]

                w = stringWidth(label, "Helvetica-Bold", 8) + 18
                h = 14
                pdf.setFillColor(fill)
                pdf.setStrokeColor(fill)
                pdf.roundRect(x, y_top - h + 3, w, h, 7, fill=1, stroke=0)
                pdf.setFillColor(text_color)
                pdf.setFont("Helvetica-Bold", 8)
                pdf.drawString(x + 9, y_top - 7, label)

            def normalize_category(raw_type: str) -> str:
                candidate = (raw_type or "").strip().lower()
                mapping = {
                    "ambiental": "Ambiental",
                    "environmental": "Ambiental",
                    "social": "Social",
                    "gobernanza": "Gobernanza",
                    "governance": "Gobernanza",
                }
                return mapping.get(candidate, raw_type if raw_type else "Otros")

            def draw_criterion_item(item: dict[str, Any], current_y: float) -> float:
                checker_files = item.get("checker_files", [])
                file_names = [f.get("file_name", "") for f in checker_files if isinstance(f, dict) and f.get("file_name")]

                dynamic_h = 102 + (len(file_names) * 13)
                current_y = ensure_space(current_y, dynamic_h)

                left = self.margin_x
                width = self.page_width - (self.margin_x * 2)
                top = current_y
                height = dynamic_h - 6

                pdf.setFillColor(colors.white)
                pdf.setStrokeColor(self.palette["gray_200"])
                pdf.roundRect(left, top - height, width, height, 6, fill=1, stroke=1)

                compliance_value = safe_value(item.get("compliance", "")).strip().lower()
                if compliance_value == "tiene":
                    compliance_label = "Tiene"
                    compliance_kind = "ok"
                elif compliance_value == "no tiene":
                    compliance_label = "No tiene"
                    compliance_kind = "error"
                else:
                    compliance_label = "En revisión"
                    compliance_kind = "warning"

                verified = bool(item.get("is_verified"))
                verification_label = "Verificado" if verified else "No verificado"
                verification_kind = "ok" if verified else "warning"

                draw_status_pill(left + width - 170, top - 12, compliance_label, compliance_kind)
                draw_status_pill(left + width - 84, top - 12, verification_label, verification_kind)

                pdf.setFillColor(self.palette["gray_900"])
                pdf.setFont("Helvetica-Bold", 11)
                title = safe_value(item.get("title", "Sin título"))
                y_text = draw_wrapped_text(title, left + 12, top - 28, width - 24, "Helvetica-Bold", 11, self.palette["gray_900"], 13)

                pdf.setFont("Helvetica", 9)
                pdf.setFillColor(self.palette["gray_700"])
                pdf.drawString(left + 12, y_text - 2, f"Tipo: {safe_value(item.get('type', ''))}")
                pdf.drawString(left + 170, y_text - 2, f"Archivos: {len(checker_files)}")

                y_files = y_text - 16
                if file_names:
                    pdf.setFillColor(self.palette["navy_soft"])
                    pdf.setFont("Helvetica-Bold", 9)
                    pdf.drawString(left + 12, y_files, "Archivos verificadores")
                    y_files -= 12

                    pdf.setFillColor(self.palette["gray_700"])
                    pdf.setFont("Helvetica", 9)
                    for file_name in file_names:
                        y_files = draw_wrapped_text(f"• {file_name}", left + 16, y_files, width - 28, "Helvetica", 9, self.palette["gray_700"], 11)

                return top - height - 12

            criteria_by_type: dict[str, list[dict[str, Any]]] = {}
            for criterion in payload.get("criteria", []):
                category = normalize_category(safe_value(criterion.get("type", "")))
                criteria_by_type.setdefault(category, []).append(criterion)

            y = draw_header_band(y)

            requested_by = payload.get("requested_by", {})
            y = draw_section_title("Solicitado por", y)
            y = draw_key_values(
                [
                    ("Nombre", safe_value(requested_by.get("name", ""))),
                    ("Correo electrónico", safe_value(requested_by.get("email", ""))),
                ],
                y,
            )
            y -= 12

            supplier = payload.get("supplier", {})
            y = draw_section_title("Datos del proveedor", y)
            y = draw_key_values(
                [
                    ("Razón social", safe_optional_value(supplier.get("business_name", ""))),
                    ("RUT", safe_optional_value(supplier.get("rut", ""))),
                    ("Industria", safe_optional_value(supplier.get("industry", ""))),
                    ("Nombre de marca", safe_optional_value(supplier.get("brand_name", ""))),
                    ("Sitio web", safe_optional_value(supplier.get("link", ""))),
                ],
                y,
            )
            y -= 12

            y = draw_section_title("Resumen ejecutivo", y)
            y = draw_summary_metrics(y)
            y -= 6

            y = draw_section_title("Detalle de criterios por categoría", y)

            for category in ["Ambiental", "Social", "Gobernanza", "Otros"]:
                items = criteria_by_type.get(category, [])
                if not items:
                    continue

                y = ensure_space(y, 30)
                pdf.setFillColor(self.palette["navy"])
                pdf.setFont("Helvetica-Bold", 11)
                pdf.drawString(self.margin_x, y, f"{category} ({len(items)})")
                y -= 16

                for item in items:
                    y = draw_criterion_item(item, y)

            draw_footer(page_counter)
            pdf.save()
            buffer.seek(0)
            return buffer
        except Exception as exc:
            raise PdfGenerationError(f"No fue posible generar el PDF: {exc}") from exc
