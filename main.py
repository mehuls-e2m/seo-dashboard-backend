"""
Main entry point for SEO Audit System.
"""
import asyncio
import logging
import sys
import aiohttp
from typing import Dict, Set
from dotenv import load_dotenv

from crawler import Crawler
from technical_audit import TechnicalAuditor
from onpage_audit import OnPageAuditor
from rule_engine import RuleEngine
from output import OutputGenerator
from robots_sitemap import SitemapParser

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main execution function."""
    print("\n" + "="*80)
    print("🔍 SEO AUDIT SYSTEM")
    print("="*80 + "\n")
    
    # Get user input
    try:
        base_url = input("🌐 Enter website URL to audit: ").strip()
        if not base_url:
            print("❌ Error: URL is required")
            return
        
        # Add protocol if missing
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'https://' + base_url
        
        max_pages_input = input("📄 Enter maximum number of pages to crawl (default: 50): ").strip()
        max_pages = int(max_pages_input) if max_pages_input.isdigit() else 50
        
        if max_pages <= 0:
            print("❌ Error: Maximum pages must be greater than 0")
            return
        
        respect_robots_input = input("🤖 Respect robots.txt? (y/n, default: y): ").strip().lower()
        respect_robots = respect_robots_input != 'n'
        
        print(f"\n🚀 Starting audit for: {base_url}")
        print(f"📊 Maximum pages to crawl: {max_pages}")
        print(f"🤖 Respect robots.txt: {'Yes' if respect_robots else 'No (audit mode)'}\n")
        
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        return
    except Exception as e:
        print(f"❌ Error getting input: {str(e)}")
        return
    
    # Initialize components
    logger.info("🔧 Initializing components...")
    crawler = Crawler(base_url, max_pages=max_pages, max_concurrent=10)
    technical_auditor = TechnicalAuditor(base_url)
    onpage_auditor = OnPageAuditor()
    rule_engine = RuleEngine()
    output_generator = OutputGenerator(base_url)
    
    # Store crawlability info
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
        crawl_results = await crawler.crawl(respect_robots=respect_robots)
        
        if not crawl_results:
            logger.error("❌ No pages were crawled. Exiting.")
            return
        
        logger.info(f"✅ Crawled {len(crawl_results)} pages")
        
        # Capture crawlability info
        if crawler.robots_checker:
            crawlability_info['robots_txt_exists'] = crawler.robots_checker.robots_exists
            
            # Extract sitemap URLs from robots.txt
            if crawler.robots_checker.gemini_enabled:
                sitemap_urls_from_robots = await crawler.robots_checker.get_sitemap_urls_with_gemini()
            else:
                sitemap_urls_from_robots = crawler.robots_checker.get_sitemap_urls()
            
            crawlability_info['sitemap_urls_from_robots'] = sitemap_urls_from_robots
            
            # Check for sitemap and get URLs from sitemap files
            sitemap_urls_set = None  # Store full sitemap URLs set for orphan detection
            try:
                async with aiohttp.ClientSession() as session:
                    sitemap_parser = SitemapParser(base_url)
                    sitemap_result = await sitemap_parser.get_all_sitemap_urls(session, crawler.robots_checker)
                    sitemap_urls = sitemap_result['urls']  # URLs extracted from sitemaps
                    sitemap_urls_set = sitemap_urls  # Store full set for orphan detection
                    all_sitemap_urls = sitemap_result['all_sitemap_urls']  # All discovered sitemap URLs
                    accessed_sitemap_urls = sitemap_result['accessed_sitemap_urls']  # All accessed sitemap URLs
                    total_links_count = sitemap_result['total_links_count']  # Total number of links
                    
                    crawlability_info['sitemap_exists'] = len(sitemap_urls) > 0 or len(sitemap_urls_from_robots) > 0
                    crawlability_info['sitemap_urls'] = list(sitemap_urls)[:10]  # Limit to first 10 (URLs from within sitemaps)
                    crawlability_info['all_sitemap_urls'] = all_sitemap_urls  # All discovered sitemap URLs (whether accessible or not)
                    crawlability_info['accessed_sitemap_urls'] = accessed_sitemap_urls  # All accessed sitemap URLs
                    crawlability_info['total_sitemap_links_count'] = total_links_count  # Total links from all sitemaps
                    crawlability_info['sitemap_urls_full'] = sitemap_urls_set  # Store full set for orphan detection
            except Exception as e:
                logger.warning(f"⚠️ Could not check sitemap: {str(e)}")
                crawlability_info['sitemap_exists'] = len(sitemap_urls_from_robots) > 0
                crawlability_info['all_sitemap_urls'] = sitemap_urls_from_robots  # Use robots.txt sitemaps as fallback
                crawlability_info['accessed_sitemap_urls'] = []
                crawlability_info['total_sitemap_links_count'] = 0
                crawlability_info['sitemap_urls_full'] = None
        
        # Step 2: Perform audits
        all_results = []
        crawled_urls = set(crawl_results.keys())
        
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
                'score': score_results
            }
            
            all_results.append(page_result)
        
        # Step 3: Check for duplicates and orphans
        # Check duplicate titles
        duplicate_titles = onpage_auditor.check_duplicate_titles()
        
        # Check duplicate descriptions
        duplicate_descriptions = onpage_auditor.check_duplicate_descriptions()
        
        # Check duplicate H1s
        duplicate_h1s = onpage_auditor.check_duplicate_h1s()
        
        # Find orphan pages using sitemap URLs if available
        sitemap_urls = crawlability_info.get('sitemap_urls_full', None)
        if sitemap_urls:
            logger.info(f"📋 Using {len(sitemap_urls)} sitemap URLs for comprehensive orphan detection")
        
        orphan_pages = onpage_auditor.find_orphan_pages(crawled_urls, sitemap_urls=sitemap_urls, base_url=base_url)
        logger.info(f"🔍 Found {len(orphan_pages)} orphan page(s)")
        
        # Add duplicate/orphan info to results
        for result in all_results:
            url = result['url']
            if url in orphan_pages:
                # Use issue-specific weight for orphan pages
                orphan_weight = rule_engine.ISSUE_WEIGHTS.get('orphan_page', -6)
                result['score']['issues'].append({
                    'category': 'On-Page',
                    'type': 'Internal Links',
                    'severity': 'high',
                    'message': 'Orphan page (no internal in-links)',
                    'weight': orphan_weight
                })
                result['score']['score'] = max(20, result['score']['score'] + orphan_weight)
                result['score']['high_count'] += 1
                result['score']['issue_count'] += 1
        
        # Step 4: Calculate site-wide statistics
        site_stats = rule_engine.calculate_site_score(all_results)
        
        # Step 5: Generate outputs
        # Stats-only JSON output
        stats_json_file = output_generator.generate_stats_json(
            all_results, site_stats, crawlability_info,
            duplicate_titles, duplicate_descriptions, duplicate_h1s, orphan_pages
        )
        
        # Detailed issues JSON output
        issues_json_file = output_generator.generate_issues_json(
            all_results, site_stats, crawlability_info,
            duplicate_titles, duplicate_descriptions, duplicate_h1s, orphan_pages
        )
        
        logger.info(f"\n✅ Audit complete! Reports saved:")
        logger.info(f"   📊 Stats JSON: {stats_json_file}")
        logger.info(f"   📋 Issues JSON: {issues_json_file}")
        
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️ Operation cancelled by user")
    except Exception as e:
        logger.error(f"\n❌ Error during audit: {str(e)}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")

