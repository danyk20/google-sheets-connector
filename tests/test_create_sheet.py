from google.oauth2.service_account import Credentials
import gspread

def test_create_sheet_success(client):
    # Payload matching expected "data": {"sheet_name": "..."}
    payload = {"data": {"sheet_name": "Test Sheet"}}

    response = client.post("/create_sheet/v1/execute", json=payload)

    # Assertions
    assert response.status_code == 200
    json_data = response.json
    assert json_data["data"] == ["Sheet creation succeeded."]  # From route logic
    assert json_data["metadata"]["error"] is None  # No error


def test_create_sheet_fail(client):
    # Wrong payload
    payload = {"data": {"sheet_name": None}}

    response = client.post("/create_sheet/v1/execute", json=payload)

    # Assertions
    assert response.status_code == 400
    json_data = response.json
    assert json_data["metadata"]["environment"] == "dev"
    assert json_data["metadata"]["original_error"] == "Sheet name must be a non-empty string up to 100 characters."