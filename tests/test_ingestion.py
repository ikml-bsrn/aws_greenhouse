import boto3
import os
from moto import mock_aws

@mock_aws
def test_ingest_to_firehose():
    # setup mock AWS environment
    os.environ['AWS_ACCESS_KEY_ID'] = 'test'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
    os.environ['AWS_DEFAULT_REGION'] = 'eu-north-1'

    # create a mock S3 bucket for testing
    s3 = boto3.client('s3', region_name='eu-north-1')
    bucket_name = "test-greenhouse-bucket"

    s3.create_bucket(Bucket=bucket_name)
    print(f"Mock S3 bucket '{bucket_name}' created.")

    # initialise mock Firehose client and create a delivery stream
    firehose = boto3.client('firehose', region_name='eu-north-1')
    delivery_stream_name = "test-greenhouse-stream"



