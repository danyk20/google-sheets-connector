import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import Mock, patch

import src.google_sheet
from src.google_sheet import (
    create_sheet,
    delete_sheet,
    get_cell_positon,
    get_sheet,
    get_sheets,
    get_cell,
    set_cell,
    get_sheet_id,
    load_environment,
    get_client,
    ManagedError,
)
from gspread import Client, Spreadsheet, Worksheet
from gspread.exceptions import WorksheetNotFound, APIError
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
import requests

SHEET_ID = "SHEET_ID"
GOOGLE_CREDENTIALS_PATH = "GOOGLE_APPLICATION_CREDENTIALS"
SHEETS_SCOPE = "SCOPE"
MOCK_SPREADSHEET_ID = "1BxiMVs0XRBfZEGJ8MmBBZjgmUUqptlbs74OgvE2upms"
MOCK_SHEET_TITLE = "TestSheet"
MOCK_ROW = 1
MOCK_COL = 1
MOCK_VALUE = "TestValue"


@pytest.fixture(autouse=True)
def reset_client():
    """Fixture to reset global _client before each test for isolation."""
    src.google_sheet._client = None


class TestGetSheetId:
    """Unit tests for get_sheet_id function."""

    @patch.dict(os.environ, {SHEET_ID: MOCK_SPREADSHEET_ID})
    def test_get_sheet_id_with_env_var(self):
        """Test retrieval when environment variable is set."""
        assert get_sheet_id() == MOCK_SPREADSHEET_ID

    @patch.dict(os.environ, clear=True)
    def test_get_sheet_id_without_env_var(self):
        """Test returns None when environment variable is not set."""
        assert get_sheet_id() is None


class TestLoadEnvironment:
    """Unit tests for load_environment function."""

    @patch("dotenv.load_dotenv")
    def test_load_environment_success(self, mock_load_dotenv, monkeypatch):
        """Test successful load when all required variables are present."""
        mock_load_dotenv.return_value = None
        monkeypatch.setenv(GOOGLE_CREDENTIALS_PATH, "/path/to/creds.json")
        monkeypatch.setenv(SHEET_ID, MOCK_SPREADSHEET_ID)
        monkeypatch.setenv(SHEETS_SCOPE, "https://www.googleapis.com/auth/spreadsheets")
        assert load_environment() is True

    @patch("dotenv.load_dotenv")
    def test_load_environment_missing_vars(self, mock_load_dotenv, monkeypatch):
        """Test failure when required environment variables are missing."""
        mock_load_dotenv.return_value = None
        monkeypatch.setenv(GOOGLE_CREDENTIALS_PATH, "/path/to/creds.json")
        monkeypatch.setenv(SHEET_ID, MOCK_SPREADSHEET_ID)
        monkeypatch.setenv(SHEETS_SCOPE, "")
        assert load_environment() is False

    @patch("dotenv.load_dotenv")
    def test_load_environment_all_missing(self, mock_load_dotenv, monkeypatch):
        """Test failure when all required environment variables are missing."""
        mock_load_dotenv.return_value = None
        monkeypatch.setenv(GOOGLE_CREDENTIALS_PATH, "")
        monkeypatch.setenv(SHEET_ID, "")
        monkeypatch.setenv(SHEETS_SCOPE, "")
        assert load_environment() is False


