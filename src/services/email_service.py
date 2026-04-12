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
        report_reference: str,
    ) -> dict:
        subject = "Tu informe de cumplimiento ya está disponible"
        body_text = (
            f"Hola {recipient_name},\n\n"
            "Tu informe de cumplimiento fue generado correctamente.\n"
            f"Proveedor: {supplier_name}\n"
            f"ID de solicitud: {request_id}\n"
            f"Referencia del informe: {report_reference}\n\n"
            "Gracias por usar nuestra plataforma."
        )

        body_html = f"""
        <html>
          <body>
            <p>Hola {recipient_name},</p>
            <p>Tu informe de cumplimiento fue generado correctamente.</p>
            <ul>
              <li><strong>Proveedor:</strong> {supplier_name}</li>
              <li><strong>ID de solicitud:</strong> {request_id}</li>
              <li><strong>Referencia del informe:</strong> <a href="{report_reference}">{report_reference}</a></li>
            </ul>
            <p>Gracias por usar nuestra plataforma.</p>
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
