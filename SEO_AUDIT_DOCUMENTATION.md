# SEO Audit Application Documentation

## Table of Contents
1. [Application Overview](#application-overview)
2. [How It Works](#how-it-works)
3. [Scoring System](#scoring-system)
4. [Issue Criteria & Thresholds](#issue-criteria--thresholds)
5. [API Endpoints](#api-endpoints)

---

## Application Overview

This SEO audit application performs comprehensive technical and on-page SEO analysis of websites. It crawls websites, analyzes various SEO factors, and provides detailed reports with scores and actionable recommendations.

### Key Features
- **Comprehensive Crawling**: Discovers pages through link following and sitemap analysis
- **Technical SEO Audit**: Checks robots.txt, sitemaps, canonical tags, redirects, HTTPS, structured data, server response times
- **On-Page SEO Audit**: Analyzes titles, meta descriptions, headings, images, internal linking, URL structure
- **Orphan Page Detection**: Identifies pages with no internal in-links using sitemap data
- **Performance Analysis**: PageSpeed insights via Google PageSpeed Insights API
- **Issue-Based Scoring**: Penalty system based on specific issue types

---

## How It Works

### 1. Crawling Process

1. **Initialization**: Starts from the homepage URL
2. **Robots.txt Check**: Fetches and parses robots.txt to respect crawl directives
3. **Sitemap Discovery**: 
   - Extracts sitemap URLs from robots.txt (using standard parser and Gemini AI fallback)
   - Discovers sitemaps from common locations (/sitemap.xml, /sitemap_index.xml, etc.)
   - Parses all sitemap files (including nested sitemaps)
4. **Link Following**: 
   - Extracts internal links from each crawled page
   - Adds discovered links to crawl queue
   - Respects max_pages limit (default: 9999)
5. **Orphan Detection**: Uses sitemap URLs to identify pages with no internal in-links

### 2. Audit Process

For each crawled page, the system performs:

#### Technical SEO Checks:
- Robots.txt directives (noindex, nofollow)
- Canonical tags
- Redirect chains and loops
- HTTPS usage
- Mixed content
- Structured data (JSON-LD, microdata, RDFa)
- Server response times (TTFB)
- HTTP status codes

#### On-Page SEO Checks:
- Title tags (presence, length, uniqueness)
- Meta descriptions (presence, length, uniqueness)
- H1 tags (presence, count, uniqueness)
- Heading structure (H1-H6 counts)
- Image alt text
- Internal linking
- URL structure
- Content length
- Open Graph tags
- Twitter Cards
- Language and encoding
- Responsive design (viewport)

### 3. Scoring Process

- **Page Score**: Starts at 100, penalties applied based on detected issues
- **Issue-Specific Weights**: Each issue type has a specific penalty weight
- **Minimum Score**: Floor of 20 (pages cannot score below 20)
- **Site Score**: Average of all individual page scores

---

## Scoring System

### Scoring Methodology

1. **Base Score**: Each page starts with a score of 100
2. **Penalty Application**: Issues reduce the score based on their specific weight
3. **Issue-Specific Weights**: Each issue type has a predefined penalty (see Issue Weights table)
4. **Minimum Floor**: Scores cannot go below 20
5. **Site Score Calculation**: Average of all page scores (no scaling factor)

### Issue Weights

| Issue Type | Penalty | Category |
|------------|---------|----------|
| **Technical SEO** | | |
| Noindex on indexable page | -15 | Critical |
| Redirect loop | -15 | Critical |
| Not using HTTPS | -15 | Critical |
| Canonical points to 404 | -12 | High |
| Canonical points to homepage | -12 | High |
| Server error (5xx) | -12 | High |
| Mixed content (JS/CSS) | -10 | High |
| Meta robots conflict | -6 | Medium |
| Canonical points to different URL | -6 | Medium |
| Redirect chain too long | -6 | Medium |
| Redirect 302 (temporary) | -4 | Medium |
| Nofollow directive | -3 | Low |
| Missing structured data | -2 | Low |
| Duplicate structured data | -2 | Low |
| **On-Page SEO** | | |
| Missing title | -8 | High |
| Title empty | -8 | High |
| Missing meta description | -6 | High |
| Meta description empty | -6 | High |
| No H1 tag | -6 | High |
| Orphan page | -6 | High |
| Title too short | -4 | Medium |
| Title too long | -4 | Medium |
| Duplicate title | -4 | Medium |
| Multiple H1 tags | -4 | Medium |
| Images missing alt text | -4 | Medium (max 3 counted) |
| Broken internal links | -4 | Medium |
| Meta description too short | -3 | Medium |
| Meta description too long | -3 | Medium |
| Title template/default | -3 | Low |
| H1 identical to title | -2 | Low |
| Images empty alt | -2 | Low (max 2 counted) |
| Duplicate description | -2 | Low |
| Excessive internal links | -2 | Low |
| Link without anchor text | -2 | Low |
| H1 other issues | -3 | Medium |
| Internal links other | -2 | Low |

### Scoring Examples

**Example 1: Good Page**
- Base: 100
- Issues: None
- **Final Score: 100**

**Example 2: Page with Minor Issues**
- Base: 100
- Title too short: -4
- Missing meta description: -6
- **Final Score: 90**

**Example 3: Page with Critical Issues**
- Base: 100
- Not using HTTPS: -15
- Missing title: -8
- No H1 tag: -6
- **Final Score: 71**

**Example 4: Page with Many Issues**
- Base: 100
- Multiple issues totaling -80
- **Final Score: 20** (minimum floor)

---

## Issue Criteria & Thresholds

### Title Tag Issues

#### Title Too Short
- **Threshold**: `<30 characters`
- **Recommended**: `30-70 characters`
- **Penalty**: `-4`
- **Description**: Title tags shorter than 30 characters may not provide enough context for search engines and users.

#### Title Too Long
- **Threshold**: `>70 characters`
- **Recommended**: `30-70 characters`
- **Penalty**: `-4`
- **Description**: Title tags longer than 70 characters may be truncated in search results.

#### Missing Title Tag
- **Threshold**: `No <title> tag found in HTML`
- **Recommended**: `Every page should have a unique, descriptive title tag`
- **Penalty**: `-8`
- **Description**: Title tags are critical for SEO and appear in search results and browser tabs.

#### Title Empty
- **Threshold**: `<title> tag exists but is empty`
- **Recommended**: `Include descriptive text in title tag`
- **Penalty**: `-8`
- **Description**: Empty title tags provide no value to search engines or users.

#### Duplicate Title
- **Threshold**: `Same title tag used on multiple pages`
- **Recommended**: `Each page should have a unique title tag`
- **Penalty**: `-4`
- **Description**: Duplicate titles can cause search engines to struggle with which page to rank for a query.

#### Title Template/Default
- **Threshold**: `Title contains generic words (home, page, untitled, new page) and is <20 characters`
- **Recommended**: `Use descriptive, unique titles`
- **Penalty**: `-3`
- **Description**: Template or default titles indicate pages that haven't been properly customized.

---

### Meta Description Issues

#### Meta Description Too Short
- **Threshold**: `<120 characters`
- **Recommended**: `120-160 characters`
- **Penalty**: `-3`
- **Description**: Meta descriptions shorter than 120 characters may not provide enough information to entice clicks from search results.

#### Meta Description Too Long
- **Threshold**: `>160 characters`
- **Recommended**: `120-160 characters`
- **Penalty**: `-3`
- **Description**: Meta descriptions longer than 160 characters may be truncated in search results.

#### Missing Meta Description
- **Threshold**: `No <meta name="description"> tag found in HTML`
- **Recommended**: `Every page should have a unique, descriptive meta description`
- **Penalty**: `-6`
- **Description**: Meta descriptions appear in search results and can influence click-through rates.

#### Meta Description Empty
- **Threshold**: `Meta description tag exists but is empty`
- **Recommended**: `Include descriptive text in meta description`
- **Penalty**: `-6`
- **Description**: Empty meta descriptions provide no value in search results.

#### Duplicate Meta Description
- **Threshold**: `Same meta description used on multiple pages`
- **Recommended**: `Each page should have a unique meta description`
- **Penalty**: `-2`
- **Description**: Duplicate meta descriptions reduce the uniqueness of search result snippets.

---

### Heading (H1) Issues

#### No H1 Tag
- **Threshold**: `No <h1> tag found on page`
- **Recommended**: `Every page should have exactly one H1 tag`
- **Penalty**: `-6`
- **Description**: H1 tags help search engines understand the main topic of the page.

#### Multiple H1 Tags
- **Threshold**: `More than 1 <h1> tag found on page`
- **Recommended**: `Exactly one H1 tag per page`
- **Penalty**: `-4`
- **Description**: Multiple H1 tags can confuse search engines about the page's main topic.

#### H1 Identical to Title
- **Threshold**: `H1 tag text exactly matches title tag text`
- **Recommended**: `H1 and title should be related but not identical`
- **Penalty**: `-2`
- **Description**: Identical H1 and title may indicate over-templating and missed optimization opportunities.

---

### Image Issues

#### Images Missing Alt Text
- **Threshold**: `Missing alt attribute on <img> tag`
- **Recommended**: `All images should have descriptive alt text (except decorative images)`
- **Penalty**: `-4 per image (maximum 3 images counted)`
- **Description**: Images without alt text are not accessible to screen readers and provide no context to search engines. SVG images are excluded from this check.

#### Images with Empty Alt Text
- **Threshold**: `Image has alt="" (empty alt attribute)`
- **Recommended**: `Use descriptive alt text or omit alt for decorative images`
- **Penalty**: `-2 per image (maximum 2 images counted)`
- **Description**: Images with empty alt attributes may indicate decorative images, but should be intentional. SVG images are excluded.

#### Oversized or Unoptimized Images
- **Threshold**: 
  - Missing width/height attributes (can cause layout shift)
  - Dimensions >2000px in width or height
  - Aspect ratio >5:1 (extreme width/height ratio)
  - Invalid dimension values
- **Recommended**: `Include width/height attributes, optimize images to appropriate sizes, maintain reasonable aspect ratios`
- **Penalty**: `Not scored (reported as issue)`
- **Description**: These issues can cause layout shifts, slow page loads, and poor user experience. SVG images are excluded from this check.

---

### Internal Linking Issues

#### Excessive Internal Links
- **Threshold**: `>100 internal links on a single page`
- **Recommended**: `<100 internal links per page`
- **Penalty**: `-2`
- **Description**: Pages with more than 100 internal links may be seen as link farms and can dilute link equity.

#### Broken Internal Links
- **Threshold**: `Internal link returns 404 or error status`
- **Recommended**: `All internal links should return 200 OK status`
- **Penalty**: `-4`
- **Description**: Broken internal links create poor user experience and waste crawl budget.

#### Link Without Anchor Text
- **Threshold**: `Link has no visible anchor text (empty or whitespace only)`
- **Recommended**: `All links should have descriptive anchor text`
- **Penalty**: `-2`
- **Description**: Links without anchor text provide no context to users or search engines about the destination.

#### Orphan Pages
- **Threshold**: `Page has 0 internal in-links (no other pages link to it)`
- **Recommended**: `All important pages should have at least one internal link pointing to them`
- **Penalty**: `-6`
- **Description**: Orphan pages are hard for search engines to discover and may not be indexed. Homepage is excluded from this check. Detection uses sitemap URLs to find true orphan pages.

---

### URL Structure Issues

#### URLs Contain Underscores
- **Threshold**: `Contains underscore (_) character in URL path`
- **Recommended**: `Use hyphens (-) instead of underscores`
- **Penalty**: `Not scored (reported as issue)`
- **Description**: Underscores in URLs are less readable and search engines treat hyphens as word separators.

#### URLs Contain Uppercase Letters
- **Threshold**: `Contains uppercase letters (A-Z) in URL path`
- **Recommended**: `Use lowercase letters only`
- **Penalty**: `Not scored (reported as issue)`
- **Description**: Uppercase letters in URLs can cause case-sensitivity issues and are less consistent.

#### URLs Too Long
- **Threshold**: `>100 characters`
- **Recommended**: `<100 characters`
- **Penalty**: `Not scored (reported as issue)`
- **Description**: URLs longer than 100 characters may be truncated in search results, browser address bars, and when shared.

#### URLs Too Deep
- **Threshold**: `>5 path levels (e.g., /level1/level2/level3/level4/level5/level6)`
- **Recommended**: `<5 path levels`
- **Penalty**: `Not scored (reported as issue)`
- **Description**: URLs with more than 5 levels of depth can be harder for search engines to crawl and are less user-friendly.

#### URLs Contain Special Characters
- **Threshold**: `Contains characters other than a-z, 0-9, hyphens (-), slashes (/), dots (.), and underscores (_)`
- **Recommended**: `Use only alphanumeric characters, hyphens, and slashes`
- **Penalty**: `Not scored (reported as issue)`
- **Description**: Special characters in URLs can cause encoding issues and are less user-friendly.

---

### Technical SEO Issues

#### Missing robots.txt File
- **Threshold**: `robots.txt file not found at /robots.txt`
- **Recommended**: `Provide robots.txt file to guide search engine crawlers`
- **Penalty**: `Not scored (reported as critical issue)`
- **Description**: robots.txt helps control which pages search engines can crawl and where to find sitemaps.

#### No Sitemaps Found
- **Threshold**: `No XML sitemap URLs found in robots.txt or common locations`
- **Recommended**: `Provide XML sitemap(s) to help search engines discover all pages`
- **Penalty**: `Not scored (reported as critical issue)`
- **Description**: Sitemaps help search engines discover and index all pages on your site, especially orphan pages.

#### Missing llms.txt File
- **Threshold**: `llms.txt file not found at /llms.txt`
- **Recommended**: `Provide llms.txt file for LLM agents`
- **Penalty**: `Not scored (reported as high issue)`
- **Description**: llms.txt helps LLM agents understand your site structure and content.

#### Pages Returning 404 Not Found
- **Threshold**: `Page returns HTTP 404 status code`
- **Recommended**: `Fix broken pages or redirect to appropriate content`
- **Penalty**: `Not scored (reported as high issue)`
- **Description**: 404 pages create poor user experience and waste crawl budget. Should be fixed or redirected (301).

#### Canonical Points to 404
- **Threshold**: `Canonical URL returns 404 Not Found`
- **Recommended**: `Canonical URL should point to an accessible page (200 OK)`
- **Penalty**: `-12`
- **Description**: Canonical tags pointing to 404 pages waste crawl budget and confuse search engines.

#### Canonical Points to Homepage
- **Threshold**: `Canonical URL points to homepage instead of current page`
- **Recommended**: `Canonical URL should point to the current page URL (self-referencing)`
- **Penalty**: `-12`
- **Description**: Canonical tags pointing to homepage can cause all pages to be treated as duplicates of the homepage.

#### Canonical Points to Different URL
- **Threshold**: `Canonical URL points to a different URL than the current page`
- **Recommended**: `Canonical URL should typically be self-referencing (point to current page)`
- **Penalty**: `-6`
- **Description**: Canonical tags pointing to different URLs should only be used for duplicate content consolidation.

#### Redirect Chain Ends in 404
- **Threshold**: `Redirect chain ends in 404 Not Found`
- **Recommended**: `Redirect chains should end at a valid page (200 OK)`
- **Penalty**: `-12`
- **Description**: Redirect chains ending in 404 waste crawl budget and create poor user experience.

#### Redirect Chain Too Long
- **Threshold**: `Redirect chain has more than 3 redirects`
- **Recommended**: `Keep redirect chains to 1-2 redirects maximum`
- **Penalty**: `-6`
- **Description**: Long redirect chains slow down page loads and waste crawl budget.

#### Redirect Loop
- **Threshold**: `Redirect creates a loop (A→B→A or circular)`
- **Recommended**: `Fix redirect loops immediately`
- **Penalty**: `-15`
- **Description**: Redirect loops can cause infinite redirects and prevent pages from loading.

#### Temporary Redirect 302
- **Threshold**: `Temporary redirect (302) used instead of permanent (301)`
- **Recommended**: `Use 301 (permanent) redirects for permanent URL changes`
- **Penalty**: `-4`
- **Description**: 302 redirects don't pass link equity as effectively as 301 redirects.

#### Page Has Noindex Directive
- **Threshold**: `Page has noindex directive (meta robots or X-Robots-Tag)`
- **Recommended**: `Remove noindex from pages that should be indexed`
- **Penalty**: `-15` (if page should be indexable)
- **Description**: noindex prevents pages from appearing in search results. Only use for pages that shouldn't be indexed.

#### Page Not Using HTTPS
- **Threshold**: `Page uses HTTP instead of HTTPS`
- **Recommended**: `Use HTTPS for all pages`
- **Penalty**: `-15`
- **Description**: HTTPS is required for security, user trust, and is a ranking factor.

#### Mixed Content
- **Threshold**: `HTTPS page loads HTTP resources (JS/CSS/images)`
- **Recommended**: `Load all resources over HTTPS`
- **Penalty**: `-10`
- **Description**: Mixed content can cause security warnings and poor user experience.

#### Missing Structured Data
- **Threshold**: `No structured data (JSON-LD, microdata, RDFa) found`
- **Recommended**: `Implement structured data for better rich snippets`
- **Penalty**: `-2`
- **Description**: Structured data helps search engines understand content and can enable rich results.

#### Duplicate Structured Data
- **Threshold**: `Multiple instances of same structured data type on page`
- **Recommended**: `Use structured data once per page per type`
- **Penalty**: `-2`
- **Description**: Duplicate structured data can confuse search engines.

#### Server Error
- **Threshold**: `Page returns 5xx server error status`
- **Recommended**: `Fix server errors immediately`
- **Penalty**: `-12`
- **Description**: Server errors prevent pages from loading and waste crawl budget.

#### Missing Viewport Meta Tag
- **Threshold**: `No <meta name="viewport"> tag found`
- **Recommended**: `Include viewport meta tag for responsive design`
- **Penalty**: `Not scored (reported as issue)`
- **Description**: Viewport meta tag is essential for mobile SEO and responsive design.

#### Missing Cache-Control Header
- **Threshold**: `No Cache-Control HTTP header present`
- **Recommended**: `Set appropriate Cache-Control headers for better performance`
- **Penalty**: `Not scored (reported as issue)`
- **Description**: Cache-Control headers help browsers and CDNs cache content, improving page load speed.

#### Missing Content Compression
- **Threshold**: `No Content-Encoding header (gzip/deflate/brotli) present`
- **Recommended**: `Enable content compression (gzip, deflate, or brotli)`
- **Penalty**: `Not scored (reported as issue)`
- **Description**: Content compression reduces file sizes and improves page load speed.

---

## API Endpoints

### 1. SEO Audit Endpoint

**POST** `/api/audit`

**Request Body:**
```json
{
  "url": "https://example.com",
  "max_pages": 100,
  "respect_robots": false
}
```

**Response:**
- `audit_stats`: High-level statistics (numbers only)
- `audit_issues`: Detailed issues with thresholds in issue names

### 2. PageSpeed Analysis Endpoint

**POST** `/api/pagespeed`

**Request Body:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
- Performance metrics for 7 pages (homepage + 6 important pages)
- Mobile and desktop averages
- Core Web Vitals (LCP, FID/INP, CLS)
- JavaScript SEO metrics

---

## Notes

1. **Sitemap Detection**: The system uses multiple methods to discover sitemaps:
   - Standard robots.txt parser
   - Gemini AI fallback for complex robots.txt
   - Common location discovery (/sitemap.xml, etc.)

2. **Orphan Page Detection**: Uses sitemap URLs to identify pages that exist in sitemaps but have no internal in-links, enabling detection of true orphan pages.

3. **Image Penalty Caps**: 
   - Missing alt text: Maximum 3 images counted (penalty: -4 each)
   - Empty alt text: Maximum 2 images counted (penalty: -2 each)
   - This prevents excessive penalties for pages with many images

4. **Minimum Score**: All pages have a minimum score of 20, regardless of issues found.

5. **SVG Exclusion**: SVG images are excluded from image-related checks and penalties.

6. **Homepage Exclusion**: Homepage is excluded from orphan page detection as it's the entry point.

---

## Version

**Last Updated**: 2024
**Version**: 1.0