class TestGetClient:
    """Unit tests for get_client function."""

    @patch("src.google_sheet.load_environment")
    @patch("src.google_sheet.os.path.exists")
    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("gspread.authorize")
    def test_get_client_success_first_call(
            self, mock_authorize, mock_from_service_account, mock_path_exists, mock_load_env, monkeypatch
    ):
        """Test successful client initialization on first call."""
        mock_load_env.return_value = True
        mock_path_exists.return_value = True
        monkeypatch.setenv(GOOGLE_CREDENTIALS_PATH, "/path/to/creds.json")
        monkeypatch.setenv(SHEET_ID, MOCK_SPREADSHEET_ID)
        monkeypatch.setenv(SHEETS_SCOPE, "https://www.googleapis.com/auth/spreadsheets")
        mock_creds = Mock(spec=Credentials)
        mock_creds.expired = False
        mock_from_service_account.return_value = mock_creds
        mock_authorize.return_value = Mock(spec=Client)

        client = get_client()
        assert client is not None
        mock_from_service_account.assert_called_once()
        mock_authorize.assert_called_once_with(mock_creds)

    @patch("src.google_sheet.load_environment")
    @patch("src.google_sheet.os.path.exists")
    def test_get_client_creds_file_missing(self, mock_path_exists, mock_load_env, monkeypatch):
        """Test failure when credentials file does not exist."""
        mock_load_env.return_value = True
        mock_path_exists.return_value = False
        monkeypatch.setenv(GOOGLE_CREDENTIALS_PATH, "/path/to/creds.json")
        monkeypatch.setenv(SHEET_ID, MOCK_SPREADSHEET_ID)
        monkeypatch.setenv(SHEETS_SCOPE, "https://www.googleapis.com/auth/spreadsheets")

        client = get_client()
        assert client is None

    @patch("src.google_sheet.load_environment")
    def test_get_client_load_env_failure(self, mock_load_env):
        """Test failure when load_environment returns False."""
        mock_load_env.return_value = False

        client = get_client()
        assert client is None

    @patch("src.google_sheet.load_environment")
    @patch("src.google_sheet.os.path.exists")
    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("gspread.authorize")
    def test_get_client_cached(self, mock_authorize, mock_from_service_account, mock_path_exists, mock_load_env,
                               monkeypatch):
        """Test client is cached after first successful initialization."""
        mock_load_env.return_value = True
        mock_path_exists.return_value = True
        monkeypatch.setenv(GOOGLE_CREDENTIALS_PATH, "/path/to/creds.json")
        monkeypatch.setenv(SHEET_ID, MOCK_SPREADSHEET_ID)
        monkeypatch.setenv(SHEETS_SCOPE, "https://www.googleapis.com/auth/spreadsheets")
        mock_creds = Mock(spec=Credentials)
        mock_creds.expired = False
        mock_from_service_account.return_value = mock_creds
        mock_client = Mock(spec=Client)
        mock_authorize.return_value = mock_client

        client1 = get_client()
        assert client1 == mock_client

        client2 = get_client()
        assert client2 == mock_client
        mock_from_service_account.assert_called_once()

    @patch("src.google_sheet.load_environment")
    @patch("src.google_sheet.os.path.exists")
    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("src.google_sheet.GoogleRequest")
    def test_get_client_creds_refresh(self, mock_google_request, mock_from_service_account, mock_path_exists,
                                      mock_load_env, monkeypatch):
        """Test credential refresh when expired."""
        mock_load_env.return_value = True
        mock_path_exists.return_value = True
        monkeypatch.setenv(GOOGLE_CREDENTIALS_PATH, "/path/to/creds.json")
        monkeypatch.setenv(SHEET_ID, MOCK_SPREADSHEET_ID)
        monkeypatch.setenv(SHEETS_SCOPE, "https://www.googleapis.com/auth/spreadsheets")
        mock_request = Mock(spec=Request)
        mock_google_request.return_value = mock_request
        mock_creds = Mock(spec=Credentials)
        mock_creds.expired = True
        mock_creds.refresh_token = "token"
        mock_from_service_account.return_value = mock_creds

        with patch.object(mock_creds, "refresh") as mock_refresh:
            get_client()
            mock_refresh.assert_called_once_with(mock_request)


