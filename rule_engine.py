"""
Rule engine for scoring and prioritizing SEO issues.
"""
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class RuleEngine:
    """Score and prioritize SEO issues based on issue-specific weights only."""
    
    # Issue-specific weights (all scoring uses only these weights)
    ISSUE_WEIGHTS = {
        # Technical SEO issues
        'noindex_on_indexable': -15,
        'nofollow_directive': -3,           # Nofollow directive
        'meta_robots_conflict': -6,         # Conflict between meta robots and header
        'canonical_404': -12,
        'canonical_to_homepage': -12,
        'canonical_other': -6,              # Other canonical issues
        'redirect_chain_404': -12,
        'redirect_loop': -15,
        'redirect_chain_too_long': -6,      # Redirect chain too long
        'redirect_302_temporary': -4,      # Uses 302 instead of 301
        'redirect_other': -6,               # Other redirect issues
        'server_error': -12,                # Server error (5xx)
        'mixed_content_js_css': -10,
        'not_https': -15,
        'missing_structured_data': -2,
        'duplicate_structured_data': -2,    # Duplicate structured data types
        
        # On-Page SEO issues
        'missing_title': -8,
        'title_empty': -8,                  # Title tag exists but is empty
        'title_too_short': -4,              # Title too short
        'title_too_long': -4,               # Title too long
        'title_template_default': -3,       # Title appears to be template/default
        'duplicate_title': -4,
        'missing_meta_description': -6,
        'meta_description_empty': -6,        # Meta description exists but is empty
        'meta_description_too_short': -3,   # Meta description too short
        'meta_description_too_long': -3,    # Meta description too long
        'duplicate_description': -2,
        'no_h1': -6,
        'multiple_h1': -4,
        'h1_identical_to_title': -2,        # H1 identical to title tag
        'h1_other': -3,                     # Other H1 issues
        'images_missing_alt': -4,           # Per image (capped at 3)
        'images_empty_alt': -2,             # Images with empty alt attribute
        'broken_internal_links': -4,
        'excessive_internal_links': -2,     # Too many internal links
        'link_without_anchor_text': -2,     # Link without anchor text
        'internal_links_other': -2,         # Other internal link issues
        'orphan_page': -6
    }
    
    def __init__(self):
        self.base_score = 100  # Starting score
    
    def calculate_page_score(self, technical_results: Dict, onpage_results: Dict) -> Dict:
        """
        Calculate SEO score for a single page.
        
        Args:
            technical_results: Technical audit results
            onpage_results: On-page audit results
            
        Returns:
            Dict with score and prioritized issues
        """
        score = self.base_score
        all_issues = []
        
        # Process technical issues
        if technical_results:
            # Noindex issues
            noindex = technical_results.get('noindex', {})
            if noindex.get('has_noindex', False):
                weight = self.ISSUE_WEIGHTS.get('noindex_on_indexable', -15)
                score += weight
                all_issues.append({
                    'category': 'Technical',
                    'type': 'Noindex',
                    'severity': 'critical',
                    'message': 'Page has noindex directive',
                    'weight': weight
                })
            
            # Nofollow issues
            if noindex.get('has_nofollow', False):
                weight = self.ISSUE_WEIGHTS.get('nofollow_directive', -3)
                score += weight
                all_issues.append({
                    'category': 'Technical',
                    'type': 'Nofollow',
                    'severity': 'medium',
                    'message': 'Page has nofollow directive',
                    'weight': weight
                })
            
            # Meta robots conflict
            if noindex.get('issues'):
                for issue in noindex['issues']:
                    if 'conflict' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('meta_robots_conflict', -6)
                        score += weight
                        all_issues.append({
                            'category': 'Technical',
                            'type': 'Meta Robots',
                            'severity': 'high',
                            'message': issue,
                            'weight': weight
                        })
            
            # Canonical issues
            canonical = technical_results.get('canonical', {})
            if canonical.get('issues'):
                for issue in canonical['issues']:
                    if '404' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('canonical_404', -12)
                    elif 'homepage' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('canonical_to_homepage', -12)
                    else:
                        weight = self.ISSUE_WEIGHTS.get('canonical_other', -6)
                    
                    score += weight
                    all_issues.append({
                        'category': 'Technical',
                        'type': 'Canonical',
                        'severity': canonical.get('severity', 'medium'),
                        'message': issue,
                        'weight': weight
                    })
            
            # Redirect issues
            redirects = technical_results.get('redirects', {})
            if redirects.get('issues'):
                for issue in redirects['issues']:
                    if '404' in issue:
                        weight = self.ISSUE_WEIGHTS.get('redirect_chain_404', -12)
                    elif 'loop' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('redirect_loop', -15)
                    elif 'too long' in issue.lower() or 'chain too long' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('redirect_chain_too_long', -6)
                    elif '302' in issue or 'temporary' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('redirect_302_temporary', -4)
                    elif 'server error' in issue.lower() or 'error' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('server_error', -12)
                    else:
                        weight = self.ISSUE_WEIGHTS.get('redirect_other', -6)
                    
                    score += weight
                    all_issues.append({
                        'category': 'Technical',
                        'type': 'Redirects',
                        'severity': redirects.get('severity', 'medium'),
                        'message': issue,
                        'weight': weight
                    })
            
            # HTTPS issues
            https = technical_results.get('https', {})
            if not https.get('is_https', True):
                weight = self.ISSUE_WEIGHTS.get('not_https', -40)
                score += weight
                all_issues.append({
                    'category': 'Technical',
                    'type': 'HTTPS',
                    'severity': 'critical',
                    'message': 'Page not served over HTTPS',
                    'weight': weight
                })
            
            if https.get('mixed_content_count', 0) > 0:
                weight = self.ISSUE_WEIGHTS.get('mixed_content_js_css', -10)
                score += weight
                all_issues.append({
                    'category': 'Technical',
                    'type': 'Mixed Content',
                    'severity': 'high',
                    'message': f"{https['mixed_content_count']} resource(s) loaded via HTTP",
                    'weight': weight
                })
            
            # Structured data issues
            structured_data = technical_results.get('structured_data', {})
            if structured_data.get('issues'):
                for issue in structured_data['issues']:
                    if 'no structured data' in issue.lower() or 'not found' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('missing_structured_data', -2)
                    elif 'duplicate' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('duplicate_structured_data', -2)
                    else:
                        weight = self.ISSUE_WEIGHTS.get('missing_structured_data', -2)
                    
                    score += weight
                    all_issues.append({
                        'category': 'Technical',
                        'type': 'Structured Data',
                        'severity': structured_data.get('severity', 'low'),
                        'message': issue,
                        'weight': weight
                    })
        
        # Process on-page issues
        if onpage_results:
            # Title issues
            title = onpage_results.get('title', {})
            if not title.get('has_title', False):
                weight = self.ISSUE_WEIGHTS.get('missing_title', -8)
                score += weight
                all_issues.append({
                    'category': 'On-Page',
                    'type': 'Title',
                    'severity': 'critical',
                    'message': 'Missing title tag',
                    'weight': weight
                })
            elif title.get('issues'):
                for issue in title['issues']:
                    # Determine specific issue type
                    if 'empty' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('title_empty', -8)
                    elif 'too short' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('title_too_short', -4)
                    elif 'too long' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('title_too_long', -4)
                    elif 'template' in issue.lower() or 'default' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('title_template_default', -3)
                    elif 'duplicate' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('duplicate_title', -4)
                    else:
                        weight = self.ISSUE_WEIGHTS.get('title_too_short', -4)  # Default for other title issues
                    
                    score += weight
                    all_issues.append({
                        'category': 'On-Page',
                        'type': 'Title',
                        'severity': title.get('severity', 'medium'),
                        'message': issue,
                        'weight': weight
                    })
            
            # Meta description issues
            meta_desc = onpage_results.get('meta_description', {})
            if not meta_desc.get('has_meta_description', False):
                weight = self.ISSUE_WEIGHTS.get('missing_meta_description', -6)
                score += weight
                all_issues.append({
                    'category': 'On-Page',
                    'type': 'Meta Description',
                    'severity': 'high',
                    'message': 'Missing meta description',
                    'weight': weight
                })
            elif meta_desc.get('issues'):
                for issue in meta_desc['issues']:
                    # Determine specific issue type
                    if 'empty' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('meta_description_empty', -6)
                    elif 'too short' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('meta_description_too_short', -3)
                    elif 'too long' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('meta_description_too_long', -3)
                    elif 'duplicate' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('duplicate_description', -2)
                    else:
                        weight = self.ISSUE_WEIGHTS.get('meta_description_too_short', -3)  # Default
                    
                    score += weight
                    all_issues.append({
                        'category': 'On-Page',
                        'type': 'Meta Description',
                        'severity': meta_desc.get('severity', 'medium'),
                        'message': issue,
                        'weight': weight
                    })
            
            # H1 issues
            h1 = onpage_results.get('h1', {})
            if h1.get('h1_count', 0) == 0:
                weight = self.ISSUE_WEIGHTS.get('no_h1', -6)
                score += weight
                all_issues.append({
                    'category': 'On-Page',
                    'type': 'H1',
                    'severity': 'high',
                    'message': 'No H1 tag found',
                    'weight': weight
                })
            elif h1.get('issues'):
                for issue in h1['issues']:
                    if 'multiple' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('multiple_h1', -4)
                    elif 'identical' in issue.lower() or 'same as title' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('h1_identical_to_title', -2)
                    else:
                        weight = self.ISSUE_WEIGHTS.get('h1_other', -3)
                    score += weight
                    all_issues.append({
                        'category': 'On-Page',
                        'type': 'H1',
                        'severity': h1.get('severity', 'medium'),
                        'message': issue,
                        'weight': weight
                    })
            
            # Image alt issues
            image_alt = onpage_results.get('image_alt', {})
            if image_alt.get('images_without_alt', 0) > 0:
                weight = self.ISSUE_WEIGHTS.get('images_missing_alt', -4)
                # More liberal: reduce impact per image and cap lower
                score += weight * min(image_alt['images_without_alt'], 3)  # Cap at 3 instead of 5
                all_issues.append({
                    'category': 'On-Page',
                    'type': 'Image Alt',
                    'severity': 'medium',
                    'message': f"{image_alt['images_without_alt']} image(s) missing alt text",
                    'weight': weight
                })
            
            # Images with empty alt attribute
            if image_alt.get('images_with_empty_alt', 0) > 0:
                weight = self.ISSUE_WEIGHTS.get('images_empty_alt', -2)
                score += weight * min(image_alt['images_with_empty_alt'], 2)  # Cap at 2
                all_issues.append({
                    'category': 'On-Page',
                    'type': 'Image Alt',
                    'severity': 'low',
                    'message': f"{image_alt['images_with_empty_alt']} image(s) with empty alt attribute",
                    'weight': weight
                })
            
            # Internal links issues
            internal_links = onpage_results.get('internal_links', {})
            if internal_links.get('issues'):
                for issue in internal_links['issues']:
                    if 'broken' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('broken_internal_links', -4)
                    elif 'excessive' in issue.lower() or 'too many' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('excessive_internal_links', -2)
                    elif 'without anchor text' in issue.lower() or 'anchor text' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('link_without_anchor_text', -2)
                    else:
                        weight = self.ISSUE_WEIGHTS.get('internal_links_other', -2)
                    score += weight
                    all_issues.append({
                        'category': 'On-Page',
                        'type': 'Internal Links',
                        'severity': internal_links.get('severity', 'low'),
                        'message': issue,
                        'weight': weight
                    })
        
        # More liberal scoring: ensure score doesn't go below 20 (instead of 0)
        # This gives pages a minimum score even with many issues
        score = max(20, score)
        
        # Sort issues by severity (critical first)
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_issues.sort(key=lambda x: (severity_order.get(x['severity'], 4), abs(x['weight'])), reverse=True)
        
        return {
            'score': score,
            'issues': all_issues,
            'issue_count': len(all_issues),
            'critical_count': len([i for i in all_issues if i['severity'] == 'critical']),
            'high_count': len([i for i in all_issues if i['severity'] == 'high']),
            'medium_count': len([i for i in all_issues if i['severity'] == 'medium']),
            'low_count': len([i for i in all_issues if i['severity'] == 'low'])
        }
    
    def calculate_site_score(self, all_page_scores: List[Dict]) -> Dict:
        """
        Calculate overall site score from all page scores.
        
        Args:
            all_page_scores: List of page result dicts (with 'score' key) or score dicts directly
            
        Returns:
            Dict with site-wide statistics
        """
        if not all_page_scores:
            return {
                'average_score': 0,
                'total_pages': 0,
                'total_issues': 0,
                'critical_issues': 0,
                'high_issues': 0
            }
        
        # Extract score dicts - handle both full page results and score dicts
        score_dicts = []
        for page in all_page_scores:
            if 'score' in page and isinstance(page['score'], dict):
                # Full page result with nested score dict
                score_dicts.append(page['score'])
            else:
                # Already a score dict
                score_dicts.append(page)
        
        total_score = sum(score['score'] for score in score_dicts)
        average_score = total_score / len(score_dicts)
        
        # Use average score directly without scaling
        # This allows sites to achieve scores up to 100
        final_average_score = average_score
        
        total_issues = sum(score['issue_count'] for score in score_dicts)
        total_critical = sum(score['critical_count'] for score in score_dicts)
        total_high = sum(score['high_count'] for score in score_dicts)
        
        return {
            'average_score': round(final_average_score, 2),
            'total_pages': len(score_dicts),
            'total_issues': total_issues,
            'critical_issues': total_critical,
            'high_issues': total_high,
            'medium_issues': sum(score['medium_count'] for score in score_dicts),
            'low_issues': sum(score['low_count'] for score in score_dicts)
        }

