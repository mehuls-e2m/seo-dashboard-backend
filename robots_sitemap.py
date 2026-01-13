"""
Robots.txt and Sitemap handling module.
"""
import asyncio
import aiohttp
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET
from typing import List, Set, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class RobotsChecker:
    """Handle robots.txt parsing and validation."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.robots_url = urljoin(base_url, '/robots.txt')
        self.parser: Optional[RobotFileParser] = None
        self.robots_exists = False
        
    async def fetch_robots(self, session: aiohttp.ClientSession) -> bool:
        """
        Fetch and parse robots.txt.
        
        Args:
            session: aiohttp session
            
        Returns:
            True if robots.txt exists and is accessible
        """
        try:
            logger.info(f"🔍 Checking robots.txt at: {self.robots_url}")
            async with session.get(self.robots_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    content = await response.text()
                    self.parser = RobotFileParser()
                    self.parser.set_url(self.robots_url)
                    self.parser.read()
                    self.robots_exists = True
                    logger.info("✅ robots.txt found and parsed successfully")
                    return True
                else:
                    logger.warning(f"⚠️ robots.txt returned status {response.status}")
                    return False
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch robots.txt: {str(e)}")
            return False
    
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
        Extract sitemap URLs from robots.txt.
        
        Returns:
            List of sitemap URLs
        """
        if not self.parser:
            return []
        
        try:
            return list(self.parser.site_maps())
        except Exception:
            return []


class SitemapParser:
    """Handle sitemap parsing and URL extraction."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.sitemap_urls: List[str] = []
        self.discovered_urls: Set[str] = set()
        
    async def discover_sitemaps(self, session: aiohttp.ClientSession, robots_checker: RobotsChecker) -> List[str]:
        """
        Discover sitemap URLs from robots.txt and common locations.
        
        Args:
            session: aiohttp session
            robots_checker: RobotsChecker instance
            
        Returns:
            List of sitemap URLs
        """
        sitemaps = []
        
        # Get from robots.txt
        sitemaps.extend(robots_checker.get_sitemap_urls())
        
        # Try common locations
        common_paths = ['/sitemap.xml', '/sitemap_index.xml', '/sitemap1.xml']
        for path in common_paths:
            sitemap_url = urljoin(self.base_url, path)
            sitemaps.append(sitemap_url)
        
        self.sitemap_urls = list(set(sitemaps))
        logger.info(f"📋 Found {len(self.sitemap_urls)} potential sitemap(s)")
        return self.sitemap_urls
    
    async def parse_sitemap(self, session: aiohttp.ClientSession, sitemap_url: str) -> Set[str]:
        """
        Parse a sitemap XML and extract URLs.
        
        Args:
            session: aiohttp session
            sitemap_url: URL of the sitemap
            
        Returns:
            Set of URLs found in sitemap
        """
        urls = set()
        
        try:
            logger.info(f"📄 Parsing sitemap: {sitemap_url}")
            async with session.get(sitemap_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.text()
                    root = ET.fromstring(content)
                    
                    # Handle sitemap index
                    if root.tag.endswith('sitemapindex'):
                        sitemap_locs = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                        for loc in sitemap_locs:
                            if loc.text:
                                # Recursively parse nested sitemaps
                                nested_urls = await self.parse_sitemap(session, loc.text.strip())
                                urls.update(nested_urls)
                    
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
    
    async def get_all_sitemap_urls(self, session: aiohttp.ClientSession, robots_checker: RobotsChecker) -> Set[str]:
        """
        Get all URLs from all discovered sitemaps.
        
        Args:
            session: aiohttp session
            robots_checker: RobotsChecker instance
            
        Returns:
            Set of all URLs from sitemaps
        """
        sitemaps = await self.discover_sitemaps(session, robots_checker)
        all_urls = set()
        
        for sitemap_url in sitemaps:
            urls = await self.parse_sitemap(session, sitemap_url)
            all_urls.update(urls)
        
        self.discovered_urls = all_urls
        logger.info(f"📊 Total URLs discovered from sitemaps: {len(all_urls)}")
        return all_urls


