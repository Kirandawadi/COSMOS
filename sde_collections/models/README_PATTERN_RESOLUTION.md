# URL Pattern Application Strategies

## Strategy 1: Exclusive Patterns

Patterns have exclusive ownership of URLs they match. System prevents creation of overlapping patterns.

Example:
```
Pattern A: */docs/*          # Matches 100 URLs
Pattern B: */docs/api/*      # Rejected - overlaps with Pattern A
Pattern C: */blog/*          # Accepted - no overlap
```

Benefits:
- Clear ownership
- Predictable effects
- Simple conflict resolution
- Easy to debug

Drawbacks:
- Less flexible
- May require many specific patterns
- May need pattern deletion/recreation to modify rules

## Strategy 2: Smallest Set Priority

Multiple patterns can match same URLs. Pattern affecting smallest URL set takes precedence.

Example:
```
Pattern A: */docs/*          # Matches 100 URLs
Pattern B: */docs/api/*      # Matches 20 URLs
Pattern C: */docs/api/v2/*   # Matches 5 URLs

For URL "/docs/api/v2/users":
- All patterns match
- Pattern C wins (5 URLs < 20 URLs < 100 URLs)
```

Benefits:
- More flexible rule creation
- Natural handling of specificity

Drawbacks:
- Complex precedence rules
- Pattern effects can change as URL sets grow
- Harder to predict/debug
- Performance impact from URL set size calculations

## Implementation Notes

Strategy 1:
```python
def save(self, *args, **kwargs):
    # Check for overlapping patterns
    overlapping = self.get_matching_delta_urls().filter(
        deltapatterns__isnull=False
    ).exists()
    if overlapping:
        raise ValidationError("Pattern would overlap existing pattern")
    super().save(*args, **kwargs)
```

Strategy 2:
```python
def apply(self):
    matching_urls = self.get_matching_delta_urls()
    my_url_count = matching_urls.count()

    # Only apply if this pattern matches fewer URLs than other matching patterns
    for url in matching_urls:
        other_patterns_min_count = url.deltapatterns.annotate(
            url_count=Count('delta_urls')
        ).aggregate(Min('url_count'))['url_count__min'] or float('inf')

        if my_url_count <= other_patterns_min_count:
            self.apply_to_url(url)
```
