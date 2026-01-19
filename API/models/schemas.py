"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, List, Any
from datetime import datetime


class AuditRequest(BaseModel):
    """Request model for audit endpoint"""
    url: str = Field(..., description="Website URL to audit", example="https://example.com")
    max_pages: Optional[int] = Field(None, description="Maximum number of pages to crawl. If not provided, crawls all pages.", ge=1, example=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "max_pages": 50
            }
        }


class SiteOverview(BaseModel):
    """Site overview statistics"""
    base_url: str
    timestamp: str
    total_crawled_pages: int
    average_seo_score: float
    total_issues: int
    critical_issues_count: int
    high_issues_count: int
    medium_issues_count: int
    low_issues_count: int


class Crawlability(BaseModel):
    """Crawlability information"""
    robots_txt_exists: bool
    robots_txt_content: Optional[str] = None
    llms_txt_exists: bool
    llms_txt_content: Optional[str] = None
    sitemap_exists: bool
    sitemap_urls_from_robots: List[str]
    sitemap_urls_from_robots_count: int
    sitemap_urls_count: int


class StatusCodeDistribution(BaseModel):
    """Status code distribution"""
    pass  # Will be a dynamic dict


class TechnicalSEO(BaseModel):
    """Technical SEO statistics"""
    noindex: Dict[str, Any]
    meta_robots: Dict[str, Any]
    canonical_tags: Dict[str, Any]
    redirects: Dict[str, Any]
    https: Dict[str, Any]
    structured_data: Dict[str, Any]


class OnPageSEO(BaseModel):
    """On-page SEO statistics"""
    title_tags: Dict[str, Any]
    meta_descriptions: Dict[str, Any]
    h1_tags: Dict[str, Any]
    headings: Dict[str, Any]
    image_alt_text: Dict[str, Any]
    internal_linking: Dict[str, Any]


class AuditStats(BaseModel):
    """Complete audit statistics response"""
    site_overview: Dict[str, Any]
    crawlability: Dict[str, Any]
    status_code_distribution: Dict[str, int]
    technical_seo: Dict[str, Any]
    onpage_seo: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "site_overview": {
                    "base_url": "https://example.com",
                    "timestamp": "20260119_105912",
                    "total_crawled_pages": 65,
                    "average_seo_score": 27.23,
                    "total_issues": 439,
                    "critical_issues_count": 2,
                    "high_issues_count": 10,
                    "medium_issues_count": 69,
                    "low_issues_count": 358
                }
            }
        }


class AuditIssuesResponse(BaseModel):
    """Complete audit issues response"""
    site_overview: Dict[str, Any]
    crawlability: Dict[str, Any]
    issues_summary: Dict[str, Any]
    open_graph: Optional[Dict[str, Any]] = None
    twitter_cards: Optional[Dict[str, Any]] = None
    external_links: Optional[Dict[str, Any]] = None
    content_analysis: Optional[Dict[str, Any]] = None
    language_and_encoding: Optional[Dict[str, Any]] = None
    # Note: technical_seo and onpage_seo sections removed as per requirements
    # Note: detailed_content removed - details are now included directly in issues_summary


class IssueDetail(BaseModel):
    """Individual issue detail"""
    issue_name: str
    category: str
    type: str
    severity: str
    number_of_issues: int
    affected_pages_count: int
    affected_pages: List[str]
    total_links_without_anchor_text: Optional[int] = None
    links_without_anchor_text: Optional[List[str]] = None


class IssuesSummary(BaseModel):
    """Summary of all issues"""
    total_unique_issue_types: int
    issues_by_severity: Dict[str, List[IssueDetail]]
    # Note: all_issues section removed as per requirements


class TechnicalSEODetails(BaseModel):
    """Detailed technical SEO information"""
    noindex: Dict[str, Any]
    meta_robots: Dict[str, Any]
    canonical_tags: Dict[str, Any]
    redirects: Dict[str, Any]
    https: Dict[str, Any]
    structured_data: Dict[str, Any]


class OnPageSEODetails(BaseModel):
    """Detailed on-page SEO information"""
    title_tags: Dict[str, Any]
    meta_descriptions: Dict[str, Any]
    h1_tags: Dict[str, Any]
    image_alt_text: Dict[str, Any]
    internal_linking: Dict[str, Any]


