import json
import base64
from inference import predict_card

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        image_b64 = body.get('image')
        
        if not image_b64:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing image field'})
            }
        
        # Decode and predict
        image_bytes = base64.b64decode(image_b64)
        result = predict_card(image_bytes)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
