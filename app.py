import json
import random
import string
import boto3
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from botocore.exceptions import ClientError

app = Flask(__name__)
CORS(app)

AWS_ACCESS_KEY_ID     = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_REGION            = os.environ.get('AWS_REGION', 'us-east-1')

@app.route('/api/create-bucket', methods=['POST'])
def create_bucket():
    body = request.get_json(silent=True) or {}

    rand_id     = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    bucket_name = f"lb-{rand_id}"

    try:
        s3 = boto3.client(
            's3',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        if AWS_REGION == 'us-east-1':
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
            )

        s3.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'error.html'}
            }
        )

        s3.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Sid": "PublicRead",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }]
            })
        )

        url = f"http://{bucket_name}.s3-website-{AWS_REGION}.amazonaws.com"
        return jsonify({ 'ok': True, 'url': url, 'bucket': bucket_name })

    except ClientError as e:
        return jsonify({ 'ok': False, 'error': str(e) }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
