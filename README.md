# learning-report-lambda

Lambda AWS (Python 3.10+) para generar un **informe PDF de cumplimiento de proveedor**, subirlo a **S3** y notificar al solicitante por **SES**.

## Propósito

Esta Lambda procesa un evento asíncrono (`InvocationType: Event`) enviado por tu API. No consulta APIs externas ni base de datos; solamente usa el payload recibido para:

1. Validar contrato de entrada.
2. Calcular métricas de resumen.
3. Generar un PDF legible con ReportLab.
4. Subir el PDF a S3.
5. Enviar correo por SES al solicitante.

## Arquitectura resumida

- `handler.py`: orquesta el flujo completo.
- `validators.py`: valida el contrato exacto del payload.
- `pdf_generator_service.py`: arma el PDF en memoria (`BytesIO`) con paginación.
- `s3_service.py`: sube a S3 y retorna metadata + presigned URL.
- `email_service.py`: envía notificación por SES.
- `config.py`: centraliza y valida variables de entorno.

## Estructura de carpetas

```text
learning-report-lambda/
├── src/
│   ├── handler.py
│   ├── config.py
│   ├── exceptions.py
│   ├── services/
│   │   ├── pdf_generator_service.py
│   │   ├── s3_service.py
│   │   └── email_service.py
│   └── utils/
│       ├── logger.py
│       └── validators.py
├── requirements.txt
├── template.yaml
└── README.md
```

## Variables de entorno

### Variables soportadas

- `APP_ENV`: ambiente de ejecución (`dev` o `prod`). Default: `dev`.
- `AWS_REGION`: región AWS.
- `S3_BUCKET_NAME`: bucket donde se almacenan los PDFs.
- `SES_SENDER_EMAIL`: remitente de correo en SES.
- `REPORTS_PREFIX`: prefijo de carpeta en S3. Default: `reports`.
- `PLATFORM_URL`: URL pública de la plataforma (se muestra en el footer del correo). Default: vacío.
- `EMAIL_LOGO_URL`: URL del logo usado en la cabecera del correo. Default: `https://i.imgur.com/15AZiBa.png`.
- `EMAIL_LOGO_PATH`: ruta local absoluta del logo para incrustarlo en base64 dentro del correo (opcional). Si se define, tiene prioridad sobre `EMAIL_LOGO_URL`.
- `LOCAL_TEST_MODE`: `true`/`false` (en minúscula recomendado). Default: `false`.

### Reglas de validación

- Si `LOCAL_TEST_MODE=false` (modo AWS), `AWS_REGION`, `S3_BUCKET_NAME` y `SES_SENDER_EMAIL` son obligatorias y no pueden estar vacías.
- Si `LOCAL_TEST_MODE=true` (modo local), esas variables pueden omitirse para pruebas sin S3/SES.

## Contrato del evento de entrada (payload oficial)

```json
{
  "request_id": "uuid",
  "requested_by": {
    "name": "string",
    "email": "string"
  },
  "supplier": {
    "id_supplier": "uuid",
    "business_name": "string",
    "country": "chl | per | arg (opcional, default: chl)",
    "rut": "string",
    "industry": "string",
    "brand_name": "string",
    "link": "string"
  },
  "criteria": [
    {
      "id_supplier_criteria": 123,
      "type": "Ambiental | Social | Gobernanza",
      "title": "string",
      "compliance": "Tiene | No tiene",
      "is_verified": true,
      "checker_files": [
        {
          "file_name": "archivo.pdf",
          "file_url": "https://..."
        }
      ]
    }
  ]
}
```

## Ejecución local (prueba rápida)

1. Exporta variables de entorno:

```bash
export APP_ENV="dev"
export LOCAL_TEST_MODE="true"
export REPORTS_PREFIX="reports"
export PLATFORM_URL="https://tu-plataforma-dev.com"
export EMAIL_LOGO_URL="https://i.imgur.com/15AZiBa.png"
# Opcional: incrustar el logo directamente en el correo para evitar compresión externa.
# Si la defines, esta variable reemplaza EMAIL_LOGO_URL.
# export EMAIL_LOGO_PATH="/ruta/absoluta/logo-comespro.png"
```

2. Ejecuta una invocación local con Python:

```python
from src.handler import lambda_handler

event = {
  "request_id": "a7f87c66-c7d4-4d4c-aec9-f34fc3f222f9",
  "requested_by": {"name": "Ana Pérez", "email": "ana@example.com"},
  "supplier": {
    "id_supplier": "ba8d4f2a-6f02-43db-8f70-cf05ff9e19e2",
    "business_name": "Proveedor Demo SPA",
    "rut": "76.123.456-7",
    "industry": "Educación",
    "brand_name": "Demo Learning",
    "link": "https://demo.example.com"
  },
  "criteria": [
    {
      "id_supplier_criteria": 1,
      "type": "Ambiental",
      "title": "Política de residuos",
      "compliance": "Tiene",
      "is_verified": True,
      "checker_files": [
        {
          "file_name": "politica-residuos.pdf",
          "file_url": "https://files.example.com/politica-residuos.pdf"
        }
      ]
    }
  ]
}

print(lambda_handler(event, None))
```

## Despliegue con AWS SAM

### Comandos

```bash
sam build
sam deploy --guided
```

### Parámetros recomendados por ambiente

Durante `sam deploy --guided`, define estos valores:

- **dev**:
  - `AppEnv=dev`
  - `S3BucketName=informes-comespro-dev`
  - `SesSenderEmail=dev@tudominio.com`
  - `PlatformUrl=https://tu-plataforma-dev.com`
  - `EmailLogoUrl=https://i.imgur.com/15AZiBa.png`
  - `LocalTestMode=false`

- **prod**:
  - `AppEnv=prod`
  - `S3BucketName=informes-comespro-prod`
  - `SesSenderEmail=reportes@tudominio.com`
  - `PlatformUrl=https://tu-plataforma.com`
  - `EmailLogoUrl=https://i.imgur.com/15AZiBa.png`
  - `LocalTestMode=false`

También puedes usar `samconfig.toml` para guardar estos parámetros y hacer el despliegue reproducible entre ejecuciones.

## Qué adaptar antes de producción

- Gestión de errores/reintentos (DLQ o destino de errores de Lambda asíncrona).
- Políticas de expiración de presigned URL según seguridad.
- Plantilla HTML de correo corporativa.
- Estrategia de versionado/retención de reportes en S3.
- Pruebas automatizadas unitarias e integración.

## Troubleshooting rápido

- **Mensaje "URL de plataforma no configurada" en el correo**  
  Ocurre cuando la variable `PLATFORM_URL` llega vacía en la Lambda desplegada.  
  Revisa los `Environment Variables` de la función en AWS o el parámetro `PlatformUrl` en SAM.
