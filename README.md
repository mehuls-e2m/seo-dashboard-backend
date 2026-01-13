# 🔍 SEO Audit System

A comprehensive Python-based Technical & On-Page SEO Audit System that performs automated crawling, rule-based validation, and structured reporting.

## Features

### Technical SEO Audits
- ✅ Robots.txt compliance checking
- ✅ Sitemap discovery and validation
- ✅ Noindex/Nofollow detection
- ✅ Canonical tag validation
- ✅ Redirect chain analysis
- ✅ HTTPS and mixed content detection
- ✅ Structured data (JSON-LD, Microdata, RDFa) validation

### On-Page SEO Audits
- ✅ Title tag analysis (length, duplicates, templates)
- ✅ Meta description validation
- ✅ H1 tag checks (count, duplicates)
- ✅ Image alt text analysis
- ✅ Internal linking analysis (orphan pages, broken links)

### Scoring & Prioritization
- ✅ Rule-based scoring system (0-100)
- ✅ Severity-based issue prioritization (Critical/High/Medium/Low)
- ✅ Site-wide statistics and averages

### Output Formats
- ✅ JSON reports (detailed)
- ✅ CSV reports (summary)
- ✅ Console reports (human-readable)

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Playwright (optional, for JavaScript rendering):**
```bash
playwright install chromium
```

## Usage

Run the main script:

```bash
python main.py
```

The system will prompt you for:
1. **Website URL** - The URL to audit (e.g., `https://example.com`)
2. **Maximum pages** - Maximum number of pages to crawl (default: 50)

### Example Session

```
🔍 SEO AUDIT SYSTEM
================================================================================

🌐 Enter website URL to audit: example.com
📄 Enter maximum number of pages to crawl (default: 50): 100

🚀 Starting audit for: https://example.com
📊 Maximum pages to crawl: 100
```

## Output Files

The system generates two output files with timestamps:

- `seo_audit_YYYYMMDD_HHMMSS.json` - Detailed JSON report with all audit data
- `seo_audit_YYYYMMDD_HHMMSS.csv` - Summary CSV report for spreadsheet analysis

## Project Structure

```
.
├── main.py                 # Main entry point
├── crawler.py             # Async web crawler
├── robots_sitemap.py      # Robots.txt and sitemap handling
├── technical_audit.py     # Technical SEO audits
├── onpage_audit.py        # On-page SEO audits
├── rule_engine.py         # Scoring and prioritization
├── output.py              # Report generation (CSV/JSON/Console)
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Features in Detail

### Crawling
- Respects robots.txt
- Rate limiting (2 requests/second per host)
- Retry logic with exponential backoff
- Concurrent crawling (configurable)
- Follows internal links only

### Logging
All operations are logged to console with emoji indicators:
- 🚀 Starting operations
- ✅ Success
- ⚠️ Warnings
- ❌ Errors
- 📊 Statistics
- 🔍 Auditing

## Scoring System

Each page receives a score from 0-100 based on:
- **Critical issues**: -40 points (e.g., noindex, not HTTPS)
- **High issues**: -20 points (e.g., missing title, canonical issues)
- **Medium issues**: -10 points (e.g., missing meta description, multiple H1s)
- **Low issues**: -5 points (e.g., missing alt text, duplicate content)

## Requirements

- Python 3.8+
- See `requirements.txt` for full dependency list

## Notes

- The crawler respects robots.txt and crawl-delay directives
- JavaScript rendering is optional (Playwright)
- All operations are logged to console for transparency
- The system is designed to be respectful and not overwhelm target servers

## License

This project is provided as-is for SEO auditing purposes.


