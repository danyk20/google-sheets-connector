# tests/conftest.py
import pytest
from unittest.mock import Mock, patch
from main import app  # Import your global app instance

def pytest_configure(config):
    config.addinivalue_line("markers", "no_mock: Skip Google/gspread mocking for this test (e.g., real integration).")

# Mock environment variables required by google_sheet.py (e.g., SHEET_ID)
@pytest.fixture(autouse=True)
def mock_env_vars(request, monkeypatch):
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/dev/null")  # Fake path
    monkeypatch.setenv("SCOPE", "https://www.googleapis.com/auth/spreadsheets")  # Example scope
    monkeypatch.setenv("SHEET_ID", "test-spreadsheet-id")
    # Skip mocking if the test is marked 'no_mock'
    if request.node.get_closest_marker('no_mock'):
        monkeypatch.setenv("SHEET_ID", "")
        return



# Patch Google Credentials and gspread.authorize to avoid real auth in tests
@pytest.fixture(autouse=True)
def mock_google_credentials(request):
    mock_creds = Mock()
    mock_creds.expired = False  # Avoid triggering refresh
    mock_creds.refresh = Mock()  # If refresh were called, do nothing

    # mock_client = Mock()  # Mock the full gspread client (returned by authorize)
    # # Add basic stubs for methods used in create_sheet (expand as needed for other functions)
    # mock_client.open_by_key.return_value = Mock()  # Mock Spreadsheet
    # mock_spreadsheet = mock_client.open_by_key.return_value
    # mock_spreadsheet.add_worksheet.return_value = Mock()  # Mock Worksheet
    # mock_worksheet = mock_spreadsheet.add_worksheet.return_value
    # mock_worksheet.row_count.return_value = Mock()
    # mock_authorize = Mock()
    # mock_worksheet.column_count.return_value = 26

    mock_client = Mock()

    # Mock the spreadsheet returned by open_by_key
    mock_spreadsheet = Mock()
    mock_client.open_by_key.return_value = mock_spreadsheet

    # Mock add_worksheet on the spreadsheet (returns a new worksheet if called)
    mock_worksheet_from_add = Mock()  # Example; configure as needed
    mock_spreadsheet.add_worksheet.return_value = mock_worksheet_from_add

    # Mock the worksheet returned by spreadsheet.worksheet(name)
    mock_worksheet = Mock()
    mock_spreadsheet.worksheet.return_value = mock_worksheet

    # Configure the worksheet's methods
    mock_worksheet.row_count = 1000
    mock_worksheet.column_count = 1000

    # Mock the worksheet cell returned by spreadsheet.worksheet(name)
    mock_worksheet_cell = Mock()
    mock_worksheet.cell.return_value = mock_worksheet_cell
    mock_worksheet_cell.value = "previous value"





    with (
        patch('src.google_sheet.gspread.authorize') as mock_authorize,
        patch('src.google_sheet.Credentials.from_service_account_file') as mock_from_file

    ):
        mock_from_file.return_value = mock_creds
        mock_authorize.return_value = mock_client
        yield


@pytest.fixture
def client():
    """Flask test client fixture."""
    app.config["TESTING"] = True  # Enable test mode
    with app.app_context():  # Ensure app/request contexts are available
        yield app.test_client()
    app.config["TESTING"] = False
