import boto3
import json
from moto import mock_aws

@mock_aws
def test_ingest_to_firehose():
    from src.ingest_data import ingestToFirehose

    try:
        # create a mock S3 bucket for testing
        s3 = boto3.client('s3', region_name='eu-north-1')
        bucket_name = "test-greenhouse-bucket"

        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "eu-north-1"})

        print(f"Mock S3 bucket '{bucket_name}' created.")

        # initialise mock Firehose client and create a delivery stream
        firehose = boto3.client('firehose', region_name='eu-north-1')
        delivery_stream_name = "test-greenhouse-stream"

        firehose.create_delivery_stream(
            DeliveryStreamName=delivery_stream_name,
            S3DestinationConfiguration={
                "RoleARN": "arn:aws:iam::123456789012:role/firehose_delivery_role", # mock role ARN
                "BucketARN": f"arn:aws:s3:::{bucket_name}",
                "BufferingHints": {
                    "SizeInMBs": 1,
                    "IntervalInSeconds": 300
                }
            }
        )
        print(firehose)
        print(f"Mock Firehose Stream '{delivery_stream_name}' created.")

    except Exception as e:
        assert False, f"Error setting up mock AWS environment: {e}"

    ## Test the "ingest_to_firehose" function with mock data
    try:
        test_data = json.dumps({
            "timestamp": "2026-02-17T11:04:59.520004",
            "outdoor_global_radiation": 122.0,
            "outdoor_air_temp": -2.6,
            "outdoor_rh": 80.6,
            "outdoor_wind_speed": 1.6,
            "indoor_temperature": 22.4,
            "indoor_vpd": 4.146669573,
            "pipe_rail_inlet_temp": 59.9,
            "grow_pipes_inlet_temp": 33.7,
            "lights_on": 1.0,
            "co2_injection_status": None,
            "indoor_co2": 1130.0
        })

        response = ingestToFirehose(test_data, stream_name="test-greenhouse-stream")

        print("Test data delivered. Response ID:", response)

        assert response is not None, "Warning: No response received from ingest_to_firehose."

    except Exception as e:
        assert False, f"Error testing ingest_to_firehose: {e}"