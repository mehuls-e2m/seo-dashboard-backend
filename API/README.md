# SEO Audit API

A FastAPI-based REST API for performing comprehensive SEO audits on websites.

## Features

- **RESTful API**: Easy-to-use HTTP endpoints
- **Async Operations**: High-performance asynchronous processing
- **Comprehensive Audits**: Technical and on-page SEO analysis
- **Structured Responses**: JSON responses with detailed statistics and issues
- **Flexible Crawling**: Configurable page limits and robots.txt respect

## Installation

1. Install dependencies from the parent directory:
```bash
cd ..
pip install -r requirements.txt
```

2. Set up environment variables (optional):
Create a `.env` file in the parent directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DEBUG=false
```

## Running the API

### Method 1: Using Uvicorn directly
```bash
cd seo-dashboard-backend
python -m uvicorn API.main:app --host 0.0.0.0 --port 8000 --reload
```

### Method 2: Using Python directly
```bash
cd seo-dashboard-backend
python API/main.py
```

### Method 3: Using the run script
```bash
cd seo-dashboard-backend
python run_api.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc

## API Endpoints

### POST /audit

Perform a comprehensive SEO audit on a website.

**Request Body:**
```json
{
  "url": "https://example.com",
  "max_pages": 100
}
```

**Parameters:**
- `url` (required): Website URL to audit
- `max_pages` (optional): Maximum number of pages to crawl. If not provided, crawls all pages.

**Note**: The API does NOT respect robots.txt by default (`respect_robots=False`) to ensure comprehensive audits. The crawler will crawl all pages it discovers, even if they are disallowed in robots.txt. See `ROBOTS_TXT_EXPLANATION.md` for details.

**Response:**
```json
{
  "audit_stats": {
    "site_overview": {
      "base_url": "https://example.com",
      "total_crawled_pages": 65,
      "average_seo_score": 27.23,
      "total_issues": 439,
      ...
    },
    "crawlability": {
      "robots_txt_exists": true,
      "robots_txt_content": "User-agent: *\n...",
      ...
    },
    "status_code_distribution": {...},
    "technical_seo": {...},
    "onpage_seo": {...}
  },
  "audit_issues": {
    "site_overview": {...},
    "crawlability": {...},
    "issues_summary": {...},
    "technical_seo": {...},
    "onpage_seo": {...}
  },
  "execution_time": 45.23
}
```

### GET /

Get API information.

### GET /health

Health check endpoint.

## Example Usage

### Using cURL
```bash
curl -X POST "http://localhost:8000/audit" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "max_pages": 50
  }'
```

### Using Python requests
```python
import requests

response = requests.post(
    "http://localhost:8000/audit",
    json={
        "url": "https://example.com",
        "max_pages": 50
    }
)

data = response.json()
print(f"Audit completed in {data['execution_time']} seconds")
print(f"Average SEO Score: {data['audit_stats']['site_overview']['average_seo_score']}")
```

### Using JavaScript fetch
```javascript
fetch('http://localhost:8000/audit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://example.com',
    max_pages: 50
  })
})
.then(response => response.json())
.then(data => {
  console.log('Execution time:', data.execution_time);
  console.log('Average SEO Score:', data.audit_stats.site_overview.average_seo_score);
});
```

## Response Structure

### audit_stats
Contains high-level statistics and overview of the audit:
- `site_overview`: Overall site metrics
- `crawlability`: Robots.txt and sitemap information
- `status_code_distribution`: HTTP status code distribution
- `technical_seo`: Technical SEO metrics
- `onpage_seo`: On-page SEO metrics

### audit_issues
Contains detailed issues found during the audit:
- `site_overview`: Overall site metrics
- `crawlability`: Robots.txt and sitemap information
- `issues_summary`: Grouped issues by severity
- `technical_seo`: Detailed technical SEO issues
- `onpage_seo`: Detailed on-page SEO issues

## Error Handling

The API returns appropriate HTTP status codes:
- `200 OK`: Audit completed successfully
- `400 Bad Request`: Invalid request parameters
- `500 Internal Server Error`: Server error during audit

Error responses follow this format:
```json
{
  "error": "Error message",
  "detail": "Detailed error description"
}
```

## Project Structure

```
API/
├── __init__.py
├── main.py                 # FastAPI application
├── core/
│   ├── __init__.py
│   └── config.py          # Configuration settings
├── models/
│   ├── __init__.py
│   └── schemas.py         # Pydantic models
├── routes/
│   ├── __init__.py
│   └── audit.py           # Audit endpoints
└── services/
    ├── __init__.py
    └── audit_service.py   # Business logic
```

## Notes

- The API does NOT respect robots.txt by default (`respect_robots=False`) to ensure comprehensive audits. See `ROBOTS_TXT_EXPLANATION.md` for details.
- When `max_pages` is not provided, the crawler will attempt to crawl all pages found.
- Large websites may take several minutes to audit.
- The API uses async operations for better performance.

## License

This project is provided as-is for SEO auditing purposes.

