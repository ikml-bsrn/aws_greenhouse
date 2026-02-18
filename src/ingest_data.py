import requests
import boto3
from moto import mock_aws # for mocking AWS services
import logging
import time
import watchtower # For logging to CloudWatch

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Configure CloudWatch logging
try:
    logger.addHandler(watchtower.CloudWatchLogHandler(log_group_name="greenhouse_producer_log"))
    logger.info("CloudWatch logging connection established.")
except Exception as e:
    logger.error(f"Failed to connect to CloudWatch: {e}")

# ---------- Functions ----------
def connectToAPIStream(api_url="http://greenhouse.shef.ac.uk:7070/stream", max_retries=None):
    retry_count = 0

    while max_retries is None or retry_count < max_retries:
        try:
            logger.info("Connecting to greenhouse data stream...")

            with requests.get(api_url, stream=True) as response:
                
                for line in response.iter_lines(decode_unicode=True): # Decode the lines
                    # Note: Pings are ignored from the server
                    # Accept the line which starts with "data: "
                    if line and line.startswith("data: "):
                            
                            raw_json = line.replace("data: ", "") # Extract only the JSON part
                            
                            yield raw_json

        # Error handling
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error: {e}")
            retry_count += 1
            if max_retries and retry_count >= max_retries:
                raise Exception("Maximum retry attempts reached. Exiting.")
            time.sleep(5)

        except KeyboardInterrupt:
            logger.info("Session interrupted. Shutting down...")
            break

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            retry_count += 1
            if max_retries and retry_count >= max_retries:
                raise Exception("Maximum retry attempts reached. Exiting.")
            time.sleep(10)

def ingestToFirehose(data, stream_name="greenhouse_stream"):
    """
    Send data to Amazon Kinesis Data Firehose.
    Args:
        data (str): The raw JSON data to send.
    """
    try:
        # Connect to Amazon Data Firehose
        firehose = boto3.client('firehose', region_name='eu-north-1')

        # Send the data to Kinesis Data Firehose
        response = firehose.put_record(
            DeliveryStreamName=stream_name,
            Record={
                'Data': str(data) + '\n' # append newline character 
                                         # for proper record separation
            })
        
        logger.info(f"A datapoint has been sent to Firehose. Response: {response.get('RecordId')}")

        return response.get('RecordId')

    # Error handling
    except Exception as e:
        logger.error(f"Error sending data to S3: {e}")
