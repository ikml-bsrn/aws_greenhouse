### This test is to verify the connection of the Greenhouse API stream and the data format of the incoming data.
### It also checks for schema changes in the incoming data by comparing it to a predefined schema.

import requests
import json

def test_greenhouse_api_stream():
    api_url = "http://greenhouse.shef.ac.uk:7070/stream"

    try:
        response = requests.get(api_url, stream=True, timeout=10)

        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

        # Read the first line of the stream to check the data format
        for line in response.iter_lines(decode_unicode=True):
            if line:
                if line.startswith("data: "):
                    raw_json = line.replace("data: ", "")
                    assert raw_json.startswith("{") and raw_json.endswith("}"), "Data is not in JSON format"

                    data = json.loads(raw_json)

                    assert len(data) == 24, f"Change in schema length detected. Please verify new changes in the API schema."
                    
                    # Pre-defined schema keys to check for
                    required_keys = ["timestamp", "outdoor_global_radiation", "outdoor_air_temp", "outdoor_rh",
                                     "outdoor_rh", "outdoor_wind_speed", "indoor_temperature", "indoor_vpd",
                                     "energy_screen_closure", "blackout_screen_closure", "lee_vent_aperture",
                                     "wind_vent_aperture","pipe_rail_inlet_temp", "grow_pipes_inlet_temp", "lights_on",
                                     "co2_injection_status", "indoor_co2"]
                    
                    # check if all required keys are present in the incoming data
                    for key in required_keys:
                        assert key in data, f"Warning: '{key}' is missing from the data. Please verify new changes in the API schema."

                    break  # Exit after checking the first valid line

    except requests.RequestException as e:
        assert False, f"Connection error: {e}"