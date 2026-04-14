import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.exceptions import EmailDeliveryError


class EmailService:
    def __init__(
        self,
        sender_email: str,
        region_name: str,
        platform_url: str = "",
        logo_url: str = "https://i.imgur.com/15AZiBa.png",
    ) -> None:
        self.sender_email = sender_email
        self.sender_name = "ComesPro"
        self.client = boto3.client("ses", region_name=region_name)
        self.platform_url = platform_url.strip()
        self.logo_url = logo_url.strip()

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
        subject = f"Informe de cumplimiento disponible | {supplier_name}"
        body_text = "".join(
            [
                f"Hola {recipient_name},\n\n",
                "Te confirmamos que el informe de cumplimiento fue generado correctamente.\n",
                f"Proveedor evaluado: {supplier_name}\n",
                f"ID de solicitud: {request_id}\n\n",
                "Ya puedes descargar los archivos del informe:\n\n",
                "1) Informe PDF (solo documento consolidado):\n",
                f"{pdf_reference}\n\n",
                "2) ZIP de verificadores (PDF + carpeta de verificadores disponibles):\n",
                f"{zip_reference}\n\n",
                (
                    f"También puedes ingresar a la plataforma:\n{self.platform_url}\n\n"
                    if self.platform_url
                    else ""
                ),
                "Si necesitas apoyo adicional, responde este correo.\n\n",
                "Saludos,\n",
                "Equipo de Cumplimiento\n",
                "Comes Pro",
            ]
        )

        platform_link_html = ""
        if self.platform_url:
            platform_link_html = f"""
            <div style=\"background: #F8F9FA; padding: 22px 20px; text-align: center; font-size: 14px; color: #666666;\">
              ¿Quieres tener mayor información?<br />
              Ingresa a la plataforma <strong>E-learning Comes Pro</strong><br /><br />
              <a
                href=\"{self.platform_url}\"
                style=\"color: #2EBC85; text-decoration: none; font-weight: 600;\"
              >
                Ir a la plataforma →
              </a>
            </div>
            """

        body_html = f"""
        <html>
          <body style=\"font-family: Arial, Helvetica, sans-serif; background-color: #F4F7F9; margin: 0; padding: 16px;\">
            <div style=\"max-width: 600px; margin: 0 auto; background: #FFFFFF; border-radius: 12px; overflow: hidden;\">
              <div style=\"background: linear-gradient(135deg, #2EBC85, #1E9B6B); padding: 24px 20px; text-align: center; color: #FFFFFF;\">
                <img src=\"{self.logo_url}\" alt=\"Comes Pro\" style=\"max-width: 130px; height: auto;\" />
                <h1 style=\"margin: 12px 0 0 0; font-size: 26px; font-weight: 700;\">¡Informe de Cumplimiento Listo!</h1>
              </div>
              <div style=\"padding: 30px 20px; color: #333333;\">
                <p style=\"font-size: 21px; font-weight: 600; color: #2EBC85; margin-bottom: 12px;\">
                  Hola {recipient_name},
                </p>
                <p>Te confirmamos que el <strong>informe de cumplimiento</strong> se generó correctamente.</p>
                <div style=\"background: #F8FCF9; border-left: 5px solid #2EBC85; padding: 18px; margin: 25px 0; border-radius: 8px;\">
                  <strong>Proveedor evaluado:</strong> {supplier_name}<br /><br />
                  <strong>ID de solicitud:</strong> {request_id}
                </div>
                <h2 style=\"text-align: center; color: #2EBC85; margin: 25px 0 20px 0; font-size: 19px;\">
                  Descarga tu informe
                </h2>
                <div style=\"margin: 30px 0;\">
                  <a href=\"{pdf_reference}\" style=\"display: block; background: #2EBC85; color: #FFFFFF; padding: 16px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; text-align: center;\">
                    📄 Descargar Informe PDF
                  </a>
                  <a href=\"{zip_reference}\" style=\"display: block; background: #1E9B6B; color: #FFFFFF; padding: 16px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; text-align: center; margin-top: 12px;\">
                    📦 Descargar ZIP con verificadores
                  </a>
                </div>
                <p style=\"text-align: center; color: #555555; font-size: 15px; line-height: 1.6; margin: 20px 0 30px 0;\">
                  El PDF contiene el documento consolidado con el resultado completo.<br />
                  El ZIP incluye el informe + todos los documentos verificadores disponibles.
                </p>
                <p style=\"margin-top: 25px; text-align: center;\">¡Saludos!</p>
                <p style=\"text-align: center; margin-top: 5px;\">
                  <strong>Equipo de Cumplimiento</strong><br />
                  Comes Pro
                </p>
              </div>
              {platform_link_html}
            </div>
          </body>
        </html>
        """

        try:
            response = self.client.send_email(
                Source=f"{self.sender_name} <{self.sender_email}>",
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
