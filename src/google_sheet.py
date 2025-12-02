import os
from typing import Optional
import logging
import traceback

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from gspread import Spreadsheet, Worksheet, WorksheetNotFound, Client
import gspread
from gspread.exceptions import APIError
from workflows_cdk import ManagedError

_client = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOOGLE_CREDENTIALS_PATH = "GOOGLE_APPLICATION_CREDENTIALS"
SHEET_ID = "SHEET_ID"
SHEETS_SCOPE = "SCOPE"


def create_sheet(sheet_name: str, spreadsheet_id: Optional[str] = None) -> Optional[tuple[str, int]]:
    """
    Create a new sheet in the specified Google Spreadsheet.

    Args:
        sheet_name (str): The title of the new sheet.
        spreadsheet_id (Optional[str]): The ID of the spreadsheet. Defaults to env var SHEET_ID.

    Returns:
        str: Error message if error occurred, None otherwise.

    Raises:
        ValueError: If sheet_name is empty or invalid.
        HttpError: If the API request fails.
    """

    if not sheet_name or not isinstance(sheet_name, str) or len(sheet_name) > 100:
        raise ValueError("Sheet name must be a non-empty string up to 100 characters.")

    try:
        client = get_client()
        spreadsheet_id = spreadsheet_id or get_sheet_id()
        if not spreadsheet_id:
            logger.error("Spreadsheet ID is required (via env var or parameter).")
            return "Spreadsheet ID is required (via env var or parameter).", 500
        existing_sheet = client.open_by_key(spreadsheet_id)
        existing_sheet.add_worksheet(
            title=sheet_name,
            rows=1000,  # Default row count
            cols=26  # Default column count (A-Z)
        )
    except APIError as e:
        logger.error(f"An error occurred when creating sheet: {e}")
        return e.error["message"], e.code
    except Exception as e:
        logger.error(f"Unexpected error creating sheet: {e}")
        logger.error(traceback.format_exc())
        return str(e), 500


def delete_sheet(client, spreadsheet_key: str, sheet_title: str) -> Optional[tuple[Exception, int]]:
    """
    Deletes a specific worksheet from a Google Sheets document.

    This function uses a pre-authenticated gspread client to open the spreadsheet
    by its key (ID), locate the worksheet by its title, and delete it. The deletion
    is permanent and cannot be undone via the API (though Google Sheets may offer
    undo in the UI if performed manually).

    Args:
        client: A pre-authenticated gspread client instance (e.g., from gspread.service_account()).
        spreadsheet_key (str): The unique key (ID) of the Google Sheets document, typically
            extracted from the document's URL.
        sheet_title (str): The exact title (name) of the worksheet to delete.

    Returns:
        bool: True if the worksheet was successfully deleted, False if the worksheet was not found.

    Raises:
        gspread.SpreadsheetNotFound: If the `spreadsheet_key` is invalid or the spreadsheet does not exist.
        gspread.AuthenticationError: If the client authentication fails or lacks permission to access or modify the spreadsheet.
        gspread.APIError: For other Google Sheets API-related errors, such as rate limits, permission issues, or if the worksheet cannot be deleted (e.g., it's the last sheet in the spreadsheet, which is not allowed).
    """
    try:
        existing_sheet: Spreadsheet = client.open_by_key(spreadsheet_key)
        worksheet: Worksheet = existing_sheet.worksheet(sheet_title)
        existing_sheet.del_worksheet(worksheet)
    except WorksheetNotFound:
        description: str = f"Google sheet '{sheet_title}' can not be found in worksheet '{spreadsheet_key}'.!"
        logger.error(description)
        logger.error(traceback.format_exc())
        return Exception(description), 400
    except Exception as e:
        logger.error(f"Unexpected error deleting sheet: {e}")
        logger.error(traceback.format_exc())
        return e, 500


