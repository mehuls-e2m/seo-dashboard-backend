"""
Audit service that wraps the existing SEO audit logic
"""
import sys
import os
import logging
import aiohttp
from typing import Dict, Set, Optional
from datetime import datetime
import time

# Add parent directory to path to import existing modules
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from crawler import Crawler
from technical_audit import TechnicalAuditor
from onpage_audit import OnPageAuditor
from rule_engine import RuleEngine
from robots_sitemap import SitemapParser
from API.services.output_generator import APIOutputGenerator

# Import API modules
try:
    from API.core.config import settings
except ImportError:
    # Fallback if running from different path
    import sys
    import os
    api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if api_dir not in sys.path:
        sys.path.insert(0, api_dir)
    from API.core.config import settings

logger = logging.getLogger(__name__)


class AuditService:
    """Service for performing SEO audits"""
    
    def __init__(self):
        self.max_pages_default = 9999  # Default number of pages to crawl when max_pages is not provided
        
    async def perform_audit(
        self,
        base_url: str,
        max_pages: Optional[int] = None,
        respect_robots: bool = False
    ) -> Dict:
        """
        Perform complete SEO audit on a website.
        
        Args:
            base_url: Website URL to audit
            max_pages: Maximum number of pages to crawl (None = crawl all)
            respect_robots: Whether to respect robots.txt (default: False for comprehensive audits)
            
        Returns:
            Dictionary containing audit_stats and audit_issues
        """
        start_time = time.time()
        
        # Normalize URL
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'https://' + base_url
        
        # Set max_pages to large number if not provided (to crawl all pages)
        if max_pages is None:
            max_pages = self.max_pages_default
            logger.info(f"No max_pages specified, setting to {max_pages} (crawl all pages)")
        
        # Initialize components
        logger.info(f"🔧 Initializing components for {base_url}")
        crawler = Crawler(
            base_url,
            max_pages=max_pages,
            max_concurrent=10,
            gemini_api_key=settings.gemini_api_key
        )
        technical_auditor = TechnicalAuditor(base_url)
        onpage_auditor = OnPageAuditor()
        rule_engine = RuleEngine()
        output_generator = APIOutputGenerator(base_url)
        
        # Store crawlability info - EXACTLY matching main.py initialization
        crawlability_info = {
            'robots_txt_exists': False,
            'sitemap_exists': False,
            'sitemap_urls': [],
            'all_sitemap_urls': [],  # All discovered sitemap URLs (whether accessible or not)
            'accessed_sitemap_urls': [],
            'total_sitemap_links_count': 0
        }
        
        try:
            # Step 1: Crawl website
            logger.info(f"🕷️ Starting crawl of {base_url} (max {max_pages} pages)")
            crawl_results = await crawler.crawl(respect_robots=respect_robots)
            
            if not crawl_results:
                raise Exception("No pages were crawled. Please check the URL and try again.")
            
            logger.info(f"✅ Crawled {len(crawl_results)} pages")
            
            # Capture crawlability info - EXACTLY matching main.py logic
            if crawler.robots_checker:
                crawlability_info['robots_txt_exists'] = crawler.robots_checker.robots_exists
                
                # Include robots.txt content if it exists
                if crawler.robots_checker.robots_exists:
                    crawlability_info['robots_txt_content'] = crawler.robots_checker.robots_content
                
                # Check for llms.txt
                crawlability_info['llms_txt_exists'] = crawler.robots_checker.llms_exists
                
                # Include llms.txt content if it exists
                if crawler.robots_checker.llms_exists:
                    crawlability_info['llms_txt_content'] = crawler.robots_checker.llms_content
                
                # Extract sitemap URLs from robots.txt - EXACTLY as in main.py
                logger.info("🔍 Extracting sitemap URLs from robots.txt...")
                if crawler.robots_checker.gemini_enabled:
                    sitemap_urls_from_robots = await crawler.robots_checker.get_sitemap_urls_with_gemini()
                else:
                    sitemap_urls_from_robots = crawler.robots_checker.get_sitemap_urls()
                
                logger.info(f"📋 Found {len(sitemap_urls_from_robots)} sitemap URL(s) from robots.txt: {sitemap_urls_from_robots}")
                crawlability_info['sitemap_urls_from_robots'] = sitemap_urls_from_robots
                
                # Check for sitemap and get URLs from sitemap files - EXACTLY as in main.py
                logger.info("🔍 Checking sitemap files and common locations...")
                try:
                    async with aiohttp.ClientSession() as session:
                        sitemap_parser = SitemapParser(base_url)
                        sitemap_result = await sitemap_parser.get_all_sitemap_urls(session, crawler.robots_checker)
                        sitemap_urls = sitemap_result['urls']  # URLs extracted from sitemaps
                        all_sitemap_urls = sitemap_result['all_sitemap_urls']  # All discovered sitemap URLs
                        accessed_sitemap_urls = sitemap_result['accessed_sitemap_urls']  # All accessed sitemap URLs
                        total_links_count = sitemap_result['total_links_count']  # Total number of links
                        
                        logger.info(f"📊 Extracted {total_links_count} URLs from {len(accessed_sitemap_urls)} accessible sitemap file(s) out of {len(all_sitemap_urls)} found")
                        crawlability_info['sitemap_exists'] = len(sitemap_urls) > 0 or len(sitemap_urls_from_robots) > 0
                        crawlability_info['sitemap_urls'] = list(sitemap_urls)[:10]  # Limit to first 10 (URLs from within sitemaps)
                        crawlability_info['all_sitemap_urls'] = all_sitemap_urls  # All discovered sitemap URLs (whether accessible or not)
                        crawlability_info['accessed_sitemap_urls'] = accessed_sitemap_urls  # All accessed sitemap URLs
                        crawlability_info['total_sitemap_links_count'] = total_links_count  # Total links from all sitemaps
                        logger.info(f"✅ Sitemap detection complete: exists={crawlability_info['sitemap_exists']}, from_robots={len(sitemap_urls_from_robots)}, all_found={len(all_sitemap_urls)}, accessed={len(accessed_sitemap_urls)}, total_links={total_links_count}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not check sitemap: {str(e)}", exc_info=True)
                    crawlability_info['sitemap_exists'] = len(sitemap_urls_from_robots) > 0
                    crawlability_info['all_sitemap_urls'] = sitemap_urls_from_robots  # Use robots.txt sitemaps as fallback
                    crawlability_info['accessed_sitemap_urls'] = []
                    crawlability_info['total_sitemap_links_count'] = 0
                    logger.info(f"⚠️ Sitemap detection fallback: exists={crawlability_info['sitemap_exists']} (based on robots.txt only)")
            
            # Step 2: Perform audits
            all_results = []
            crawled_urls = set(crawl_results.keys())
            
            logger.info("🔍 Performing audits on crawled pages...")
            for url, crawl_data in crawl_results.items():
                # Technical audit
                technical_results = technical_auditor.audit_page(
                    url=url,
                    html=crawl_data['content'],
                    status_code=crawl_data['status_code'],
                    headers=crawl_data['headers'],
                    redirect_chain=crawl_data.get('redirect_chain', [])
                )
                
                # On-page audit
                onpage_results = onpage_auditor.audit_page(
                    html=crawl_data['content'],
                    url=url,
                    crawled_urls=crawled_urls
                )
                
                # Calculate score
                score_results = rule_engine.calculate_page_score(technical_results, onpage_results)
                
                # Combine results
                page_result = {
                    'url': url,
                    'status_code': crawl_data['status_code'],
                    'technical': technical_results,
                    'onpage': onpage_results,
                    'score': score_results,
                    'html_content': crawl_data['content'],  # Include HTML for additional SEO analysis
                    'headers': crawl_data.get('headers', {}),  # Include headers for caching/compression/CDN analysis
                    'server_response_time_ms': crawl_data.get('server_response_time_ms')  # Include server response time
                }
                
                all_results.append(page_result)
            
            # Step 3: Check for duplicates and orphans
            logger.info("🔍 Checking for duplicates and orphan pages...")
            duplicate_titles = onpage_auditor.check_duplicate_titles()
            duplicate_descriptions = onpage_auditor.check_duplicate_descriptions()
            duplicate_h1s = onpage_auditor.check_duplicate_h1s()
            orphan_pages = onpage_auditor.find_orphan_pages(crawled_urls)
            
            # Add duplicate/orphan info to results
            for result in all_results:
                url = result['url']
                if url in orphan_pages:
                    result['score']['issues'].append({
                        'category': 'On-Page',
                        'type': 'Internal Links',
                        'severity': 'high',
                        'message': 'Orphan page (no internal in-links)',
                        'weight': -15
                    })
                    result['score']['score'] = max(0, result['score']['score'] - 15)
                    result['score']['high_count'] += 1
                    result['score']['issue_count'] += 1
            
            # Step 4: Calculate site-wide statistics
            logger.info("📊 Calculating site-wide statistics...")
            site_stats = rule_engine.calculate_site_score(all_results)
            
            # Step 5: Generate audit data using API-specific output generator
            audit_stats = output_generator.generate_audit_stats(
                all_results, site_stats, crawlability_info,
                duplicate_titles, duplicate_descriptions, duplicate_h1s, orphan_pages
            )
            
            audit_issues = output_generator.generate_audit_issues(
                all_results, site_stats, crawlability_info,
                duplicate_titles, duplicate_descriptions, duplicate_h1s, orphan_pages
            )
            
            execution_time = time.time() - start_time
            
            logger.info(f"✅ Audit complete! (Execution time: {execution_time:.2f}s)")
            
            return {
                'audit_stats': audit_stats,
                'audit_issues': audit_issues,
                'execution_time': execution_time
            }
            
        except Exception as e:
            logger.error(f"❌ Error during audit: {str(e)}", exc_info=True)
            raise

