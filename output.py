"""
Output module for generating CSV, JSON, and console reports.
"""
import json
import csv
import pandas as pd
import re
from typing import Dict, List, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OutputGenerator:
    """Generate various output formats for SEO audit results."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def generate_json(self, all_results: List[Dict], output_file: str = None) -> str:
        """
        Generate JSON output with all audit results.
        
        Args:
            all_results: List of audit result dicts
            output_file: Optional output file path
            
        Returns:
            JSON string
        """
        if output_file is None:
            output_file = f"seo_audit_{self.timestamp}.json"
        
        output_data = {
            'base_url': self.base_url,
            'timestamp': self.timestamp,
            'total_pages': len(all_results),
            'results': all_results
        }
        
        json_str = json.dumps(output_data, indent=2, ensure_ascii=False)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        logger.info(f"✅ JSON report saved to: {output_file}")
        return output_file
    
    def generate_stats_json(self, all_results: List[Dict], site_stats: Dict, 
                           crawlability_info: Dict, duplicate_titles: Dict,
                           duplicate_descriptions: Dict, duplicate_h1s: Dict,
                           orphan_pages: Set, output_file: str = None) -> str:
        """
        Generate stats-only JSON with final statistics (no detailed issues).
        
        Args:
            all_results: List of audit result dicts
            site_stats: Site-wide statistics
            crawlability_info: Robots.txt and sitemap info
            duplicate_titles: Dict of duplicate titles
            duplicate_descriptions: Dict of duplicate descriptions
            duplicate_h1s: Dict of duplicate H1s
            orphan_pages: Set of orphan page URLs
            output_file: Optional output file path
            
        Returns:
            JSON file path
        """
        if output_file is None:
            output_file = f"seo_audit_stats_{self.timestamp}.json"
        
        total_pages = len(all_results)
        
        # Status code distribution
        status_codes = {}
        for result in all_results:
            code = result.get('status_code', 0)
            status_codes[str(code)] = status_codes.get(str(code), 0) + 1
        
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
        
        # On-page SEO statistics
        pages_with_title = sum(1 for r in all_results 
                              if r.get('onpage', {}).get('title', {}).get('has_title', False))
        pages_with_meta_desc = sum(1 for r in all_results 
                                  if r.get('onpage', {}).get('meta_description', {}).get('has_meta_description', False))
        pages_with_h1 = sum(1 for r in all_results 
                           if r.get('onpage', {}).get('h1', {}).get('h1_count', 0) > 0)
        pages_without_h1_count = sum(1 for r in all_results 
                                     if r.get('onpage', {}).get('h1', {}).get('h1_count', 0) == 0)
        multiple_h1_pages_count = sum(1 for r in all_results 
                                      if r.get('onpage', {}).get('h1', {}).get('h1_count', 0) > 1)
        total_images = sum(r.get('onpage', {}).get('image_alt', {}).get('total_images', 0) for r in all_results)
        images_without_alt = sum(r.get('onpage', {}).get('image_alt', {}).get('images_without_alt', 0) for r in all_results)
        total_internal_links = sum(r.get('onpage', {}).get('internal_links', {}).get('internal_link_count', 0) for r in all_results)
        broken_internal_links = sum(r.get('onpage', {}).get('internal_links', {}).get('broken_link_count', 0) for r in all_results)
        
        # Build stats-only JSON
        stats_data = {
            'site_overview': {
                'base_url': self.base_url,
                'timestamp': self.timestamp,
                'total_crawled_pages': total_pages,
                'average_seo_score': round(site_stats.get('average_score', 0), 2),
                'total_issues': site_stats.get('total_issues', 0),
                'critical_issues_count': site_stats.get('critical_issues', 0),
                'high_issues_count': site_stats.get('high_issues', 0),
                'medium_issues_count': site_stats.get('medium_issues', 0),
                'low_issues_count': site_stats.get('low_issues', 0)
            },
            'crawlability': {
                'robots_txt_exists': crawlability_info.get('robots_txt_exists', False),
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
                }
            },
            'onpage_seo': {
                'title_tags': {
                    'pages_with_title': pages_with_title,
                    'coverage_percentage': round((pages_with_title / total_pages * 100), 2) if total_pages > 0 else 0,
                    'duplicate_titles_count': len(duplicate_titles)
                },
                'meta_descriptions': {
                    'pages_with_meta_description': pages_with_meta_desc,
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
                'image_alt_text': {
                    'total_images': total_images,
                    'images_without_alt': images_without_alt,
                    'compliance_percentage': round(((total_images - images_without_alt) / total_images * 100), 2) if total_images > 0 else 100
                },
                'internal_linking': {
                    'total_internal_links': total_internal_links,
                    'broken_internal_links': broken_internal_links,
                    'orphan_pages_count': len(orphan_pages)
                }
            }
        }
        
        json_str = json.dumps(stats_data, indent=2, ensure_ascii=False)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        logger.info(f"✅ Stats JSON report saved to: {output_file}")
        return output_file
    
    def generate_issues_json(self, all_results: List[Dict], site_stats: Dict, 
                             crawlability_info: Dict, duplicate_titles: Dict,
                             duplicate_descriptions: Dict, duplicate_h1s: Dict,
                             orphan_pages: Set, output_file: str = None) -> str:
        """
        Generate detailed issues JSON with all issues and affected pages.
        
        Args:
            all_results: List of audit result dicts
            site_stats: Site-wide statistics
            crawlability_info: Robots.txt and sitemap info
            duplicate_titles: Dict of duplicate titles
            duplicate_descriptions: Dict of duplicate descriptions
            duplicate_h1s: Dict of duplicate H1s
            orphan_pages: Set of orphan page URLs
            output_file: Optional output file path
            
        Returns:
            JSON file path
        """
        if output_file is None:
            output_file = f"seo_audit_issues_{self.timestamp}.json"
        
        # Group issues by type and collect URLs
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
                        'number_of_issues': 0,
                        'affected_pages': [],
                        'links_without_anchor_text': set()
                    }
                issues_by_type[issue_key]['number_of_issues'] += 1
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
                'number_of_issues': issue_data['number_of_issues'],
                'affected_pages_count': len(set(issue_data['affected_pages'])),
                'affected_pages': list(set(issue_data['affected_pages']))
            }
            
            # For "Link without anchor text" issue, add the links information
            if issue_data['issue_name'] == "Link without anchor text" and issue_data['links_without_anchor_text']:
                issue_dict['total_links_without_anchor_text'] = len(issue_data['links_without_anchor_text'])
                issue_dict['links_without_anchor_text'] = sorted(list(issue_data['links_without_anchor_text']))
            
            issues_list.append(issue_dict)
        
        issues_list.sort(key=lambda x: (severity_order.get(x['severity'], 4), -x['affected_pages_count']))
        
        # Calculate Technical SEO details
        total_pages = len(all_results)
        
        # Technical SEO - Noindex
        noindex_pages = [r.get('url', '') for r in all_results 
                        if r.get('technical', {}).get('noindex', {}).get('has_noindex', False)]
        
        # Technical SEO - Meta Robots
        meta_robots_details = []
        for r in all_results:
            meta_robots = r.get('technical', {}).get('meta_robots', {})
            if meta_robots.get('has_meta_robots', False):
                meta_robots_details.append({
                    'url': r.get('url', ''),
                    'meta_content': meta_robots.get('meta_content', ''),
                    'header_content': meta_robots.get('header_content', '')
                })
        
        # Technical SEO - Canonical
        canonical_issues_details = []
        for r in all_results:
            canonical = r.get('technical', {}).get('canonical', {})
            if canonical.get('issues', []):
                canonical_issues_details.append({
                    'url': r.get('url', ''),
                    'canonical_url': canonical.get('canonical_url', ''),
                    'issues': canonical.get('issues', [])
                })
        
        # Technical SEO - Redirects
        redirect_issues_details = []
        for r in all_results:
            redirects = r.get('technical', {}).get('redirects', {})
            if redirects.get('issues', []):
                redirect_issues_details.append({
                    'url': r.get('url', ''),
                    'status_code': redirects.get('status_code', 0),
                    'redirect_chain_length': redirects.get('redirect_chain_length', 0),
                    'issues': redirects.get('issues', [])
                })
        
        # Technical SEO - HTTPS/Mixed Content
        mixed_content_details = []
        for r in all_results:
            https = r.get('technical', {}).get('https', {})
            if https.get('mixed_content_count', 0) > 0:
                mixed_content_details.append({
                    'url': r.get('url', ''),
                    'mixed_content_count': https.get('mixed_content_count', 0),
                    'issues': https.get('issues', [])[:5]  # Limit issues
                })
        
        non_https_pages = [r.get('url', '') for r in all_results 
                          if not r.get('technical', {}).get('https', {}).get('is_https', True)]
        
        # Technical SEO - Structured Data
        structured_data_details = []
        for r in all_results:
            structured_data = r.get('technical', {}).get('structured_data', {})
            if structured_data.get('errors', []):
                structured_data_details.append({
                    'url': r.get('url', ''),
                    'errors': structured_data.get('errors', []),
                    'schema_types': structured_data.get('schema_types', [])
                })
        
        # On-Page SEO - Title Tags
        title_issues_details = []
        for r in all_results:
            title = r.get('onpage', {}).get('title', {})
            if title.get('issues', []):
                title_issues_details.append({
                    'url': r.get('url', ''),
                    'title_text': title.get('title_text', ''),
                    'title_length': title.get('title_length', 0),
                    'issues': title.get('issues', [])
                })
        
        pages_without_title = [r.get('url', '') for r in all_results 
                              if not r.get('onpage', {}).get('title', {}).get('has_title', False)]
        
        # On-Page SEO - Meta Descriptions
        meta_desc_issues_details = []
        for r in all_results:
            meta_desc = r.get('onpage', {}).get('meta_description', {})
            if meta_desc.get('issues', []):
                meta_desc_issues_details.append({
                    'url': r.get('url', ''),
                    'description_length': meta_desc.get('description_length', 0),
                    'issues': meta_desc.get('issues', [])
                })
        
        pages_without_meta_desc = [r.get('url', '') for r in all_results 
                                  if not r.get('onpage', {}).get('meta_description', {}).get('has_meta_description', False)]
        
        # On-Page SEO - H1 Tags
        h1_issues_details = []
        for r in all_results:
            h1 = r.get('onpage', {}).get('h1', {})
            if h1.get('issues', []):
                h1_issues_details.append({
                    'url': r.get('url', ''),
                    'h1_count': h1.get('h1_count', 0),
                    'h1_texts': h1.get('h1_texts', []),
                    'issues': h1.get('issues', [])
                })
        
        pages_without_h1 = [r.get('url', '') for r in all_results 
                           if r.get('onpage', {}).get('h1', {}).get('h1_count', 0) == 0]
        multiple_h1_pages = [r.get('url', '') for r in all_results 
                            if r.get('onpage', {}).get('h1', {}).get('h1_count', 0) > 1]
        
        # On-Page SEO - Image Alt Text
        image_alt_issues_details = []
        for r in all_results:
            image_alt = r.get('onpage', {}).get('image_alt', {})
            if image_alt.get('images_without_alt', 0) > 0:
                image_alt_issues_details.append({
                    'url': r.get('url', ''),
                    'total_images': image_alt.get('total_images', 0),
                    'images_without_alt': image_alt.get('images_without_alt', 0),
                    'issues': image_alt.get('issues', [])[:5]
                })
        
        # On-Page SEO - Internal Linking
        internal_link_issues_details = []
        for r in all_results:
            internal_links = r.get('onpage', {}).get('internal_links', {})
            if internal_links.get('issues', []):
                internal_link_issues_details.append({
                    'url': r.get('url', ''),
                    'internal_link_count': internal_links.get('internal_link_count', 0),
                    'broken_link_count': internal_links.get('broken_link_count', 0),
                    'issues': internal_links.get('issues', [])[:5]
                })
        
        # Build detailed issues JSON
        issues_data = {
            'site_overview': {
                'base_url': self.base_url,
                'timestamp': self.timestamp,
                'total_crawled_pages': total_pages,
                'average_seo_score': round(site_stats.get('average_score', 0), 2),
                'total_issues': site_stats.get('total_issues', 0),
                'critical_issues_count': site_stats.get('critical_issues', 0),
                'high_issues_count': site_stats.get('high_issues', 0),
                'medium_issues_count': site_stats.get('medium_issues', 0),
                'low_issues_count': site_stats.get('low_issues', 0)
            },
            'crawlability': {
                'robots_txt_exists': crawlability_info.get('robots_txt_exists', False),
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
                },
                'all_issues': issues_list
            },
            'technical_seo': {
                'noindex': {
                    'pages_with_noindex': {
                        'count': len(noindex_pages),
                        'pages': noindex_pages
                    }
                },
                'meta_robots': {
                    'pages_with_meta_robots': {
                        'count': len(meta_robots_details),
                        'details': meta_robots_details
                    }
                },
                'canonical_tags': {
                    'pages_with_canonical_issues': {
                        'count': len(canonical_issues_details),
                        'details': canonical_issues_details
                    }
                },
                'redirects': {
                    'pages_with_redirect_issues': {
                        'count': len(redirect_issues_details),
                        'details': redirect_issues_details
                    }
                },
                'https': {
                    'non_https_pages': {
                        'count': len(non_https_pages),
                        'pages': non_https_pages
                    },
                    'mixed_content_pages': {
                        'count': len(mixed_content_details),
                        'details': mixed_content_details
                    }
                },
                'structured_data': {
                    'pages_with_structured_data_errors': {
                        'count': len(structured_data_details),
                        'details': structured_data_details
                    }
                }
            },
            'onpage_seo': {
                'title_tags': {
                    'pages_without_title': {
                        'count': len(pages_without_title),
                        'pages': pages_without_title
                    },
                    'pages_with_title_issues': {
                        'count': len(title_issues_details),
                        'details': title_issues_details
                    },
                    'duplicate_titles': {
                        'count': len(duplicate_titles),
                        'details': [{'title': title, 'pages': urls} for title, urls in duplicate_titles.items()]
                    }
                },
                'meta_descriptions': {
                    'pages_without_meta_description': {
                        'count': len(pages_without_meta_desc),
                        'pages': pages_without_meta_desc
                    },
                    'pages_with_meta_description_issues': {
                        'count': len(meta_desc_issues_details),
                        'details': meta_desc_issues_details
                    },
                    'duplicate_descriptions': {
                        'count': len(duplicate_descriptions),
                        'details': [{'description': desc[:100], 'pages': urls} for desc, urls in duplicate_descriptions.items()]
                    }
                },
                'h1_tags': {
                    'pages_without_h1': {
                        'count': len(pages_without_h1),
                        'pages': pages_without_h1
                    },
                    'pages_with_multiple_h1': {
                        'count': len(multiple_h1_pages),
                        'pages': multiple_h1_pages
                    },
                    'pages_with_h1_issues': {
                        'count': len(h1_issues_details),
                        'details': h1_issues_details
                    },
                    'duplicate_h1s': {
                        'count': len(duplicate_h1s),
                        'details': [{'h1_text': h1_text, 'pages': urls} for h1_text, urls in duplicate_h1s.items()]
                    }
                },
                'image_alt_text': {
                    'pages_with_image_alt_issues': {
                        'count': len(image_alt_issues_details),
                        'details': image_alt_issues_details
                    }
                },
                'internal_linking': {
                    'orphan_pages': {
                        'count': len(orphan_pages),
                        'pages': list(orphan_pages)
                    },
                    'pages_with_internal_link_issues': {
                        'count': len(internal_link_issues_details),
                        'details': internal_link_issues_details
                    }
                }
            }
        }
        
        json_str = json.dumps(issues_data, indent=2, ensure_ascii=False)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        logger.info(f"✅ Issues JSON report saved to: {output_file}")
        return output_file
    
    def _normalize_issue_message(self, message: str) -> str:
        """
        Normalize issue message to remove dynamic values and counts.
        
        Args:
            message: Original issue message
            
        Returns:
            Normalized issue message
        """
        if not message:
            return message
        
        original = message
        
        # Normalize "Link without anchor text: URL" to just "Link without anchor text"
        # "Link without anchor text: https://..." -> "Link without anchor text"
        if message.startswith("Link without anchor text:"):
            return "Link without anchor text"
        
        # Remove leading numbers from "image(s) missing alt text" pattern
        # "6 image(s) missing alt text" -> "image(s) missing alt text"
        # "2 image(s) missing alt text" -> "image(s) missing alt text"
        message = re.sub(r'^\d+\s+(image\(s\)\s+missing\s+alt\s+text)', r'\1', message, flags=re.IGNORECASE)
        
        # Remove character counts from title/description length issues
        # "Title too short (26 chars, recommended: 30-70)" -> "Title too short"
        # "Title too long (85 chars, recommended: 30-70)" -> "Title too long"
        message = re.sub(r'\s*\([^)]*chars[^)]*\)', '', message)
        message = re.sub(r'\s*,\s*recommended:.*$', '', message)
        message = re.sub(r'\s*\(recommended:.*?\)', '', message)
        
        # Remove numbers from other patterns like "2 resource(s) loaded via HTTP"
        # "resource(s) loaded via HTTP" -> "resource(s) loaded via HTTP"
        message = re.sub(r'^\d+\s+(resource\(s\)|script\(s\)|stylesheet\(s\))', r'\1', message, flags=re.IGNORECASE)
        
        # Remove any remaining trailing parentheses with numbers/chars/details
        message = re.sub(r'\s*\([^)]*\)\s*$', '', message)
        
        # Clean up extra spaces
        message = re.sub(r'\s+', ' ', message).strip()
        
        # If normalization removed everything, return original
        if not message:
            return original
        
        return message
    
    def generate_site_summary_json(self, all_results: List[Dict], site_stats: Dict, 
                                   crawlability_info: Dict, duplicate_titles: Dict,
                                   duplicate_descriptions: Dict, duplicate_h1s: Dict,
                                   orphan_pages: Set, output_file: str = None) -> str:
        """
        Generate overall site audit summary JSON with issues grouped and statistics.
        
        Args:
            all_results: List of audit result dicts
            site_stats: Site-wide statistics
            crawlability_info: Robots.txt and sitemap info
            duplicate_titles: Dict of duplicate titles
            duplicate_descriptions: Dict of duplicate descriptions
            duplicate_h1s: Dict of duplicate H1s
            orphan_pages: Set of orphan page URLs
            output_file: Optional output file path
            
        Returns:
            JSON file path
        """
        if output_file is None:
            output_file = f"seo_audit_summary_{self.timestamp}.json"
        
        # Group issues by type and collect URLs
        issues_by_type = {}
        for result in all_results:
            url = result.get('url', '')
            issues = result.get('score', {}).get('issues', [])
            
            for issue in issues:
                original_message = issue.get('message', '')
                normalized_message = self._normalize_issue_message(original_message)
                
                # Use normalized message for grouping, but keep original message for display if needed
                issue_key = f"{issue.get('category', 'Unknown')} - {issue.get('type', 'Unknown')} - {normalized_message}"
                
                if issue_key not in issues_by_type:
                    issues_by_type[issue_key] = {
                        'issue_name': normalized_message,
                        'category': issue.get('category', 'Unknown'),
                        'type': issue.get('type', 'Unknown'),
                        'severity': issue.get('severity', 'low'),
                        'number_of_issues': 0,
                        'affected_pages': [],
                        'links_without_anchor_text': set()  # Store unique links for "Link without anchor text" issue
                    }
                issues_by_type[issue_key]['number_of_issues'] += 1
                issues_by_type[issue_key]['affected_pages'].append(url)
                
                # Extract link URL from "Link without anchor text: URL" messages
                if normalized_message == "Link without anchor text" and original_message.startswith("Link without anchor text:"):
                    link_url = original_message.replace("Link without anchor text:", "").strip()
                    # Note: URL might be truncated (limited to 50 chars in onpage_audit.py)
                    # We collect what we have - full URLs will need to be checked in detailed reports
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
                'number_of_issues': issue_data['number_of_issues'],
                'affected_pages_count': len(set(issue_data['affected_pages'])),  # Use unique pages
                'affected_pages': list(set(issue_data['affected_pages']))  # Remove duplicates
            }
            
            # For "Link without anchor text" issue, add the links information
            if issue_data['issue_name'] == "Link without anchor text" and issue_data['links_without_anchor_text']:
                issue_dict['total_links_without_anchor_text'] = len(issue_data['links_without_anchor_text'])
                issue_dict['links_without_anchor_text'] = sorted(list(issue_data['links_without_anchor_text']))
            
            issues_list.append(issue_dict)
        
        issues_list.sort(key=lambda x: (severity_order.get(x['severity'], 4), -x['affected_pages_count']))
        
        # Calculate additional statistics
        total_pages = len(all_results)
        
        # Status code distribution
        status_codes = {}
        for result in all_results:
            code = result.get('status_code', 0)
            status_codes[str(code)] = status_codes.get(str(code), 0) + 1
        
        # Technical SEO statistics
        noindex_pages = [r.get('url', '') for r in all_results 
                        if r.get('technical', {}).get('noindex', {}).get('has_noindex', False)]
        pages_with_canonical = sum(1 for r in all_results 
                                  if r.get('technical', {}).get('canonical', {}).get('has_canonical', False))
        pages_with_canonical_issues = [r.get('url', '') for r in all_results 
                                      if r.get('technical', {}).get('canonical', {}).get('issues', [])]
        
        https_pages = sum(1 for r in all_results 
                         if r.get('technical', {}).get('https', {}).get('is_https', False))
        mixed_content_pages = [r.get('url', '') for r in all_results 
                              if r.get('technical', {}).get('https', {}).get('mixed_content_count', 0) > 0]
        
        pages_with_structured_data = sum(1 for r in all_results 
                                        if r.get('technical', {}).get('structured_data', {}).get('has_structured_data', False))
        schema_types = set()
        for r in all_results:
            types = r.get('technical', {}).get('structured_data', {}).get('schema_types', [])
            schema_types.update(types)
        
        redirect_issues = [r.get('url', '') for r in all_results 
                          if r.get('technical', {}).get('redirects', {}).get('issues', [])]
        
        # On-page SEO statistics
        pages_with_title = sum(1 for r in all_results 
                              if r.get('onpage', {}).get('title', {}).get('has_title', False))
        pages_with_meta_desc = sum(1 for r in all_results 
                                  if r.get('onpage', {}).get('meta_description', {}).get('has_meta_description', False))
        pages_with_h1 = sum(1 for r in all_results 
                           if r.get('onpage', {}).get('h1', {}).get('h1_count', 0) > 0)
        pages_without_h1 = [r.get('url', '') for r in all_results 
                           if r.get('onpage', {}).get('h1', {}).get('h1_count', 0) == 0]
        multiple_h1_pages = [r.get('url', '') for r in all_results 
                            if r.get('onpage', {}).get('h1', {}).get('h1_count', 0) > 1]
        
        total_images = sum(r.get('onpage', {}).get('image_alt', {}).get('total_images', 0) for r in all_results)
        images_without_alt = sum(r.get('onpage', {}).get('image_alt', {}).get('images_without_alt', 0) for r in all_results)
        
        total_internal_links = sum(r.get('onpage', {}).get('internal_links', {}).get('internal_link_count', 0) for r in all_results)
        broken_internal_links = sum(r.get('onpage', {}).get('internal_links', {}).get('broken_link_count', 0) for r in all_results)
        
        # Build summary JSON
        summary_data = {
            'site_overview': {
                'base_url': self.base_url,
                'timestamp': self.timestamp,
                'total_crawled_pages': total_pages,
                'average_seo_score': site_stats.get('average_score', 0),
                'total_issues': site_stats.get('total_issues', 0),
                'critical_issues_count': site_stats.get('critical_issues', 0),
                'high_issues_count': site_stats.get('high_issues', 0),
                'medium_issues_count': site_stats.get('medium_issues', 0),
                'low_issues_count': site_stats.get('low_issues', 0)
            },
            'crawlability': {
                'robots_txt_exists': crawlability_info.get('robots_txt_exists', False),
                'sitemap_exists': len(crawlability_info.get('all_sitemap_urls', [])) > 0,
                'all_sitemap_urls': crawlability_info.get('all_sitemap_urls', []),
                'total_sitemap_links_count': crawlability_info.get('total_sitemap_links_count', 0)
            },
            'status_code_distribution': status_codes,
            'issues_summary': {
                'total_unique_issue_types': len(issues_list),
                'issues_by_severity': {
                    'critical': [i for i in issues_list if i['severity'] == 'critical'],
                    'high': [i for i in issues_list if i['severity'] == 'high'],
                    'medium': [i for i in issues_list if i['severity'] == 'medium'],
                    'low': [i for i in issues_list if i['severity'] == 'low']
                },
                'all_issues': issues_list
            },
            'technical_seo_overview': {
                'noindex_pages': {
                    'count': len(noindex_pages),
                    'pages': noindex_pages
                },
                'canonical_tags': {
                    'pages_with_canonical': pages_with_canonical,
                    'pages_with_canonical_issues': {
                        'count': len(pages_with_canonical_issues),
                        'pages': pages_with_canonical_issues
                    }
                },
                'https': {
                    'https_pages_count': https_pages,
                    'https_coverage_percentage': round((https_pages / total_pages * 100), 2) if total_pages > 0 else 0,
                    'mixed_content_pages': {
                        'count': len(mixed_content_pages),
                        'pages': mixed_content_pages
                    }
                },
                'structured_data': {
                    'pages_with_structured_data': pages_with_structured_data,
                    'coverage_percentage': round((pages_with_structured_data / total_pages * 100), 2) if total_pages > 0 else 0,
                    'schema_types_found': list(schema_types)
                },
                'redirects': {
                    'pages_with_redirect_issues': {
                        'count': len(redirect_issues),
                        'pages': redirect_issues
                    }
                }
            },
            'onpage_seo_overview': {
                'title_tags': {
                    'pages_with_title': pages_with_title,
                    'coverage_percentage': round((pages_with_title / total_pages * 100), 2) if total_pages > 0 else 0,
                    'duplicate_titles_count': len(duplicate_titles)
                },
                'meta_descriptions': {
                    'pages_with_meta_description': pages_with_meta_desc,
                    'coverage_percentage': round((pages_with_meta_desc / total_pages * 100), 2) if total_pages > 0 else 0,
                    'duplicate_descriptions_count': len(duplicate_descriptions)
                },
                'h1_tags': {
                    'pages_with_h1': pages_with_h1,
                    'coverage_percentage': round((pages_with_h1 / total_pages * 100), 2) if total_pages > 0 else 0,
                    'pages_without_h1': {
                        'count': len(pages_without_h1),
                        'pages': pages_without_h1
                    },
                    'pages_with_multiple_h1': {
                        'count': len(multiple_h1_pages),
                        'pages': multiple_h1_pages
                    },
                    'duplicate_h1s_count': len(duplicate_h1s)
                },
                'image_alt_text': {
                    'total_images': total_images,
                    'images_without_alt': images_without_alt,
                    'compliance_percentage': round(((total_images - images_without_alt) / total_images * 100), 2) if total_images > 0 else 100
                },
                'internal_linking': {
                    'total_internal_links': total_internal_links,
                    'broken_internal_links': broken_internal_links,
                    'orphan_pages': {
                        'count': len(orphan_pages),
                        'pages': list(orphan_pages)
                    }
                }
            }
        }
        
        json_str = json.dumps(summary_data, indent=2, ensure_ascii=False)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        logger.info(f"✅ Site summary JSON report saved to: {output_file}")
        return output_file
    
    def generate_csv(self, all_results: List[Dict], output_file: str = None) -> str:
        """
        Generate CSV output with summary of audit results.
        
        Args:
            all_results: List of audit result dicts
            output_file: Optional output file path
            
        Returns:
            CSV file path
        """
        if output_file is None:
            output_file = f"seo_audit_{self.timestamp}.csv"
        
        rows = []
        for result in all_results:
            url = result.get('url', '')
            score = result.get('score', {}).get('score', 0)
            
            # Extract top issues
            issues = result.get('score', {}).get('issues', [])
            top_issues = ', '.join([i['message'] for i in issues[:5]])
            
            # Technical issues
            technical = result.get('technical', {})
            has_noindex = technical.get('noindex', {}).get('has_noindex', False)
            has_canonical = technical.get('canonical', {}).get('has_canonical', False)
            is_https = technical.get('https', {}).get('is_https', True)
            has_structured_data = technical.get('structured_data', {}).get('has_structured_data', False)
            
            # On-page issues
            onpage = result.get('onpage', {})
            has_title = onpage.get('title', {}).get('has_title', False)
            has_meta_desc = onpage.get('meta_description', {}).get('has_meta_description', False)
            h1_count = onpage.get('h1', {}).get('h1_count', 0)
            images_without_alt = onpage.get('image_alt', {}).get('images_without_alt', 0)
            internal_links = onpage.get('internal_links', {}).get('internal_link_count', 0)
            
            rows.append({
                'URL': url,
                'SEO Score': score,
                'Critical Issues': result.get('score', {}).get('critical_count', 0),
                'High Issues': result.get('score', {}).get('high_count', 0),
                'Medium Issues': result.get('score', {}).get('medium_count', 0),
                'Low Issues': result.get('score', {}).get('low_count', 0),
                'Top Issues': top_issues,
                'Has Noindex': has_noindex,
                'Has Canonical': has_canonical,
                'Is HTTPS': is_https,
                'Has Structured Data': has_structured_data,
                'Has Title': has_title,
                'Has Meta Description': has_meta_desc,
                'H1 Count': h1_count,
                'Images Without Alt': images_without_alt,
                'Internal Links': internal_links
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        logger.info(f"✅ CSV report saved to: {output_file}")
        return output_file
    
    def generate_detailed_csv(self, all_results: List[Dict], output_file: str = None) -> str:
        """
        Generate detailed CSV with all links and all their issues.
        
        Args:
            all_results: List of audit result dicts
            output_file: Optional output file path
            
        Returns:
            CSV file path
        """
        if output_file is None:
            output_file = f"seo_audit_detailed_{self.timestamp}.csv"
        
        rows = []
        for result in all_results:
            url = result.get('url', '')
            score = result.get('score', {}).get('score', 0)
            status_code = result.get('status_code', 0)
            
            # Get all issues
            issues = result.get('score', {}).get('issues', [])
            all_issue_messages = ' | '.join([f"[{i['severity'].upper()}] {i['message']}" for i in issues])
            
            # Technical details
            technical = result.get('technical', {})
            noindex = technical.get('noindex', {})
            canonical = technical.get('canonical', {})
            redirects = technical.get('redirects', {})
            https = technical.get('https', {})
            structured_data = technical.get('structured_data', {})
            
            # On-page details
            onpage = result.get('onpage', {})
            title = onpage.get('title', {})
            meta_desc = onpage.get('meta_description', {})
            h1 = onpage.get('h1', {})
            image_alt = onpage.get('image_alt', {})
            internal_links = onpage.get('internal_links', {})
            
            rows.append({
                'URL': url,
                'Status Code': status_code,
                'SEO Score': score,
                'Total Issues': len(issues),
                'Critical Issues': result.get('score', {}).get('critical_count', 0),
                'High Issues': result.get('score', {}).get('high_count', 0),
                'Medium Issues': result.get('score', {}).get('medium_count', 0),
                'Low Issues': result.get('score', {}).get('low_count', 0),
                'All Issues': all_issue_messages,
                # Technical SEO
                'Has Noindex': noindex.get('has_noindex', False),
                'Noindex Issues': ' | '.join(noindex.get('issues', [])),
                'Has Canonical': canonical.get('has_canonical', False),
                'Canonical URL': canonical.get('canonical_url', ''),
                'Canonical Issues': ' | '.join(canonical.get('issues', [])),
                'Redirect Chain Length': redirects.get('redirect_chain_length', 0),
                'Redirect Issues': ' | '.join(redirects.get('issues', [])),
                'Is HTTPS': https.get('is_https', False),
                'Mixed Content Count': https.get('mixed_content_count', 0),
                'HTTPS Issues': ' | '.join(https.get('issues', [])[:3]),
                'Has Structured Data': structured_data.get('has_structured_data', False),
                'Schema Types': ', '.join(structured_data.get('schema_types', [])),
                'Schema Issues': ' | '.join(structured_data.get('issues', [])),
                # On-Page SEO
                'Has Title': title.get('has_title', False),
                'Title Text': title.get('title_text', '')[:100],
                'Title Length': title.get('title_length', 0),
                'Title Issues': ' | '.join(title.get('issues', [])),
                'Has Meta Description': meta_desc.get('has_meta_description', False),
                'Meta Description Length': meta_desc.get('description_length', 0),
                'Meta Description Issues': ' | '.join(meta_desc.get('issues', [])),
                'H1 Count': h1.get('h1_count', 0),
                'H1 Issues': ' | '.join(h1.get('issues', [])),
                'Total Images': image_alt.get('total_images', 0),
                'Images Without Alt': image_alt.get('images_without_alt', 0),
                'Image Alt Issues': ' | '.join(image_alt.get('issues', [])),
                'Internal Links': internal_links.get('internal_link_count', 0),
                'Broken Internal Links': internal_links.get('broken_link_count', 0),
                'Internal Link Issues': ' | '.join(internal_links.get('issues', [])[:3])
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        logger.info(f"✅ Detailed CSV report saved to: {output_file}")
        return output_file
    
    def generate_issues_grouped_csv(self, all_results: List[Dict], output_file: str = None) -> str:
        """
        Generate CSV with links grouped by issues found.
        
        Args:
            all_results: List of audit result dicts
            output_file: Optional output file path
            
        Returns:
            CSV file path
        """
        if output_file is None:
            output_file = f"seo_audit_issues_grouped_{self.timestamp}.csv"
        
        # Group issues by type
        issues_by_type = {}
        for result in all_results:
            url = result.get('url', '')
            issues = result.get('score', {}).get('issues', [])
            
            for issue in issues:
                # Create a unique key for the issue
                issue_key = f"{issue.get('category', 'Unknown')} - {issue.get('type', 'Unknown')} - {issue.get('message', '')}"
                
                if issue_key not in issues_by_type:
                    issues_by_type[issue_key] = {
                        'Category': issue.get('category', 'Unknown'),
                        'Type': issue.get('type', 'Unknown'),
                        'Issue Message': issue.get('message', ''),
                        'Severity': issue.get('severity', 'low'),
                        'URLs': []
                    }
                issues_by_type[issue_key]['URLs'].append(url)
        
        # Convert to rows
        rows = []
        for issue_key, issue_data in issues_by_type.items():
            rows.append({
                'Category': issue_data['Category'],
                'Type': issue_data['Type'],
                'Issue Message': issue_data['Issue Message'],
                'Severity': issue_data['Severity'].upper(),
                'Affected Pages Count': len(issue_data['URLs']),
                'URLs': ' | '.join(issue_data['URLs'])
            })
        
        # Sort by severity and count
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        rows.sort(key=lambda x: (severity_order.get(x['Severity'], 4), -x['Affected Pages Count']))
        
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        logger.info(f"✅ Issues-grouped CSV report saved to: {output_file}")
        return output_file
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status."""
        status_map = {
            'good': '✅',
            'warning': '⚠️',
            'error': '❌',
            'info': 'ℹ️'
        }
        return status_map.get(status, '⚪')
    
    def _aggregate_site_status(self, all_results: List[Dict], check_type: str, check_key: str) -> Dict:
        """
        Aggregate status across all pages for a specific check.
        
        Args:
            all_results: List of audit results
            check_type: 'technical' or 'onpage'
            check_key: Key within the check type (e.g., 'noindex', 'canonical')
            
        Returns:
            Dict with aggregated status and counts
        """
        total = len(all_results)
        good_count = 0
        warning_count = 0
        error_count = 0
        info_count = 0
        issues_found = []
        
        for result in all_results:
            check_data = result.get(check_type, {}).get(check_key, {})
            status = check_data.get('status', 'unknown')
            
            if status == 'good':
                good_count += 1
            elif status == 'warning':
                warning_count += 1
            elif status == 'error':
                error_count += 1
            elif status == 'info':
                info_count += 1
            
            # Collect issues
            check_issues = check_data.get('issues', [])
            if check_issues:
                issues_found.extend(check_issues[:2])  # Limit to 2 per page
        
        # Determine overall status
        if error_count > 0:
            overall_status = 'error'
        elif warning_count > 0:
            overall_status = 'warning'
        elif info_count > 0:
            overall_status = 'info'
        else:
            overall_status = 'good'
        
        return {
            'status': overall_status,
            'total': total,
            'good': good_count,
            'warning': warning_count,
            'error': error_count,
            'info': info_count,
            'sample_issues': issues_found[:5]  # Limit to 5 total
        }
    
    def print_console_report(self, all_results: List[Dict], site_stats: Dict, 
                            crawlability_info: Dict, duplicate_titles: Dict,
                            duplicate_descriptions: Dict, duplicate_h1s: Dict,
                            orphan_pages: Set):
        """
        Print comprehensive console report organized by sections.
        
        Args:
            all_results: List of audit result dicts
            site_stats: Site-wide statistics
            crawlability_info: Robots.txt and sitemap info
            duplicate_titles: Dict of duplicate titles
            duplicate_descriptions: Dict of duplicate descriptions
            duplicate_h1s: Dict of duplicate H1s
            orphan_pages: Set of orphan page URLs
        """
        print("\n" + "="*80)
        print("🔍 SEO AUDIT REPORT")
        print("="*80)
        print(f"\n📊 Site: {self.base_url}")
        print(f"📅 Timestamp: {self.timestamp}")
        print(f"📄 Pages Audited: {site_stats.get('total_pages', 0)}")
        print(f"⭐ Average SEO Score: {site_stats.get('average_score', 0)}/100")
        print(f"\n📈 Issue Summary:")
        print(f"   🔴 Critical: {site_stats.get('critical_issues', 0)}")
        print(f"   🟠 High: {site_stats.get('high_issues', 0)}")
        print(f"   🟡 Medium: {site_stats.get('medium_issues', 0)}")
        print(f"   🟢 Low: {site_stats.get('low_issues', 0)}")
        
        # ========================================================================
        # TECHNICAL SEO SECTION
        # ========================================================================
        print("\n" + "="*80)
        print("🔧 TECHNICAL SEO")
        print("="*80)
        
        # Crawlability Checks
        print("\n📋 Crawlability Checks:")
        print("-"*80)
        
        # Robots.txt
        robots_status = 'good' if crawlability_info.get('robots_txt_exists', False) else 'warning'
        robots_emoji = self._get_status_emoji(robots_status)
        print(f"   {robots_emoji} Robots.txt: ", end="")
        if crawlability_info.get('robots_txt_exists', False):
            print("✅ Present and accessible")
        else:
            print("⚠️ Not found or not accessible")
        
        # Sitemap
        all_sitemap_urls = crawlability_info.get('all_sitemap_urls', [])
        total_sitemap_links_count = crawlability_info.get('total_sitemap_links_count', 0)
        sitemap_exists = len(all_sitemap_urls) > 0
        sitemap_status = 'good' if sitemap_exists else 'warning'
        sitemap_emoji = self._get_status_emoji(sitemap_status)
        print(f"   {sitemap_emoji} Sitemap: ", end="")
        
        if sitemap_exists:
            print(f"✅ Found {len(all_sitemap_urls)} sitemap(s) with {total_sitemap_links_count} total links:")
            for sitemap_url in all_sitemap_urls:
                print(f"      • {sitemap_url}")
        else:
            print("❌ Not found")
        
        # Noindex Tags
        print("\n📋 Noindex Tags:")
        print("-"*80)
        noindex_agg = self._aggregate_site_status(all_results, 'technical', 'noindex')
        noindex_emoji = self._get_status_emoji(noindex_agg['status'])
        print(f"   {noindex_emoji} Status: ", end="")
        if noindex_agg['error'] > 0:
            print(f"❌ {noindex_agg['error']} page(s) with noindex directive")
            # Get URLs with noindex
            noindex_urls = [r.get('url', '') for r in all_results 
                           if r.get('technical', {}).get('noindex', {}).get('has_noindex', False)]
            for url in noindex_urls[:10]:
                print(f"      • {url}")
            if len(noindex_urls) > 10:
                print(f"      ... and {len(noindex_urls) - 10} more page(s)")
        else:
            print("✅ No noindex directives found on indexable pages")
        
        # Canonical Tags
        print("\n📋 Canonical Tags:")
        print("-"*80)
        canonical_agg = self._aggregate_site_status(all_results, 'technical', 'canonical')
        canonical_emoji = self._get_status_emoji(canonical_agg['status'])
        print(f"   {canonical_emoji} Status: ", end="")
        if canonical_agg['error'] > 0:
            print(f"❌ {canonical_agg['error']} page(s) with canonical issues")
            # Get URLs with canonical issues
            canonical_error_urls = []
            for r in all_results:
                if r.get('technical', {}).get('canonical', {}).get('status') == 'error':
                    url = r.get('url', '')
                    issues = r.get('technical', {}).get('canonical', {}).get('issues', [])
                    canonical_error_urls.append((url, issues[0] if issues else 'Canonical issue'))
            
            for url, issue_msg in canonical_error_urls[:10]:
                print(f"      • {url}")
                print(f"        Issue: {issue_msg}")
            if len(canonical_error_urls) > 10:
                print(f"      ... and {len(canonical_error_urls) - 10} more page(s)")
        elif canonical_agg['warning'] > 0:
            print(f"⚠️ {canonical_agg['warning']} page(s) with canonical warnings")
            canonical_warning_urls = [r.get('url', '') for r in all_results 
                                     if r.get('technical', {}).get('canonical', {}).get('status') == 'warning']
            for url in canonical_warning_urls[:5]:
                print(f"      • {url}")
        else:
            print(f"✅ {canonical_agg['good']}/{canonical_agg['total']} pages have proper canonical tags")
        
        # Meta Robots
        print("\n📋 Meta Robots:")
        print("-"*80)
        meta_robots_agg = self._aggregate_site_status(all_results, 'technical', 'meta_robots')
        meta_robots_emoji = self._get_status_emoji(meta_robots_agg['status'])
        print(f"   {meta_robots_emoji} Status: ", end="")
        pages_with_meta = sum(1 for r in all_results if r.get('technical', {}).get('meta_robots', {}).get('has_meta_robots', False))
        print(f"ℹ️ {pages_with_meta}/{meta_robots_agg['total']} pages have meta robots tags")
        if meta_robots_agg['sample_issues']:
            for issue in meta_robots_agg['sample_issues'][:2]:
                print(f"      • {issue}")
        
        # Server Responses
        print("\n📋 Server Responses:")
        print("-"*80)
        status_codes = {}
        for result in all_results:
            code = result.get('status_code', 0)
            status_codes[code] = status_codes.get(code, 0) + 1
        
        response_status = 'good' if all(code in [200, 301] for code in status_codes.keys()) else 'warning'
        response_emoji = self._get_status_emoji(response_status)
        print(f"   {response_emoji} Status Codes:")
        for code, count in sorted(status_codes.items()):
            code_emoji = '✅' if code == 200 else ('ℹ️' if code in [301, 302] else '❌')
            print(f"      {code_emoji} {code}: {count} page(s)")
        
        # Redirect Chains
        print("\n📋 Redirect Chains:")
        print("-"*80)
        redirect_agg = self._aggregate_site_status(all_results, 'technical', 'redirects')
        redirect_emoji = self._get_status_emoji(redirect_agg['status'])
        print(f"   {redirect_emoji} Status: ", end="")
        if redirect_agg['error'] > 0:
            print(f"❌ {redirect_agg['error']} page(s) with redirect issues")
            for issue in redirect_agg['sample_issues'][:3]:
                print(f"      • {issue}")
        else:
            redirect_pages = sum(1 for r in all_results if r.get('technical', {}).get('redirects', {}).get('redirect_chain_length', 0) > 1)
            if redirect_pages > 0:
                print(f"ℹ️ {redirect_pages} page(s) have redirects (check individual pages)")
            else:
                print("✅ No redirect chain issues found")
        
        # HTTPS / Mixed Content
        print("\n📋 HTTPS / Mixed Content:")
        print("-"*80)
        https_agg = self._aggregate_site_status(all_results, 'technical', 'https')
        https_emoji = self._get_status_emoji(https_agg['status'])
        print(f"   {https_emoji} Status: ", end="")
        https_pages = sum(1 for r in all_results if r.get('technical', {}).get('https', {}).get('is_https', False))
        mixed_content_pages = sum(1 for r in all_results if r.get('technical', {}).get('https', {}).get('mixed_content_count', 0) > 0)
        print(f"✅ {https_pages}/{https_agg['total']} pages served over HTTPS")
        if mixed_content_pages > 0:
            print(f"   ⚠️ {mixed_content_pages} page(s) have mixed content (HTTP resources on HTTPS pages)")
            for issue in https_agg['sample_issues'][:2]:
                if 'HTTP' in issue:
                    print(f"      • {issue}")
        
        # Schema Errors
        print("\n📋 Structured Data (Schema):")
        print("-"*80)
        schema_agg = self._aggregate_site_status(all_results, 'technical', 'structured_data')
        schema_emoji = self._get_status_emoji(schema_agg['status'])
        print(f"   {schema_emoji} Status: ", end="")
        pages_with_schema = sum(1 for r in all_results if r.get('technical', {}).get('structured_data', {}).get('has_structured_data', False))
        print(f"ℹ️ {pages_with_schema}/{schema_agg['total']} pages have structured data")
        if schema_agg['error'] > 0 or schema_agg['warning'] > 0:
            print(f"   ⚠️ {schema_agg['error'] + schema_agg['warning']} page(s) have schema errors")
            for issue in schema_agg['sample_issues'][:3]:
                print(f"      • {issue}")
        else:
            schema_types = set()
            for r in all_results:
                types = r.get('technical', {}).get('structured_data', {}).get('schema_types', [])
                schema_types.update(types)
            if schema_types:
                print(f"   Schema types found: {', '.join(list(schema_types)[:5])}")
        
        # ========================================================================
        # ON-PAGE SEO SECTION
        # ========================================================================
        print("\n" + "="*80)
        print("📝 ON-PAGE SEO")
        print("="*80)
        
        # Title Tags
        print("\n📋 Title Tags:")
        print("-"*80)
        title_agg = self._aggregate_site_status(all_results, 'onpage', 'title')
        title_emoji = self._get_status_emoji(title_agg['status'])
        print(f"   {title_emoji} Status: ", end="")
        if title_agg['error'] > 0:
            print(f"❌ {title_agg['error']} page(s) missing or have title issues")
            # Get URLs with title issues
            title_error_urls = [r.get('url', '') for r in all_results 
                               if not r.get('onpage', {}).get('title', {}).get('has_title', False)]
            for url in title_error_urls[:10]:
                print(f"      • {url}")
            if len(title_error_urls) > 10:
                print(f"      ... and {len(title_error_urls) - 10} more page(s)")
        else:
            print(f"✅ {title_agg['good']}/{title_agg['total']} pages have proper title tags")
        
        # Check for duplicates
        if duplicate_titles:
            print(f"   ⚠️ {len(duplicate_titles)} duplicate title(s) found across pages")
            for title, urls in list(duplicate_titles.items())[:3]:
                print(f"      • '{title[:50]}...' appears on {len(urls)} pages:")
                for url in urls[:5]:
                    print(f"        - {url}")
                if len(urls) > 5:
                    print(f"        ... and {len(urls) - 5} more page(s)")
        
        # Meta Descriptions
        print("\n📋 Meta Descriptions:")
        print("-"*80)
        meta_agg = self._aggregate_site_status(all_results, 'onpage', 'meta_description')
        meta_emoji = self._get_status_emoji(meta_agg['status'])
        print(f"   {meta_emoji} Status: ", end="")
        if meta_agg['error'] > 0:
            print(f"❌ {meta_agg['error']} page(s) missing meta descriptions")
            # Get URLs missing meta descriptions
            meta_error_urls = [r.get('url', '') for r in all_results 
                             if not r.get('onpage', {}).get('meta_description', {}).get('has_meta_description', False)]
            for url in meta_error_urls[:10]:
                print(f"      • {url}")
            if len(meta_error_urls) > 10:
                print(f"      ... and {len(meta_error_urls) - 10} more page(s)")
        elif meta_agg['warning'] > 0:
            print(f"⚠️ {meta_agg['warning']} page(s) have meta description length issues")
            meta_warning_urls = [r.get('url', '') for r in all_results 
                                if r.get('onpage', {}).get('meta_description', {}).get('status') == 'warning']
            for url in meta_warning_urls[:5]:
                print(f"      • {url}")
        else:
            print(f"✅ {meta_agg['good']}/{meta_agg['total']} pages have proper meta descriptions")
        
        # Check for duplicates
        if duplicate_descriptions:
            print(f"   ⚠️ {len(duplicate_descriptions)} duplicate description(s) found")
            for desc, urls in list(duplicate_descriptions.items())[:2]:
                print(f"      • Description appears on {len(urls)} pages:")
                for url in urls[:5]:
                    print(f"        - {url}")
                if len(urls) > 5:
                    print(f"        ... and {len(urls) - 5} more page(s)")
        
        # H1 Tags
        print("\n📋 H1 Tags:")
        print("-"*80)
        h1_agg = self._aggregate_site_status(all_results, 'onpage', 'h1')
        h1_emoji = self._get_status_emoji(h1_agg['status'])
        print(f"   {h1_emoji} Status: ", end="")
        if h1_agg['error'] > 0:
            print(f"❌ {h1_agg['error']} page(s) missing H1 tags")
            # Get URLs missing H1
            h1_error_urls = [r.get('url', '') for r in all_results 
                            if r.get('onpage', {}).get('h1', {}).get('h1_count', 0) == 0]
            for url in h1_error_urls[:10]:
                print(f"      • {url}")
            if len(h1_error_urls) > 10:
                print(f"      ... and {len(h1_error_urls) - 10} more page(s)")
        elif h1_agg['warning'] > 0:
            print(f"⚠️ {h1_agg['warning']} page(s) have multiple H1 tags")
            h1_warning_urls = []
            for r in all_results:
                h1_count = r.get('onpage', {}).get('h1', {}).get('h1_count', 0)
                if h1_count > 1:
                    h1_warning_urls.append((r.get('url', ''), h1_count))
            
            for url, h1_count in h1_warning_urls[:5]:
                print(f"      • {url} ({h1_count} H1 tags)")
        else:
            print(f"✅ {h1_agg['good']}/{h1_agg['total']} pages have proper H1 tags (exactly 1)")
        
        # Check for duplicates
        if duplicate_h1s:
            print(f"   ⚠️ {len(duplicate_h1s)} duplicate H1(s) found across pages")
            for h1_text, urls in list(duplicate_h1s.items())[:2]:
                print(f"      • '{h1_text[:50]}...' appears on {len(urls)} pages:")
                for url in urls[:5]:
                    print(f"        - {url}")
                if len(urls) > 5:
                    print(f"        ... and {len(urls) - 5} more page(s)")
        
        # Image Alt Text
        print("\n📋 Image Alt Text:")
        print("-"*80)
        alt_agg = self._aggregate_site_status(all_results, 'onpage', 'image_alt')
        alt_emoji = self._get_status_emoji(alt_agg['status'])
        print(f"   {alt_emoji} Status: ", end="")
        total_images = sum(r.get('onpage', {}).get('image_alt', {}).get('total_images', 0) for r in all_results)
        images_without_alt = sum(r.get('onpage', {}).get('image_alt', {}).get('images_without_alt', 0) for r in all_results)
        if images_without_alt > 0:
            print(f"⚠️ {images_without_alt} image(s) missing alt text (out of {total_images} total)")
            pages_with_issues = sum(1 for r in all_results if r.get('onpage', {}).get('image_alt', {}).get('images_without_alt', 0) > 0)
            print(f"   Found on {pages_with_issues} page(s)")
        else:
            print(f"✅ All images have alt text ({total_images} images checked)")
        
        # Internal Linking
        print("\n📋 Internal Linking:")
        print("-"*80)
        links_agg = self._aggregate_site_status(all_results, 'onpage', 'internal_links')
        links_emoji = self._get_status_emoji(links_agg['status'])
        print(f"   {links_emoji} Status: ", end="")
        total_links = sum(r.get('onpage', {}).get('internal_links', {}).get('internal_link_count', 0) for r in all_results)
        broken_links = sum(r.get('onpage', {}).get('internal_links', {}).get('broken_link_count', 0) for r in all_results)
        print(f"ℹ️ {total_links} total internal links found")
        if broken_links > 0:
            print(f"   ⚠️ {broken_links} potentially broken internal link(s)")
        if orphan_pages:
            print(f"   ⚠️ {len(orphan_pages)} orphan page(s) found (no internal in-links)")
            for orphan in list(orphan_pages)[:3]:
                print(f"      • {orphan[:60]}...")
        if links_agg['error'] > 0:
            for issue in links_agg['sample_issues'][:2]:
                print(f"      • {issue}")
        
        # ========================================================================
        # SUMMARY
        # ========================================================================
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        
        # Top pages with issues
        sorted_results = sorted(all_results, key=lambda x: x.get('score', {}).get('score', 100))
        
        print(f"\n🔴 Top 5 Pages with Most Issues:")
        print("-"*80)
        for i, result in enumerate(sorted_results[:5], 1):
            url = result.get('url', '')
            score = result.get('score', {}).get('score', 0)
            issue_count = result.get('score', {}).get('issue_count', 0)
            
            print(f"{i}. {url[:65]}...")
            print(f"   Score: {score}/100 | Issues: {issue_count}")
            
            # Show top 2 issues
            issues = result.get('score', {}).get('issues', [])[:2]
            for issue in issues:
                severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(issue['severity'], '⚪')
                print(f"   {severity_emoji} {issue['message']}")
        
        # ========================================================================
        # DETAILED ISSUES WITH URLs
        # ========================================================================
        print("\n" + "="*80)
        print("📋 DETAILED ISSUES BY CATEGORY (WITH URLs)")
        print("="*80)
        
        # Group issues by type and collect URLs
        issues_by_type = {}
        for result in all_results:
            url = result.get('url', '')
            issues = result.get('score', {}).get('issues', [])
            
            for issue in issues:
                issue_key = f"{issue.get('category', 'Unknown')} - {issue.get('type', 'Unknown')} - {issue.get('message', '')}"
                if issue_key not in issues_by_type:
                    issues_by_type[issue_key] = {
                        'severity': issue.get('severity', 'low'),
                        'category': issue.get('category', 'Unknown'),
                        'type': issue.get('type', 'Unknown'),
                        'message': issue.get('message', ''),
                        'urls': []
                    }
                issues_by_type[issue_key]['urls'].append(url)
        
        # Sort by severity and count
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_issues = sorted(issues_by_type.items(), 
                             key=lambda x: (severity_order.get(x[1]['severity'], 4), len(x[1]['urls'])), 
                             reverse=True)
        
        for issue_key, issue_data in sorted_issues[:20]:  # Show top 20 issue types
            severity = issue_data['severity']
            severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(severity, '⚪')
            url_count = len(issue_data['urls'])
            
            print(f"\n{severity_emoji} {issue_data['category']} > {issue_data['type']}")
            print(f"   Issue: {issue_data['message']}")
            print(f"   Affected Pages: {url_count}")
            print(f"   URLs:")
            for url in issue_data['urls'][:10]:  # Show first 10 URLs
                print(f"      • {url}")
            if url_count > 10:
                print(f"      ... and {url_count - 10} more page(s)")
        
        print("\n" + "="*80)
        print("✅ Audit Complete!")
        print("="*80 + "\n")
