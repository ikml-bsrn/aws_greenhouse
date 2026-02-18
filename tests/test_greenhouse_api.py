### This test is to verify the connection of the Greenhouse API stream and the data format of the incoming data.
### It also checks for schema changes in the incoming data by comparing it to a predefined schema.

import requests
import json
from src.ingest_data import connectToAPIStream, ingestToFirehose

def test_greenhouse_api_stream():

    api_url = "http://greenhouse.shef.ac.uk:7070/stream"

    try:
        data_stream = connectToAPIStream(api_url=api_url, max_retries=1)

        raw_json = next(data_stream) # Get the first data point from the stream

        # check if data is received from the API stream
        assert raw_json is not None, "No data received from the API stream."

        # check if the data is in JSON format
        assert raw_json.startswith("{") and data_stream.endswith("}"), "Data is not in JSON format"

        data = json.loads(raw_json)

        # check for schema changes
        assert len(data) == 24, f"Change in schema length detected. Please verify new changes in the API schema."
                    
        # pre-defined schema keys to check for
        required_keys = ["timestamp", "outdoor_global_radiation", "outdoor_air_temp", "outdoor_rh",
                            "outdoor_rh", "outdoor_wind_speed", "indoor_temperature", "indoor_vpd",
                            "energy_screen_closure", "blackout_screen_closure", "lee_vent_aperture",
                            "wind_vent_aperture","pipe_rail_inlet_temp", "grow_pipes_inlet_temp", "lights_on",
                            "co2_injection_status", "indoor_co2"]
        
        # check if all required keys are present in the incoming data
        for key in required_keys:
            assert key in data, f"Warning: '{key}' is missing from the data. Please verify new changes in the API schema."


    except Exception as e:
        assert False, f"Connection error: {e}"