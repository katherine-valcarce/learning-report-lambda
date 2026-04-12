+# learning-report-lambda
+
+Lambda AWS (Python 3.10+) para generar un **informe PDF de cumplimiento de proveedor**, subirlo a **S3** y notificar al solicitante por **SES**.
+
+## Propósito
+
+Esta Lambda procesa un evento asíncrono (`InvocationType: Event`) enviado por tu API. No consulta APIs externas ni base de datos; solamente usa el payload recibido para:
+
+1. Validar contrato de entrada.
+2. Calcular métricas de resumen.
+3. Generar un PDF legible con ReportLab.
+4. Subir el PDF a S3.
+5. Enviar correo por SES al solicitante.
+
+## Arquitectura resumida
+
+- `handler.py`: orquesta el flujo completo.
+- `validators.py`: valida el contrato exacto del payload.
+- `pdf_generator_service.py`: arma el PDF en memoria (`BytesIO`) con paginación.
+- `s3_service.py`: sube a S3 y retorna metadata + presigned URL.
+- `email_service.py`: envía notificación por SES.
+- `config.py`: centraliza y valida variables de entorno.
+
+## Estructura de carpetas
+
+```text
+learning-report-lambda/
+├── src/
+│   ├── handler.py
+│   ├── config.py
+│   ├── exceptions.py
+│   ├── services/
+│   │   ├── pdf_generator_service.py
+│   │   ├── s3_service.py
+│   │   └── email_service.py
+│   └── utils/
+│       ├── logger.py
+│       └── validators.py
+├── requirements.txt
+└── README.md
+```
+
+## Variables de entorno
+
+Obligatorias:
+
+- `S3_BUCKET_NAME`
+- `SES_SENDER_EMAIL`
+- `AWS_REGION`
+
+Opcional:
+
+- `REPORTS_PREFIX` (default: `reports`)
+
+## Contrato del evento de entrada (payload oficial)
+
+```json
+{
+  "request_id": "uuid",
+  "requested_by": {
+    "name": "string",
+    "email": "string"
+  },
+  "supplier": {
+    "id_supplier": "uuid",
+    "business_name": "string",
+    "rut": "string",
+    "industry": "string",
+    "brand_name": "string",
+    "link": "string",
+    "slug": "string"
+  },
+  "criteria": [
+    {
+      "id_supplier_criteria": 123,
+      "type": "Ambiental | Social | Gobernanza",
+      "title": "string",
+      "compliance": "Tiene | No tiene",
+      "is_verified": true,
+      "checker_files": [
+        {
+          "file_name": "archivo.pdf",
+          "file_url": "https://..."
+        }
+      ]
+    }
+  ]
+}
+```
+
+## Ejecución local (prueba rápida)
+
+1. Exporta variables de entorno:
+
+```bash
+export S3_BUCKET_NAME="mi-bucket"
+export SES_SENDER_EMAIL="no-reply@midominio.com"
+export AWS_REGION="us-east-1"
+export REPORTS_PREFIX="reports"
+```
+
+2. Ejecuta una invocación local con Python:
+
+```python
+from src.handler import lambda_handler
+
+event = {
+  "request_id": "a7f87c66-c7d4-4d4c-aec9-f34fc3f222f9",
+  "requested_by": {"name": "Ana Pérez", "email": "ana@example.com"},
+  "supplier": {
+    "id_supplier": "ba8d4f2a-6f02-43db-8f70-cf05ff9e19e2",
+    "business_name": "Proveedor Demo SPA",
+    "rut": "76.123.456-7",
+    "industry": "Educación",
+    "brand_name": "Demo Learning",
+    "link": "https://demo.example.com",
+    "slug": "proveedor-demo"
+  },
+  "criteria": [
+    {
+      "id_supplier_criteria": 1,
+      "type": "Ambiental",
+      "title": "Política de residuos",
+      "compliance": "Tiene",
+      "is_verified": True,
+      "checker_files": [
+        {"file_name": "politica-residuos.pdf", "file_url": "https://files.example.com/politica-residuos.pdf"}
+      ]
+    }
+  ]
+}
+
+print(lambda_handler(event, None))
+```
+
+> Nota: para enviar correo real en SES y subir a S3, la cuenta/rol de ejecución debe tener permisos IAM correctos y, si SES está en sandbox, destinatarios verificados.
+
+## Despliegue (resumen)
+
+1. Empaqueta el código + dependencias de `requirements.txt`.
+2. Configura runtime Python 3.10+.
+3. Define handler: `src.handler.lambda_handler`.
+4. Configura variables de entorno requeridas.
+5. Asigna permisos IAM mínimos:
+   - `s3:PutObject` sobre bucket destino.
+   - `ses:SendEmail` sobre remitente configurado.
+   - `logs:*` básico para CloudWatch Logs.
+
+## Qué adaptar antes de producción
+
+- Gestión de errores/reintentos (DLQ o destino de errores de Lambda asíncrona).
+- Políticas de expiración de presigned URL según seguridad.
+- Plantilla HTML de correo corporativa.
+- Estrategia de versionado/retención de reportes en S3.
+- Pruebas automatizadas unitarias e integración.
 
EOF
)