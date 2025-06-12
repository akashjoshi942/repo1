import json
import boto3

s3_client = boto3.client('s3')
textract_client = boto3.client('textract', region_name='us-west-2')

def lambda_handler(event, context):
    try:
        # Extract bucket name and object key from the S3 event
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        file_key = event['Records'][0]['s3']['object']['key']
        # Extract processing method from event payload (default to DetectDocumentText)
        processing_method = event.get("processing_method", "DetectDocumentText")

        # Ensure the S3 object is accessible before calling Textract
        try:
            s3_client.head_object(Bucket=bucket_name, Key=file_key)
        except Exception as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Error accessing S3 object: {str(e)}"})
            }

        # Choose processing method: DetectDocumentText (raw text) or AnalyzeDocument (forms/tables)
        #processing_method = "DetectDocumentText"  # Change to "AnalyzeDocument" for structured analysis

        extracted_data = {}

        if processing_method == "DetectDocumentText":
            response = textract_client.detect_document_text(
                Document={'S3Object': {'Bucket': bucket_name, 'Name': file_key}}
            )

            # Extract text from Textract response
            for item in response['Blocks']:
                if item['BlockType'] == 'LINE':
                    extracted_data[item['Id']] = item['Text']

        

        elif processing_method == "AnalyzeDocument":
            response = textract_client.analyze_document(
                Document={'S3Object': {'Bucket': bucket_name, 'Name': file_key}},
                FeatureTypes=['FORMS']
            )

            # Extract form data from Textract response
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    if 'Text' in block:
                        extracted_data[block['Id']] = block['Text']
                    elif 'SelectionStatus' in block:
                        extracted_data[block['Id']] = block['SelectionStatus']
        

        elif processing_method == "AnalyzeId":
            response = textract_client.analyze_id(
                DocumentPages=[
                    {'S3Object': {'Bucket': bucket_name, 'Name': file_key}}
                ]
            )

            # Extract detected ID fields
            for document in response['IdentityDocuments']:
                for field in document['IdentityDocumentFields']:
                    field_type = field['Type']['Text']
                    field_value = field['ValueDetection']['Text']
                    extracted_data[field_type] = field_value


        return {
            'statusCode': 200,
            'body': json.dumps(extracted_data)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Unexpected error: {str(e)}"})
        }
