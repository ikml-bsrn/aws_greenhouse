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
    logger.addHandler(watchtower.CloudWatchLogHandler(log_group="greenhouse_producer_log"))
    logger.info("CloudWatch logging connection established")
except Exception as e:
    logger.error(f"Failed to connect to CloudWatch: {e}")

# ---------- Functions ----------
def ingest_to_firehose(data):
    """
    Send data to Amazon Kinesis Data Firehose.
    Args:
        data (str): The raw JSON data to send.
    """
    try:
        # Connect to Amazon Data Firehose
        firehose = boto3.client('firehose', region_name='eu-north-1')

        # Send the data to Kinesis Data Firehose
        firehose.put_record(
            DeliveryStreamName="greenhouse_stream",
            Record={
                'Data': str(data) + '\n' # append newline character 
                                         # for proper record separation
            })
        
        logger.info(f"A datapoint has been sent to Firehose.")

    # Error handling
    except Exception as e:
        logger.error(f"Error sending data to S3: {e}")

def connect_to_api_stream(api_url="http://greenhouse.shef.ac.uk:7070/stream"):
    while True:
        try:
            logger.info("Connecting to greenhouse data stream...")

            with requests.get(api_url, stream=True) as response:
                for line in response.iter_lines(decode_unicode=True): # Decode the lines
                    if line:
                        # Note: Pings are ignored from the server
                        # Accept the line which starts with "data: "
                        if line.startswith("data: "):

                            raw_json = line.replace("data: ", "") # Extract only the JSON part

                            ingest_to_firehose(raw_json)

        # Error handling
        except requests.RequestException as e:
            logger.error(f"Connection error: {e}")
            logger.info("Reconnecting in 10 seconds...")
            time.sleep(10)

        except KeyboardInterrupt:
            logger.info("Session interrupted. Shutting down...")
            break

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    connect_to_api_stream(api_url="http://greenhouse.shef.ac.uk:7070/stream")