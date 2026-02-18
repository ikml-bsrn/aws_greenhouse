import logging
from src.ingest_data import connectToAPIStream, ingestToFirehose

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def main():
    
    try:
        json_data = connectToAPIStream(api_url="http://greenhouse.shef.ac.uk:7070/stream", max_retries=3)

        ingestToFirehose(data=json_data, stream_name="greenhouse_stream")
    except KeyboardInterrupt:
        logging.info("Session interrupted. Shutting down...")
    except Exception as e:
        logging.error(f"Application failed: {e}")

if __name__ == "__main__":
    main()