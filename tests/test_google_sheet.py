import pytest
from unittest.mock import MagicMock, patch
from src import google_sheet


class TestGoogleSheetUtils:

    @patch('src.google_sheet.get_client')
    @patch('src.google_sheet.get_sheet_id')
    def test_create_sheet_success(self, mock_get_id, mock_get_client):
        """Test creating a sheet successfully."""
        # Setup Mocks
        mock_get_id.return_value = "mock_spreadsheet_id"

        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()

        mock_get_client.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet

        # Execute
        result = google_sheet.create_sheet("New Tab Name")

        # Assert
        mock_client.open_by_key.assert_called_with("mock_spreadsheet_id")
        mock_spreadsheet.add_worksheet.assert_called_with(
            title="New Tab Name", rows=1000, cols=26
        )
        assert result is None  # Returns None on success

    def test_create_sheet_validation(self):
        """Test input validation without mocking API."""
        with pytest.raises(ValueError) as excinfo:
            google_sheet.create_sheet("")  # Empty name
        assert "Sheet name must be a non-empty string" in str(excinfo.value)

    @patch('src.google_sheet.get_sheet')
    def test_get_cell_value(self, mock_get_sheet):
        """Test retrieving a cell value."""
        # Setup Mock
        mock_worksheet = MagicMock()
        mock_cell = MagicMock()
        mock_cell.value = "Hello World"

        mock_worksheet.cell.return_value = mock_cell
        mock_get_sheet.return_value = mock_worksheet

        # Execute
        # Note: We pass a mock client because get_cell requires it
        mock_client = MagicMock()
        value = google_sheet.get_cell(mock_client, "sheet_key", "Tab1", 1, 1)

        # Assert
        assert value == "Hello World"
        mock_worksheet.cell.assert_called_with(1, 1)

    def test_get_cell_position_validation(self):
        """Test the helper function validation."""
        mock_worksheet = MagicMock()
        mock_worksheet.row_count = 10
        mock_worksheet.column_count = 10

        # Valid case
        row, col = google_sheet.get_cell_positon({"row": "5", "column": "5"}, mock_worksheet)
        assert row == 5
        assert col == 5

        # Invalid case (out of bounds)
        from workflows_cdk import ManagedError
        with pytest.raises(ManagedError):
            google_sheet.get_cell_positon({"row": "100", "column": "1"}, mock_worksheet)