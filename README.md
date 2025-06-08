# Timesheet API

A minimal FastAPI application that provides PDF processing capabilities with OCR using LLMs.

## Features

- Health check endpoint
- PDF processing with OCR via LLM vision models
- Structured data extraction from PDFs
- Configurable LLM providers (OpenAI, Anthropic, Gemini)

## Setup

### Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) for dependency management

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/timesheet-api.git
cd timesheet-api
```

2. Create a virtual environment and install dependencies:

```bash
uv venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
uv pip install -e .
```

3. Configure environment variables:

Create a `.env` file in the root directory by copying the `.env.example` file:

```bash
cp .env.example .env
```

Edit the `.env` file and set your LLM API keys:

```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GEMINI_API_KEY=your_gemini_api_key

# Default LLM settings (modify as needed)
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4-vision
```

## Usage

### Starting the server

Run the server with:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### API Endpoints

#### Health Check

```
GET /health
```

Returns the service health status.

#### PDF Processing

```
POST /ocr/pdf
```

Process a PDF file and extract structured data using LLM-based OCR.

**Request:**

- `file`: PDF file (required)
- `extract_keys`: Comma-separated list of keys to extract from the document (optional)
- `custom_prompt`: Custom prompt for the LLM (optional)
- `llm_config_data`: JSON string with LLM configuration (optional)

**Example LLM config:**

```json
{
  "provider": "anthropic",
  "model": "claude-3-opus-20240229",
  "temperature": 0.2,
  "max_tokens": 4000
}
```

**Response:**

```json
{
  "pages": [
    {
      "page_number": 1,
      "text": "Extracted text from page 1",
      "confidence": "high",
      "data": {
        "title": "Sample Document",
        "date": "2023-01-01",
        "custom_field": "value"
      }
    },
    {
      "page_number": 2,
      "text": "Extracted text from page 2",
      "confidence": "high",
      "data": {
        "signature": "John Doe",
        "total": "$1,234.56"
      }
    }
  ]
}
```

## Using with Postman

1. Create a new POST request to `http://127.0.0.1:8000/ocr/pdf`
2. In the "Body" tab, select "form-data"
3. Add the following key-value pairs:
   - `file`: Select a PDF file (Type: File)
   - `extract_keys`: Add comma-separated keys (e.g., "title,date,amount")
   - `llm_config_data`: Add JSON config (optional)
   - `custom_prompt`: Add custom prompt text (optional)
4. Send the request

## LLM Integration

The API uses vision language models for OCR and data extraction. You can configure which LLM provider and model to use either:

1. Globally in the `.env` file
2. Per API route in the code
3. Per request using the `llm_config_data` parameter

### Supported LLM Providers

- **OpenAI**: GPT-4 Vision models
- **Anthropic**: Claude 3 Vision models
- **Gemini**: Gemini Pro Vision models

### Configuration Options

- `provider`: LLM provider (e.g., "openai", "anthropic", "gemini")
- `model`: LLM model name
- `temperature`: Temperature for LLM generation (0.0 to 1.0)
- `max_tokens`: Maximum tokens for LLM generation

## Development

### Running Tests

```bash
pytest
```

### Project Structure

```
timesheet-api/
├── app/
│   ├── main.py                  # FastAPI application
│   ├── services/
│   │   ├── pdf_service.py       # PDF processing service
│   │   └── llm/                 # LLM integration
│   │       ├── client.py        # LLM API client
│   │       ├── config.py        # LLM configuration
│   │       └── ocr_service.py   # OCR service using LLMs
│   ├── schemas/
│   │   └── pdf.py               # Pydantic schemas for PDF processing
│   └── tests/                   # Test modules
├── .env.example                 # Example environment variables
├── pyproject.toml               # Project configuration
└── README.md                    # Project documentation
```

## License

MIT 