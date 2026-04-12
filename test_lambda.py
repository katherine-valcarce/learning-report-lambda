import os

from src.handler import lambda_handler

os.environ["LOCAL_TEST_MODE"] = "true"

event = {
    "request_id": "test-123",
    "requested_by": {
        "name": "Kathy",
        "email": "test@test.com",
    },
    "supplier": {
        "id_supplier": "sup-1",
        "business_name": "Empresa Test",
        "rut": "12.345.678-9",
        "industry": "Retail",
        "brand_name": "Marca Test",
        "link": "https://empresa-test.cl",
        "slug": "empresa-test",
    },
    "criteria": [
        {
            "id_supplier_criteria": 1,
            "type": "Ambiental",
            "title": "Política ambiental",
            "compliance": "Tiene",
            "is_verified": True,
            "checker_files": [
                {
                    "file_name": "politica-ambiental.pdf",
                    "file_url": "https://example.com/politica-ambiental.pdf",
                }
            ],
        },
        {
            "id_supplier_criteria": 2,
            "type": "Gobernanza",
            "title": "Código de ética",
            "compliance": "No tiene",
            "is_verified": False,
            "checker_files": [],
        },
    ],
}

response = lambda_handler(event, None)
print(response)