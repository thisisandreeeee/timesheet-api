# Timesheet API

A minimal FastAPI application with a health check endpoint and PDF processing capabilities.

## Requirements

- Python 3.9+
- uv (Python package manager)

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/timesheet-api.git
   cd timesheet-api
   ```

2. Set up a virtual environment and install dependencies with uv:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev]"
   ```

3. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at http://127.0.0.1:8000.

## Available Endpoints

- Health Check: `GET /health`
- PDF OCR Processing: `POST /ocr/pdf`
- API Documentation: `GET /docs`

## PDF Processing

The API includes an endpoint to process PDF files:

1. Upload a PDF file to `/ocr/pdf` using a multipart/form-data request
2. Optionally specify `extract_keys` to define specific data fields to extract
3. The API will:
   - Validate the PDF file
   - Split it into individual pages
   - Perform OCR on each page (currently implemented as a no-op)
   - Extract structured data as a dictionary
   - Return the results for each page

### Parameters

- `file`: PDF file to process (required)
- `extract_keys`: Array of strings specifying which keys to extract from the document (optional)

### Using Postman

To send a request using Postman:

1. Set up a POST request to `http://127.0.0.1:8000/ocr/pdf`
2. In the Body tab, select "form-data"
3. Add a key called `file` and select "File" as the type, then browse for your PDF
4. Optionally, add one or more `extract_keys` fields. For example:
   - Key: `extract_keys` Value: `field1`
   - Key: `extract_keys` Value: `field2`
5. Send the request

### Example Response

```json
{
  "status": "success",
  "message": "PDF processed successfully",
  "pages_processed": 2,
  "results": [
    {
      "page_number": 1,
      "text": "Sample OCR text for page 1",
      "confidence": "high",
      "data": {
        "field1": "Value 1",
        "field2": "Value 2"
      }
    },
    {
      "page_number": 2,
      "text": "Sample OCR text for page 2",
      "confidence": "medium",
      "data": {
        "field1": "Value 3",
        "field2": "Value 4"
      }
    }
  ]
}
```

If no `extract_keys` are provided, the API will extract all possible fields (currently returns sample data):

```json
{
  "data": {
    "title": "Sample Document",
    "date": "2023-06-15",
    "total_amount": "1,234.56",
    "sender": "ABC Company",
    "recipient": "XYZ Corporation"
  }
}
```

## Development

### Running tests
```bash
pytest
```

### Code formatting
```bash
black .
isort .
```

### Linting
```bash
ruff .
``` 