class TestGetCellPositon:
    """Unit tests for get_cell_positon function."""

    @pytest.fixture
    def mock_worksheet(self):
        mock_ws = Mock(spec=Worksheet)
        mock_ws.row_count = 1000
        mock_ws.column_count = 26
        return mock_ws

    def test_valid_position(self, mock_worksheet):
        """Test valid row and column within bounds."""
        data = {"row": "1", "column": "1"}
        row, col = get_cell_positon(data, mock_worksheet)
        assert row == 1 and col == 1, "Should return (1, 1) for valid input"

    def test_missing_keys(self, mock_worksheet):
        """Test raises ManagedError for missing keys."""
        data = {"row": "1"}  # Missing column
        with pytest.raises(ManagedError, match="Missing required 'row' or 'column' fields!"):
            get_cell_positon(data, mock_worksheet)

    def test_non_digit_values(self, mock_worksheet):
        """Test raises ManagedError for non-digit values."""
        data = {"row": "abc", "column": "1"}
        with pytest.raises(ManagedError, match="Invalid 'row' or 'column' fields"):
            get_cell_positon(data, mock_worksheet)

    def test_out_of_bounds_row(self, mock_worksheet):
        """Test raises ManagedError for row out of bounds."""
        data = {"row": "1001", "column": "1"}  # Exceeds row_count
        with pytest.raises(ManagedError, match="Invalid row number!"):
            get_cell_positon(data, mock_worksheet)

    def test_out_of_bounds_column(self, mock_worksheet):
        """Test raises ManagedError for column out of bounds."""
        data = {"row": "1", "column": "27"}  # Exceeds column_count
        with pytest.raises(ManagedError, match="Invalid column number!"):
            get_cell_positon(data, mock_worksheet)

    def test_zero_or_negative(self, mock_worksheet):
        """Test raises ManagedError for zero or negative values."""
        data = {"row": "0", "column": "1"}
        with pytest.raises(ManagedError, match="Invalid row number!"):
            get_cell_positon(data, mock_worksheet)


class TestGetSheet:
    """Unit tests for get_sheet function."""

    def test_get_sheet_success(self):
        """Test successful retrieval of worksheet."""
        mock_client = Mock(spec=Client)
        mock_spreadsheet = Mock(spec=Spreadsheet)
        mock_worksheet = Mock(spec=Worksheet)
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        with patch("src.google_sheet.get_client", return_value=mock_client):
            result = get_sheet(mock_client, MOCK_SPREADSHEET_ID, MOCK_SHEET_TITLE)
            assert result == mock_worksheet
            mock_client.open_by_key.assert_called_once_with(MOCK_SPREADSHEET_ID)
            mock_spreadsheet.worksheet.assert_called_once_with(MOCK_SHEET_TITLE)


class TestGetSheets:
    """Unit tests for get_sheets function."""

    def test_get_sheets_success(self):
        """Test successful retrieval of sheet names."""
        mock_client = Mock(spec=Client)
        mock_spreadsheet = Mock(spec=Spreadsheet)
        mock_worksheets = [Mock(spec=Worksheet, title="Sheet1"), Mock(spec=Worksheet, title="Sheet2")]
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheets.return_value = mock_worksheets

        with patch("src.google_sheet.get_client", return_value=mock_client):
            result = get_sheets(mock_client, MOCK_SPREADSHEET_ID)
            assert result == ["Sheet1", "Sheet2"]
            mock_client.open_by_key.assert_called_once_with(MOCK_SPREADSHEET_ID)
            mock_spreadsheet.worksheets.assert_called_once()


class TestGetCell:
    """Unit tests for get_cell function."""

    def test_get_cell_success(self):
        """Test successful cell value retrieval."""
        mock_worksheet = Mock(spec=Worksheet)
        mock_cell = Mock()
        mock_cell.value = MOCK_VALUE
        mock_worksheet.cell.return_value = mock_cell

        with patch("src.google_sheet.get_sheet", return_value=mock_worksheet):
            result = get_cell(None, MOCK_SPREADSHEET_ID, MOCK_SHEET_TITLE, MOCK_ROW, MOCK_COL)
            assert result == MOCK_VALUE
            mock_worksheet.cell.assert_called_once_with(MOCK_ROW, MOCK_COL)


class TestSetCell:
    """Unit tests for set_cell function."""

    def test_set_cell_success(self):
        """Test successful cell value update."""
        mock_worksheet = Mock(spec=Worksheet)

        with patch("src.google_sheet.get_sheet", return_value=mock_worksheet):
            set_cell(None, MOCK_SPREADSHEET_ID, MOCK_SHEET_TITLE, MOCK_ROW, MOCK_COL, MOCK_VALUE)
            mock_worksheet.update_cell.assert_called_once_with(MOCK_ROW, MOCK_COL, MOCK_VALUE)