def get_cell_positon(data: dict, worksheet: Worksheet):
    """
        Validates and retrieves the row and column indices from input data against a Google Sheet worksheet.

        This function extracts row and column numbers from a dictionary, converts them to integers,
        and validates that they fall within the bounds of the specified worksheet. It raises a custom
        ManagedError if the indices are invalid, ensuring safe access to cell positions.

        Args:
            data (dict): A dictionary containing 'row' and 'column' keys with string or integer values
                representing the 1-indexed positions.
            worksheet (gspread.Worksheet): The target worksheet object from gspread.

        Returns:
            tuple[int, int]: A tuple of validated (row, column) integers.

        Raises:
            ValueError: If the 'row' or 'column' keys are missing from data or cannot be converted to integers.
            ManagedError: If the row or column indices are out of bounds (less than 1 or exceeding the worksheet's row_count or column_count).
        """
    if "row" not in data or "column" not in data:
        raise ManagedError("Missing required 'row' or 'column' fields!")
    if not data["row"].isdigit() or not data["column"].isdigit():
        raise ManagedError("Invalid 'row' or 'column' fields - only positive integer values allowed!")
    row = int(data["row"])
    column = int(data["column"])
    if row < 1 or row > worksheet.row_count:
        raise ManagedError("Invalid row number!")
    if column < 1 or column > worksheet.column_count:
        raise ManagedError("Invalid column number!")
    return row, column


def get_sheet(client, spreadsheet_key: str, sheet_title: str) -> Worksheet:
    """
        Retrieves a specific worksheet from a Google Sheets document using its key and title.

        This function uses a pre-authenticated gspread client to open the spreadsheet by its unique key (ID),
        locate the worksheet by its exact title, and return the worksheet object for further operations.
        The spreadsheet key is typically extracted from the document's URL.

        Args:
            client: A pre-authenticated gspread client instance (e.g., from gspread.authorize(credentials)).
            spreadsheet_key (str): The unique key (ID) of the Google Sheets document, typically
                extracted from the document's URL.
            sheet_title (str): The exact title (name) of the worksheet to retrieve.

        Returns:
            gspread.Worksheet: The requested worksheet object.

        Raises:
            gspread.SpreadsheetNotFound: If the `spreadsheet_key` is invalid or the spreadsheet does not exist.
            gspread.WorksheetNotFound: If the `sheet_title` does not match any worksheet in the spreadsheet.
            gspread.AuthenticationError: If the client authentication fails or lacks permission to access the spreadsheet.
            gspread.APIError: For other Google Sheets API-related errors, such as rate limits or permission issues.
        """
    existing_sheet: Spreadsheet = client.open_by_key(spreadsheet_key)
    return existing_sheet.worksheet(sheet_title)


def get_sheets(client, spreadsheet_key: str) -> list[str]:
    """
    Retrieves the names of all worksheets in a Google Sheets document.

    This function uses a pre-authenticated gspread client to open the spreadsheet
    by its key (ID) and extract the titles of all worksheets.

    Args:
        client: A pre-authenticated gspread client instance (e.g., from gspread.service_account()).
        spreadsheet_key (str): The unique key (ID) of the Google Sheets document, typically
            extracted from the document's URL.

    Returns:
        List[str]: A list of strings, where each string is the title (name) of a worksheet in the spreadsheet.

    Raises:
        gspread.SpreadsheetNotFound: If the `spreadsheet_key` is invalid or the spreadsheet does not exist.
        gspread.WorksheetNotFound: If no worksheets are found (unlikely, but possible).
        gspread.AuthenticationError: If the client authentication fails or lacks permission to access the spreadsheet.
        gspread.APIError: For other Google Sheets API-related errors, such as rate limits or permission issues.
    """
    existing_sheet: Spreadsheet = client.open_by_key(spreadsheet_key)
    worksheets: list[Worksheet] = existing_sheet.worksheets()
    sheet_names: list[str] = [worksheet.title for worksheet in worksheets]
    return sheet_names


