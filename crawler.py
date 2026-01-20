"""
Async web crawler with rate limiting, retry logic, and robots.txt compliance.
"""
import asyncio
import aiohttp
from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Set, Dict, Optional, List
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime

from utils import normalize_url, get_domain, is_internal_link
from robots_sitemap import RobotsChecker

logger = logging.getLogger(__name__)


class Crawler:
    """Async web crawler with rate limiting and retry logic."""
    
    def __init__(self, base_url: str, max_pages: int = 100, max_concurrent: int = 10, gemini_api_key: Optional[str] = None):
        self.base_url = normalize_url(base_url)
        self.base_domain = get_domain(self.base_url)
        self.max_pages = max_pages
        self.max_concurrent = max_concurrent
        self.respect_robots = True  # Will be set by crawl() method
        self.gemini_api_key = gemini_api_key
        
        self.visited: Set[str] = set()
        self.queue: asyncio.Queue = asyncio.Queue()
        self.results: Dict[str, Dict] = {}
        self.robots_checker: Optional[RobotsChecker] = None
        
        # Rate limiter: 2 requests per second per host
        self.limiter = AsyncLimiter(max_rate=2, time_period=1)
        
        # Statistics
        self.stats = {
            'crawled': 0,
            'failed': 0,
            'blocked_by_robots': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def initialize(self, session: aiohttp.ClientSession, respect_robots: bool = True):
        """
        Initialize crawler with robots.txt check.
        
        Args:
            session: aiohttp session
            respect_robots: If False, will crawl even if blocked by robots.txt (for audit purposes)
        """
        self.robots_checker = RobotsChecker(self.base_url, gemini_api_key=self.gemini_api_key)
        await self.robots_checker.fetch_robots(session)
        
        # Add seed URL to queue
        can_fetch = self.robots_checker.can_fetch(self.base_url) if self.robots_checker.parser else True
        
        if can_fetch:
            await self.queue.put(self.base_url)
        else:
            if respect_robots:
                logger.error("❌ Seed URL is blocked by robots.txt!")
                raise Exception("Cannot crawl: seed URL blocked by robots.txt")
            else:
                await self.queue.put(self.base_url)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def fetch_url(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """
        Fetch a single URL with retry logic.
        
        Args:
            session: aiohttp session
            url: URL to fetch
            
        Returns:
            Dict with response data or None if failed
        """
        async with self.limiter:
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=30),
                    allow_redirects=True,
                    headers={
                        'User-Agent': 'SEO-Audit-Bot/1.0 (Technical SEO Audit Tool)'
                    }
                ) as response:
                    content = await response.text()
                    
                    # Get final URL after redirects
                    final_url = str(response.url)
                    
                    # Get redirect chain
                    redirect_chain = []
                    if response.history:
                        redirect_chain = [str(h.url) for h in response.history]
                        redirect_chain.append(final_url)
                    
                    result = {
                        'url': url,
                        'final_url': final_url,
                        'status_code': response.status,
                        'content': content,
                        'headers': dict(response.headers),
                        'redirect_chain': redirect_chain,
                        'content_type': response.headers.get('Content-Type', ''),
                        'content_length': len(content),
                        'fetch_time': datetime.now().isoformat()
                    }
                    
                    return result
                    
            except asyncio.TimeoutError:
                logger.warning(f"⏱️ Timeout fetching {url}")
                return None
            except Exception as e:
                logger.error(f"❌ Error fetching {url}: {str(e)}")
                return None
    
    def extract_links(self, html: str, base_url: str) -> Set[str]:
        """
        Extract all links from HTML content.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            Set of normalized URLs
        """
        from bs4 import BeautifulSoup
        
        links = set()
        try:
            soup = BeautifulSoup(html, 'lxml')
            for tag in soup.find_all('a', href=True):
                href = tag['href']
                if href:
                    # Resolve relative URLs
                    absolute_url = urljoin(base_url, href)
                    normalized = normalize_url(absolute_url)
                    
                    # Only include internal links
                    if is_internal_link(normalized, self.base_domain):
                        links.add(normalized)
        except Exception as e:
            logger.warning(f"⚠️ Error extracting links: {str(e)}")
        
        return links
    
    async def crawl_worker(self, session: aiohttp.ClientSession):
        """Worker coroutine for crawling URLs from queue."""
        while True:
            try:
                # Get URL from queue with timeout
                url = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                # No more URLs in queue
                break
            
            # Check if we've reached max pages
            if len(self.visited) >= self.max_pages:
                logger.info(f"📊 Reached maximum page limit ({self.max_pages})")
                break
            
            # Skip if already visited
            if url in self.visited:
                self.queue.task_done()
                continue
            
            # Check robots.txt (only if respect_robots is True)
            if self.respect_robots and self.robots_checker and self.robots_checker.parser:
                if not self.robots_checker.can_fetch(url):
                    self.stats['blocked_by_robots'] += 1
                    self.queue.task_done()
                    continue
            
            # Mark as visited
            self.visited.add(url)
            
            # Fetch URL
            result = await self.fetch_url(session, url)
            
            if result:
                self.results[url] = result
                self.stats['crawled'] += 1
                
                # Extract links and add to queue
                if result['status_code'] == 200:
                    links = self.extract_links(result['content'], result['final_url'])
                    for link in links:
                        if link not in self.visited and link not in [q for q in self.queue._queue]:
                            if len(self.visited) + self.queue.qsize() < self.max_pages:
                                await self.queue.put(link)
            else:
                self.stats['failed'] += 1
            
            self.queue.task_done()
            
            # Progress update
            if self.stats['crawled'] % 20 == 0:
                logger.info(f"📈 Progress: {self.stats['crawled']}/{self.max_pages} pages crawled")
    
    async def crawl(self, respect_robots: bool = True) -> Dict[str, Dict]:
        """
        Main crawl method that orchestrates the crawling process.
        
        Args:
            respect_robots: If False, will crawl even if blocked by robots.txt (for audit purposes)
        
        Returns:
            Dict mapping URLs to their crawl results
        """
        self.respect_robots = respect_robots
        self.stats['start_time'] = datetime.now()
        logger.info(f"🕷️ Starting crawl of {self.base_url} (max {self.max_pages} pages)")
        
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            await self.initialize(session, respect_robots=respect_robots)
            
            # Start worker tasks
            workers = [
                asyncio.create_task(self.crawl_worker(session))
                for _ in range(self.max_concurrent)
            ]
            
            # Wait for all workers to complete
            await asyncio.gather(*workers)
            
            # Wait for any remaining queue items
            await self.queue.join()
        
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info(f"✅ Crawl completed!")
        logger.info(f"📊 Statistics:")
        logger.info(f"   - Pages crawled: {self.stats['crawled']}")
        logger.info(f"   - Pages failed: {self.stats['failed']}")
        logger.info(f"   - Blocked by robots: {self.stats['blocked_by_robots']}")
        logger.info(f"   - Duration: {duration:.2f} seconds")
        
        return self.results

