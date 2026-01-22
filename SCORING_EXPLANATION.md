# SEO Health Score Calculation - Detailed Explanation

## Overview

The SEO health score is calculated using a **two-tier penalty system**:
1. **Severity Weights** - Generic penalties based on issue severity level
2. **Issue-Specific Weights** - Custom penalties for specific, well-known issues

Both systems work together, with **Issue-Specific Weights taking priority** when available.

---

## 1. Severity Weights (Generic Penalty System)

### Purpose
Severity weights provide a **fallback/default penalty** for issues that don't have a specific weight defined. They're based on the severity level assigned to an issue.

### Values (Lines 14-19 in `rule_engine.py`)
```python
SEVERITY_WEIGHTS = {
    'critical': -15,  # Most severe issues
    'high': -8,       # High priority issues
    'medium': -4,    # Medium priority issues
    'low': -2        # Low priority issues
}
```

### When Used
Severity weights are used when:
- An issue has a severity level but **no specific weight** is defined in `ISSUE_WEIGHTS`
- The issue type is generic and doesn't match any specific issue pattern

### Examples from Code

**Example 1: Title tag issues (Line 151)**
```python
elif title.get('issues'):
    for issue in title['issues']:
        weight = self.SEVERITY_WEIGHTS.get(title.get('severity', 'medium'), -10)
        # If severity is 'high', weight = -8
        # If severity is 'medium', weight = -4
        # If severity is 'low', weight = -2
```

**Example 2: Meta description issues (Line 175)**
```python
elif meta_desc.get('issues'):
    for issue in meta_desc['issues']:
        weight = self.SEVERITY_WEIGHTS.get(meta_desc.get('severity', 'medium'), -10)
        # Uses severity-based penalty
```

**Example 3: Canonical issues (Line 80)**
```python
else:
    weight = self.SEVERITY_WEIGHTS.get(canonical.get('severity', 'medium'), -10)
    # Used when canonical issue doesn't match '404' or 'homepage' patterns
```

**Example 4: Image alt text (Line 215)**
```python
weight = self.SEVERITY_WEIGHTS.get('medium', -4)
score += weight * min(image_alt['images_without_alt'], 3)  # -4 per image, max 3 images = -12
```

---

## 2. Issue-Specific Weights (Custom Penalty System)

### Purpose
Issue-specific weights provide **precise, tailored penalties** for well-known SEO issues that have a significant impact. These take **priority over severity weights**.

### Values (Lines 22-39 in `rule_engine.py`)
```python
ISSUE_WEIGHTS = {
    'noindex_on_indexable': -15,      # Page has noindex but should be indexable
    'canonical_404': -12,              # Canonical points to 404 page
    'canonical_to_homepage': -12,      # Canonical points to homepage
    'missing_title': -8,               # No title tag at all
    'missing_meta_description': -6,     # No meta description
    'no_h1': -6,                       # No H1 tag
    'redirect_chain_404': -12,          # Redirect chain ends in 404
    'redirect_loop': -15,               # Redirect loop detected
    'mixed_content_js_css': -10,        # Mixed HTTP/HTTPS content
    'not_https': -15,                   # Page not served over HTTPS
    'missing_structured_data': -2,      # No structured data
    'broken_internal_links': -4,        # Broken internal links
    'orphan_page': -6,                  # Page with no internal in-links
    'duplicate_title': -4,              # Duplicate title tags
    'duplicate_description': -2,        # Duplicate meta descriptions
    'multiple_h1': -4                  # Multiple H1 tags
}
```

### When Used
Issue-specific weights are used when:
- The code **explicitly checks for a specific issue pattern**
- The issue matches a known SEO problem with a defined weight

### Examples from Code

**Example 1: Missing Title Tag (Line 140)**
```python
if not title.get('has_title', False):
    weight = self.ISSUE_WEIGHTS.get('missing_title', -20)  # Uses -8 from ISSUE_WEIGHTS
    score += weight  # Score: 100 - 8 = 92
```

**Example 2: Canonical 404 (Line 75-76)**
```python
if '404' in issue.lower():
    weight = self.ISSUE_WEIGHTS.get('canonical_404', -30)  # Uses -12 from ISSUE_WEIGHTS
    score += weight  # Score: 100 - 12 = 88
```

