def lambda_handler(event, context):
    print("Event recibido:", event)

    return {
        "statusCode": 200,
        "body": "Lambda funcionando"
    }