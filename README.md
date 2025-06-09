# Timesheet API

A FastAPI application that provides employee and timesheet management capabilities, as well as PDF processing with OCR.

## Features

- Employee management (CRUD operations)
- Timesheet management (CRUD operations)
- Validation of timesheet data
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

### API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Employee Endpoints

- `GET /employees` - List all employees
- `POST /employees` - Create a new employee
- `GET /employees/{uuid}` - Get employee details
- `PUT /employees/{uuid}` - Update employee details
- `DELETE /employees/{uuid}` - Delete employee

### Timesheet Endpoints

- `GET /employees/{uuid}/timesheets` - List all timesheets for an employee
- `GET /employees/{uuid}/timesheets/{year}/{month}` - Get specific timesheet
- `POST /employees/{uuid}/timesheets` - Create a new timesheet
- `PUT /employees/{uuid}/timesheets/{year}/{month}` - Update timesheet
- `DELETE /employees/{uuid}/timesheets/{year}/{month}` - Delete timesheet

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

### Running Tests

```bash
pytest
```

## License

MIT 