class AuditResponse(BaseModel):
    """Complete audit response with both stats and issues"""
    audit_stats: AuditStats
    audit_issues: AuditIssuesResponse
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "audit_stats": {},
                "audit_issues": {},
                "execution_time": 45.23
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    status_code: int = 500


class PagespeedRequest(BaseModel):
    """Request model for pagespeed endpoint"""
    homepage_url: str = Field(..., description="Homepage URL to analyze", example="https://example.com")
    
    class Config:
        json_schema_extra = {
            "example": {
                "homepage_url": "https://example.com"
            }
        }


class MobileAverage(BaseModel):
    """Mobile average metrics"""
    load_time_ms: float
    page_size_bytes: float
    dom_elements: float
    scripts_count: float
    stylesheets_count: float
    lcp_ms: float
    fid_ms: float
    inp_ms: float
    cls_score: float


class DesktopAverage(BaseModel):
    """Desktop average metrics"""
    load_time_ms: float
    page_size_bytes: float
    dom_elements: float
    scripts_count: float
    stylesheets_count: float
    lcp_ms: float
    fid_ms: float
    inp_ms: float
    cls_score: float


class JavaScriptSEO(BaseModel):
    """JavaScript SEO metrics"""
    js_heavy_pages_percent: int
    dom_content_loaded_avg_ms: int
    fully_rendered_avg_ms: int
    hydration_issues_detected: bool


class MobileFirst(BaseModel):
    """Mobile-first metrics"""
    content_parity: bool
    structured_data_parity: bool
    lazy_loaded_content_issues: bool


class CoreWebVitals(BaseModel):
    """Core Web Vitals metrics"""
    lcp_avg_ms: int
    fid_avg_ms: int
    inp_avg_ms: int
    cls_avg_score: float
    lcp_status: str  # good, needs_improvement, poor
    fid_status: str  # good, needs_improvement, poor
    inp_status: str  # good, needs_improvement, poor
    cls_status: str  # good, needs_improvement, poor


class PerformanceMetrics(BaseModel):
    """Performance metrics"""
    enabled: bool
    pages_tested: int
    mobile_average: MobileAverage
    desktop_average: DesktopAverage
    javascript_seo: JavaScriptSEO
    mobile_first: MobileFirst
    core_web_vitals: CoreWebVitals


class PagespeedResponse(BaseModel):
    """Response model for pagespeed endpoint"""
    homepage_url: str
    total_pages_analyzed: int
    pages_analyzed: List[str]
    average_page_size_bytes: float
    average_dom_elements: float
    average_scripts_count: float
    average_stylesheets_count: float
    total_scripts_count: int
    total_images_count: int
    performance: PerformanceMetrics
    
    class Config:
        json_schema_extra = {
            "example": {
                "homepage_url": "https://example.com",
                "total_pages_analyzed": 5,
                "pages_analyzed": [
                    "https://example.com",
                    "https://example.com/about",
                    "https://example.com/products"
                ],
                "average_page_size_bytes": 245678.0,
                "average_dom_elements": 342.0,
                "average_scripts_count": 12.5,
                "average_stylesheets_count": 3.2,
                "total_scripts_count": 63,
                "total_images_count": 79,
                "performance": {
                    "enabled": True,
                    "pages_tested": 5,
                    "mobile_average": {
                        "load_time_ms": 1200.0,
                        "page_size_bytes": 245678.0,
                        "dom_elements": 342.0,
                        "scripts_count": 12.5,
                        "stylesheets_count": 3.2
                    },
                    "desktop_average": {
                        "load_time_ms": 960.0,
                        "page_size_bytes": 245678.0,
                        "dom_elements": 342.0,
                        "scripts_count": 12.5,
                        "stylesheets_count": 3.2
                    },
                    "javascript_seo": {
                        "js_heavy_pages_percent": 42,
                        "dom_content_loaded_avg_ms": 2400,
                        "fully_rendered_avg_ms": 3900,
                        "hydration_issues_detected": True
                    },
                    "mobile_first": {
                        "content_parity": True,
                        "structured_data_parity": True,
                        "lazy_loaded_content_issues": False
                    }
                }
            }
        }

