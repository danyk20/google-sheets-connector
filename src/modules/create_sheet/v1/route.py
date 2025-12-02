import logging

from main import router
from workflows_cdk import Response, Request
from flask import request as flask_request

from src.google_sheet import create_sheet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.route("/execute", methods=["POST"])
def execute():
    """
        Executes the action to create a new Google Sheet with the specified name.

        Expected request structure:
        - data: Contains "sheet_name" (str, the name of the sheet to create).

        Process:
        - Calls the create_sheet function with the provided sheet name.
        - Constructs a success or failure message based on the result.

        Returns:
            On success (200): dict with "data": list[str] (confirmation message),
                              "metadata": {"error": None}.
            On error: dict with error message in "data",
                      "metadata": {"error": str}, and appropriate status_code.
        """
    data = Request(flask_request).data
    error_message, error_code = create_sheet(data["sheet_name"]) or (None, None)
    output = [f"Sheet creation {'failed' if error_message else 'succeeded'}."]

    return Response(data=output, metadata={"error": error_message}, status_code=error_code if error_code else 200)
