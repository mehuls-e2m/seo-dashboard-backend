"""
Main entry point for SEO Audit System.
"""
import asyncio
import logging
import sys
import aiohttp
from typing import Dict, Set

from crawler import Crawler
from technical_audit import TechnicalAuditor
from onpage_audit import OnPageAuditor
from rule_engine import RuleEngine
from output import OutputGenerator
from robots_sitemap import SitemapParser

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
        'sitemap_urls': []
    }
    
    try:
        # Step 1: Crawl website
        logger.info("="*80)
        logger.info("STEP 1: CRAWLING WEBSITE")
        logger.info("="*80)
        crawl_results = await crawler.crawl(respect_robots=respect_robots)
        
        if not crawl_results:
            logger.error("❌ No pages were crawled. Exiting.")
            return
        
        logger.info(f"✅ Crawled {len(crawl_results)} pages")
        
        # Capture crawlability info
        if crawler.robots_checker:
            crawlability_info['robots_txt_exists'] = crawler.robots_checker.robots_exists
            # Check for sitemap
            try:
                async with aiohttp.ClientSession() as session:
                    sitemap_parser = SitemapParser(base_url)
                    sitemap_urls = await sitemap_parser.get_all_sitemap_urls(session, crawler.robots_checker)
                    crawlability_info['sitemap_exists'] = len(sitemap_urls) > 0
                    crawlability_info['sitemap_urls'] = list(sitemap_urls)[:10]  # Limit to first 10
            except Exception as e:
                logger.warning(f"⚠️ Could not check sitemap: {str(e)}")
                crawlability_info['sitemap_exists'] = False
        
        # Step 2: Perform audits
        logger.info("\n" + "="*80)
        logger.info("STEP 2: PERFORMING SEO AUDITS")
        logger.info("="*80)
        
        all_results = []
        crawled_urls = set(crawl_results.keys())
        
        for url, crawl_data in crawl_results.items():
            logger.info(f"\n📄 Auditing: {url}")
            
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
            
            logger.info(f"   Score: {score_results['score']}/100 | Issues: {score_results['issue_count']}")
        
        # Step 3: Check for duplicates and orphans
        logger.info("\n" + "="*80)
        logger.info("STEP 3: ANALYZING DUPLICATES AND ORPHAN PAGES")
        logger.info("="*80)
        
        # Check duplicate titles
        duplicate_titles = onpage_auditor.check_duplicate_titles()
        if duplicate_titles:
            logger.warning(f"⚠️ Found {len(duplicate_titles)} duplicate title(s)")
            for title, urls in list(duplicate_titles.items())[:5]:
                logger.warning(f"   Title '{title[:50]}...' appears on {len(urls)} pages")
        
        # Check duplicate descriptions
        duplicate_descriptions = onpage_auditor.check_duplicate_descriptions()
        if duplicate_descriptions:
            logger.warning(f"⚠️ Found {len(duplicate_descriptions)} duplicate description(s)")
        
        # Check duplicate H1s
        duplicate_h1s = onpage_auditor.check_duplicate_h1s()
        if duplicate_h1s:
            logger.warning(f"⚠️ Found {len(duplicate_h1s)} duplicate H1(s)")
        
        # Find orphan pages
        orphan_pages = onpage_auditor.find_orphan_pages(crawled_urls)
        if orphan_pages:
            logger.warning(f"⚠️ Found {len(orphan_pages)} orphan page(s) (no internal in-links)")
            for orphan in list(orphan_pages)[:5]:
                logger.warning(f"   Orphan: {orphan}")
        
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
        logger.info("\n" + "="*80)
        logger.info("STEP 4: CALCULATING SITE-WIDE STATISTICS")
        logger.info("="*80)
        
        site_stats = rule_engine.calculate_site_score(all_results)
        logger.info(f"⭐ Average SEO Score: {site_stats['average_score']}/100")
        logger.info(f"📊 Total Issues: {site_stats['total_issues']}")
        logger.info(f"   Critical: {site_stats['critical_issues']}")
        logger.info(f"   High: {site_stats['high_issues']}")
        
        # Step 5: Generate outputs
        logger.info("\n" + "="*80)
        logger.info("STEP 5: GENERATING REPORTS")
        logger.info("="*80)
        
        # JSON output
        json_file = output_generator.generate_json(all_results)
        
        # CSV outputs
        csv_file = output_generator.generate_csv(all_results)
        detailed_csv_file = output_generator.generate_detailed_csv(all_results)
        issues_grouped_csv_file = output_generator.generate_issues_grouped_csv(all_results)
        
        # Console output
        output_generator.print_console_report(all_results, site_stats, crawlability_info, 
                                             duplicate_titles, duplicate_descriptions, 
                                             duplicate_h1s, orphan_pages)
        
        logger.info(f"\n✅ Audit complete! Reports saved:")
        logger.info(f"   📄 JSON: {json_file if isinstance(json_file, str) else 'seo_audit_*.json'}")
        logger.info(f"   📊 Summary CSV: {csv_file}")
        logger.info(f"   📋 Detailed CSV (all links): {detailed_csv_file}")
        logger.info(f"   🔍 Issues Grouped CSV: {issues_grouped_csv_file}")
        
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

