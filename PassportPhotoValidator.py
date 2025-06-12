import json
import boto3
import os
import sys
import base64

def write_to_file(filename, data):
    with open(filename, 'wb') as f:
        f.write(base64.b64decode(data))

def lambda_handler(event, context):
    # TODO implement
  
    client = boto3.client('rekognition')
    encodedImage = event['photo']
    print(encodedImage)

    write_to_file('/tmp/passport.jpg',encodedImage)
    
    
    try:    
        imgFile = open('/tmp/passport.jpg', 'rb')  
        imgBytes = imgFile.read()   
        imgFile.close()
    except :
        print('Could not return file')

    imgobj={'Bytes': imgBytes}

    response_labels =client.detect_faces(Image=imgobj)
    
    face_details = response_labels['FaceDetails']
    
    if len(face_details) == 0:
        return {
            "statusCode": 400,
            "body": "Invalid image: wrong image has been uploaded."
    }
    
    if len(face_details) != 1:
        return {
            "statusCode": 400,
            "body": "Invalid image: must contain exactly one face."
        }

    face = face_details[0]

    # Check if image is blurry
    sharpness = face['Quality']['Sharpness']
    brightness = face['Quality']['Brightness']

    result = {
        "FaceDetected": True,
        "Sharpness": sharpness,
        "Brightness": brightness,
        "IsBlurry": sharpness < 80,
        "IsTooDarkOrBright": brightness < 40 or brightness > 95
    }

    return {
        "statusCode": 200,
        "body": str(result)
    }