import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.exceptions import EmailDeliveryError


class EmailService:
    def __init__(self, sender_email: str, region_name: str) -> None:
        self.sender_email = sender_email
        self.client = boto3.client("ses", region_name=region_name)

    def send_report_ready_email(
        self,
        *,
        recipient_name: str,
        recipient_email: str,
        supplier_name: str,
        request_id: str,
        pdf_reference: str,
        zip_reference: str,
    ) -> dict:
        subject = f"Informe de cumplimiento disponible | Proveedor {supplier_name}"
        body_text = (
            f"Hola {recipient_name},\n\n"
            "Te confirmamos que el informe de cumplimiento fue generado correctamente.\n"
            f"Proveedor evaluado: {supplier_name}\n"
            f"ID de solicitud: {request_id}\n\n"
            "Ya puedes descargar los archivos del informe:\n\n"
            "1) Informe PDF (solo documento consolidado):\n"
            f"{pdf_reference}\n\n"
            "2) ZIP de verificadores (PDF + carpeta de verificadores disponibles):\n"
            f"{zip_reference}\n\n"
            "Si necesitas apoyo adicional, responde este correo.\n\n"
            "Saludos,\n"
            "Equipo de Cumplimiento"
        )

        body_html = f"""
        <html>
          <body style=\"font-family: Arial, sans-serif; color: #1F2937;\">
            <p>Hola {recipient_name},</p>
            <p>
              Te confirmamos que el informe de cumplimiento fue generado correctamente.
            </p>
            <ul>
              <li><strong>Proveedor evaluado:</strong> {supplier_name}</li>
              <li><strong>ID de solicitud:</strong> {request_id}</li>
            </ul>
            <p>Puedes acceder a los archivos desde los siguientes enlaces:</p>
            <ul>
              <li>
                <strong>Informe PDF:</strong> documento consolidado del resultado.
                <br />
                <a
                  href=\"{pdf_reference}\"
                  style=\"display: inline-block; margin-top: 8px; background: #1D4ED8; color: #FFFFFF; padding: 10px 16px; text-decoration: none; border-radius: 6px;\"
                >
                  Descargar Informe PDF
                </a>
              </li>
              <li style=\"margin-top: 16px;\">
                <strong>ZIP de verificadores:</strong> incluye el informe PDF y los verificadores disponibles.
                <br />
                <a
                  href=\"{zip_reference}\"
                  style=\"display: inline-block; margin-top: 8px; background: #0F766E; color: #FFFFFF; padding: 10px 16px; text-decoration: none; border-radius: 6px;\"
                >
                  Descargar ZIP de verificadores
                </a>
              </li>
            </ul>
            <p>Si necesitas apoyo adicional, responde este correo.</p>
            <p>Saludos,<br/>Equipo de Cumplimiento</p>
          </body>
        </html>
        """

        try:
            response = self.client.send_email(
                Source=self.sender_email,
                Destination={"ToAddresses": [recipient_email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": body_text, "Charset": "UTF-8"},
                        "Html": {"Data": body_html, "Charset": "UTF-8"},
                    },
                },
            )
            return response
        except (ClientError, BotoCoreError) as exc:
            raise EmailDeliveryError(f"Error enviando correo con SES: {exc}") from exc
