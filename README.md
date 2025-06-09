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

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Run tests:

```bash
pytest
```

## License

MIT 