# Pattern Resolution System

## Overview
The pattern system uses a "smallest set priority" strategy for resolving conflicts between overlapping patterns. This applies to title patterns, division patterns, and document type patterns. The pattern that matches the smallest set of URLs takes precedence.

## How It Works

When multiple patterns match a URL, the system:
1. Counts how many total URLs each pattern matches
2. Compares the counts
3. Applies the pattern that matches the fewest URLs

### Example
```
Pattern A: */docs/*          # Matches 100 URLs
Pattern B: */docs/api/*      # Matches 20 URLs
Pattern C: */docs/api/v2/*   # Matches 5 URLs

For URL "/docs/api/v2/users":
- All patterns match
- Pattern C wins (5 URLs < 20 URLs < 100 URLs)
```

## Pattern Types and Resolution

### Title Patterns
```python
# More specific title pattern takes precedence
Pattern A: */docs/* → title="Documentation"           # 100 URLs
Pattern B: */docs/api/* → title="API Reference"       # 20 URLs
Result: URL gets title "API Reference"
```

### Division Patterns
```python
# More specific division assignment wins
Pattern A: *.pdf → division="GENERAL"                 # 500 URLs
Pattern B: */specs/*.pdf → division="ENGINEERING"     # 50 URLs
Result: URL gets division "ENGINEERING"
```

### Document Type Patterns
```python
# Most specific document type classification applies
Pattern A: */docs/* → type="DOCUMENTATION"            # 200 URLs
Pattern B: */docs/data/* → type="DATA"                # 30 URLs
Result: URL gets type "DATA"
```