**Example 3: Not HTTPS (Line 114)**
```python
if not https.get('is_https', True):
    weight = self.ISSUE_WEIGHTS.get('not_https', -40)  # Uses -15 from ISSUE_WEIGHTS
    score += weight  # Score: 100 - 15 = 85
```

**Example 4: Broken Internal Links (Line 230-231)**
```python
if 'broken' in issue.lower():
    weight = self.ISSUE_WEIGHTS.get('broken_internal_links', -10)  # Uses -4 from ISSUE_WEIGHTS
    score += weight  # Score: 100 - 4 = 96
```

**Example 5: Multiple H1 Tags (Line 199-200)**
```python
if 'multiple' in issue.lower():
    weight = self.ISSUE_WEIGHTS.get('multiple_h1', -10)  # Uses -4 from ISSUE_WEIGHTS
    score += weight  # Score: 100 - 4 = 96
```

---

## 3. Priority System: How They Work Together

### Decision Logic Flow

```
1. Check if issue matches a specific pattern
   ↓ YES → Use ISSUE_WEIGHTS (specific penalty)
   ↓ NO  → Check severity level
            ↓ Use SEVERITY_WEIGHTS (generic penalty)
```

### Code Examples Showing Priority

**Example 1: Canonical Issues (Lines 74-80)**
```python
if canonical.get('issues'):
    for issue in canonical['issues']:
        if '404' in issue.lower():
            # PRIORITY 1: Specific pattern match → Use ISSUE_WEIGHTS
            weight = self.ISSUE_WEIGHTS.get('canonical_404', -30)  # -12
        elif 'homepage' in issue.lower():
            # PRIORITY 1: Specific pattern match → Use ISSUE_WEIGHTS
            weight = self.ISSUE_WEIGHTS.get('canonical_to_homepage', -30)  # -12
        else:
            # PRIORITY 2: No pattern match → Use SEVERITY_WEIGHTS
            weight = self.SEVERITY_WEIGHTS.get(canonical.get('severity', 'medium'), -10)
            # If severity='high' → -8, if 'medium' → -4, if 'low' → -2
```

**Example 2: Title Issues (Lines 139-159)**
```python
if not title.get('has_title', False):
    # PRIORITY 1: Missing title → Use ISSUE_WEIGHTS
    weight = self.ISSUE_WEIGHTS.get('missing_title', -20)  # -8
elif title.get('issues'):
    # PRIORITY 2: Other title issues → Use SEVERITY_WEIGHTS
    for issue in title['issues']:
        weight = self.SEVERITY_WEIGHTS.get(title.get('severity', 'medium'), -10)
        # Uses severity-based penalty
```

**Example 3: Internal Links (Lines 228-234)**
```python
if internal_links.get('issues'):
    for issue in internal_links['issues']:
        if 'broken' in issue.lower():
            # PRIORITY 1: Broken links → Use ISSUE_WEIGHTS
            weight = self.ISSUE_WEIGHTS.get('broken_internal_links', -10)  # -4
        else:
            # PRIORITY 2: Other link issues → Use SEVERITY_WEIGHTS
            weight = self.SEVERITY_WEIGHTS.get(internal_links.get('severity', 'low'), -5)  # -2
```

---

## 4. Page Score Calculation

### Step-by-Step Process

1. **Start with base score** (Line 55)
   ```python
   score = self.base_score  # score = 100
   ```

2. **Process Technical Issues** (Lines 59-133)
   - Check noindex → Apply `ISSUE_WEIGHTS['noindex_on_indexable']` = -15
   - Check canonical → Apply specific or severity weight
   - Check redirects → Apply specific or severity weight
   - Check HTTPS → Apply `ISSUE_WEIGHTS['not_https']` = -15
   - Check mixed content → Apply `ISSUE_WEIGHTS['mixed_content_js_css']` = -10

3. **Process On-Page Issues** (Lines 136-241)
   - Check title → Apply `ISSUE_WEIGHTS['missing_title']` = -8 or severity weight
   - Check meta description → Apply `ISSUE_WEIGHTS['missing_meta_description']` = -6 or severity weight
   - Check H1 → Apply `ISSUE_WEIGHTS['no_h1']` = -6 or severity weight
   - Check image alt → Apply severity weight × number of images (capped at 3)
   - Check internal links → Apply specific or severity weight

