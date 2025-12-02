import logging

from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from src.google_sheet import get_sheet_id, get_client, get_sheets, delete_sheet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.route("/execute", methods=["POST"])
def execute():
    """
    Executes the action to delete a specified Google Sheet.

    Expected request structure:
    - data: Contains "sheet_name" (str, the sheet to delete).

    Process:
    - Calls the delete_sheet API with authenticated client and sheet ID.
    - Constructs a success or failure message based on the result.

    Returns:
        On success (200): dict with "data": list[str] (confirmation message),
                          "metadata": {"error": None}.
        On error: dict with error message in "data",
    """
    request = Request(flask_request)

    data = request.data
    if "sheet_name" not in data:
        return Response(data="Error - bad request", metadata={"error": "missing required key `sheet_name`"},
                        status_code=400)

    error, response_code = delete_sheet(get_client(), get_sheet_id(), data["sheet_name"]) or (None, None)

    output = ["Sheet `" + str(data["sheet_name"]) + ("` failed to be" if error else "` was successfully") + " deleted!"]

    return Response(data=output, metadata={"error": str(error) if error else None},
                    status_code=response_code if response_code else 200)


@router.route("/content", methods=["GET", "POST"])
def content():
    """
    Handles requests to fetch data for dynamic form fields, specifically for the "sheets" content object.
    This populates choices (e.g., dropdown options) based on the provided content_object_names.

    Expected request structure:
    - data: Contains "content_object_names" (list of strings or dicts with "id" keys).
    - credentials: Contains "connection_data" for authentication (used to get client and sheet ID).

    For "sheets", it retrieves a list of sheet names using the authenticated client and sheet ID.

    Returns:
        dict: {
            "content_objects": [
                {
                    "content_object_name": str,  # e.g., "sheets"
                    "data": list[dict]  # Each item: {"value": str, "label": str}
                }
            ]
        }
        Empty list if no matching content_object_names.
    """
    request = Request(flask_request)

    data = request.data
    content_object_names = data.get("content_object_names", [])

    # Extract content object names from objects if needed
    if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
        content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]

    content_objects = []  # this is the list of content objects that will be returned to the frontend

    for content_object_name in content_object_names:
        if content_object_name == "sheets":
            # logic here
            data = get_sheets(get_client(), get_sheet_id())
            content_objects.append({
                "content_object_name": "sheets",
                "data": data
            })

    return Response(data={"content_objects": content_objects})
