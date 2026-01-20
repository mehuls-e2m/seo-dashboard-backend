"""
Robots.txt and Sitemap handling module.
"""
import asyncio
import aiohttp
import os
import re
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET
from typing import List, Set, Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Try to import google.generativeai, but make it optional
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("⚠️ google-generativeai not installed. Gemini integration disabled. Install with: pip install google-generativeai")


class RobotsChecker:
    """Handle robots.txt parsing and validation."""
    
    def __init__(self, base_url: str, gemini_api_key: Optional[str] = None):
        self.base_url = base_url
        self.robots_url = urljoin(base_url, '/robots.txt')
        self.llms_url = urljoin(base_url, '/llms.txt')
        self.parser: Optional[RobotFileParser] = None
        self.robots_exists = False
        self.robots_content: str = ""
        self.llms_exists = False
        self.llms_content: str = ""
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        self.gemini_enabled = GEMINI_AVAILABLE and self.gemini_api_key is not None
        
        if self.gemini_enabled:
            try:
                genai.configure(api_key=self.gemini_api_key)
            except Exception as e:
                logger.warning(f"⚠️ Failed to configure Gemini API: {str(e)}")
                self.gemini_enabled = False
        
    async def fetch_robots(self, session: aiohttp.ClientSession) -> bool:
        """
        Fetch and parse robots.txt and llms.txt.
        
        Args:
            session: aiohttp session
            
        Returns:
            True if robots.txt exists and is accessible
        """
        robots_fetched = False
        headers = {
            'User-Agent': 'SEO-Audit-Bot/1.0 (Technical SEO Audit Tool)',
            'Accept': 'text/plain, */*'
        }
        try:
            async with session.get(
                self.robots_url,
                timeout=aiohttp.ClientTimeout(total=10),
                headers=headers
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    self.robots_content = content
                    self.parser = RobotFileParser()
                    self.parser.set_url(self.robots_url)
                    self.parser.read()
                    self.robots_exists = True
                    robots_fetched = True
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch robots.txt: {str(e)}")
        
        # Also check for llms.txt
        try:
            async with session.get(
                self.llms_url,
                timeout=aiohttp.ClientTimeout(total=10),
                headers=headers
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    self.llms_content = content
                    self.llms_exists = True
                    logger.info("✅ Found llms.txt")
        except Exception as e:
            # llms.txt is optional, so we don't log a warning
            pass
        
        return robots_fetched
    
    def can_fetch(self, url: str, user_agent: str = '*') -> bool:
        """
        Check if a URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            user_agent: User agent string
            
        Returns:
            True if allowed, False if disallowed
        """
        if not self.parser:
            return True  # Default to allowed if no robots.txt
        
        try:
            return self.parser.can_fetch(user_agent, url)
        except Exception:
            return True
    
    def get_sitemap_urls(self) -> List[str]:
        """
        Extract sitemap URLs from robots.txt using standard parser.
        
        Returns:
            List of sitemap URLs
        """
        if not self.parser:
            return []
        
        try:
            return list(self.parser.site_maps())
        except Exception:
            return []
    
    async def get_sitemap_urls_with_gemini(self) -> List[str]:
        """
        Extract sitemap URLs from robots.txt using Gemini 2.5 Flash model.
        This is more robust and can handle various formats, comments, and edge cases.
        
        Returns:
            List of sitemap URLs extracted by Gemini
        """
        if not self.gemini_enabled:
            logger.warning("⚠️ Gemini not available, falling back to standard parser")
            return self.get_sitemap_urls()
        
        if not self.robots_content:
            logger.warning("⚠️ No robots.txt content available")
            return []
        
        try:
            logger.info("🤖 Using Gemini 2.5 Flash to extract sitemap URLs from robots.txt")
            
            # Prepare prompt for Gemini
            prompt = f"""Analyze the following robots.txt file and extract all sitemap URLs.

robots.txt content:
{self.robots_content}

Instructions:
1. Find all lines that contain "Sitemap:" (case-insensitive)
2. Extract the URLs that follow "Sitemap:"
3. Return ONLY a JSON array of URLs, one per line
4. Do not include any explanations or additional text
5. Handle relative URLs by converting them to absolute URLs using the base domain: {self.base_url}
6. Return empty array [] if no sitemaps found

Example output format:
["https://example.com/sitemap.xml", "https://example.com/sitemap_index.xml"]

Output:"""
            
            # Use Gemini 2.5 Flash model strictly
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            # Parse response
            response_text = response.text.strip()
            
            # Try to extract JSON array from response
            # Handle cases where response might have markdown formatting
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                import json
                try:
                    sitemaps_json = json.loads(json_match.group(0))
                    sitemap_urls = []
                    
                    for url in sitemaps_json:
                        if isinstance(url, str):
                            # Ensure absolute URL
                            if not url.startswith(('http://', 'https://')):
                                url = urljoin(self.base_url, url.lstrip('/'))
                            sitemap_urls.append(url)
                    
                    logger.info(f"✅ Gemini extracted {len(sitemap_urls)} sitemap URL(s)")
                    if sitemap_urls:
                        for idx, url in enumerate(sitemap_urls, 1):
                            logger.info(f"   {idx}. {url}")
                    return sitemap_urls
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Failed to parse Gemini JSON response: {str(e)}")
            
            # Fallback: Try to extract URLs directly from response text
            url_pattern = r'https?://[^\s,\]]+'
            urls = re.findall(url_pattern, response_text)
            if urls:
                logger.info(f"✅ Gemini extracted {len(urls)} sitemap URL(s) (via regex fallback)")
                return urls
            
            logger.warning("⚠️ Gemini response format unexpected, falling back to standard parser")
            return self.get_sitemap_urls()
            
        except Exception as e:
            logger.warning(f"⚠️ Error using Gemini for sitemap extraction: {str(e)}, falling back to standard parser")
            return self.get_sitemap_urls()


class SitemapParser:
    """Handle sitemap parsing and URL extraction."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.sitemap_urls: List[str] = []
        self.discovered_urls: Set[str] = set()
        self.accessed_sitemap_urls: List[str] = []  # Track all successfully accessed sitemap URLs
        self.all_found_sitemap_urls: List[str] = []  # Track all sitemap URLs found (from robots.txt + nested ones)
        
    async def discover_sitemaps_from_robots(self, robots_checker: RobotsChecker) -> List[str]:
        """
        Discover sitemap URLs from robots.txt only.
        Uses Gemini 2.5 Flash to extract from robots.txt if available.
        
        Args:
            robots_checker: RobotsChecker instance
            
        Returns:
            List of sitemap URLs from robots.txt
        """
        sitemaps = []
        
        # Get from robots.txt using Gemini if available, otherwise use standard parser
        if robots_checker.gemini_enabled:
            gemini_sitemaps = await robots_checker.get_sitemap_urls_with_gemini()
            sitemaps.extend(gemini_sitemaps)
        else:
            sitemaps.extend(robots_checker.get_sitemap_urls())
        
        self.sitemap_urls = list(set(sitemaps))
        logger.info(f"📋 Found {len(self.sitemap_urls)} sitemap URL(s) from robots.txt")
        return self.sitemap_urls
    
    async def parse_sitemap(self, session: aiohttp.ClientSession, sitemap_url: str) -> Set[str]:
        """
        Parse a sitemap XML and extract URLs.
        Tracks successfully accessed sitemap URLs and discovers nested sitemap URLs from sitemap indexes.
        
        Args:
            session: aiohttp session
            sitemap_url: URL of the sitemap
            
        Returns:
            Set of URLs found in sitemap
        """
        urls = set()
        
        try:
            async with session.get(
                sitemap_url,
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'SEO-Audit-Bot/1.0 (Technical SEO Audit Tool)',
                    'Accept': 'application/xml, text/xml, */*',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            ) as response:
                if response.status == 200:
                    # Track this sitemap as successfully accessed
                    if sitemap_url not in self.accessed_sitemap_urls:
                        self.accessed_sitemap_urls.append(sitemap_url)
                    
                    # Track all found sitemap URLs
                    if sitemap_url not in self.all_found_sitemap_urls:
                        self.all_found_sitemap_urls.append(sitemap_url)
                    
                    content = await response.text()
                    root = ET.fromstring(content)
                    
                    # Handle sitemap index
                    if root.tag.endswith('sitemapindex'):
                        sitemap_locs = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                        nested_sitemap_urls = []
                        for loc in sitemap_locs:
                            if loc.text:
                                nested_sitemap_url = loc.text.strip()
                                nested_sitemap_urls.append(nested_sitemap_url)
                                # Track nested sitemap URLs found
                                if nested_sitemap_url not in self.all_found_sitemap_urls:
                                    self.all_found_sitemap_urls.append(nested_sitemap_url)
                                # Recursively parse nested sitemaps
                                nested_urls = await self.parse_sitemap(session, nested_sitemap_url)
                                urls.update(nested_urls)
                        
                        if nested_sitemap_urls:
                            logger.info(f"📋 Found {len(nested_sitemap_urls)} nested sitemap(s) in {sitemap_url}")
                    
                    # Handle regular sitemap
                    elif root.tag.endswith('urlset'):
                        url_locs = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                        for loc in url_locs:
                            if loc.text:
                                urls.add(loc.text.strip())
                    
                    logger.info(f"✅ Extracted {len(urls)} URLs from {sitemap_url}")
                else:
                    logger.warning(f"⚠️ Sitemap {sitemap_url} returned status {response.status}")
        except ET.ParseError as e:
            logger.error(f"❌ Error parsing sitemap XML {sitemap_url}: {str(e)}")
        except Exception as e:
            logger.warning(f"⚠️ Could not parse sitemap {sitemap_url}: {str(e)}")
        
        return urls
    
    async def get_all_sitemap_urls(self, session: aiohttp.ClientSession, robots_checker: RobotsChecker) -> Dict:
        """
        Get all URLs from sitemaps following the flow:
        1. First, find sitemap URLs from robots.txt using Gemini (or standard parser)
        2. Then visit those sitemaps and retrieve all nested sitemap URLs from sitemap indexes
        3. Collect all sitemap URLs found (from robots.txt + all nested ones discovered)
        
        Args:
            session: aiohttp session
            robots_checker: RobotsChecker instance
            
        Returns:
            Dictionary with:
            - 'urls': Set of all URLs from sitemaps
            - 'all_sitemap_urls': List of all sitemap URLs found (from robots.txt + all nested ones)
            - 'accessed_sitemap_urls': List of all successfully accessed sitemap URLs (including nested ones)
            - 'total_links_count': Total number of links found in all sitemaps
        """
        # Reset tracking lists for this run
        self.accessed_sitemap_urls = []
        self.all_found_sitemap_urls = []
        
        # Step 1: Get sitemap URLs from robots.txt using Gemini (or standard parser)
        logger.info("🔍 Step 1: Extracting sitemap URLs from robots.txt...")
        robots_sitemaps = await self.discover_sitemaps_from_robots(robots_checker)
        
        if not robots_sitemaps:
            logger.warning("⚠️ No sitemap URLs found in robots.txt")
            return {
                'urls': set(),
                'all_sitemap_urls': [],
                'accessed_sitemap_urls': [],
                'total_links_count': 0
            }
        
        # Step 2: Visit each sitemap from robots.txt and extract URLs (including nested sitemaps)
        logger.info(f"🔍 Step 2: Visiting {len(robots_sitemaps)} sitemap(s) from robots.txt to retrieve all nested sitemap URLs...")
        all_urls = set()
        
        for sitemap_url in robots_sitemaps:
            urls = await self.parse_sitemap(session, sitemap_url)
            all_urls.update(urls)
        
        self.discovered_urls = all_urls
        total_links_count = len(all_urls)
        
        logger.info(f"📊 Total URLs discovered from sitemaps: {total_links_count}")
        logger.info(f"📋 Found {len(self.all_found_sitemap_urls)} total sitemap URL(s) (from robots.txt + nested ones):")
        for idx, sitemap_url in enumerate(self.all_found_sitemap_urls, 1):
            status = "✅" if sitemap_url in self.accessed_sitemap_urls else "❌"
            logger.info(f"   {idx}. {status} {sitemap_url}")
        
        return {
            'urls': all_urls,
            'all_sitemap_urls': self.all_found_sitemap_urls,  # All sitemap URLs found (robots.txt + nested)
            'accessed_sitemap_urls': self.accessed_sitemap_urls,  # Only successfully accessed
            'total_links_count': total_links_count
        }