class TestCreateSheet:
    """Unit tests for create_sheet function."""

    @pytest.mark.parametrize("invalid_name", [("", "Empty string"), (123, "Non-string"), ("a" * 101, "Too long")])
    def test_create_sheet_invalid_name(self, invalid_name):
        """Test ValueError for invalid sheet name."""
        with pytest.raises(ValueError, match="Sheet name must be a non-empty string up to 100 characters."):
            create_sheet(invalid_name)

    def test_create_sheet_valid_name_success(self):
        """Test successful sheet creation."""
        mock_client = Mock(spec=Client)
        mock_spreadsheet = Mock(spec=Spreadsheet)

        with patch("src.google_sheet.get_client", return_value=mock_client), \
                patch("src.google_sheet.get_sheet_id", return_value=MOCK_SPREADSHEET_ID), \
                patch.object(mock_client, "open_by_key", return_value=mock_spreadsheet):
            result = create_sheet(MOCK_SHEET_TITLE)
            assert result is None
            mock_client.open_by_key.assert_called_once_with(MOCK_SPREADSHEET_ID)
            mock_spreadsheet.add_worksheet.assert_called_once_with(
                title=MOCK_SHEET_TITLE, rows=1000, cols=26
            )

    @pytest.mark.no_mock  # Skip mocks; use empty value
    def test_create_sheet_no_client(self):
        """Test error when client is None."""
        result = create_sheet(MOCK_SHEET_TITLE)
        assert isinstance(result, tuple)
        assert "Spreadsheet ID is required" in result[0]
        assert result[1] == 500

    @patch("src.google_sheet.get_client")
    @patch("src.google_sheet.get_sheet_id")
    def test_create_sheet_api_error(self, mock_get_id, mock_get_client):
        """Test APIError handling."""
        mock_client = Mock(spec=Client)
        mock_get_id.return_value = MOCK_SPREADSHEET_ID
        mock_get_client.return_value = mock_client

        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': {
                'code': 400,
                'message': 'API failed',
                'status': 'INVALID_ARGUMENT'
            }
        }
        mock_api_error = APIError(mock_response)
        mock_client.open_by_key.side_effect = mock_api_error

        result = create_sheet(MOCK_SHEET_TITLE)
        assert isinstance(result, tuple)
        assert "API failed" == result[0]
        assert result[1] == 400


class TestDeleteSheet:
    """Unit tests for delete_sheet function."""

    def test_delete_sheet_success(self):
        """Test successful sheet deletion."""
        mock_client = Mock(spec=Client)
        mock_spreadsheet = Mock(spec=Spreadsheet)
        mock_worksheet = Mock(spec=Worksheet)
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        result = delete_sheet(mock_client, MOCK_SPREADSHEET_ID, MOCK_SHEET_TITLE)
        assert result is None
        mock_client.open_by_key.assert_called_once_with(MOCK_SPREADSHEET_ID)
        mock_spreadsheet.worksheet.assert_called_once_with(MOCK_SHEET_TITLE)
        mock_spreadsheet.del_worksheet.assert_called_once_with(mock_worksheet)

    def test_delete_sheet_worksheet_not_found(self):
        """Test handling of WorksheetNotFound."""
        mock_client = Mock(spec=Client)
        mock_spreadsheet = Mock(spec=Spreadsheet)
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.side_effect = WorksheetNotFound("Not found")

        result = delete_sheet(mock_client, MOCK_SPREADSHEET_ID, MOCK_SHEET_TITLE)
        assert isinstance(result, tuple)
        assert isinstance(result[0], Exception)
        assert "can not be found" in str(result[0])
        assert result[1] == 400

    def test_delete_sheet_unexpected_error(self):
        """Test handling of unexpected exceptions."""
        mock_client = Mock(spec=Client)
        mock_client.open_by_key.side_effect = Exception("Unexpected error")

        result = delete_sheet(mock_client, MOCK_SPREADSHEET_ID, MOCK_SHEET_TITLE)
        assert isinstance(result, tuple)
        assert isinstance(result[0], Exception)
        assert "Unexpected error" == str(result[0])
        assert result[1] == 500