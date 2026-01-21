"""
Independent output generator for API responses
"""
from typing import Dict, List, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class APIOutputGenerator:
    """Generate API-specific output format"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def generate_audit_stats(
        self,
        all_results: List[Dict],
        site_stats: Dict,
        crawlability_info: Dict,
        duplicate_titles: Dict,
        duplicate_descriptions: Dict,
        duplicate_h1s: Dict,
        orphan_pages: Set
    ) -> Dict:
        """
        Generate comprehensive audit statistics with detailed fields.
        """
        total_pages = len(all_results)
        
        # Calculate unique issue counts (based on issue types, not affected pages/images)
        unique_issues_by_type = {}
        for result in all_results:
            issues = result.get('score', {}).get('issues', [])
            for issue in issues:
                original_message = issue.get('message', '')
                normalized_message = self._normalize_issue_message(original_message)
                issue_key = f"{issue.get('category', 'Unknown')} - {issue.get('type', 'Unknown')} - {normalized_message}"
                if issue_key not in unique_issues_by_type:
                    unique_issues_by_type[issue_key] = {
                        'severity': issue.get('severity', 'low')
                    }
        
        # Count unique issues by severity
        total_unique_issues = len(unique_issues_by_type)
        critical_unique = sum(1 for issue in unique_issues_by_type.values() if issue['severity'] == 'critical')
        high_unique = sum(1 for issue in unique_issues_by_type.values() if issue['severity'] == 'high')
        medium_unique = sum(1 for issue in unique_issues_by_type.values() if issue['severity'] == 'medium')
        low_unique = sum(1 for issue in unique_issues_by_type.values() if issue['severity'] == 'low')
        
        # Status code distribution - Initialize with all important status codes
        important_status_codes = ['200', '301', '302', '304', '400', '401', '403', '404', '500', '502', '503', '504']
        status_codes = {code: 0 for code in important_status_codes}
        
        # Count actual status codes from results
        for result in all_results:
            code = result.get('status_code', 0)
            code_str = str(code)
            if code_str in status_codes:
                status_codes[code_str] += 1
            else:
                # Include any other status codes that appear
                status_codes[code_str] = status_codes.get(code_str, 0) + 1
        
        # Technical SEO statistics
        noindex_pages_count = sum(1 for r in all_results 
                                  if r.get('technical', {}).get('noindex', {}).get('has_noindex', False))
        pages_with_canonical = sum(1 for r in all_results 
                                  if r.get('technical', {}).get('canonical', {}).get('has_canonical', False))
        pages_with_canonical_issues_count = sum(1 for r in all_results 
                                              if r.get('technical', {}).get('canonical', {}).get('issues', []))
        https_pages = sum(1 for r in all_results 
                         if r.get('technical', {}).get('https', {}).get('is_https', False))
        mixed_content_pages_count = sum(1 for r in all_results 
                                       if r.get('technical', {}).get('https', {}).get('mixed_content_count', 0) > 0)
        pages_with_structured_data = sum(1 for r in all_results 
                                        if r.get('technical', {}).get('structured_data', {}).get('has_structured_data', False))
        schema_types = set()
        for r in all_results:
            types = r.get('technical', {}).get('structured_data', {}).get('schema_types', [])
            schema_types.update(types)
        redirect_issues_count = sum(1 for r in all_results 
                                    if r.get('technical', {}).get('redirects', {}).get('issues', []))
        pages_with_meta_robots = sum(1 for r in all_results 
                                    if r.get('technical', {}).get('meta_robots', {}).get('has_meta_robots', False))
        
        # Server response time statistics (Time to First Byte - TTFB)
        server_response_times = []
        for r in all_results:
            response_time = r.get('server_response_time_ms')
            if response_time is not None and isinstance(response_time, (int, float)) and response_time > 0:
                server_response_times.append(response_time)
        
        if server_response_times:
            min_server_response_time = round(min(server_response_times), 2)
            max_server_response_time = round(max(server_response_times), 2)
            avg_server_response_time = round(sum(server_response_times) / len(server_response_times), 2)
        else:
            min_server_response_time = 0
            max_server_response_time = 0
            avg_server_response_time = 0
        
        # On-page SEO statistics - Detailed
        pages_with_title = sum(1 for r in all_results 
                              if r.get('onpage', {}).get('title', {}).get('has_title', False))
        pages_without_title_tags = total_pages - pages_with_title
        
        # Title length issues with actual content
        title_too_short = 0
        title_too_short_details = []  # List of {url, title_text, title_length}
        title_too_long = 0
        title_too_long_details = []  # List of {url, title_text, title_length}
        
        for r in all_results:
            url = r.get('url', '')
            title = r.get('onpage', {}).get('title', {})
            if title.get('has_title', False):
                title_text = title.get('title_text', '')
                title_length = title.get('title_length', 0)
                issues = title.get('issues', [])
                for issue in issues:
                    if 'too short' in issue.lower():
                        title_too_short += 1
                        title_too_short_details.append({
                            'url': url,
                            'title_text': title_text,
                            'title_length': title_length
                        })
                        break
                    elif 'too long' in issue.lower():
                        title_too_long += 1
                        title_too_long_details.append({
                            'url': url,
                            'title_text': title_text,
                            'title_length': title_length
                        })
                        break
        
        pages_with_meta_desc = sum(1 for r in all_results 
                                  if r.get('onpage', {}).get('meta_description', {}).get('has_meta_description', False))
        pages_without_meta_description = total_pages - pages_with_meta_desc
        
        # Meta description too short with actual content
        meta_description_too_short = 0
        meta_description_too_short_details = []  # List of {url, description_text, description_length}
        meta_description_too_long = 0
        meta_description_too_long_details = []  # List of {url, description_text, description_length}
        
        for r in all_results:
            url = r.get('url', '')
            meta_desc = r.get('onpage', {}).get('meta_description', {})
            if meta_desc.get('has_meta_description', False):
                description_text = meta_desc.get('description_text', '')
                description_length = meta_desc.get('description_length', 0)
                issues = meta_desc.get('issues', [])
                for issue in issues:
                    if 'too short' in issue.lower():
                        meta_description_too_short += 1
                        meta_description_too_short_details.append({
                            'url': url,
                            'description_text': description_text,
                            'description_length': description_length
                        })
                        break
                    elif 'too long' in issue.lower():
                        meta_description_too_long += 1
                        meta_description_too_long_details.append({
                            'url': url,
                            'description_text': description_text,
                            'description_length': description_length
                        })
                        break
        
        # H1-H6 counting
        pages_with_h1 = sum(1 for r in all_results 
                           if r.get('onpage', {}).get('h1', {}).get('h1_count', 0) > 0)
        pages_without_h1_count = sum(1 for r in all_results 
                                     if r.get('onpage', {}).get('h1', {}).get('h1_count', 0) == 0)
        multiple_h1_pages_count = sum(1 for r in all_results 
                                      if r.get('onpage', {}).get('h1', {}).get('h1_count', 0) > 1)
        
        # Count total H1-H6 tags across all pages
        # Use headings data if available, otherwise fallback to h1 data
        total_h1 = 0
        total_h2 = 0
        total_h3 = 0
        total_h4 = 0
        total_h5 = 0
        total_h6 = 0
        
        for r in all_results:
            onpage = r.get('onpage', {})
            headings = onpage.get('headings', {})
            if headings:
                # Use headings data if available
                total_h1 += headings.get('h1_count', 0)
                total_h2 += headings.get('h2_count', 0)
                total_h3 += headings.get('h3_count', 0)
                total_h4 += headings.get('h4_count', 0)
                total_h5 += headings.get('h5_count', 0)
                total_h6 += headings.get('h6_count', 0)
            else:
                # Fallback to h1 data for backward compatibility
                h1_data = onpage.get('h1', {})
                total_h1 += h1_data.get('h1_count', 0)
        
        # Calculate averages per page
        avg_h1_per_page = round(total_h1 / total_pages, 2) if total_pages > 0 else 0
        avg_h2_per_page = round(total_h2 / total_pages, 2) if total_pages > 0 else 0
        avg_h3_per_page = round(total_h3 / total_pages, 2) if total_pages > 0 else 0
        avg_h4_per_page = round(total_h4 / total_pages, 2) if total_pages > 0 else 0
        avg_h5_per_page = round(total_h5 / total_pages, 2) if total_pages > 0 else 0
        avg_h6_per_page = round(total_h6 / total_pages, 2) if total_pages > 0 else 0
        total_images = sum(r.get('onpage', {}).get('image_alt', {}).get('total_images', 0) for r in all_results)
        images_without_alt = sum(r.get('onpage', {}).get('image_alt', {}).get('images_without_alt', 0) for r in all_results)
        
        # Collect all image URLs without alt text (actual image URLs, not webpage URLs)
        # Exclude SVG images - only count proper images
        all_images_without_alt_urls = []
        for r in all_results:
            image_alt = r.get('onpage', {}).get('image_alt', {})
            # Use images_without_alt_urls if available, otherwise empty list
            image_urls = image_alt.get('images_without_alt_urls', [])
            if image_urls:
                # Filter out SVG images
                proper_images = [img_url for img_url in image_urls 
                               if not (img_url.lower().endswith('.svg') or '.svg' in img_url.lower())]
                all_images_without_alt_urls.extend(proper_images)
        total_internal_links = sum(r.get('onpage', {}).get('internal_links', {}).get('internal_link_count', 0) for r in all_results)
        broken_internal_links = sum(r.get('onpage', {}).get('internal_links', {}).get('broken_link_count', 0) for r in all_results)
        
        # Count links without anchor text (count all links, not just pages)
        link_without_anchor_tags = 0
        for r in all_results:
            # Check internal links issues
            internal_links = r.get('onpage', {}).get('internal_links', {})
            issues = internal_links.get('issues', [])
            for issue in issues:
                if isinstance(issue, str) and 'Link without anchor text' in issue:
                    # Extract count if available, otherwise count as 1
                    link_without_anchor_tags += 1
            # Also check score issues for link without anchor text
            score_issues = r.get('score', {}).get('issues', [])
            for issue in score_issues:
                message = issue.get('message', '')
                if 'Link without anchor text' in message:
                    link_without_anchor_tags += 1
        
        # Build comprehensive stats
        stats_data = {
            'site_overview': {
                'base_url': self.base_url,
                'timestamp': self.timestamp,
                'total_crawled_pages': total_pages,
                'average_seo_score': round(site_stats.get('average_score', 0), 2),
                'total_issues': total_unique_issues,  # Count of unique issue types
                'critical_issues_count': critical_unique,
                'high_issues_count': high_unique,
                'medium_issues_count': medium_unique,
                'low_issues_count': low_unique
            },
            'crawlability': {
                'robots_txt_exists': crawlability_info.get('robots_txt_exists', False),
                'robots_txt_content': crawlability_info.get('robots_txt_content') if crawlability_info.get('robots_txt_exists', False) else None,
                'llms_txt_exists': crawlability_info.get('llms_txt_exists', False),
                'llms_txt_content': crawlability_info.get('llms_txt_content') if crawlability_info.get('llms_txt_exists', False) else None,
                'sitemap_exists': len(crawlability_info.get('all_sitemap_urls', [])) > 0,
                'all_sitemap_urls': crawlability_info.get('all_sitemap_urls', []),
                'total_sitemap_links_count': crawlability_info.get('total_sitemap_links_count', 0)
            },
            'status_code_distribution': status_codes,
            'technical_seo': {
                'noindex': {
                    'pages_with_noindex': noindex_pages_count,
                    'percentage': round((noindex_pages_count / total_pages * 100), 2) if total_pages > 0 else 0
                },
                'meta_robots': {
                    'pages_with_meta_robots': pages_with_meta_robots,
                    'percentage': round((pages_with_meta_robots / total_pages * 100), 2) if total_pages > 0 else 0
                },
                'canonical_tags': {
                    'pages_with_canonical': pages_with_canonical,
                    'pages_with_canonical_issues': pages_with_canonical_issues_count,
                    'coverage_percentage': round((pages_with_canonical / total_pages * 100), 2) if total_pages > 0 else 0
                },
                'redirects': {
                    'pages_with_redirect_issues': redirect_issues_count,
                    'percentage': round((redirect_issues_count / total_pages * 100), 2) if total_pages > 0 else 0
                },
                'https': {
                    'https_pages': https_pages,
                    'coverage_percentage': round((https_pages / total_pages * 100), 2) if total_pages > 0 else 0,
                    'mixed_content_pages': mixed_content_pages_count,
                    'mixed_content_percentage': round((mixed_content_pages_count / total_pages * 100), 2) if total_pages > 0 else 0
                },
                'structured_data': {
                    'pages_with_structured_data': pages_with_structured_data,
                    'coverage_percentage': round((pages_with_structured_data / total_pages * 100), 2) if total_pages > 0 else 0,
                    'schema_types_found': list(schema_types),
                    'total_schema_types': len(schema_types)
                },
                'server_response_time': {
                    'min_time_ms': min_server_response_time,
                    'max_time_ms': max_server_response_time,
                    'avg_time_ms': avg_server_response_time,
                    'pages_measured': len(server_response_times),
                    'total_pages': total_pages
                }
            },
            'onpage_seo': {
                'title_tags': {
                    'pages_with_title': pages_with_title,
                    'pages_without_title_tags': pages_without_title_tags,
                    'title_too_short_count': title_too_short,
                    'title_too_long_count': title_too_long,
                    'coverage_percentage': round((pages_with_title / total_pages * 100), 2) if total_pages > 0 else 0,
                    'duplicate_titles_count': len(duplicate_titles)
                },
                'meta_descriptions': {
                    'pages_with_meta_description': pages_with_meta_desc,
                    'pages_without_meta_description': pages_without_meta_description,
                    'meta_description_too_short_count': meta_description_too_short,
                    'meta_description_too_long_count': meta_description_too_long,
                    'coverage_percentage': round((pages_with_meta_desc / total_pages * 100), 2) if total_pages > 0 else 0,
                    'duplicate_descriptions_count': len(duplicate_descriptions)
                },
                'h1_tags': {
                    'pages_with_h1': pages_with_h1,
                    'coverage_percentage': round((pages_with_h1 / total_pages * 100), 2) if total_pages > 0 else 0,
                    'pages_without_h1': pages_without_h1_count,
                    'pages_with_multiple_h1': multiple_h1_pages_count,
                    'duplicate_h1s_count': len(duplicate_h1s)
                },
                'headings': {
                    'total_h1': total_h1,
                    'total_h2': total_h2,
                    'total_h3': total_h3,
                    'total_h4': total_h4,
                    'total_h5': total_h5,
                    'total_h6': total_h6,
                    'avg_h1_per_page': avg_h1_per_page,
                    'avg_h2_per_page': avg_h2_per_page,
                    'avg_h3_per_page': avg_h3_per_page,
                    'avg_h4_per_page': avg_h4_per_page,
                    'avg_h5_per_page': avg_h5_per_page,
                    'avg_h6_per_page': avg_h6_per_page
                },
                'image_alt_text': {
                    'total_images': total_images,
                    'images_without_alt': images_without_alt,
                    'compliance_percentage': round(((total_images - images_without_alt) / total_images * 100), 2) if total_images > 0 else 100
                },
                'internal_linking': {
                    'total_internal_links': total_internal_links,
                    'broken_internal_links': broken_internal_links,
                    'link_without_anchor_tags': link_without_anchor_tags,
                    'orphan_pages_count': len(orphan_pages)
                }
            }
        }
        
        # Extract additional SEO stats and distribute to relevant sections
        additional_stats = self._extract_additional_seo_stats(all_results)
        
        # Add to technical_seo: open_graph, twitter_cards, language_and_encoding
        stats_data['technical_seo']['open_graph'] = additional_stats.get('open_graph', {})
        stats_data['technical_seo']['twitter_cards'] = additional_stats.get('twitter_cards', {})
        stats_data['technical_seo']['language_and_encoding'] = additional_stats.get('language_and_encoding', {})
        
        # Add to onpage_seo: external_links, content_analysis
        stats_data['onpage_seo']['external_links'] = additional_stats.get('external_links', {})
        stats_data['onpage_seo']['content_analysis'] = additional_stats.get('content_analysis', {})
        
        # Extract advanced SEO stats
        advanced_stats = self._extract_advanced_seo_data(all_results)
        
        # Add new advanced SEO sections to technical_seo
        stats_data['technical_seo']['pagination'] = advanced_stats.get('pagination', {})
        stats_data['technical_seo']['caching_compression'] = advanced_stats.get('caching_compression', {})
        stats_data['technical_seo']['cdn_behavior'] = advanced_stats.get('cdn_behavior', {})
        stats_data['technical_seo']['markups'] = advanced_stats.get('markups', {})
        stats_data['technical_seo']['hreflang_usage'] = advanced_stats.get('hreflang_usage', {})
        stats_data['technical_seo']['image_optimization'] = advanced_stats.get('image_optimization', {})
        
        # Add remaining advanced SEO sections to onpage_seo
        stats_data['onpage_seo']['responsive_design'] = advanced_stats.get('responsive_design', {})
        
        return stats_data
    
    def _extract_additional_seo_stats(self, all_results: List[Dict]) -> Dict:
        """Extract additional SEO statistics (numbers only) for audit_stats."""
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse, urljoin
        import re
        
        total_pages = len(all_results)
        pages_with_og = 0
        pages_with_twitter = 0
        total_external_links = 0
        total_content_length = 0
        pages_with_lang = 0
        pages_with_encoding = 0
        languages = set()
        encodings = set()
        external_domains = {}
        og_tags_found = set()
        twitter_tags_found = set()
        
        for result in all_results:
            url = result.get('url', '')
            html = result.get('html_content', '')
            
            if not html:
                continue
            
            try:
                soup = BeautifulSoup(html, 'lxml')
                base_domain = urlparse(self.base_url).netloc
                
                # Check Open Graph tags
                og_tags = soup.find_all('meta', attrs={'property': re.compile(r'^og:', re.I)})
                if og_tags:
                    pages_with_og += 1
                    for tag in og_tags:
                        prop = tag.get('property', '').lower()
                        og_tags_found.add(prop)
                
                # Check Twitter Card tags
                twitter_tags = soup.find_all('meta', attrs={'name': re.compile(r'^twitter:', re.I)})
                if twitter_tags:
                    pages_with_twitter += 1
                    for tag in twitter_tags:
                        name = tag.get('name', '').lower()
                        twitter_tags_found.add(name)
                
                # Check language
                html_tag = soup.find('html')
                if html_tag:
                    lang = html_tag.get('lang', '')
                    if lang:
                        pages_with_lang += 1
                        languages.add(lang)
                
                # Check encoding
                meta_charset = soup.find('meta', attrs={'charset': True})
                if meta_charset:
                    encoding = meta_charset.get('charset', '').lower()
                    if encoding:
                        pages_with_encoding += 1
                        encodings.add(encoding)
                else:
                    # Check content-type meta tag
                    meta_content_type = soup.find('meta', attrs={'http-equiv': re.compile(r'content-type', re.I)})
                    if meta_content_type:
                        content = meta_content_type.get('content', '')
                        charset_match = re.search(r'charset=([^;]+)', content, re.I)
                        if charset_match:
                            encoding = charset_match.group(1).strip().lower()
                            pages_with_encoding += 1
                            encodings.add(encoding)
                
                # Extract external links
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if href:
                        absolute_url = urljoin(url, href)
                        parsed = urlparse(absolute_url)
                        link_domain = parsed.netloc
                        
                        if link_domain and link_domain != base_domain:
                            total_external_links += 1
                            external_domains[link_domain] = external_domains.get(link_domain, 0) + 1
                
                # Calculate content length (text only, excluding scripts/styles)
                for script in soup(['script', 'style', 'meta', 'link', 'head']):
                    script.decompose()
                text_content = soup.get_text()
                char_count = len(text_content)
                total_content_length += char_count
                
            except Exception as e:
                logger.warning(f"⚠️ Error extracting additional SEO stats for {url}: {str(e)}")
                continue
        
        avg_content_length = round(total_content_length / total_pages, 0) if total_pages > 0 else 0
        
        return {
            'open_graph': {
                'pages_with_og_tags': pages_with_og,
                'pages_without_og_tags': total_pages - pages_with_og,
                'coverage_percentage': round((pages_with_og / total_pages * 100), 2) if total_pages > 0 else 0,
                'unique_og_tags_count': len(og_tags_found)
            },
            'twitter_cards': {
                'pages_with_twitter_tags': pages_with_twitter,
                'pages_without_twitter_tags': total_pages - pages_with_twitter,
                'coverage_percentage': round((pages_with_twitter / total_pages * 100), 2) if total_pages > 0 else 0,
                'unique_twitter_tags_count': len(twitter_tags_found)
            },
            'external_links': {
                'total_external_links': total_external_links,
                'unique_external_domains': len(external_domains),
                'average_external_links_per_page': round(total_external_links / total_pages, 2) if total_pages > 0 else 0
            },
            'content_analysis': {
                'average_content_length': avg_content_length,
                'total_content_length': total_content_length
            },
            'language_and_encoding': {
                'pages_with_lang_attribute': pages_with_lang,
                'unique_languages_count': len(languages),
                'pages_with_encoding': pages_with_encoding,
                'unique_encodings_count': len(encodings)
            }
        }
    
    def generate_audit_issues(
        self,
        all_results: List[Dict],
        site_stats: Dict,
        crawlability_info: Dict,
        duplicate_titles: Dict,
        duplicate_descriptions: Dict,
        duplicate_h1s: Dict,
        orphan_pages: Set
    ) -> Dict:
        """
        Generate audit issues (without all_issues and without separated technical_seo/onpage_seo sections).
        """
        total_pages = len(all_results)
        
        # Group issues by type and collect URLs
        # Each unique issue type should have number_of_issues = 1 (one unique issue)
        # affected_pages_count shows how many pages are affected by this issue
        issues_by_type = {}
        for result in all_results:
            url = result.get('url', '')
            issues = result.get('score', {}).get('issues', [])
            
            for issue in issues:
                original_message = issue.get('message', '')
                normalized_message = self._normalize_issue_message(original_message)
                
                issue_key = f"{issue.get('category', 'Unknown')} - {issue.get('type', 'Unknown')} - {normalized_message}"
                
                if issue_key not in issues_by_type:
                    issues_by_type[issue_key] = {
                        'issue_name': normalized_message,
                        'category': issue.get('category', 'Unknown'),
                        'type': issue.get('type', 'Unknown'),
                        'severity': issue.get('severity', 'low'),
                        'affected_pages': [],
                        'links_without_anchor_text': set()
                    }
                # Track affected pages (avoid duplicates)
                if url not in issues_by_type[issue_key]['affected_pages']:
                    issues_by_type[issue_key]['affected_pages'].append(url)
                
                # Extract link URL from "Link without anchor text: URL" messages
                if normalized_message == "Link without anchor text" and original_message.startswith("Link without anchor text:"):
                    link_url = original_message.replace("Link without anchor text:", "").strip()
                    if link_url:
                        issues_by_type[issue_key]['links_without_anchor_text'].add(link_url)
        
        # Convert to list and sort by severity and count
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        issues_list = []
        for issue_key, issue_data in issues_by_type.items():
            issue_dict = {
                'issue_name': issue_data['issue_name'],
                'category': issue_data['category'],
                'type': issue_data['type'],
                'severity': issue_data['severity'],
                'number_of_issues': 1,  # Each unique issue type counts as 1 issue
                'affected_pages_count': len(issue_data['affected_pages']),
                'affected_pages': issue_data['affected_pages']
            }
            
            # For "Link without anchor text" issue, add the links information
            if issue_data['issue_name'] == "Link without anchor text" and issue_data['links_without_anchor_text']:
                issue_dict['total_links_without_anchor_text'] = len(issue_data['links_without_anchor_text'])
                issue_dict['links_without_anchor_text'] = sorted(list(issue_data['links_without_anchor_text']))
            
            issues_list.append(issue_dict)
        
        issues_list.sort(key=lambda x: (severity_order.get(x['severity'], 4), -x.get('affected_pages_count', 0)))
        
        # Calculate total issues based on unique issue types (not affected pages/images)
        total_unique_issues = len(issues_list)
        
        # Count issues by severity from the grouped issues list
        critical_issues_count = sum(1 for issue in issues_list if issue['severity'] == 'critical')
        high_issues_count = sum(1 for issue in issues_list if issue['severity'] == 'high')
        medium_issues_count = sum(1 for issue in issues_list if issue['severity'] == 'medium')
        low_issues_count = sum(1 for issue in issues_list if issue['severity'] == 'low')
        
        # Collect detailed content and attach to relevant issues
        # Map issue names to their details
        title_too_short_details = {}
        title_too_long_details = {}
        meta_description_too_short_details = {}
        meta_description_too_long_details = {}
        images_without_alt_details = {}  # url -> list of image URLs
        
        for r in all_results:
            url = r.get('url', '')
            # Title details
            title = r.get('onpage', {}).get('title', {})
            if title.get('has_title', False):
                title_text = title.get('title_text', '')
                title_length = title.get('title_length', 0)
                issues = title.get('issues', [])
                for issue in issues:
                    if 'too short' in issue.lower():
                        if url not in title_too_short_details:
                            title_too_short_details[url] = {
                                'url': url,
                                'title_text': title_text,
                                'title_length': title_length
                            }
                        break
                    elif 'too long' in issue.lower():
                        if url not in title_too_long_details:
                            title_too_long_details[url] = {
                                'url': url,
                                'title_text': title_text,
                                'title_length': title_length
                            }
                        break
            
            # Meta description details
            meta_desc = r.get('onpage', {}).get('meta_description', {})
            if meta_desc.get('has_meta_description', False):
                description_text = meta_desc.get('description_text', '')
                description_length = meta_desc.get('description_length', 0)
                issues = meta_desc.get('issues', [])
                for issue in issues:
                    if 'too short' in issue.lower():
                        if url not in meta_description_too_short_details:
                            meta_description_too_short_details[url] = {
                                'url': url,
                                'description_text': description_text,
                                'description_length': description_length
                            }
                        break
                    elif 'too long' in issue.lower():
                        if url not in meta_description_too_long_details:
                            meta_description_too_long_details[url] = {
                                'url': url,
                                'description_text': description_text,
                                'description_length': description_length
                            }
                        break
            
            # Image URLs without alt text
            image_alt = r.get('onpage', {}).get('image_alt', {})
            image_urls = image_alt.get('images_without_alt_urls', [])
            if image_urls:
                images_without_alt_details[url] = image_urls
        
        # Attach details to relevant issues in issues_list
        for issue_dict in issues_list:
            issue_name = issue_dict.get('issue_name', '').lower()
            
            # Title too short - match variations like "title too short"
            if 'title' in issue_name and 'too short' in issue_name:
                details = [title_too_short_details[url] for url in issue_dict['affected_pages'] if url in title_too_short_details]
                if details:
                    issue_dict['details'] = details
                    # Remove affected_pages since details already contain URLs
                    issue_dict.pop('affected_pages', None)
            
            # Title too long - match variations like "title too long"
            elif 'title' in issue_name and 'too long' in issue_name:
                details = [title_too_long_details[url] for url in issue_dict['affected_pages'] if url in title_too_long_details]
                if details:
                    issue_dict['details'] = details
                    # Remove affected_pages since details already contain URLs
                    issue_dict.pop('affected_pages', None)
            
            # Meta description too short - match variations
            elif ('meta description' in issue_name or 'description' in issue_name) and 'too short' in issue_name:
                details = [meta_description_too_short_details[url] for url in issue_dict['affected_pages'] if url in meta_description_too_short_details]
                if details:
                    issue_dict['details'] = details
                    # Remove affected_pages since details already contain URLs
                    issue_dict.pop('affected_pages', None)
            
            # Meta description too long - match variations
            elif ('meta description' in issue_name or 'description' in issue_name) and 'too long' in issue_name:
                details = [meta_description_too_long_details[url] for url in issue_dict['affected_pages'] if url in meta_description_too_long_details]
                if details:
                    issue_dict['details'] = details
                    # Remove affected_pages since details already contain URLs
                    issue_dict.pop('affected_pages', None)
            
            # Images missing alt text - match variations like "image(s) missing alt text"
            elif 'image' in issue_name and ('missing alt' in issue_name or 'alt' in issue_name):
                # Collect all image URLs from affected pages (excluding SVG images)
                all_image_urls = []
                for url in issue_dict.get('affected_pages', []):
                    if url in images_without_alt_details:
                        # Filter out SVG images
                        page_images = [img_url for img_url in images_without_alt_details[url] 
                                     if not (img_url.lower().endswith('.svg') or '.svg' in img_url.lower())]
                        all_image_urls.extend(page_images)
                
                if all_image_urls:
                    issue_dict['images_without_alt_urls'] = all_image_urls
                    issue_dict['number_of_images'] = len(all_image_urls)  # Count of images with issue
                    # Remove affected_pages_count and affected_pages since we have image-specific data
                    issue_dict.pop('affected_pages_count', None)
                    issue_dict.pop('affected_pages', None)
        
        # Add additional issues from other sections (crawlability, status codes, advanced SEO, etc.)
        additional_issues = self._extract_additional_issues(
            all_results, crawlability_info, orphan_pages
        )
        issues_list.extend(additional_issues)
        
        # Re-sort issues list after adding additional issues
        issues_list.sort(key=lambda x: (severity_order.get(x['severity'], 4), -x.get('affected_pages_count', x.get('number_of_images', 0))))
        
        # Extract additional SEO data
        additional_seo_data = self._extract_additional_seo_data(all_results)
        
        # Extract advanced SEO data
        advanced_seo_data = self._extract_advanced_seo_data(all_results)
        
        # Calculate server response time statistics for issues output
        server_response_times_issues = []
        for r in all_results:
            response_time = r.get('server_response_time_ms')
            if response_time is not None and isinstance(response_time, (int, float)) and response_time > 0:
                server_response_times_issues.append(response_time)
        
        if server_response_times_issues:
            min_time = round(min(server_response_times_issues), 2)
            max_time = round(max(server_response_times_issues), 2)
            avg_time = round(sum(server_response_times_issues) / len(server_response_times_issues), 2)
        else:
            min_time = 0
            max_time = 0
            avg_time = 0
        
        # Build issues data (without all_issues and without separated technical_seo/onpage_seo)
        # Use counts based on unique issue types, not affected pages/images
        issues_data = {
            'site_overview': {
                'base_url': self.base_url,
                'timestamp': self.timestamp,
                'total_crawled_pages': total_pages,
                'average_seo_score': round(site_stats.get('average_score', 0), 2),
                'total_issues': total_unique_issues,  # Count of unique issue types
                'critical_issues_count': critical_issues_count,
                'high_issues_count': high_issues_count,
                'medium_issues_count': medium_issues_count,
                'low_issues_count': low_issues_count
            },
            'crawlability': {
                'robots_txt_exists': crawlability_info.get('robots_txt_exists', False),
                'robots_txt_content': crawlability_info.get('robots_txt_content') if crawlability_info.get('robots_txt_exists', False) else None,
                'llms_txt_exists': crawlability_info.get('llms_txt_exists', False),
                'llms_txt_content': crawlability_info.get('llms_txt_content') if crawlability_info.get('llms_txt_exists', False) else None,
                'sitemap_exists': len(crawlability_info.get('all_sitemap_urls', [])) > 0,
                'all_sitemap_urls': crawlability_info.get('all_sitemap_urls', []),
                'total_sitemap_links_count': crawlability_info.get('total_sitemap_links_count', 0)
            },
            'issues_summary': {
                'total_unique_issue_types': len(issues_list),
                'issues_by_severity': {
                    'critical': [i for i in issues_list if i['severity'] == 'critical'],
                    'high': [i for i in issues_list if i['severity'] == 'high'],
                    'medium': [i for i in issues_list if i['severity'] == 'medium'],
                    'low': [i for i in issues_list if i['severity'] == 'low']
                }
            },
            **additional_seo_data,
            # Advanced SEO sections
            'pagination': advanced_seo_data.get('pagination', {}),
            'caching_compression': advanced_seo_data.get('caching_compression', {}),
            'image_optimization': advanced_seo_data.get('image_optimization', {}),
            'responsive_design': advanced_seo_data.get('responsive_design', {}),
            'cdn_behavior': advanced_seo_data.get('cdn_behavior', {}),
            'markups': advanced_seo_data.get('markups', {}),
            'hreflang_usage': advanced_seo_data.get('hreflang_usage', {}),
            # Server response time
            'server_response_time': {
                'min_time_ms': min_time,
                'max_time_ms': max_time,
                'avg_time_ms': avg_time,
                'pages_measured': len(server_response_times_issues),
                'total_pages': total_pages
            }
        }
        
        return issues_data
    
    def _normalize_issue_message(self, message: str) -> str:
        """Normalize issue message to remove dynamic values."""
        if not message:
            return message
        
        import re
        original = message
        
        # Normalize "Link without anchor text: URL" to just "Link without anchor text"
        if message.startswith("Link without anchor text:"):
            return "Link without anchor text"
        
        # Normalize "Canonical points to different URL: <URL>" to just "Canonical points to different URL"
        if message.startswith("Canonical points to different URL:"):
            return "Canonical points to different URL"
        
        # Remove leading numbers from "image(s) missing alt text" pattern
        message = re.sub(r'^\d+\s+(image\(s\)\s+missing\s+alt\s+text)', r'\1', message, flags=re.IGNORECASE)
        
        # Remove character counts from title/description length issues
        message = re.sub(r'\s*\([^)]*chars[^)]*\)', '', message)
        message = re.sub(r'\s*,\s*recommended:.*$', '', message)
        message = re.sub(r'\s*\(recommended:.*?\)', '', message)
        
        # Remove numbers from other patterns
        message = re.sub(r'^\d+\s+(resource\(s\)|script\(s\)|stylesheet\(s\))', r'\1', message, flags=re.IGNORECASE)
        
        # Remove any remaining trailing parentheses with numbers/chars/details
        message = re.sub(r'\s*\([^)]*\)\s*$', '', message)
        
        # Clean up extra spaces
        message = re.sub(r'\s+', ' ', message).strip()
        
        # If normalization removed everything, return original
        if not message:
            return original
        
        return message
    
    def _extract_additional_seo_data(self, all_results: List[Dict]) -> Dict:
        """Extract additional SEO data: Open Graph, Twitter Cards, external links, content analysis, etc."""
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse, urljoin
        import re
        
        total_pages = len(all_results)
        pages_with_og = 0
        pages_with_twitter = 0
        total_external_links = 0
        total_content_length = 0
        pages_with_lang = 0
        pages_with_encoding = 0
        languages = set()
        encodings = set()
        external_domains = {}  # Will store: {domain: set of unique URLs}
        external_domains_count = {}  # Will store: {domain: count of unique URLs}
        og_tags_found = set()
        twitter_tags_found = set()
        pages_without_og = []
        pages_without_twitter = []
        
        for result in all_results:
            url = result.get('url', '')
            html = result.get('html_content', '')
            
            if not html:
                continue
            
            try:
                soup = BeautifulSoup(html, 'lxml')
                base_domain = urlparse(self.base_url).netloc
                
                # Check Open Graph tags
                og_tags = soup.find_all('meta', attrs={'property': re.compile(r'^og:', re.I)})
                if og_tags:
                    pages_with_og += 1
                    for tag in og_tags:
                        prop = tag.get('property', '').lower()
                        og_tags_found.add(prop)
                else:
                    pages_without_og.append(url)
                
                # Check Twitter Card tags
                twitter_tags = soup.find_all('meta', attrs={'name': re.compile(r'^twitter:', re.I)})
                if twitter_tags:
                    pages_with_twitter += 1
                    for tag in twitter_tags:
                        name = tag.get('name', '').lower()
                        twitter_tags_found.add(name)
                else:
                    pages_without_twitter.append(url)
                
                # Check language
                html_tag = soup.find('html')
                if html_tag:
                    lang = html_tag.get('lang', '')
                    if lang:
                        pages_with_lang += 1
                        languages.add(lang)
                
                # Check encoding
                meta_charset = soup.find('meta', attrs={'charset': True})
                if meta_charset:
                    encoding = meta_charset.get('charset', '').lower()
                    if encoding:
                        pages_with_encoding += 1
                        encodings.add(encoding)
                else:
                    # Check content-type meta tag
                    meta_content_type = soup.find('meta', attrs={'http-equiv': re.compile(r'content-type', re.I)})
                    if meta_content_type:
                        content = meta_content_type.get('content', '')
                        charset_match = re.search(r'charset=([^;]+)', content, re.I)
                        if charset_match:
                            encoding = charset_match.group(1).strip().lower()
                            pages_with_encoding += 1
                            encodings.add(encoding)
                
                # Extract external links - track unique URLs per domain
                links = soup.find_all('a', href=True)
                page_external_urls = set()  # Track unique external URLs for this page
                
                for link in links:
                    href = link.get('href', '')
                    if href:
                        absolute_url = urljoin(url, href)
                        parsed = urlparse(absolute_url)
                        link_domain = parsed.netloc
                        
                        if link_domain and link_domain != base_domain:
                            # Normalize URL (remove fragment, query params for counting unique URLs per domain)
                            normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                            
                            # Count total external links (all occurrences)
                            total_external_links += 1
                            
                            # Track unique URLs per domain (avoid duplicates)
                            if link_domain not in external_domains:
                                external_domains[link_domain] = set()
                            
                            # Add unique URL to domain's set
                            external_domains[link_domain].add(normalized_url)
                
                # After processing all links on the page, update counts
                for domain, unique_urls in external_domains.items():
                    external_domains_count[domain] = len(unique_urls)
                
                # Calculate content length (text only, excluding scripts/styles)
                for script in soup(['script', 'style', 'meta', 'link', 'head']):
                    script.decompose()
                text_content = soup.get_text()
                char_count = len(text_content)
                total_content_length += char_count
                
            except Exception as e:
                logger.warning(f"⚠️ Error extracting additional SEO data for {url}: {str(e)}")
                continue
        
        avg_content_length = round(total_content_length / total_pages, 0) if total_pages > 0 else 0
        
        return {
            'open_graph': {
                'pages_with_og_tags': pages_with_og,
                'pages_without_og_tags': len(pages_without_og),
                'coverage_percentage': round((pages_with_og / total_pages * 100), 2) if total_pages > 0 else 0,
                'og_tags_found': sorted(list(og_tags_found)),
                'pages_missing_og': pages_without_og[:20]  # Limit to first 20
            },
            'twitter_cards': {
                'pages_with_twitter_tags': pages_with_twitter,
                'pages_without_twitter_tags': len(pages_without_twitter),
                'coverage_percentage': round((pages_with_twitter / total_pages * 100), 2) if total_pages > 0 else 0,
                'twitter_tags_found': sorted(list(twitter_tags_found)),
                'pages_missing_twitter': pages_without_twitter[:20]  # Limit to first 20
            },
            'external_links': {
                'total_external_links': total_external_links,
                'unique_external_domains': len(external_domains),
                'top_external_domains': sorted(external_domains_count.items(), key=lambda x: x[1], reverse=True)[:10]
            },
            'content_analysis': {
                'average_content_length': avg_content_length,
                'total_content_length': total_content_length
            },
            'language_and_encoding': {
                'pages_with_lang_attribute': pages_with_lang,
                'languages_found': sorted(list(languages)),
                'pages_with_encoding': pages_with_encoding,
                'encodings_found': sorted(list(encodings))
            }
        }
    
    def _extract_additional_issues(
        self, 
        all_results: List[Dict], 
        crawlability_info: Dict, 
        orphan_pages: Set
    ) -> List[Dict]:
        """
        Extract additional issues from crawlability, status codes, and other sections.
        These are issues that don't come from the score issues but are important to report.
        """
        additional_issues = []
        total_pages = len(all_results)
        
        # === CRAWLABILITY ISSUES ===
        # No robots.txt - Critical
        if not crawlability_info.get('robots_txt_exists', False):
            additional_issues.append({
                'issue_name': 'Missing robots.txt file',
                'category': 'Technical',
                'type': 'Crawlability',
                'severity': 'critical',
                'number_of_issues': 1,
                'affected_pages_count': 0,
                'description': 'robots.txt file is missing. This file helps search engines understand which pages should be crawled.'
            })
        
        # No sitemaps found - Critical
        all_sitemap_urls = crawlability_info.get('all_sitemap_urls', [])
        if not all_sitemap_urls:
            additional_issues.append({
                'issue_name': 'No sitemaps found',
                'category': 'Technical',
                'type': 'Crawlability',
                'severity': 'critical',
                'number_of_issues': 1,
                'affected_pages_count': 0,
                'description': 'No XML sitemaps were found. Sitemaps help search engines discover and index all pages on your site.'
            })
        
        # No llms.txt - High
        if not crawlability_info.get('llms_txt_exists', False):
            additional_issues.append({
                'issue_name': 'Missing llms.txt file',
                'category': 'Technical',
                'type': 'Crawlability',
                'severity': 'high',
                'number_of_issues': 1,
                'affected_pages_count': 0,
                'description': 'llms.txt file is missing. This file helps LLM agents understand your site structure and content.'
            })
        
        # === ORPHAN PAGES ===
        if orphan_pages:
            additional_issues.append({
                'issue_name': 'Orphan pages (no internal in-links)',
                'category': 'On-Page',
                'type': 'Internal Links',
                'severity': 'high',
                'number_of_issues': 1,
                'affected_pages_count': len(orphan_pages),
                'affected_pages': sorted(list(orphan_pages))[:50],  # Limit to first 50
                'description': f'{len(orphan_pages)} page(s) have no internal links pointing to them, making them hard to discover.'
            })
        
        # === 404 RESPONSES ===
        pages_404 = [r.get('url', '') for r in all_results if r.get('status_code') == 404]
        if pages_404:
            additional_issues.append({
                'issue_name': 'Pages returning 404 Not Found',
                'category': 'Technical',
                'type': 'HTTP Status',
                'severity': 'high',
                'number_of_issues': 1,
                'affected_pages_count': len(pages_404),
                'affected_pages': sorted(pages_404)[:50],  # Limit to first 50
                'description': f'{len(pages_404)} page(s) are returning 404 status codes. These pages should be fixed or redirected.'
            })
        
        # === OVERSIZED IMAGES ===
        # Collect oversized images with criteria
        oversized_images_data = []
        for result in all_results:
            url = result.get('url', '')
            html = result.get('html_content', '')
            if not html:
                continue
            
            try:
                from bs4 import BeautifulSoup
                from urllib.parse import urljoin
                soup = BeautifulSoup(html, 'lxml')
                images = soup.find_all('img')
                
                for img in images:
                    img_src = img.get('src', '') or img.get('data-src', '')
                    if not img_src or (img_src.lower().endswith('.svg') or '.svg' in img_src.lower()):
                        continue  # Skip SVG images
                    
                    img_url = urljoin(url, img_src)
                    width_attr = img.get('width', '')
                    height_attr = img.get('height', '')
                    
                    # Check if image might be oversized
                    # Criteria: Missing dimensions OR dimensions suggest large image (>2000px)
                    is_oversized = False
                    criteria = []
                    
                    if not width_attr or not height_attr:
                        is_oversized = True
                        criteria.append('Missing width/height attributes (can cause layout shift)')
                    else:
                        try:
                            width = int(width_attr)
                            height = int(height_attr)
                            # Check if image dimensions are very large (likely not optimized)
                            if width > 2000 or height > 2000:
                                is_oversized = True
                                criteria.append(f'Large dimensions ({width}x{height}px) - consider resizing')
                            # Check aspect ratio (very wide or tall images might be problematic)
                            if width > 0 and height > 0:
                                aspect_ratio = max(width, height) / min(width, height)
                                if aspect_ratio > 5:
                                    is_oversized = True
                                    criteria.append(f'Extreme aspect ratio ({aspect_ratio:.1f}:1) - may need optimization')
                        except (ValueError, TypeError):
                            is_oversized = True
                            criteria.append('Invalid dimension values')
                    
                    if is_oversized:
                        oversized_images_data.append({
                            'image_url': img_url,
                            'page_url': url,
                            'criteria': criteria,
                            'width': width_attr if width_attr else 'unknown',
                            'height': height_attr if height_attr else 'unknown'
                        })
            except Exception as e:
                logger.warning(f"⚠️ Error checking oversized images for {url}: {str(e)}")
                continue
        
        if oversized_images_data:
            # Limit to first 50 images
            oversized_images_data = oversized_images_data[:50]
            additional_issues.append({
                'issue_name': 'Oversized or unoptimized images',
                'category': 'On-Page',
                'type': 'Image Optimization',
                'severity': 'medium',
                'number_of_issues': 1,
                'number_of_images': len(oversized_images_data),
                'oversized_images': oversized_images_data,
                'criteria': [
                    'Missing width/height attributes (can cause layout shift)',
                    'Large dimensions (>2000px width or height)',
                    'Extreme aspect ratio (>5:1)',
                    'Invalid dimension values'
                ],
                'description': f'{len(oversized_images_data)} image(s) may be oversized or unoptimized. Images are flagged if they: (1) are missing width/height attributes, (2) have dimensions larger than 2000px, (3) have extreme aspect ratios (>5:1), or (4) have invalid dimension values. These issues can cause layout shifts, slow page loads, and poor user experience.'
            })
        
        # === MISSING VIEWPORT (Responsive Design) ===
        pages_missing_viewport = []
        for result in all_results:
            html = result.get('html_content', '')
            if html:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'lxml')
                    viewport = soup.find('meta', attrs={'name': 'viewport'})
                    if not viewport:
                        pages_missing_viewport.append(result.get('url', ''))
                except:
                    pass
        
        if pages_missing_viewport:
            additional_issues.append({
                'issue_name': 'Missing viewport meta tag',
                'category': 'Technical',
                'type': 'Responsive Design',
                'severity': 'high',
                'number_of_issues': 1,
                'affected_pages_count': len(pages_missing_viewport),
                'affected_pages': sorted(pages_missing_viewport)[:50],
                'description': 'Viewport meta tag is missing. This is essential for responsive design and mobile SEO.'
            })
        
        # === MISSING CACHE HEADERS ===
        pages_missing_cache = []
        for result in all_results:
            headers = result.get('headers', {})
            headers_lower = {k.lower(): v for k, v in headers.items()}
            if not headers_lower.get('cache-control'):
                pages_missing_cache.append(result.get('url', ''))
        
        if pages_missing_cache and len(pages_missing_cache) > total_pages * 0.5:  # If more than 50% of pages
            additional_issues.append({
                'issue_name': 'Missing Cache-Control headers',
                'category': 'Technical',
                'type': 'Performance',
                'severity': 'medium',
                'number_of_issues': 1,
                'affected_pages_count': len(pages_missing_cache),
                'affected_pages': sorted(pages_missing_cache)[:50],
                'description': f'{len(pages_missing_cache)} page(s) are missing Cache-Control headers, which can impact page load performance.'
            })
        
        # === MISSING COMPRESSION ===
        pages_without_compression = []
        for result in all_results:
            headers = result.get('headers', {})
            headers_lower = {k.lower(): v for k, v in headers.items()}
            content_encoding = headers_lower.get('content-encoding', '')
            if not content_encoding or content_encoding not in ['gzip', 'deflate', 'br', 'brotli']:
                pages_without_compression.append(result.get('url', ''))
        
        if pages_without_compression and len(pages_without_compression) > total_pages * 0.5:  # If more than 50% of pages
            additional_issues.append({
                'issue_name': 'Missing content compression',
                'category': 'Technical',
                'type': 'Performance',
                'severity': 'medium',
                'number_of_issues': 1,
                'affected_pages_count': len(pages_without_compression),
                'affected_pages': sorted(pages_without_compression)[:50],
                'description': f'{len(pages_without_compression)} page(s) are not using content compression (gzip/deflate/brotli), which can slow down page loads.'
            })
        
        return additional_issues
    
    def _extract_advanced_seo_data(self, all_results: List[Dict]) -> Dict:
        """
        Extract advanced SEO data: Pagination, Caching, Image Optimization, 
        Responsive Design, CDN, Markups, Hreflang.
        """
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse, urljoin
        import re
        
        total_pages = len(all_results)
        
        # Pagination
        pages_with_prev = 0
        pages_with_next = 0
        pages_with_pagination = 0
        pagination_issues = []
        
        # Caching & Compression
        pages_with_cache_control = 0
        pages_with_etag = 0
        pages_with_expires = 0
        pages_with_compression = 0
        pages_missing_cache = []
        cache_control_values = set()
        compression_types = set()
        
        # Image Optimization
        total_images = 0
        webp_images = 0
        avif_images = 0
        lazy_loaded_images = 0
        responsive_images = 0
        images_with_dimensions = 0
        images_without_dimensions = 0
        oversized_images = []  # URLs of images that might be oversized
        
        # Responsive Design
        pages_with_viewport = 0
        pages_with_responsive_images = 0
        pages_with_media_queries = 0
        pages_missing_viewport = []
        
        # CDN Behavior
        cdn_domains = set()
        static_resource_domains = set()
        pages_using_cdn = 0
        cdn_domains_found = []
        
        # Markups/Structured Data
        pages_with_json_ld = 0
        pages_with_microdata = 0
        pages_with_rdfa = 0
        schema_types_found = set()
        total_schemas = 0
        
        # Hreflang
        pages_with_hreflang = 0
        hreflang_languages = set()
        hreflang_issues = []
        
        for result in all_results:
            url = result.get('url', '')
            html = result.get('html_content', '')
            headers = result.get('headers', {})
            
            if not html:
                continue
            
            try:
                soup = BeautifulSoup(html, 'lxml')
                base_domain = urlparse(self.base_url).netloc
                base_parsed = urlparse(self.base_url)
                
                # === PAGINATION HANDLING ===
                prev_link = soup.find('link', rel='prev')
                next_link = soup.find('link', rel='next')
                pagination_keywords = ['pagination', 'page', 'next', 'previous', 'prev']
                pagination_elements = soup.find_all(['nav', 'ul', 'div'], 
                    class_=re.compile('|'.join(pagination_keywords), re.I))
                
                has_pagination = False
                if prev_link or next_link:
                    has_pagination = True
                    pages_with_prev += 1 if prev_link else 0
                    pages_with_next += 1 if next_link else 0
                elif pagination_elements:
                    has_pagination = True
                
                if has_pagination:
                    pages_with_pagination += 1
                elif not has_pagination and total_pages > 1:
                    # Check if URL looks like it might need pagination (e.g., /page/2, ?page=2)
                    if re.search(r'[/?]page[=/]\d+', url, re.I):
                        pagination_issues.append(url)
                
                # === CACHING & COMPRESSION ===
                headers_lower = {k.lower(): v for k, v in headers.items()}
                
                cache_control = headers_lower.get('cache-control', '')
                if cache_control:
                    pages_with_cache_control += 1
                    cache_control_values.add(cache_control)
                else:
                    pages_missing_cache.append(url)
                
                if headers_lower.get('etag'):
                    pages_with_etag += 1
                
                if headers_lower.get('expires'):
                    pages_with_expires += 1
                
                content_encoding = headers_lower.get('content-encoding', '')
                if content_encoding and content_encoding in ['gzip', 'deflate', 'br', 'brotli']:
                    pages_with_compression += 1
                    compression_types.add(content_encoding)
                
                # === IMAGE OPTIMIZATION ===
                images = soup.find_all('img')
                page_images = []
                
                for img in images:
                    total_images += 1
                    img_src = img.get('src', '') or img.get('data-src', '')
                    
                    if img_src:
                        img_url = urljoin(url, img_src)
                        img_lower = img_url.lower()
                        
                        # Check formats
                        if '.webp' in img_lower:
                            webp_images += 1
                        elif '.avif' in img_lower:
                            avif_images += 1
                        
                        # Check lazy loading
                        if img.get('loading') == 'lazy' or 'lazy' in img.get('class', []):
                            lazy_loaded_images += 1
                        
                        # Check responsive images (srcset)
                        if img.get('srcset'):
                            responsive_images += 1
                        
                        # Check dimensions
                        width_attr = img.get('width', '')
                        height_attr = img.get('height', '')
                        if width_attr and height_attr:
                            images_with_dimensions += 1
                            # Check if dimensions suggest oversized image
                            try:
                                width = int(width_attr)
                                height = int(height_attr)
                                # Flag if dimensions are very large (>2000px) or extreme aspect ratio
                                if width > 2000 or height > 2000:
                                    oversized_images.append(img_url)
                                elif width > 0 and height > 0:
                                    aspect_ratio = max(width, height) / min(width, height)
                                    if aspect_ratio > 5:
                                        oversized_images.append(img_url)
                            except (ValueError, TypeError):
                                # Invalid dimensions, treat as potentially oversized
                                oversized_images.append(img_url)
                        else:
                            images_without_dimensions += 1
                            # Missing dimensions can cause layout shift and indicate potential optimization issues
                            if img_src:
                                oversized_images.append(img_url)
                
                # === RESPONSIVE DESIGN ===
                viewport = soup.find('meta', attrs={'name': 'viewport'})
                if viewport:
                    pages_with_viewport += 1
                else:
                    pages_missing_viewport.append(url)
                
                # Check for responsive images (srcset/sizes)
                if soup.find_all('img', srcset=True):
                    pages_with_responsive_images += 1
                
                # Check for media queries in style tags (simplified)
                style_tags = soup.find_all('style')
                for style in style_tags:
                    if style.string and '@media' in style.string:
                        pages_with_media_queries += 1
                        break
                
                # Check link tags with media attributes
                if soup.find_all('link', attrs={'media': True}):
                    pages_with_media_queries += 1
                
                # === CDN BEHAVIOR ===
                # Check static resources (images, CSS, JS)
                static_resources = []
                for img in soup.find_all('img', src=True):
                    img_url = urljoin(url, img.get('src', ''))
                    static_resources.append(urlparse(img_url).netloc)
                
                for link in soup.find_all('link', rel='stylesheet', href=True):
                    css_url = urljoin(url, link.get('href', ''))
                    static_resources.append(urlparse(css_url).netloc)
                
                for script in soup.find_all('script', src=True):
                    js_url = urljoin(url, script.get('src', ''))
                    static_resources.append(urlparse(js_url).netloc)
                
                # Identify CDN domains (different from base domain)
                for resource_domain in static_resources:
                    if resource_domain and resource_domain != base_domain:
                        static_resource_domains.add(resource_domain)
                        # Check for common CDN indicators
                        if any(cdn in resource_domain.lower() for cdn in ['cdn', 'cloudfront', 'cloudflare', 'fastly', 'akamai']):
                            cdn_domains.add(resource_domain)
                
                # Check CDN headers
                cdn_headers = ['cf-ray', 'x-cache', 'x-served-by', 'x-cdn']
                has_cdn_headers = any(h in headers_lower for h in cdn_headers)
                has_cdn_domains = len(cdn_domains) > 0
                
                # Count page as using CDN if it has CDN headers OR CDN domains (count only once per page)
                if has_cdn_headers or has_cdn_domains:
                    pages_using_cdn += 1
                    if has_cdn_domains:
                        cdn_domains_found.extend(list(cdn_domains))
                
                # === MARKUPS/STRUCTURED DATA ===
                # JSON-LD
                json_ld_scripts = soup.find_all('script', type='application/ld+json')
                if json_ld_scripts:
                    pages_with_json_ld += 1
                    total_schemas += len(json_ld_scripts)
                    for script in json_ld_scripts:
                        try:
                            import json
                            data = json.loads(script.string)
                            if isinstance(data, dict) and '@type' in data:
                                schema_types_found.add(data['@type'])
                            elif isinstance(data, list):
                                for item in data:
                                    if isinstance(item, dict) and '@type' in item:
                                        schema_types_found.add(item['@type'])
                        except:
                            pass
                
                # Microdata (itemscope)
                if soup.find_all(attrs={'itemscope': True}):
                    pages_with_microdata += 1
                    microdata_types = soup.find_all(attrs={'itemtype': True})
                    for item in microdata_types:
                        itemtype = item.get('itemtype', '')
                        if itemtype:
                            schema_types_found.add(itemtype.split('/')[-1])
                
                # RDFa (already handled in technical audit, but count here too)
                if soup.find_all(attrs={'typeof': True}) or soup.find_all(attrs={'property': True, 'vocab': True}):
                    pages_with_rdfa += 1
                
                # === HREFLANG USAGE ===
                hreflang_links = soup.find_all('link', rel='alternate', hreflang=True)
                if hreflang_links:
                    pages_with_hreflang += 1
                    for link in hreflang_links:
                        hreflang = link.get('hreflang', '').lower()
                        href = link.get('href', '')
                        
                        if hreflang:
                            hreflang_languages.add(hreflang)
                        
                        # Check for common issues
                        if hreflang == 'x-default' and not href:
                            hreflang_issues.append(f"{url}: x-default without href")
                        
                        # Check if hreflang URL is absolute
                        if href and not href.startswith(('http://', 'https://')):
                            hreflang_issues.append(f"{url}: Relative hreflang URL: {href}")
                
            except Exception as e:
                logger.warning(f"⚠️ Error extracting advanced SEO data for {url}: {str(e)}")
                continue
        
        # Calculate percentages and prepare final data
        return {
            'pagination': {
                'pages_with_pagination': pages_with_pagination,
                'pages_with_prev_next': pages_with_prev + pages_with_next,
                'pagination_coverage_percentage': round((pages_with_pagination / total_pages * 100), 2) if total_pages > 0 else 0,
                'pagination_issues': pagination_issues[:20]  # Limit to first 20
            },
            'caching_compression': {
                'pages_with_cache_control': pages_with_cache_control,
                'pages_with_etag': pages_with_etag,
                'pages_with_expires': pages_with_expires,
                'pages_with_compression': pages_with_compression,
                'cache_coverage_percentage': round((pages_with_cache_control / total_pages * 100), 2) if total_pages > 0 else 0,
                'compression_coverage_percentage': round((pages_with_compression / total_pages * 100), 2) if total_pages > 0 else 0,
                'compression_types': sorted(list(compression_types)),
                'pages_missing_cache': pages_missing_cache[:20]  # Limit to first 20
            },
            'image_optimization': {
                'total_images': total_images,
                'webp_images': webp_images,
                'avif_images': avif_images,
                'lazy_loaded_images': lazy_loaded_images,
                'responsive_images': responsive_images,
                'images_with_dimensions': images_with_dimensions,
                'images_without_dimensions': images_without_dimensions,
                'lazy_loading_percentage': round((lazy_loaded_images / total_images * 100), 2) if total_images > 0 else 0,
                'responsive_images_percentage': round((responsive_images / total_images * 100), 2) if total_images > 0 else 0,
                'modern_format_percentage': round(((webp_images + avif_images) / total_images * 100), 2) if total_images > 0 else 0,
                'oversized_images_sample': oversized_images[:20]  # Limit to first 20
            },
            'responsive_design': {
                'pages_with_viewport': pages_with_viewport,
                'pages_with_responsive_images': pages_with_responsive_images,
                'pages_with_media_queries': pages_with_media_queries,
                'viewport_coverage_percentage': round((pages_with_viewport / total_pages * 100), 2) if total_pages > 0 else 0,
                'pages_missing_viewport': pages_missing_viewport[:20]  # Limit to first 20
            },
            'cdn_behavior': {
                'pages_using_cdn': pages_using_cdn,
                'cdn_coverage_percentage': round((pages_using_cdn / total_pages * 100), 2) if total_pages > 0 else 0,
                'cdn_domains_found': sorted(list(set(cdn_domains_found)))[:10],  # Top 10 CDN domains
                'unique_static_resource_domains': len(static_resource_domains),
                'static_resource_domains': sorted(list(static_resource_domains))[:10]
            },
            'markups': {
                'pages_with_json_ld': pages_with_json_ld,
                'pages_with_microdata': pages_with_microdata,
                'pages_with_rdfa': pages_with_rdfa,
                'total_schemas_found': total_schemas,
                'unique_schema_types': len(schema_types_found),
                'schema_types_found': sorted(list(schema_types_found))[:20],  # Top 20 schema types
                'json_ld_coverage_percentage': round((pages_with_json_ld / total_pages * 100), 2) if total_pages > 0 else 0
            },
            'hreflang_usage': {
                'pages_with_hreflang': pages_with_hreflang,
                'hreflang_coverage_percentage': round((pages_with_hreflang / total_pages * 100), 2) if total_pages > 0 else 0,
                'unique_languages': len(hreflang_languages),
                'languages_found': sorted(list(hreflang_languages)),
                'hreflang_issues': hreflang_issues[:20]  # Limit to first 20
            }
        }

