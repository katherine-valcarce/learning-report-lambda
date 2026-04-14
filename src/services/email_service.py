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
        zip_reference: str,
    ) -> dict:
        subject = f"Informe de cumplimiento disponible | Proveedor {supplier_name}"
        body_text = (
            f"Hola {recipient_name},\n\n"
            "Te confirmamos que el informe de cumplimiento fue generado correctamente.\n"
            f"Proveedor evaluado: {supplier_name}\n"
            f"ID de solicitud: {request_id}\n\n"
            "Ya puedes acceder al paquete ZIP del informe en el siguiente enlace/referencia:\n"
            f"{zip_reference}\n\n"
            "El archivo ZIP incluye:\n"
            "- Informe PDF consolidado\n"
            "- Archivos verificadores asociados a los criterios evaluados\n\n"
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
            <p>
              Ya puedes acceder al paquete ZIP del informe en el siguiente enlace/referencia:
              <a href=\"{zip_reference}\">Descargar paquete ZIP</a>
            </p>
            <p>El archivo ZIP incluye:</p>
            <ul>
              <li>Informe PDF consolidado</li>
              <li>Archivos verificadores asociados a los criterios evaluados</li>
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
