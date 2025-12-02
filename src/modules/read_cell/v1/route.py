import logging
import traceback

from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from src.google_sheet import get_client, get_sheet_id, get_cell_positon, get_sheet, get_cell, get_sheets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.route("/execute", methods=["POST"])
def execute():
    """
    Executes the action to read a cell value from a specified Google Sheet.

    Expected request structure:
    - data: Contains form fields like "sheet_name" (str),
           and position info (e.g., cell reference) or direct "row" (str) and "column" (str).

    Process:
    - Determines row and column from provided data (cell reference or direct inputs).
    - If position resolution fails, uses direct row/column and returns 400 error.
    - Retrieves the cell value and logs any errors.

    Returns:
        On success (200): dict with "data": value (str),
                          "metadata": {"row": int, "column": int, "sheet": str}.
        On error (400/500): Error response with message.
    """
    print("flask_request", flask_request)
    request = Request(flask_request)

    data = request.data

    sheet_name = data["sheet_name"]
    try:
        row, column = get_cell_positon(data, get_sheet(get_client(), get_sheet_id(), sheet_name))
    except Exception as e:
        selected_row: str = data["row"]
        selected_column: str = data["column"]
        logger.error(
            f"An error while reading cell in {sheet_name} on row:{selected_row} column:{selected_column} : {e}")
        logger.error(traceback.format_exc())
        return Response.error(str(e), status_code=400)

    try:
        value: str = get_cell(get_client(), get_sheet_id(), sheet_name, row, column)
        return Response(data=value, metadata={"row": row, "column": column, "sheet": sheet_name})
    except Exception as e:
        logger.error(f"Unexpected error while reading cell in {sheet_name} on row:{row} column:{column} : {e}")
        logger.error(traceback.format_exc())
        return Response.error(str(e), status_code=500)


@router.route("/content", methods=["GET", "POST"])
def content():
    """
    Handles requests to fetch data for dynamic form fields, specifically for the "sheets" content object.
    This populates choices dropdown options based on the provided content_object_names.

    For "sheets", it retrieves a list of sheet names using the authenticated client and sheet ID.
    """
    request = Request(flask_request)

    data = request.data
    content_object_names = data.get("content_object_names", [])

    if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
        content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]

    content_objects = []  # this is the list of content objects that will be returned to the frontend

    for content_object_name in content_object_names:
        if content_object_name == "sheets":
            data = get_sheets(get_client(), get_sheet_id())
            content_objects.append({
                "content_object_name": "sheets",
                "data": data
            })

    return Response(data={"content_objects": content_objects})
