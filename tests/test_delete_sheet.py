def test_delete_sheet_success(client):
    # Payload matching expected "data": {"sheet_name": "..."}
    payload = {"data": {"sheet_name": "Test Sheet"}}

    response = client.post("/delete_sheet/v1/execute", json=payload)

    # Assertions
    assert response.status_code == 200
    json_data = response.json
    assert json_data["data"] == ["Sheet `Test Sheet` was successfully deleted!"]  # From route logic
    assert json_data["metadata"]["error"] is None  # No error


def test_delete_sheet_fail(client):
    # Wrong payload
    payload = {"data": {"wrong_key": "My_Sheet"}}

    response = client.post("/delete_sheet/v1/execute", json=payload)

    # Assertions
    assert response.status_code == 400
    json_data = response.json
    assert json_data["metadata"]["error"] == "missing required key `sheet_name`"