def get_cell(client, spreadsheet_key: str, sheet_title: str, row: int, column: int) -> str:
    """
    Retrieves the value from a specific cell in a Google Sheet.

    This function uses a pre-authenticated gspread client to open the spreadsheet
    by its name, access the specified worksheet, and fetch the value at the given
    row and column position. Row and column indices are 1-indexed, matching Google
    Sheets' conventions.

    Args:
        client: A pre-authenticated gspread client instance (e.g., from gspread.authorize(credentials)).
        spreadsheet_key (str): The name of the Google Spreadsheet (must match exactly; alternatively, use the spreadsheet key/ID for uniqueness).
        sheet_title (str): The exact title (name) of the worksheet within the spreadsheet.
        row (int): The row number (1-indexed) of the cell to retrieve.
        column (int): The column number (1-indexed) of the cell to retrieve.

    Returns:
        str or None: The value in the specified cell as a string, or None if the cell is empty or an error occurs during retrieval.

    Raises:
        gspread.SpreadsheetNotFound: If the `spreadsheet_name` does not exist or is inaccessible.
        gspread.WorksheetNotFound: If the `sheet_name` does not exist within the spreadsheet.
        gspread.AuthenticationError: If the client authentication fails or lacks permission to access the spreadsheet.
        gspread.APIError: For other Google Sheets API-related errors, such as rate limits or invalid row/column indices.
    """
    worksheet: Worksheet = get_sheet(client, spreadsheet_key, sheet_title)
    return worksheet.cell(row, column).value


def set_cell(client, spreadsheet_key: str, sheet_title: str, row: int, column: int, value: str) -> None:
    """
    Sets the value in a specific cell in a Google Sheet.

        This function uses a pre-authenticated gspread client to open the spreadsheet
        by its unique key (ID), retrieve the specified worksheet, and update the value
        at the given row and column position. Row and column indices are 1-indexed,
        matching Google Sheets' conventions. The update is performed via the API and
        takes effect immediately. No validation is performed on row/column bounds,
        so invalid positions may raise API errors.

        Args:
            client: A pre-authenticated gspread client instance (e.g., from gspread.authorize(credentials)).
            spreadsheet_key (str): The unique key (ID) of the Google Sheets document, typically
                extracted from the document's URL (e.g., '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms').
            sheet_title (str): The exact title (name) of the worksheet within the spreadsheet.
            row (int): The row number (1-indexed) of the cell to update.
            column (int): The column number (1-indexed) of the cell to update.
            value (str): The value to set in the cell.

        Returns:
            None: This function does not return a value; it modifies the sheet in place.

        Raises:
            gspread.SpreadsheetNotFound: If the `spreadsheet_key` is invalid or the spreadsheet does not exist.
            gspread.WorksheetNotFound: If the `sheet_title` does not match any worksheet in the spreadsheet.
            gspread.AuthenticationError: If the client authentication fails or lacks permission to access or modify the spreadsheet.
            gspread.APIError: For other Google Sheets API-related errors, such as rate limits, permission issues, or invalid row/column indices.
        """
    worksheet: Worksheet = get_sheet(client, spreadsheet_key, sheet_title)
    worksheet.update_cell(row, column, value)


def get_sheet_id() -> str:
    """
    Loads sheet id from environment variables.

    Returns:
        str: sheet id from environment variables.
    """
    return os.getenv(SHEET_ID)


def load_environment() -> bool:
    """
    Load environment variables from .env file.

    Returns:
        bool: True if all required variables are loaded successfully, False otherwise.
    """
    load_dotenv()
    required_vars = [GOOGLE_CREDENTIALS_PATH, SHEET_ID, SHEETS_SCOPE]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    logger.info("Environment variables loaded successfully.")
    return True


def get_client() -> Optional[Client]:
    """
    Lazily initialize and return the gspread client to avoid repeated credential loading
    and PyO3 initialization issues.

    Returns:
        gspread.Client: The authorized client, or None if initialization fails.
    """
    global _client
    if _client is None:
        if not load_environment():
            return None

        credentials_path = os.getenv(GOOGLE_CREDENTIALS_PATH)
        if not credentials_path or not os.path.exists(credentials_path):
            logger.error(f"Google credentials file not found at: {credentials_path}")
            return None

        scope = os.getenv(SHEETS_SCOPE)
        if not scope:
            logger.error("Google Sheets scope not found in environment.")
            return None

        try:
            creds = Credentials.from_service_account_file(
                credentials_path,
                scopes=[scope]
            )
            if creds.expired and creds.refresh_token:
                creds.refresh(GoogleRequest())

            _client = gspread.authorize(creds)
            logger.info("gspread client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize gspread client: {e}")
            logger.error(traceback.format_exc())
            return None

    return _client
