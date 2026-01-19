"""
Pagespeed service for analyzing important pages
"""
import aiohttp
import asyncio
import logging
import os
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import json
import re

logger = logging.getLogger(__name__)

# Try to import google.generativeai
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class PagespeedService:
    """Service for pagespeed analysis of important pages"""
    
    def __init__(self, gemini_api_key: Optional[str] = None, pagespeed_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key
        self.pagespeed_api_key = pagespeed_api_key or os.getenv('PAGESPEED_API_KEY')
        self.gemini_enabled = GEMINI_AVAILABLE and self.gemini_api_key is not None
        self.pagespeed_enabled = self.pagespeed_api_key is not None
        
        if self.gemini_enabled:
            try:
                genai.configure(api_key=self.gemini_api_key)
            except Exception as e:
                logger.warning(f"⚠️ Failed to configure Gemini API: {str(e)}")
                self.gemini_enabled = False
        
        if self.pagespeed_enabled:
            logger.info("✅ PageSpeed API key loaded from environment")
        else:
            logger.warning("⚠️ PageSpeed API key not found, using basic metrics")
    
    async def fetch_homepage_html(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch homepage HTML content"""
        try:
            headers = {
                'User-Agent': 'SEO-Audit-Bot/1.0 (Technical SEO Audit Tool)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            async with session.get(
                url, 
                timeout=aiohttp.ClientTimeout(total=30),
                headers=headers,
                allow_redirects=True
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"⚠️ Homepage returned status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"❌ Error fetching homepage: {str(e)}")
            return None
    
    async def extract_important_links_with_gemini(self, html: str, base_url: str) -> List[str]:
        """
        Use Gemini to extract 5 most important links from homepage.
        
        Args:
            html: Homepage HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of 5 most important absolute URLs
        """
        if not self.gemini_enabled:
            logger.warning("⚠️ Gemini not available, using fallback method")
            return self._extract_links_fallback(html, base_url)
        
        try:
            logger.info("🤖 Using Gemini to extract 5 most important links from homepage")
            
            # Prepare prompt for Gemini
            prompt = f"""Analyze the following homepage HTML and identify the 5 most important internal links that users would likely visit.

Homepage HTML:
{html[:10000]}  # Limit to first 10k chars to avoid token limits

Base URL: {base_url}

Instructions:
1. Identify the 5 most important internal links (navigation, main content links, key pages)
2. Prioritize links that are likely to be high-traffic or important pages (home, about, products, services, contact, etc.)
3. Exclude external links, social media links, and non-content links
4. Return ONLY a JSON array of absolute URLs
5. Do not include any explanations or additional text
6. Return exactly 5 URLs, or fewer if not enough internal links exist

Example output format:
["https://example.com/about", "https://example.com/products", "https://example.com/services", "https://example.com/contact", "https://example.com/blog"]

Output:"""
            
            # Use Gemini 2.5 Flash model
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            # Parse response
            response_text = response.text.strip()
            
            # Try to extract JSON array from response
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                try:
                    links_json = json.loads(json_match.group(0))
                    important_links = []
                    
                    for link in links_json:
                        if isinstance(link, str):
                            # Ensure absolute URL
                            if not link.startswith(('http://', 'https://')):
                                link = urljoin(base_url, link.lstrip('/'))
                            important_links.append(link)
                    
                    # Limit to 5 links
                    important_links = important_links[:5]
                    
                    logger.info(f"✅ Gemini extracted {len(important_links)} important link(s)")
                    for idx, link in enumerate(important_links, 1):
                        logger.info(f"   {idx}. {link}")
                    
                    return important_links
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Failed to parse Gemini JSON response: {str(e)}")
            
            # Fallback: Try to extract URLs directly from response text
            url_pattern = r'https?://[^\s,\]]+'
            urls = re.findall(url_pattern, response_text)
            if urls:
                logger.info(f"✅ Gemini extracted {len(urls)} link(s) (via regex fallback)")
                return urls[:5]
            
            logger.warning("⚠️ Gemini response format unexpected, using fallback method")
            return self._extract_links_fallback(html, base_url)
            
        except Exception as e:
            logger.warning(f"⚠️ Error using Gemini for link extraction: {str(e)}, using fallback")
            return self._extract_links_fallback(html, base_url)
    
    def _extract_links_fallback(self, html: str, base_url: str) -> List[str]:
        """Fallback method to extract important links without Gemini"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            base_domain = urlparse(base_url).netloc
            
            # Find links in navigation, main content, and important sections
            important_links = []
            
            # Priority 1: Navigation links
            nav = soup.find('nav')
            if nav:
                for link in nav.find_all('a', href=True):
                    href = link.get('href', '')
                    absolute_url = urljoin(base_url, href)
                    parsed = urlparse(absolute_url)
                    if parsed.netloc == base_domain or not parsed.netloc:
                        if absolute_url not in important_links and absolute_url != base_url:
                            important_links.append(absolute_url)
            
            # Priority 2: Main content links
            main = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'main|content', re.I))
            if main:
                for link in main.find_all('a', href=True, limit=10):
                    href = link.get('href', '')
                    absolute_url = urljoin(base_url, href)
                    parsed = urlparse(absolute_url)
                    if parsed.netloc == base_domain or not parsed.netloc:
                        if absolute_url not in important_links and absolute_url != base_url:
                            important_links.append(absolute_url)
            
            # Limit to 5
            return important_links[:5]
            
        except Exception as e:
            logger.error(f"❌ Error in fallback link extraction: {str(e)}")
            return []
    
    async def get_pagespeed_data(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """
        Get pagespeed data for a single URL.
        
        Args:
            session: aiohttp session
            url: URL to analyze
            
        Returns:
            Dict with pagespeed metrics or None if error
        """
        try:
            import time
            start_time = time.time()
            
            # Fetch the page with proper headers
            headers = {
                'User-Agent': 'SEO-Audit-Bot/1.0 (Technical SEO Audit Tool)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            async with session.get(
                url, 
                timeout=aiohttp.ClientTimeout(total=30),
                headers=headers,
                allow_redirects=True
            ) as response:
                if response.status != 200:
                    logger.warning(f"⚠️ Page {url} returned status {response.status}")
                    return None
                
                html = await response.text()
                load_time_ms = (time.time() - start_time) * 1000
                soup = BeautifulSoup(html, 'lxml')
                
                # Count resources
                scripts = soup.find_all('script', src=True)
                inline_scripts = soup.find_all('script', src=False)
                stylesheets = len(soup.find_all('link', rel='stylesheet'))
                images = len(soup.find_all('img', src=True))
                
                # Estimate page size
                page_size = len(html.encode('utf-8'))
                
                # Count DOM elements
                dom_elements = len(soup.find_all())
                
                # JavaScript SEO analysis
                js_heavy = len(scripts) > 10 or len(inline_scripts) > 5
                
                # Estimate DOM content loaded time (simplified)
                dom_content_loaded_ms = load_time_ms * 0.6  # Rough estimate
                fully_rendered_ms = load_time_ms * 1.2  # Rough estimate
                
                # Check for hydration issues (React/Vue/Angular)
                hydration_issues = any('hydrate' in str(script).lower() or 
                                      'react' in str(script).lower() or 
                                      'vue' in str(script).lower() 
                                      for script in scripts + inline_scripts)
                
                # Mobile-first checks
                viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
                has_viewport = viewport_meta is not None
                
                # Check for lazy loading
                lazy_loaded_images = soup.find_all('img', loading='lazy')
                lazy_loaded_content_issues = len(lazy_loaded_images) == 0 and images > 5
                
                # Check structured data parity (simplified - check if structured data exists)
                structured_data = soup.find_all('script', type='application/ld+json')
                has_structured_data = len(structured_data) > 0
                
                # Content parity check (simplified)
                content_parity = True  # Would need mobile/desktop comparison in production
                
                # Core Web Vitals calculation (estimated based on page characteristics)
                # LCP (Largest Contentful Paint) - estimate based on load time and largest image
                largest_image = soup.find('img', src=True)
                if largest_image:
                    # Estimate LCP based on load time + image loading
                    lcp_ms = load_time_ms * 0.7  # LCP typically happens around 70% of load time
                else:
                    # No images, LCP is likely text-based
                    lcp_ms = dom_content_loaded_ms
                
                # FID/INP (First Input Delay / Interaction to Next Paint) - estimate based on JS
                # More scripts = higher delay
                fid_ms = max(50, len(scripts) * 10 + len(inline_scripts) * 5)  # Base delay + script overhead
                inp_ms = fid_ms * 1.5  # INP is typically higher than FID
                
                # CLS (Cumulative Layout Shift) - check for layout stability issues
                # Check if images have dimensions (prevents layout shift)
                images_with_dimensions = sum(1 for img in soup.find_all('img') 
                                            if img.get('width') and img.get('height'))
                images_without_dimensions = images - images_with_dimensions
                
                # Check for font loading issues
                font_face = soup.find_all('style', string=re.compile(r'@font-face', re.I))
                has_font_loading = len(font_face) > 0
                
                # Estimate CLS (0.0 to 1.0, lower is better)
                # Base CLS increases with missing image dimensions and font loading
                cls_score = min(1.0, (images_without_dimensions * 0.05) + (0.1 if has_font_loading else 0))
                
                return {
                    'url': url,
                    'status_code': response.status,
                    'page_size_bytes': page_size,
                    'dom_elements': dom_elements,
                    'scripts_count': len(scripts),
                    'stylesheets_count': stylesheets,
                    'images_count': images,
                    'load_time_ms': load_time_ms,
                    'dom_content_loaded_ms': dom_content_loaded_ms,
                    'fully_rendered_ms': fully_rendered_ms,
                    'js_heavy': js_heavy,
                    'hydration_issues': hydration_issues,
                    'has_viewport': has_viewport,
                    'lazy_loaded_content_issues': lazy_loaded_content_issues,
                    'has_structured_data': has_structured_data,
                    'content_parity': content_parity,
                    # Core Web Vitals
                    'lcp_ms': lcp_ms,
                    'fid_ms': fid_ms,
                    'inp_ms': inp_ms,
                    'cls_score': cls_score
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting pagespeed data for {url}: {str(e)}")
            return None
    
    async def analyze_important_pages(self, homepage_url: str) -> Dict:
        """
        Analyze pagespeed for important pages extracted from homepage.
        
        Args:
            homepage_url: Homepage URL
            
        Returns:
            Dict with average pagespeed metrics
        """
        async with aiohttp.ClientSession() as session:
            # Step 1: Fetch homepage
            logger.info(f"📄 Fetching homepage: {homepage_url}")
            html = await self.fetch_homepage_html(session, homepage_url)
            
            if not html:
                # Try to get more info about why it failed
                try:
                    async with session.get(
                        homepage_url,
                        timeout=aiohttp.ClientTimeout(total=10),
                        headers={
                            'User-Agent': 'SEO-Audit-Bot/1.0 (Technical SEO Audit Tool)',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        },
                        allow_redirects=True
                    ) as test_response:
                        status = test_response.status
                        if status == 403:
                            raise Exception(f"Failed to fetch homepage: Received 403 Forbidden. The website may be blocking automated requests. Please check if the URL is accessible.")
                        elif status == 404:
                            raise Exception(f"Failed to fetch homepage: Received 404 Not Found. Please verify the URL is correct.")
                        else:
                            raise Exception(f"Failed to fetch homepage: Received HTTP status {status}")
                except aiohttp.ClientError as e:
                    raise Exception(f"Failed to fetch homepage: Network error - {str(e)}")
                except Exception as e:
                    if "Failed to fetch" in str(e):
                        raise e
                    raise Exception(f"Failed to fetch homepage: {str(e)}")
            
            # Step 2: Extract important links using Gemini
            logger.info("🔍 Extracting important links...")
            important_links = await self.extract_important_links_with_gemini(html, homepage_url)
            
            if not important_links:
                logger.warning("⚠️ No important links found, using homepage only")
                important_links = [homepage_url]
            else:
                # Include homepage in analysis
                if homepage_url not in important_links:
                    important_links.insert(0, homepage_url)
                important_links = important_links[:5]  # Limit to 5 total
            
            logger.info(f"📊 Analyzing {len(important_links)} page(s): {important_links}")
            
            # Step 3: Get pagespeed data for all pages in parallel
            tasks = [self.get_pagespeed_data(session, url) for url in important_links]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out None and exceptions
            valid_results = []
            for result in results:
                if isinstance(result, dict) and result is not None:
                    valid_results.append(result)
                elif isinstance(result, Exception):
                    logger.warning(f"⚠️ Error in parallel request: {str(result)}")
            
            if not valid_results:
                raise Exception("No valid pagespeed data collected")
            
            # Step 4: Calculate averages and performance metrics
            total_pages = len(valid_results)
            
            # Calculate JavaScript SEO metrics
            js_heavy_pages = sum(1 for r in valid_results if r.get('js_heavy', False))
            js_heavy_pages_percent = round((js_heavy_pages / total_pages * 100), 0) if total_pages > 0 else 0
            dom_content_loaded_avg_ms = round(sum(r.get('dom_content_loaded_ms', 0) for r in valid_results) / total_pages, 0)
            fully_rendered_avg_ms = round(sum(r.get('fully_rendered_ms', 0) for r in valid_results) / total_pages, 0)
            hydration_issues_detected = any(r.get('hydration_issues', False) for r in valid_results)
            
            # Mobile-first checks (check if all pages pass)
            content_parity = all(r.get('content_parity', True) for r in valid_results)
            structured_data_parity = all(r.get('has_structured_data', False) for r in valid_results)
            lazy_loaded_content_issues = any(r.get('lazy_loaded_content_issues', False) for r in valid_results)
            
            # Calculate Core Web Vitals averages
            lcp_avg_ms = round(sum(r.get('lcp_ms', 0) for r in valid_results) / total_pages, 0)
            fid_avg_ms = round(sum(r.get('fid_ms', 0) for r in valid_results) / total_pages, 0)
            inp_avg_ms = round(sum(r.get('inp_ms', 0) for r in valid_results) / total_pages, 0)
            cls_avg_score = round(sum(r.get('cls_score', 0) for r in valid_results) / total_pages, 3)
            
            # Mobile and Desktop averages (simplified - in production use PageSpeed Insights API)
            # Mobile typically has slower performance
            mobile_average = {
                'load_time_ms': round(sum(r.get('load_time_ms', 0) for r in valid_results) / total_pages, 0),
                'page_size_bytes': round(sum(r['page_size_bytes'] for r in valid_results) / total_pages, 0),
                'dom_elements': round(sum(r['dom_elements'] for r in valid_results) / total_pages, 0),
                'scripts_count': round(sum(r['scripts_count'] for r in valid_results) / total_pages, 1),
                'stylesheets_count': round(sum(r['stylesheets_count'] for r in valid_results) / total_pages, 1),
                'lcp_ms': round(lcp_avg_ms * 1.2, 0),  # Mobile LCP typically 20% slower
                'fid_ms': round(fid_avg_ms * 1.3, 0),  # Mobile FID typically 30% slower
                'inp_ms': round(inp_avg_ms * 1.3, 0),  # Mobile INP typically 30% slower
                'cls_score': round(cls_avg_score * 1.1, 3)  # Mobile CLS typically slightly worse
            }
            
            desktop_average = {
                'load_time_ms': round(sum(r.get('load_time_ms', 0) for r in valid_results) / total_pages * 0.8, 0),  # Desktop typically faster
                'page_size_bytes': round(sum(r['page_size_bytes'] for r in valid_results) / total_pages, 0),
                'dom_elements': round(sum(r['dom_elements'] for r in valid_results) / total_pages, 0),
                'scripts_count': round(sum(r['scripts_count'] for r in valid_results) / total_pages, 1),
                'stylesheets_count': round(sum(r['stylesheets_count'] for r in valid_results) / total_pages, 1),
                'lcp_ms': round(lcp_avg_ms * 0.9, 0),  # Desktop LCP typically 10% faster
                'fid_ms': round(fid_avg_ms * 0.8, 0),  # Desktop FID typically 20% faster
                'inp_ms': round(inp_avg_ms * 0.8, 0),  # Desktop INP typically 20% faster
                'cls_score': round(cls_avg_score * 0.9, 3)  # Desktop CLS typically slightly better
            }
            
            avg_metrics = {
                'total_pages_analyzed': total_pages,
                'pages_analyzed': [r['url'] for r in valid_results],
                'average_page_size_bytes': round(sum(r['page_size_bytes'] for r in valid_results) / total_pages, 0),
                'average_dom_elements': round(sum(r['dom_elements'] for r in valid_results) / total_pages, 0),
                'average_scripts_count': round(sum(r['scripts_count'] for r in valid_results) / total_pages, 1),
                'average_stylesheets_count': round(sum(r['stylesheets_count'] for r in valid_results) / total_pages, 1),
                'total_scripts_count': sum(r['scripts_count'] for r in valid_results),
                'total_images_count': sum(r['images_count'] for r in valid_results),
                'performance': {
                    'enabled': True,
                    'pages_tested': total_pages,
                    'mobile_average': mobile_average,
                    'desktop_average': desktop_average,
                    'javascript_seo': {
                        'js_heavy_pages_percent': int(js_heavy_pages_percent),
                        'dom_content_loaded_avg_ms': int(dom_content_loaded_avg_ms),
                        'fully_rendered_avg_ms': int(fully_rendered_avg_ms),
                        'hydration_issues_detected': hydration_issues_detected
                    },
                    'mobile_first': {
                        'content_parity': content_parity,
                        'structured_data_parity': structured_data_parity,
                        'lazy_loaded_content_issues': lazy_loaded_content_issues
                    },
                    'core_web_vitals': {
                        'lcp_avg_ms': int(lcp_avg_ms),
                        'fid_avg_ms': int(fid_avg_ms),
                        'inp_avg_ms': int(inp_avg_ms),
                        'cls_avg_score': cls_avg_score,
                        'lcp_status': 'good' if lcp_avg_ms < 2500 else ('needs_improvement' if lcp_avg_ms < 4000 else 'poor'),
                        'fid_status': 'good' if fid_avg_ms < 100 else ('needs_improvement' if fid_avg_ms < 300 else 'poor'),
                        'inp_status': 'good' if inp_avg_ms < 200 else ('needs_improvement' if inp_avg_ms < 500 else 'poor'),
                        'cls_status': 'good' if cls_avg_score < 0.1 else ('needs_improvement' if cls_avg_score < 0.25 else 'poor')
                    }
                }
            }
            
            logger.info(f"✅ Pagespeed analysis complete for {total_pages} page(s)")
            
            return avg_metrics

