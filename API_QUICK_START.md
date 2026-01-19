# SEO Audit API - Quick Start Guide

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the API

### Option 1: Using the run script
```bash
python run_api.py
```

### Option 2: Using uvicorn directly
```bash
python -m uvicorn API.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using Python directly
```bash
python API/main.py
```

## Accessing the API

Once running, the API will be available at:
- **API Base URL**: http://localhost:8000
- **Interactive Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoint

### POST /audit

Perform SEO audit on a website.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/audit" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "max_pages": 50
  }'
```

**Request Body:**
- `url` (required): Website URL to audit
- `max_pages` (optional): Maximum pages to crawl. If omitted, crawls all pages.

**Note**: The API does NOT respect robots.txt by default to ensure comprehensive audits. The crawler will analyze all pages it discovers, even if they are disallowed in robots.txt.

**Response:**
Returns a JSON object with:
- `audit_stats`: Statistics and overview
- `audit_issues`: Detailed issues found
- `execution_time`: Time taken in seconds

## Example Response Structure

```json
{
  "audit_stats": {
    "site_overview": {
      "base_url": "https://example.com",
      "total_crawled_pages": 65,
      "average_seo_score": 27.23,
      "total_issues": 439,
      "critical_issues_count": 2,
      "high_issues_count": 10,
      "medium_issues_count": 69,
      "low_issues_count": 358
    },
    "crawlability": {
      "robots_txt_exists": true,
      "robots_txt_content": "User-agent: *\n...",
      "sitemap_exists": true
    },
    "technical_seo": {...},
    "onpage_seo": {...}
  },
  "audit_issues": {
    "issues_summary": {...},
    "technical_seo": {...},
    "onpage_seo": {...}
  },
  "execution_time": 45.23
}
```

## Testing with Swagger UI

1. Start the API server
2. Navigate to http://localhost:8000/docs
3. Click on `/audit` endpoint
4. Click "Try it out"
5. Fill in the request body:
   ```json
   {
     "url": "https://example.com",
     "max_pages": 50
   }
   ```
6. Click "Execute"
7. View the response

## Notes

- Large websites may take several minutes to audit
- If `max_pages` is not provided, the crawler will attempt to crawl all pages
- The API does NOT respect robots.txt by default (`respect_robots=False`) to ensure comprehensive audits
- All responses are in JSON format
- See `API/ROBOTS_TXT_EXPLANATION.md` for details about robots.txt handling

