def test_update_cell_success(client):
    # Payload matching expected "data": {"sheet_name": "..."}
    payload = {"data": {"sheet_name": "Test Sheet", "row": "1", "column": "1", "value" : "test"}}

    response = client.post("/update_cell/v1/execute", json=payload)

    # Assertions
    assert response.status_code == 200
    json_data = response.json
    assert json_data["data"] == "test"  # From route logic
    assert json_data["metadata"]["row"] == 1
    assert json_data["metadata"]["column"] == 1
    assert json_data["metadata"]["sheet"] == "Test Sheet"
    assert json_data["metadata"]["old_value"] == "previous value"


def test_update_cell_fail_row(client):
    # Wrong payload
    payload = {"data": {"sheet_name": "Test Sheet", "row": "0", "column": "1", "value": "test"}}

    response = client.post("/update_cell/v1/execute", json=payload)

    # Assertions
    assert response.status_code == 400
    json_data = response.json
    assert json_data["error"] == "Invalid row number!"

def test_update_cell_fail_column(client):
    # Wrong payload
    payload = {"data": {"sheet_name": "Test Sheet", "row": "1", "column": "0", "value": "test"}}

    response = client.post("/update_cell/v1/execute", json=payload)

    # Assertions
    assert response.status_code == 400
    json_data = response.json
    assert json_data["error"] == "Invalid column number!"