4. **Apply Minimum Floor** (Line 245)
   ```python
   score = max(20, score)  # Score cannot go below 20
   ```

### Example Calculation

**Scenario: Page with multiple issues**

```
Initial Score: 100

Technical Issues:
- Noindex directive: -15 (ISSUE_WEIGHTS)
- Not HTTPS: -15 (ISSUE_WEIGHTS)
- Canonical 404: -12 (ISSUE_WEIGHTS)

On-Page Issues:
- Missing title: -8 (ISSUE_WEIGHTS)
- Missing meta description: -6 (ISSUE_WEIGHTS)
- No H1: -6 (ISSUE_WEIGHTS)
- 2 images without alt: -8 (SEVERITY_WEIGHTS['medium'] × 2 = -4 × 2)
- Title too short (severity='high'): -8 (SEVERITY_WEIGHTS['high'])

Total Penalties: -15 -15 -12 -8 -6 -6 -8 -8 = -78
Final Score: 100 - 78 = 22
After Floor: max(20, 22) = 22
```

---

## 5. Site Score Calculation

### Process (Lines 261-309)

1. **Extract all page scores** (Lines 280-288)
   ```python
   score_dicts = []
   for page in all_page_scores:
       if 'score' in page and isinstance(page['score'], dict):
           score_dicts.append(page['score'])
   ```

2. **Calculate average** (Lines 290-291)
   ```python
   total_score = sum(score['score'] for score in score_dicts)
   average_score = total_score / len(score_dicts)
   ```

3. **Apply scaling factor** (Line 295)
   ```python
   scaled_average_score = average_score * 0.7  # 70% of average
   ```

4. **Round and return** (Line 302)
   ```python
   'average_score': round(scaled_average_score, 2)
   ```

### Example Calculation

**Scenario: Site with 5 pages**

```
Page 1 Score: 85
Page 2 Score: 72
Page 3 Score: 90
Page 4 Score: 68
Page 5 Score: 88

Total: 85 + 72 + 90 + 68 + 88 = 403
Average: 403 / 5 = 80.6
Scaled (70%): 80.6 × 0.7 = 56.42
Final Site Score: 56.42
```

---

## 6. Key Differences: Severity vs Issue-Specific

| Aspect | Severity Weights | Issue-Specific Weights |
|--------|-----------------|----------------------|
| **Purpose** | Generic fallback for any issue | Specific penalties for known issues |
| **Priority** | Lower (used when no specific match) | Higher (takes precedence) |
| **Flexibility** | Works for any severity level | Only for predefined issues |
| **Examples** | Title too short, meta too long | Missing title, canonical 404, not HTTPS |
| **Usage** | `SEVERITY_WEIGHTS.get(severity, default)` | `ISSUE_WEIGHTS.get('issue_key', default)` |

---

## 7. Why Two Systems?

### Severity Weights
- **Flexibility**: Can handle any new issue type without code changes
- **Consistency**: Same severity level = same penalty across different issue types
- **Simplicity**: Easy to understand and maintain

### Issue-Specific Weights
- **Precision**: Tailored penalties based on actual SEO impact
- **Control**: Fine-tune penalties for critical issues
- **Clarity**: Makes it explicit what penalty applies to what issue

### Combined Benefits
- **Best of both worlds**: Specific control where needed, generic fallback elsewhere
- **Maintainability**: Easy to adjust specific issues without affecting others
- **Scalability**: Can add new specific weights as needed

---

## 8. Summary

1. **Page Score** = 100 - (sum of all penalties)
   - Penalties come from either `ISSUE_WEIGHTS` (priority) or `SEVERITY_WEIGHTS` (fallback)
   - Minimum score is 20

2. **Site Score** = (Average of all page scores) × 0.7
   - Scaled to 70% to be more conservative
   - Rounded to 2 decimal places

3. **Priority Order**:
   - First: Check for specific issue pattern → Use `ISSUE_WEIGHTS`
   - Second: Use severity level → Use `SEVERITY_WEIGHTS`

4. **Scoring Philosophy**:
   - **Liberal scoring**: Reduced penalties from original values
   - **Minimum floor**: Pages can't score below 20
   - **Conservative site score**: 70% scaling factor

