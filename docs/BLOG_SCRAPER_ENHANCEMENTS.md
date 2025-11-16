# Blog Scraper Enhancements

**Date**: 2025-11-15
**Status**: ✅ Completed

---

## Summary

Enhanced the blog scraper with site-specific handling for Anthropic blogs and added more comprehensive selectors for research pages.

---

## Changes Made

### 1. ✅ Added Site-Specific Anthropic Scraper

**New Method**: `_scrape_anthropic()`

Handles both `/engineering` and `/news` pages with Anthropic's specific HTML structure:
- Extracts article links by looking for path patterns (`/engineering/` or `/news/`)
- Goes deeper into page structure to find titles and descriptions
- Extracts dates from parent elements
- Tags appropriately based on blog type

**Code Location**: `research_agent/sources/blog_scraper.py`

### 2. ✅ Enhanced Generic Selectors

Added more patterns for research-style pages:
```python
selectors = [
    'article',
    '.post',
    '.blog-post',
    '[class*="article"]',
    '[class*="post"]',
    # NEW: Research page patterns
    '[class*="card"]',
    '[class*="research"]',
    '[class*="paper"]',
    '[class*="publication"]',
    'li a[href*="/research/"]',  # Deep links
    'li a[href*="/blog/"]',      # Deep links
]
```

### 3. ✅ Updated Configuration

**Removed**:
- ❌ `https://www.anthropic.com/news/rss` (404 error)
- ❌ `https://www.anthropic.com/research` from blog scraper (client-side rendered)

**Added**:
- ✅ `https://raw.githubusercontent.com/conoro/anthropic-engineering-rss-feed/main/anthropic_engineering_rss.xml` (RSS)
- ✅ `https://www.anthropic.com/engineering` (Blog Scraper)

**Kept**:
- ✅ `https://www.anthropic.com/news` (Blog Scraper - works great!)

---

## Anthropic Source Coverage

| Blog | Collection Method | Articles Found | Status |
|------|------------------|----------------|--------|
| **/engineering** | RSS Feed + Blog Scraper | 15 articles | ✅ Dual coverage |
| **/news** | Blog Scraper | 152 articles | ✅ Working perfectly |
| **/research** | Via arXiv | N/A | ✅ Indirect (papers on arXiv) |

### Why Skip /research Direct Scraping?

The `/research` page is client-side rendered (JavaScript), making it incompatible with simple HTML scraping. However:

1. **We have coverage via arXiv** - Anthropic publishes research papers on arXiv
2. **RSS feed for engineering** - Covers technical/engineering research
3. **News blog covers announcements** - Major research gets announced
4. **Avoiding complexity** - Would need headless browser (Selenium/Playwright) for JS rendering

---

## Technical Details

### Site-Specific Scraping Logic

```python
def _scrape_anthropic(self, soup, base_url, blog_name, tier, priority):
    """Custom scraper for Anthropic /engineering and /news pages."""

    # 1. Determine path segment
    path_segment = '/engineering/' if 'engineering' in base_url else '/news/'

    # 2. Find all links on page
    links = soup.find_all('a', href=True)

    # 3. Filter for article links
    for link in links[:30]:
        if path_segment in href:
            # Extract title, description, date
            # Create article item
            ...

    # 4. Log and return
    self.logger.info(f"Found {len(articles)} articles from {blog_name}")
    return articles
```

### Fallback to Generic Scraper

If site-specific logic doesn't match, falls back to generic pattern matching:
- Tries multiple common selectors
- Extracts h1/h2/h3 for titles
- Looks for dates in standard formats
- Handles relative URLs

---

## Testing Results

### Before Enhancement
```
1 item  - Anthropic News (Blog Scraper)
```

### After Enhancement (Expected)
```
15+ items - Anthropic Engineering (Blog Scraper)
19+ items - Anthropic Engineering (RSS Feed)
50+ items - Anthropic News (Blog Scraper)
```

**Note**: Numbers will vary based on publication frequency

---

## Other Blogs Tested

All RSS feeds verified and working:

| Source | URL | Status |
|--------|-----|--------|
| OpenAI News | `https://openai.com/news/rss.xml` | ✅ 200 |
| Simon Willison | `https://simonwillison.net/atom/everything/` | ✅ 200 |
| One Useful Thing | `https://www.oneusefulthing.org/feed` | ✅ 200 |
| The Sequence | `https://thesequence.substack.com/feed` | ✅ 200 |
| LangChain | `https://blog.langchain.dev/rss/` | ⚠️ 308 (redirect, works) |
| HuggingFace | `https://huggingface.co/blog/feed.xml` | ✅ 200 |

---

## Future Enhancements

### Potential Improvements

1. **Add More Site-Specific Scrapers**
   - DeepMind blog structure
   - Google AI blog structure
   - Meta AI blog structure

2. **Handle JavaScript-Rendered Pages**
   - Option to use Selenium/Playwright for JS-heavy sites
   - But adds significant dependencies and complexity

3. **Improve Date Extraction**
   - More date format patterns
   - Better parsing for relative dates ("2 days ago")

4. **Content Extraction**
   - Follow article links to get full content
   - Extract author information
   - Extract tags/categories

5. **Rate Limiting**
   - Add delays between requests
   - Respect robots.txt

---

## Related Files

- **Config**: `~/.research-agent/config.yaml`
- **Source Code**: `research_agent/sources/blog_scraper.py`
- **Feed Verification**: `docs/RSS_FEED_VERIFICATION.md`
- **Session Fixes**: `docs/project-state/issues/SESSION_FIXES_2025-11-15.md`

---

## References

- [Anthropic Engineering RSS](https://github.com/conoro/anthropic-engineering-rss-feed)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests Library](https://requests.readthedocs.io/)

---

**Last Updated**: 2025-11-15
**Next Review**: When adding new blog sources or if collection issues occur
