# PDF OCR API - Product Requirements Document

## Overview

The PDF OCR API (`/ocr/pdf`) provides a robust solution for extracting structured data from PDF documents, specifically optimized for timesheet processing. This endpoint leverages advanced LLM-based OCR capabilities to accurately extract key information from scanned documents.

## Technical Specifications

### Endpoint Details

- **URL**: `/ocr/pdf`
- **Method**: POST
- **Content-Type**: multipart/form-data

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | PDF file to process (must be valid PDF format) |
| llm_config_data | String (JSON) | No | Optional LLM configuration in JSON format |

### LLM Configuration Options

The API supports customizing the LLM configuration for each request:

```json
{
  "provider": "gemini",
  "model": "gemini-2.0-flash-lite",
  "temperature": 0.0,
  "max_tokens": null
}
```

Supported providers:
- `openai` - OpenAI models
- `anthropic` - Anthropic Claude models
- `gemini` - Google Gemini models

### Response Format

#### Success Response (200 OK)

```json
{
  "pages": [
    {
      "page_number": 1,
      "data": {
        "name": "John Doe",
        "staff_code": "A-12345",
        "month": "Jan-2024",
        "total_working_days": 22,
        "total_ot_hours": 15,
        "total_working_sundays": 2,
        "total_sunday_ot": 8
      }
    }
  ]
}
```

#### Error Responses

- **400 Bad Request**: Invalid PDF file or configuration
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server-side processing error

Each error response follows this format:
```json
{
  "detail": "Error message describing the issue"
}
```

## Processing Pipeline

1. **Validation**: Verifies the uploaded file is a valid PDF document
2. **Page Splitting**: Divides multi-page PDFs into individual pages
3. **OCR Processing**: Uses LLM vision capabilities to extract structured data
4. **Data Standardization**: Formats and validates extracted data according to business rules
5. **Response Generation**: Returns the structured data in a consistent JSON format

## Data Extraction Capabilities

The OCR service is specifically configured to extract the following fields from timesheet PDFs:

| Field | Type | Description |
|-------|------|-------------|
| name | string | Employee name |
| staff_code | string | Employee ID (format: `<letter>-<numbers>`) |
| month | string | Reporting month (format: `%b-%Y`, e.g., "Jan-2024") |
| total_working_days | integer | Total number of working days |
| total_ot_hours | integer | Total overtime hours |
| total_working_sundays | integer | Number of Sundays worked |
| total_sunday_ot | integer | Total Sunday overtime hours |

## Business Rules

The OCR service applies the following business rules to standardize extracted data:

1. Staff code must follow the naming convention of `<letter>-<numbers>`
2. Month must follow the naming convention of `%b-%Y` (e.g., "Jan-2024")
3. Sunday/holiday work detection:
   - If start/end or HR fields are updated for a highlighted date, the person worked that day
   - If fields are blank, the person did not work that day
   - Supervisor's signature column indicates work verification

## Default Configuration

The default LLM configuration for the OCR PDF endpoint:

```python
ocr_pdf_config = LLMConfig(
    provider=LLMProvider(os.getenv("OCR_LLM_PROVIDER", LLMProvider.GEMINI)),
    model=os.getenv("OCR_LLM_MODEL", "gemini-2.0-flash-lite"),
    temperature=0.0,
)
```

## Error Handling

The API implements comprehensive error handling:

1. **PDF Validation Errors**: Catches and reports issues with invalid PDF files
2. **Processing Errors**: Handles exceptions during PDF splitting and processing
3. **LLM Service Errors**: Manages errors from the LLM API with appropriate retries
4. **Data Validation Errors**: Ensures extracted data meets schema requirements

## Performance Considerations

- Uses asynchronous processing for optimal performance
- Implements retry mechanisms for LLM API calls
- Optimizes PDF handling to minimize memory usage
- Configurable timeouts for LLM requests

## Security Considerations

- Validates file types to prevent security vulnerabilities
- Implements proper error handling to avoid information leakage
- Configurable via environment variables for secure deployment

## Future Enhancements

1. Support for additional document types (images, scanned documents)
2. Enhanced field extraction capabilities
3. Custom extraction templates for different document types
4. Batch processing capabilities for multiple documents
5. Confidence scores for extracted fields 