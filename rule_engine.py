"""
Rule engine for scoring and prioritizing SEO issues.
"""
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class RuleEngine:
    """Score and prioritize SEO issues based on severity and impact."""
    
    # Severity weights (more liberal - reduced penalties)
    SEVERITY_WEIGHTS = {
        'critical': -15,  # Reduced from -40
        'high': -8,       # Reduced from -20
        'medium': -4,    # Reduced from -10
        'low': -2        # Reduced from -5
    }
    
    # Issue-specific weights (more liberal - reduced penalties)
    ISSUE_WEIGHTS = {
        'noindex_on_indexable': -15,  # Reduced from -40
        'canonical_404': -12,         # Reduced from -30
        'canonical_to_homepage': -12, # Reduced from -30
        'missing_title': -8,          # Reduced from -20
        'missing_meta_description': -6, # Reduced from -15
        'no_h1': -6,                  # Reduced from -15
        'redirect_chain_404': -12,    # Reduced from -30
        'redirect_loop': -15,         # Reduced from -40
        'mixed_content_js_css': -10,  # Reduced from -25
        'not_https': -15,             # Reduced from -40
        'missing_structured_data': -2, # Reduced from -5
        'broken_internal_links': -4,  # Reduced from -10
        'orphan_page': -6,            # Reduced from -15
        'duplicate_title': -4,        # Reduced from -10
        'duplicate_description': -2,   # Reduced from -5
        'multiple_h1': -4             # Reduced from -10
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
            if technical_results.get('noindex', {}).get('has_noindex', False):
                score += self.ISSUE_WEIGHTS.get('noindex_on_indexable', -40)
                all_issues.append({
                    'category': 'Technical',
                    'type': 'Noindex',
                    'severity': 'critical',
                    'message': 'Page has noindex directive',
                    'weight': self.ISSUE_WEIGHTS.get('noindex_on_indexable', -40)
                })
            
            # Canonical issues
            canonical = technical_results.get('canonical', {})
            if canonical.get('issues'):
                for issue in canonical['issues']:
                    if '404' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('canonical_404', -30)
                    elif 'homepage' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('canonical_to_homepage', -30)
                    else:
                        weight = self.SEVERITY_WEIGHTS.get(canonical.get('severity', 'medium'), -10)
                    
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
                        weight = self.ISSUE_WEIGHTS.get('redirect_chain_404', -30)
                    elif 'loop' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('redirect_loop', -40)
                    else:
                        weight = self.SEVERITY_WEIGHTS.get(redirects.get('severity', 'medium'), -10)
                    
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
                weight = self.ISSUE_WEIGHTS.get('mixed_content_js_css', -25)
                score += weight
                all_issues.append({
                    'category': 'Technical',
                    'type': 'Mixed Content',
                    'severity': 'high',
                    'message': f"{https['mixed_content_count']} resource(s) loaded via HTTP",
                    'weight': weight
                })
        
        # Process on-page issues
        if onpage_results:
            # Title issues
            title = onpage_results.get('title', {})
            if not title.get('has_title', False):
                weight = self.ISSUE_WEIGHTS.get('missing_title', -20)
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
                    weight = self.SEVERITY_WEIGHTS.get(title.get('severity', 'medium'), -10)
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
                weight = self.ISSUE_WEIGHTS.get('missing_meta_description', -15)
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
                    weight = self.SEVERITY_WEIGHTS.get(meta_desc.get('severity', 'medium'), -10)
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
                weight = self.ISSUE_WEIGHTS.get('no_h1', -15)
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
                        weight = self.ISSUE_WEIGHTS.get('multiple_h1', -10)
                    else:
                        weight = self.SEVERITY_WEIGHTS.get(h1.get('severity', 'medium'), -10)
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
                weight = self.SEVERITY_WEIGHTS.get('medium', -4)
                # More liberal: reduce impact per image and cap lower
                score += weight * min(image_alt['images_without_alt'], 3)  # Cap at 3 instead of 5
                all_issues.append({
                    'category': 'On-Page',
                    'type': 'Image Alt',
                    'severity': 'medium',
                    'message': f"{image_alt['images_without_alt']} image(s) missing alt text",
                    'weight': weight
                })
            
            # Internal links issues
            internal_links = onpage_results.get('internal_links', {})
            if internal_links.get('issues'):
                for issue in internal_links['issues']:
                    if 'broken' in issue.lower():
                        weight = self.ISSUE_WEIGHTS.get('broken_internal_links', -10)
                    else:
                        weight = self.SEVERITY_WEIGHTS.get(internal_links.get('severity', 'low'), -5)
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
        
        # Reduce the score size by applying a scaling factor (0.7 = 70% of original score)
        # This makes the score more conservative and smaller
        scaled_average_score = average_score * 0.7
        
        total_issues = sum(score['issue_count'] for score in score_dicts)
        total_critical = sum(score['critical_count'] for score in score_dicts)
        total_high = sum(score['high_count'] for score in score_dicts)
        
        return {
            'average_score': round(scaled_average_score, 2),
            'total_pages': len(score_dicts),
            'total_issues': total_issues,
            'critical_issues': total_critical,
            'high_issues': total_high,
            'medium_issues': sum(score['medium_count'] for score in score_dicts),
            'low_issues': sum(score['low_count'] for score in score_dicts)
        }

