"""
Utility functions for URL normalization, domain extraction, and common helpers.
"""
import re
from urllib.parse import urljoin, urlparse, urlunparse
from typing import Optional
import tldextract


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """
    Normalize a URL by removing fragments, trailing slashes, and resolving relative URLs.
    
    Args:
        url: URL to normalize
        base_url: Base URL for resolving relative URLs
        
    Returns:
        Normalized URL string
    """
    if not url:
        return ""
    
    # Resolve relative URLs
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    # Parse URL
    parsed = urlparse(url)
    
    # Remove fragment
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        ''  # Remove fragment
    ))
    
    # Remove trailing slash (except for root)
    if normalized.endswith('/') and len(parsed.path) > 1:
        normalized = normalized[:-1]
    
    return normalized.lower()


def get_domain(url: str) -> str:
    """
    Extract the registered domain from a URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain string (e.g., 'example.com')
    """
    try:
        extracted = tldextract.extract(url)
        return f"{extracted.domain}.{extracted.suffix}"
    except Exception:
        parsed = urlparse(url)
        return parsed.netloc


def is_internal_link(url: str, base_domain: str) -> bool:
    """
    Check if a URL is an internal link (same domain).
    
    Args:
        url: URL to check
        base_domain: Base domain to compare against
        
    Returns:
        True if internal, False otherwise
    """
    try:
        url_domain = get_domain(url)
        return url_domain == base_domain
    except Exception:
        return False


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def get_url_path(url: str) -> str:
    """
    Extract the path component from a URL.
    
    Args:
        url: URL to extract path from
        
    Returns:
        Path string
    """
    try:
        parsed = urlparse(url)
        return parsed.path
    except Exception:
        return ""


