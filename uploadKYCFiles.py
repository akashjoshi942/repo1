import boto3
import base64
import os
import re
from botocore.vendored import requests

s3 = boto3.client('s3')
BUCKET_NAME = 'dbdtcckyctextract'

def lambda_handler(event, context):
    try:
        # Get and decode the base64-encoded body
        body = base64.b64decode(event['body'])
        headers = event['headers']
        content_type = headers.get('content-type') or headers.get('Content-Type')

        # Extract boundary from Content-Type
        match = re.search(r'boundary=(.*)', content_type)
        if not match:
            return {"statusCode": 400, "body": "Missing boundary in content-type"}
        
        boundary = match.group(1)
        boundary_bytes = ('--' + boundary).encode()

        # Split by boundary
        parts = body.split(boundary_bytes)

        for part in parts:
            # Look for Content-Disposition with filename
            if b'Content-Disposition' in part and b'filename=' in part:
                header_end = part.find(b'\r\n\r\n')
                headers = part[:header_end].decode()
                content = part[header_end + 4:].rstrip(b'\r\n--')

                # Extract filename
                filename_match = re.search(r'filename="([^"]+)"', headers)
                if not filename_match:
                    continue

                filename = filename_match.group(1)

                # Upload to S3
                s3.put_object(Bucket=BUCKET_NAME, Key=filename, Body=content)

                return {
                    "statusCode": 200,
                    "body": f"File '{filename}' uploaded successfully."
                }

        return {"statusCode": 400, "body": "No valid file found in request"}

    except Exception as e:
        return {"statusCode": 500, "body": f"Error: {str(e)}"}
