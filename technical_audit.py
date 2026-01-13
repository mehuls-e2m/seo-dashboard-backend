"""
Technical SEO audit module: noindex, canonical, redirects, HTTPS, structured data.
"""
from bs4 import BeautifulSoup
import extruct
from typing import Dict, List, Optional
import logging
from urllib.parse import urlparse
import json
import re

logger = logging.getLogger(__name__)


class TechnicalAuditor:
    """Perform technical SEO audits on crawled pages."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
    
    def audit_noindex(self, html: str, headers: Dict) -> Dict:
        """
        Check for noindex directives in meta tags and headers.
        
        Args:
            html: HTML content
            headers: HTTP response headers
            
        Returns:
            Dict with audit results
        """
        issues = []
        severity = "low"
        has_noindex = False
        has_nofollow = False
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Check meta robots tag
            meta_robots = soup.find('meta', attrs={'name': re.compile(r'robots|googlebot', re.I)})
            if meta_robots:
                content = meta_robots.get('content', '').lower()
                if 'noindex' in content:
                    issues.append("Meta robots tag contains 'noindex'")
                    has_noindex = True
                    severity = "critical"
                if 'nofollow' in content:
                    issues.append("Meta robots tag contains 'nofollow'")
                    has_nofollow = True
                    if severity != "critical":
                        severity = "medium"
            
            # Check X-Robots-Tag header
            x_robots = headers.get('X-Robots-Tag', '').lower()
            if x_robots:
                if 'noindex' in x_robots:
                    issues.append("X-Robots-Tag header contains 'noindex'")
                    has_noindex = True
                    severity = "critical"
                if 'nofollow' in x_robots:
                    issues.append("X-Robots-Tag header contains 'nofollow'")
                    has_nofollow = True
                    if severity != "critical":
                        severity = "medium"
            
            # Check for conflicts
            if meta_robots and x_robots:
                meta_content = meta_robots.get('content', '').lower()
                if ('noindex' in meta_content and 'noindex' not in x_robots) or \
                   ('noindex' not in meta_content and 'noindex' in x_robots):
                    issues.append("Conflict between meta robots tag and X-Robots-Tag header")
                    severity = "high"
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking noindex: {str(e)}")
        
        return {
            'has_noindex': has_noindex,
            'has_nofollow': has_nofollow,
            'status': 'error' if has_noindex else 'good',
            'issues': issues,
            'severity': severity
        }
    
    def audit_meta_robots(self, html: str, headers: Dict) -> Dict:
        """
        Check meta robots tag separately (for reporting).
        
        Args:
            html: HTML content
            headers: HTTP response headers
            
        Returns:
            Dict with audit results
        """
        has_meta_robots = False
        meta_content = ""
        header_content = ""
        issues = []
        severity = "low"
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Check meta robots tag
            meta_robots = soup.find('meta', attrs={'name': re.compile(r'robots|googlebot', re.I)})
            if meta_robots:
                has_meta_robots = True
                meta_content = meta_robots.get('content', '')
            
            # Check X-Robots-Tag header
            x_robots = headers.get('X-Robots-Tag', '')
            if x_robots:
                header_content = x_robots
            
            # If no meta robots and no header, it's fine (default behavior)
            if not has_meta_robots and not header_content:
                status = 'good'
            else:
                status = 'info'  # Present but may have directives
                
        except Exception as e:
            logger.warning(f"⚠️ Error checking meta robots: {str(e)}")
            status = 'error'
        
        return {
            'has_meta_robots': has_meta_robots,
            'meta_content': meta_content,
            'header_content': header_content,
            'status': status,
            'issues': issues,
            'severity': severity
        }
    
    def audit_canonical(self, html: str, page_url: str) -> Dict:
        """
        Check canonical tag implementation.
        
        Args:
            html: HTML content
            page_url: URL of the page
            
        Returns:
            Dict with audit results
        """
        issues = []
        severity = "low"
        canonical_url = None
        status = "good"
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Find canonical tag
            canonical = soup.find('link', attrs={'rel': 'canonical'})
            
            if not canonical:
                issues.append("Missing canonical tag")
                severity = "high"
                status = "error"
            else:
                canonical_url = canonical.get('href', '')
                if not canonical_url:
                    issues.append("Canonical tag has empty href")
                    severity = "high"
                    status = "error"
                else:
                    # Check if canonical points to homepage incorrectly
                    from urllib.parse import urlparse
                    canonical_parsed = urlparse(canonical_url)
                    page_parsed = urlparse(page_url)
                    
                    if canonical_parsed.path == '/' and page_parsed.path != '/':
                        issues.append("Canonical points to homepage instead of current page")
                        severity = "critical"
                        status = "error"
                    
                    # Check if canonical is self-referential (good)
                    if canonical_url == page_url:
                        status = "good"  # This is correct
                    else:
                        # Check if it's a relative URL that resolves to same page
                        from utils import normalize_url
                        normalized_canonical = normalize_url(canonical_url, page_url)
                        if normalized_canonical != normalize_url(page_url):
                            issues.append(f"Canonical points to different URL: {canonical_url}")
                            severity = "medium"
                            status = "warning"
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking canonical: {str(e)}")
            status = "error"
        
        return {
            'has_canonical': canonical_url is not None,
            'canonical_url': canonical_url,
            'status': status,
            'issues': issues,
            'severity': severity
        }
    
    def audit_redirects(self, status_code: int, redirect_chain: List[str]) -> Dict:
        """
        Check redirect chain for issues.
        
        Args:
            status_code: HTTP status code
            redirect_chain: List of URLs in redirect chain
            
        Returns:
            Dict with audit results
        """
        issues = []
        severity = "low"
        status = "good"
        
        # Check status code
        if status_code == 200:
            status = "good"
        elif status_code == 301:
            status = "info"  # Permanent redirect - usually OK
        elif status_code == 302:
            issues.append("Uses 302 (temporary) redirect instead of 301")
            severity = "medium"
            status = "warning"
        elif status_code == 404:
            issues.append("Redirect chain ends in 404")
            severity = "critical"
            status = "error"
        elif status_code >= 500:
            issues.append(f"Server error: {status_code}")
            severity = "critical"
            status = "error"
        elif 300 <= status_code < 400:
            status = "info"
        
        # Check redirect chain length
        if len(redirect_chain) > 2:
            issues.append(f"Redirect chain too long ({len(redirect_chain)} hops)")
            severity = "high"
            status = "error"
        
        # Check for redirect loops
        if len(redirect_chain) != len(set(redirect_chain)):
            issues.append("Redirect loop detected")
            severity = "critical"
            status = "error"
        
        return {
            'status_code': status_code,
            'redirect_chain_length': len(redirect_chain),
            'status': status,
            'issues': issues,
            'severity': severity
        }
    
    def audit_https(self, url: str, html: str) -> Dict:
        """
        Check HTTPS implementation and mixed content.
        
        Args:
            url: Page URL
            html: HTML content
            
        Returns:
            Dict with audit results
        """
        issues = []
        severity = "low"
        mixed_content_count = 0
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            is_https = parsed.scheme == 'https'
            
            # Check if page is HTTPS
            if not is_https:
                issues.append("Page is not served over HTTPS")
                severity = "critical"
                return {
                    'is_https': False,
                    'mixed_content_count': 0,
                    'issues': issues,
                    'severity': severity
                }
            
            # Check for mixed content
            soup = BeautifulSoup(html, 'lxml')
            
            # Check images
            for img in soup.find_all('img', src=True):
                src = img.get('src', '')
                if src.startswith('http://'):
                    mixed_content_count += 1
                    issues.append(f"Image loaded via HTTP: {src[:50]}...")
            
            # Check scripts
            for script in soup.find_all('script', src=True):
                src = script.get('src', '')
                if src.startswith('http://'):
                    mixed_content_count += 1
                    issues.append(f"Script loaded via HTTP: {src[:50]}...")
                    severity = "high" if severity != "critical" else severity
            
            # Check stylesheets
            for link in soup.find_all('link', rel='stylesheet', href=True):
                href = link.get('href', '')
                if href.startswith('http://'):
                    mixed_content_count += 1
                    issues.append(f"Stylesheet loaded via HTTP: {href[:50]}...")
                    severity = "high" if severity != "critical" else severity
            
            if mixed_content_count > 0:
                if severity != "high" and severity != "critical":
                    severity = "medium"
        
        except Exception as e:
            logger.warning(f"⚠️ Error checking HTTPS: {str(e)}")
            is_https = urlparse(url).scheme == 'https'
        
        return {
            'is_https': is_https,
            'mixed_content_count': mixed_content_count,
            'status': 'good' if is_https and mixed_content_count == 0 else ('warning' if is_https else 'error'),
            'issues': issues[:10],  # Limit to first 10 issues
            'severity': severity
        }
    
    def audit_structured_data(self, html: str) -> Dict:
        """
        Check structured data (JSON-LD, Microdata, RDFa).
        
        Args:
            html: HTML content
            
        Returns:
            Dict with audit results
        """
        issues = []
        severity = "low"
        schemas = []
        errors = []
        
        try:
            # Extract structured data
            data = extruct.extract(html, uniform=True)
            
            # Check JSON-LD
            json_ld = data.get('@graph', []) if '@graph' in data else []
            if not json_ld:
                json_ld = data.get('json-ld', [])
            
            for item in json_ld:
                if isinstance(item, dict):
                    # Check for required fields
                    if '@type' not in item:
                        errors.append("JSON-LD missing @type")
                        severity = "high"
                    if '@context' not in item:
                        errors.append("JSON-LD missing @context")
                        if severity != "high":
                            severity = "medium"
                    
                    schema_type = item.get('@type', 'Unknown')
                    schemas.append(schema_type)
            
            # Check for duplicate schemas
            if len(schemas) != len(set(schemas)):
                issues.append("Duplicate structured data types detected")
                if severity != "high":
                    severity = "medium"
            
            # Check Microdata
            microdata = data.get('microdata', [])
            if microdata:
                schemas.extend([item.get('type', 'Unknown') for item in microdata if isinstance(item, dict)])
            
            # Check RDFa
            rdfa = data.get('rdfa', [])
            if rdfa:
                schemas.extend([item.get('@type', 'Unknown') for item in rdfa if isinstance(item, dict) and '@type' in item])
            
            if not schemas:
                issues.append("No structured data found")
                severity = "low"
        
        except Exception as e:
            logger.warning(f"⚠️ Error checking structured data: {str(e)}")
            errors.append(f"Error parsing structured data: {str(e)}")
            severity = "medium"
        
        return {
            'has_structured_data': len(schemas) > 0,
            'schema_types': list(set(schemas)),
            'schema_count': len(schemas),
            'errors': errors,
            'status': 'good' if len(schemas) > 0 and len(errors) == 0 else ('warning' if len(errors) > 0 else 'info'),
            'issues': issues,
            'severity': severity
        }
    
    def audit_page(self, url: str, html: str, status_code: int, headers: Dict, redirect_chain: List[str]) -> Dict:
        """
        Perform all technical SEO audits on a page.
        
        Args:
            url: Page URL
            html: HTML content
            status_code: HTTP status code
            headers: HTTP response headers
            redirect_chain: Redirect chain
            
        Returns:
            Dict with all audit results
        """
        logger.info(f"🔍 Performing technical SEO audit for: {url}")
        
        results = {
            'url': url,
            'noindex': self.audit_noindex(html, headers),
            'meta_robots': self.audit_meta_robots(html, headers),
            'canonical': self.audit_canonical(html, url),
            'redirects': self.audit_redirects(status_code, redirect_chain),
            'https': self.audit_https(url, html),
            'structured_data': self.audit_structured_data(html)
        }
        
        return results

