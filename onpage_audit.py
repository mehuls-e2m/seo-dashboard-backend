"""
On-page SEO audit module: title, meta description, H1, alt text, internal linking.
"""
from bs4 import BeautifulSoup
from typing import Dict, List, Set
import logging
from rapidfuzz import fuzz
import networkx as nx
import re

logger = logging.getLogger(__name__)


class OnPageAuditor:
    """Perform on-page SEO audits on crawled pages."""
    
    def __init__(self):
        self.all_titles: Dict[str, str] = {}  # url -> title
        self.all_descriptions: Dict[str, str] = {}  # url -> description
        self.all_h1s: Dict[str, List[str]] = {}  # url -> [h1 texts]
        self.link_graph = nx.DiGraph()  # For internal linking analysis
    
    def audit_title(self, html: str, url: str) -> Dict:
        """
        Check title tag implementation.
        
        Args:
            html: HTML content
            url: Page URL
            
        Returns:
            Dict with audit results
        """
        issues = []
        severity = "low"
        title_text = ""
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            title_tag = soup.find('title')
            
            if not title_tag:
                issues.append("Missing title tag")
                severity = "critical"
            else:
                title_text = title_tag.get_text().strip()
                self.all_titles[url] = title_text
                
                if not title_text:
                    issues.append("Title tag is empty")
                    severity = "critical"
                else:
                    # Check length
                    length = len(title_text)
                    if length < 30:
                        issues.append(f"Title too short ({length} chars, recommended: 30-70)")
                        severity = "high"
                    elif length > 70:
                        issues.append(f"Title too long ({length} chars, recommended: 30-70)")
                        severity = "medium"
                    
                    # Check for template leakage
                    if any(word in title_text.lower() for word in ['home', 'page', 'untitled', 'new page']):
                        if len(title_text) < 20:
                            issues.append("Title appears to be a template/default")
                            severity = "medium"
        
        except Exception as e:
            logger.warning(f"⚠️ Error checking title: {str(e)}")
        
        return {
            'has_title': bool(title_text),
            'title_text': title_text,
            'title_length': len(title_text),
            'status': 'good' if title_text and 30 <= len(title_text) <= 70 and not issues else ('error' if not title_text else 'warning'),
            'issues': issues,
            'severity': severity
        }
    
    def check_duplicate_titles(self) -> Dict[str, List[str]]:
        """
        Check for duplicate titles across all pages.
        
        Returns:
            Dict mapping title text to list of URLs with that title
        """
        duplicates = {}
        title_to_urls = {}
        
        for url, title in self.all_titles.items():
            if title:
                if title not in title_to_urls:
                    title_to_urls[title] = []
                title_to_urls[title].append(url)
        
        for title, urls in title_to_urls.items():
            if len(urls) > 1:
                duplicates[title] = urls
        
        return duplicates
    
    def audit_meta_description(self, html: str, url: str) -> Dict:
        """
        Check meta description implementation.
        
        Args:
            html: HTML content
            url: Page URL
            
        Returns:
            Dict with audit results
        """
        issues = []
        severity = "low"
        description_text = ""
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            meta_desc = soup.find('meta', attrs={'name': re.compile(r'description', re.I)})
            
            if not meta_desc:
                issues.append("Missing meta description")
                severity = "high"
            else:
                description_text = meta_desc.get('content', '').strip()
                self.all_descriptions[url] = description_text
                
                if not description_text:
                    issues.append("Meta description is empty")
                    severity = "high"
                else:
                    # Check length
                    length = len(description_text)
                    if length < 120:
                        issues.append(f"Meta description too short ({length} chars, recommended: 120-160)")
                        severity = "medium"
                    elif length > 160:
                        issues.append(f"Meta description too long ({length} chars, recommended: 120-160)")
                        severity = "low"
        
        except Exception as e:
            logger.warning(f"⚠️ Error checking meta description: {str(e)}")
        
        return {
            'has_meta_description': bool(description_text),
            'description_text': description_text,
            'description_length': len(description_text),
            'status': 'good' if description_text and 120 <= len(description_text) <= 160 and not issues else ('error' if not description_text else 'warning'),
            'issues': issues,
            'severity': severity
        }
    
    def check_duplicate_descriptions(self) -> Dict[str, List[str]]:
        """
        Check for duplicate meta descriptions across all pages.
        
        Returns:
            Dict mapping description text to list of URLs with that description
        """
        duplicates = {}
        desc_to_urls = {}
        
        for url, desc in self.all_descriptions.items():
            if desc:
                if desc not in desc_to_urls:
                    desc_to_urls[desc] = []
                desc_to_urls[desc].append(url)
        
        for desc, urls in desc_to_urls.items():
            if len(urls) > 1:
                duplicates[desc] = urls
        
        return duplicates
    
    def audit_headings(self, html: str, url: str) -> Dict:
        """
        Check all heading tags (H1-H6) implementation.
        
        Args:
            html: HTML content
            url: Page URL
            
        Returns:
            Dict with audit results for all headings
        """
        issues = []
        severity = "low"
        h1_texts = []
        h2_texts = []
        h3_texts = []
        h4_texts = []
        h5_texts = []
        h6_texts = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            h1_tags = soup.find_all('h1')
            h2_tags = soup.find_all('h2')
            h3_tags = soup.find_all('h3')
            h4_tags = soup.find_all('h4')
            h5_tags = soup.find_all('h5')
            h6_tags = soup.find_all('h6')
            
            # Process H1 tags
            if len(h1_tags) == 0:
                issues.append("No H1 tag found")
                severity = "high"
            elif len(h1_tags) > 1:
                issues.append(f"Multiple H1 tags found ({len(h1_tags)})")
                severity = "medium"
            
            for h1 in h1_tags:
                text = h1.get_text().strip()
                if text:
                    h1_texts.append(text)
            
            self.all_h1s[url] = h1_texts
            
            # Process H2-H6 tags
            for h2 in h2_tags:
                text = h2.get_text().strip()
                if text:
                    h2_texts.append(text)
            
            for h3 in h3_tags:
                text = h3.get_text().strip()
                if text:
                    h3_texts.append(text)
            
            for h4 in h4_tags:
                text = h4.get_text().strip()
                if text:
                    h4_texts.append(text)
            
            for h5 in h5_tags:
                text = h5.get_text().strip()
                if text:
                    h5_texts.append(text)
            
            for h6 in h6_tags:
                text = h6.get_text().strip()
                if text:
                    h6_texts.append(text)
            
            # Check if H1 is identical to title (over-templated)
            if url in self.all_titles:
                title = self.all_titles[url]
                for h1_text in h1_texts:
                    if h1_text.lower() == title.lower():
                        issues.append("H1 is identical to title tag (may indicate over-templating)")
                        if severity != "high" and severity != "medium":
                            severity = "low"
        
        except Exception as e:
            logger.warning(f"⚠️ Error checking headings: {str(e)}")
        
        return {
            'h1_count': len(h1_texts),
            'h1_texts': h1_texts,
            'h2_count': len(h2_texts),
            'h2_texts': h2_texts,
            'h3_count': len(h3_texts),
            'h3_texts': h3_texts,
            'h4_count': len(h4_texts),
            'h4_texts': h4_texts,
            'h5_count': len(h5_texts),
            'h5_texts': h5_texts,
            'h6_count': len(h6_texts),
            'h6_texts': h6_texts,
            'status': 'good' if len(h1_texts) == 1 and not issues else ('error' if len(h1_texts) == 0 else 'warning'),
            'issues': issues,
            'severity': severity
        }
    
    def audit_h1(self, html: str, url: str) -> Dict:
        """
        Check H1 tag implementation (kept for backward compatibility).
        Now uses audit_headings internally.
        
        Args:
            html: HTML content
            url: Page URL
            
        Returns:
            Dict with audit results
        """
        headings_result = self.audit_headings(html, url)
        # Return H1-specific data for backward compatibility
        return {
            'h1_count': headings_result['h1_count'],
            'h1_texts': headings_result['h1_texts'],
            'status': headings_result['status'],
            'issues': headings_result['issues'],
            'severity': headings_result['severity']
        }
    
    def check_duplicate_h1s(self) -> Dict[str, List[str]]:
        """
        Check for duplicate H1s across all pages.
        
        Returns:
            Dict mapping H1 text to list of URLs with that H1
        """
        duplicates = {}
        h1_to_urls = {}
        
        for url, h1_list in self.all_h1s.items():
            for h1_text in h1_list:
                if h1_text:
                    if h1_text not in h1_to_urls:
                        h1_to_urls[h1_text] = []
                    h1_to_urls[h1_text].append(url)
        
        for h1_text, urls in h1_to_urls.items():
            if len(urls) > 1:
                duplicates[h1_text] = urls
        
        return duplicates
    
    def audit_image_alt(self, html: str, url: str = "") -> Dict:
        """
        Check image alt text implementation.
        
        Args:
            html: HTML content
            url: Page URL (for making relative image URLs absolute)
            
        Returns:
            Dict with audit results
        """
        from urllib.parse import urljoin, urlparse
        
        issues = []
        severity = "low"
        images_without_alt = []
        images_with_empty_alt = []
        total_images = 0
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            images = soup.find_all('img')
            total_images = len(images)
            
            # Get base URL for making relative image URLs absolute
            base_url = url if url else ""
            
            for img in images:
                src = img.get('src', '')
                alt = img.get('alt', None)
                
                # Make image URL absolute if relative
                if src:
                    if not src.startswith(('http://', 'https://', 'data:', '//')):
                        if base_url:
                            src = urljoin(base_url, src)
                    elif src.startswith('//'):
                        src = 'https:' + src
                
                # Skip very small images (likely decorative)
                width = img.get('width', '')
                height = img.get('height', '')
                
                if alt is None:
                    images_without_alt.append(src)  # Store full URL, not truncated
                elif alt == '':
                    # Empty alt might be intentional for decorative images
                    # But we'll flag it for review
                    images_with_empty_alt.append(src)  # Store full URL, not truncated
            
            if images_without_alt:
                issues.append(f"{len(images_without_alt)} image(s) missing alt attribute")
                severity = "medium"
            
            if images_with_empty_alt:
                issues.append(f"{len(images_with_empty_alt)} image(s) with empty alt attribute")
                if severity == "low":
                    severity = "low"
        
        except Exception as e:
            logger.warning(f"⚠️ Error checking image alt: {str(e)}")
        
        return {
            'total_images': total_images,
            'images_without_alt': len(images_without_alt),
            'images_without_alt_urls': images_without_alt,  # Store actual image URLs
            'images_with_empty_alt': len(images_with_empty_alt),
            'images_with_empty_alt_urls': images_with_empty_alt,  # Store actual image URLs
            'status': 'good' if len(images_without_alt) == 0 else 'warning',
            'issues': issues,
            'severity': severity
        }
    
    def audit_internal_links(self, html: str, url: str, crawled_urls: Set[str]) -> Dict:
        """
        Check internal linking implementation.
        
        Args:
            html: HTML content
            url: Page URL
            crawled_urls: Set of all crawled URLs
            
        Returns:
            Dict with audit results
        """
        issues = []
        severity = "low"
        internal_links = []
        broken_links = []
        links_to_redirects = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                anchor_text = link.get_text().strip()
                
                # Resolve relative URLs
                from urllib.parse import urljoin
                absolute_url = urljoin(url, href)
                from utils import normalize_url, is_internal_link, get_domain
                
                base_domain = get_domain(url)
                normalized = normalize_url(absolute_url)
                
                if is_internal_link(normalized, base_domain):
                    internal_links.append(normalized)
                    
                    # Add to link graph
                    self.link_graph.add_edge(url, normalized)
                    
                    # Check if link is to a crawled page
                    if normalized in crawled_urls:
                        pass  # Link is valid
                    else:
                        # Could be broken or not crawled yet
                        broken_links.append(normalized)
                    
                    # Check anchor text
                    if not anchor_text:
                        issues.append(f"Link without anchor text: {normalized[:50]}")
            
            # Check for excessive links
            if len(internal_links) > 100:
                issues.append(f"Excessive internal links ({len(internal_links)}, recommended: <100)")
                severity = "low"
            
            if broken_links:
                issues.append(f"{len(broken_links)} potentially broken internal link(s)")
                if severity != "high":
                    severity = "medium"
        
        except Exception as e:
            logger.warning(f"⚠️ Error checking internal links: {str(e)}")
        
        return {
            'internal_link_count': len(internal_links),
            'broken_link_count': len(broken_links),
            'status': 'good' if len(broken_links) == 0 and len(internal_links) > 0 else ('error' if len(broken_links) > 0 else 'warning'),
            'issues': issues[:10],  # Limit to first 10
            'severity': severity
        }
    
    def find_orphan_pages(self, all_urls: Set[str]) -> Set[str]:
        """
        Find pages with no internal in-links (orphans).
        
        Args:
            all_urls: Set of all crawled URLs
            
        Returns:
            Set of orphan page URLs
        """
        orphans = set()
        
        for url in all_urls:
            # Check if URL has any in-links
            if url in self.link_graph:
                in_degree = self.link_graph.in_degree(url)
                if in_degree == 0:
                    orphans.add(url)
            else:
                # URL not in graph at all (no links to or from it)
                orphans.add(url)
        
        return orphans
    
    def audit_page(self, html: str, url: str, crawled_urls: Set[str]) -> Dict:
        """
        Perform all on-page SEO audits on a page.
        
        Args:
            html: HTML content
            url: Page URL
            crawled_urls: Set of all crawled URLs
            
        Returns:
            Dict with all audit results
        """
        # Get headings data (includes H1-H6)
        headings_data = self.audit_headings(html, url)
        
        results = {
            'url': url,
            'title': self.audit_title(html, url),
            'meta_description': self.audit_meta_description(html, url),
            'h1': {
                'h1_count': headings_data['h1_count'],
                'h1_texts': headings_data['h1_texts'],
                'status': headings_data['status'],
                'issues': headings_data['issues'],
                'severity': headings_data['severity']
            },
            'headings': headings_data,  # Include all H1-H6 data
            'image_alt': self.audit_image_alt(html, url),  # Pass URL for absolute image URLs
            'internal_links': self.audit_internal_links(html, url, crawled_urls)
        }
        
        return results

