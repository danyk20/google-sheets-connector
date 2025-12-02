# Stacksync Google Sheets Connector

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green.svg)](https://flask.palletsprojects.com/)


![Stacksync](https://cdn.brandfetch.io/id9Bpy_H9O/theme/dark/logo.svg?c=1dxbfHSJFAPEGdCLU4o5B)

## Overview

This project provides a robust, scalable backend service for automating workflows involving **Google Sheets** and **CRM systems** (e.g., Salesforce). Built with **Flask** and integrated with the **Workflows CDK** (Custom Development Kit), it enables seamless operations such as reading/updating cells, creating/deleting sheets.

The service acts as a RESTful API, handling authentication via Google Service Accounts for Sheets and configurable credentials for CRM integrations. It supports dynamic form population for UI-driven workflows and includes comprehensive error handling, logging, and metadata responses for auditability.

### Key Features
- **Google Sheets Integration**:
  - Read cell values with position resolution.
  - Update cells with value replacement and old-value logging.
  - Create new sheets with custom names.
  - Delete existing sheets.
  - Dynamic population of available sheet names for dropdown UIs.
- **Workflows CDK Compatibility**:
  - Custom routes for `/execute` (action execution) and `/content` (dynamic UI data).
  - Structured responses with data, metadata, and error handling.
- **Extensibility**:
  - Modular `src.google_sheet` module for Sheets utilities.
  - Easy addition of new routes or CRM providers.

This backend is ideal for no-code/low-code platforms, ETL pipelines, or internal automation tools.


## 🚀 What is a Stacksync Connector?

A Stacksync Connector is a microservice that enables workflows to interact with external systems, APIs, and data sources. 

- **Authenticate** with third-party services (OAuth, API keys, custom auth)
- **Execute actions** (create, read, update, delete operations)
- **Fetch dynamic content** for form fields and user interfaces
- **Handle errors gracefully** with comprehensive logging and monitoring
- **Scale automatically** with containerized deployment

## Prerequisites
- Python 3.10 or higher.
- Google Cloud Service Account credentials (JSON key file) for Sheets access.
- Flask and required dependencies (see `requirements.txt` below).
- Optional: CRM API credentials (e.g., Salesforce OAuth tokens).

## 🏁 Quick Start

### 1. **Clone the Repository**:
   ```bash
   git clone https://github.com/danyk20/google-sheets-connector.git
   cd google-sheets-connector
   ```

### 2. **Set Up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

### 3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### 4. **Configure Environment**:
   - Set variables in `.env` file:

## Usage

Run the application:
```bash
./run_dev.sh
```

The server starts on `http://localhost:2003` (configurable via Flask). Use tools like Ngrok for public exposure.

### API Endpoints

All endpoints expect JSON payloads and return structured responses.

#### Google Sheets Operations

- **Read Cell** (`POST /execute` - Read Route):
  - **Payload**: `{"sheet_name": "Sheet1", "row": "1", "column": "2"}`.
  - **Response (200)**: `{"data": "Old Value", "metadata": {"row": 1, "column": 1, "sheet": "Sheet1"}}`.
  - **Errors**: 400 (Invalid position), 500 (API failure).

- **Update Cell** (`POST /execute` - Update Route):
  - **Payload**: `{"sheet_name": "Sheet1", "value": "New Value", "row": "1", "column": "1"}`.
  - **Response (200)**: `{"data": "New Value", "metadata": {"row": 1, "column": 1, "sheet": "Sheet1", "old_value": "Old Value"}}`.
  - **Errors**: 400 (Position resolution), 500 (Update failure).

- **Create Sheet** (`POST /execute` - Create Route):
  - **Payload**: `{"sheet_name": "NewSheet"}`.
  - **Response (200)**: `{"data": ["Sheet creation succeeded."], "metadata": {"error": null}}`.
  - **Errors**: 500 (Creation failure).

- **Delete Sheet** (`POST /execute` - Delete Route):
  - **Payload**: `{"sheet_name": "SheetToDelete"}`.
  - **Response (200)**: `{"data": ["Sheet deletion succeeded."], "metadata": {"error": null}}`.
  - **Errors**: 500 (Deletion failure).

- **Dynamic Content** (`POST /content` - All Routes):
  - **Payload**: `{"content_object_names": ["sheets"]}`.
  - **Response (200)**: `{"content_objects": [{"content_object_name": "sheets", "data": ["Sheet1", "Sheet2"]}]}`.
  - Populates UI dropdowns with available sheets.


## 📚 Documentation

For detailed implementation guides, best practices, and advanced topics, refer to the documentation in the `/documentation` folder:

## 🏗️ Project Structure


```
.
├── Dockerfile
├── README.md
├── app_config.yaml
├── config
│         ├── Dockerfile.dev
│         ├── entrypoint.sh
│         └── gunicorn_config.py
├── main.py
├── requirements.txt
├── run_dev.bat
├── run_dev.sh
└── src
    ├── google_sheet.py
    └── modules
        ├── create_contacts
        │         ├── README.md
        │         └── v1
        │             ├── module_config.yaml
        │             ├── route.py
        │             └── schema.json
        ├── create_sheet
        │         └── v1
        │             ├── module_config.yaml
        │             ├── route.py
        │             └── schema.json
        ├── delete_sheet
        │         └── v1
        │             ├── module_config.yaml
        │             ├── route.py
        │             └── schema.json
        ├── read_cell
        │         └── v1
        │             ├── module_config.yaml
        │             ├── route.py
        │             └── schema.json
        └── update_cell
            └── v1
                ├── module_config.yaml
                ├── route.py
                └── schema.json
```

### Example Request (curl)
```bash
curl -X POST http://127.0.0.1:5000/read_cell/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"data":{"sheet_name": "Sheet1", "value": "Updated", "row": "1", "column": "1"}}'
```

### Module Components

Each module consists of three core files:

- **`route.py`** - Business logic and API handlers
- **`schema.json`** - Form definition and validation rules
- **`module_config.yaml`** - Module metadata and settings

### Environment Variables

Set these environment variables for your connector:

```bash
ENVIRONMENT=dev|stage|prod
REGION=usnv|besg|other
API_KEY=your-api-key
SENTRY_DSN=your-sentry-dsn
GOOGLE_APPLICATION_CREDENTIALS=[path_to_auth.json]  # For auth
SCOPE=https://www.googleapis.com/auth/spreadsheets  
SHEET_ID=[your_sheet_id]
```

## 🛡️ Security Best Practices

- **Never commit secrets** - Use environment variables
- **Validate all inputs** - Use schema validation extensively
- **Handle errors gracefully** - Implement proper error responses
- **Log security events** - Do not log user data.
- **Use HTTPS only** - Enforce secure connections

## 📞 Support & Resources

- **Documentation**: [Stacksync Docs](https://docs.stacksync.com/)
- **Community**: [Join our Slack](https://docs.stacksync.com/start-here/community)

## Testing
- Unit tests: Use `pytest` for `src.google_sheet` functions (mock Google API calls).
- Integration: Test endpoints with valid Service Account credentials.
- Mock responses for offline testing.

```shell
pytest tests
```


Follow PEP 8 style guidelines. Add tests for new features.

---

*Built with ❤️ for efficient workflow automation.*
