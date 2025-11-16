# RSS Feed Verification Report

**Date**: 2025-11-15
**Status**: ✅ Verified and Updated

---

## Summary

- **Total Feeds Tested**: 12
- **Working**: 10 ✅
- **Redirects** (working): 2 ⚠️
- **Broken**: 1 ❌ (removed)
- **New Feeds Added**: 2

---

## Changes Made

### ✅ Fixed: Anthropic RSS Feed
**Issue**: `https://www.anthropic.com/news/rss` returns 404

**Solution**: Replaced with working community-maintained Engineering RSS feed
- **Old (broken)**: `https://www.anthropic.com/news/rss`
- **New (working)**: `https://raw.githubusercontent.com/conoro/anthropic-engineering-rss-feed/main/anthropic_engineering_rss.xml`
- **Focus**: Research engineering, interpretability, alignment

### ✅ Added: Anthropic Research Page
**Added**: `https://www.anthropic.com/research` to blog scraper
- **Tier**: 1 (Primary Source)
- **Priority**: Critical
- **Content**: Published research papers, interpretability work, alignment research

---

## Verified RSS Feeds (Tier 1 - Research Labs)

| Feed | URL | Status | Notes |
|------|-----|--------|-------|
| **Anthropic Engineering** | `https://raw.githubusercontent.com/conoro/anthropic-engineering-rss-feed/main/anthropic_engineering_rss.xml` | ✅ 200 | Community-maintained, updated regularly |
| **OpenAI News** | `https://openai.com/news/rss.xml` | ✅ 200 | Official RSS feed |
| **OpenAI Research** | `https://raw.githubusercontent.com/Olshansk/rss-feeds/refs/heads/main/feeds/feed_openai_research.xml` | ✅ 200 | Community-curated research papers |

---

## Verified RSS Feeds (Tier 2 - Synthesis Sources)

| Feed | URL | Status | Notes |
|------|-----|--------|-------|
| **One Useful Thing** (Ethan Mollick) | `https://www.oneusefulthing.org/feed` | ✅ 200 | Practical strategy, transformation |
| **Simon Willison** | `https://simonwillison.net/atom/everything/` | ✅ 200 | Technical implementation, agents |
| **AI Snake Oil** | `https://aisnakeoil.substack.com/feed` | ⚠️ 301 | Redirect works fine with feedparser |
| **Interconnects** (Nathan Lambert) | `https://www.interconnects.ai/feed` | ✅ 200 | Technical + strategic |
| **Chip Huyen** | `https://huyenchip.com/feed` | ✅ 200 | MLOps, production patterns |
| **Eugene Yan** | `https://eugeneyan.com/rss/` | ✅ 200 | Applied ML patterns |
| **The Sequence** | `https://thesequence.substack.com/feed` | ✅ 200 | Weekly ML/AI developments |

---

## Verified RSS Feeds (Tier 5 - Implementation)

| Feed | URL | Status | Notes |
|------|-----|--------|-------|
| **LangChain Blog** | `https://blog.langchain.dev/rss/` | ⚠️ 308 | Redirect works fine with feedparser |
| **HuggingFace Blog** | `https://huggingface.co/blog/feed.xml` | ✅ 200 | Transformers, model deployment |

---

## Blog Scraper Targets (Tier 1)

| Site | URL | Status | Notes |
|------|-----|--------|-------|
| **Anthropic News** | `https://www.anthropic.com/news` | ✅ 200 | Company announcements |
| **Anthropic Research** | `https://www.anthropic.com/research` | ✅ 200 | **NEW** - Research papers |
| **DeepMind Blog** | `https://deepmind.google/discover/blog/` | ✅ 200 | Research blog |
| **Google AI Blog** | `https://ai.googleblog.com/` | ✅ 200 | Research announcements |
| **Meta AI Blog** | `https://ai.meta.com/blog/` | ✅ 200 | Research updates |

---

## Additional Anthropic Resources

### Research Sites
- **Main Research Page**: https://www.anthropic.com/research
- **Alignment Blog**: https://alignment.anthropic.com/
- **Transformer Circuits**: https://transformer-circuits.pub/

### RSS Options Considered
- ❌ **RSSHub Feed**: `https://rsshub.app/anthropic/news` - Returns 522 (unreliable)
- ❌ **Official RSS**: `https://www.anthropic.com/news/rss` - Returns 404 (doesn't exist)
- ✅ **Engineering RSS**: `https://raw.githubusercontent.com/conoro/anthropic-engineering-rss-feed/main/anthropic_engineering_rss.xml` - **SELECTED**

---

## Feed Collection Stats (Latest Run)

From database query showing actual items collected:
```
61 items - arXiv papers
19 items - Simon Willison (RSS)
10 items - DeepMind (Blog Scraper)
10 items - OpenAI News (RSS)
 4 items - HackerNews (API)
 4 items - The Sequence (RSS)
 2 items - Interconnects (RSS)
 2 items - LangChain (RSS)
 1 item  - Anthropic News (Blog Scraper)
 1 item  - HuggingFace (RSS)
 1 item  - One Useful Thing (RSS)
 1 item  - Latent Space (RSS)
 1 item  - Last Week in AI (RSS)
```

**Total**: 117 unique items from 13 sources in last 7 days

---

## Testing Methodology

### HTTP Status Code Test
```bash
curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url"
```

### Success Criteria
- **200**: Perfect, feed working
- **301/308**: Redirect, works with feedparser
- **404/522**: Broken, needs replacement

---

## Recommendations

### Immediate
- ✅ **DONE**: Replace broken Anthropic RSS with working Engineering feed
- ✅ **DONE**: Add Anthropic Research page to blog scraper

### Future Enhancements
1. **Monitor RSSHub**: Check if `https://rsshub.app/anthropic/news` becomes stable
2. **Add Alignment Blog**: Consider adding `https://alignment.anthropic.com/` to blog scraper
3. **Add Transformer Circuits**: Consider adding `https://transformer-circuits.pub/` for interpretability research

### Feed Reliability Monitoring
Create a health check script to periodically verify all RSS feeds are still working:
```bash
research-agent test-config  # Future CLI command (Issue #60)
```

---

## References

- [Anthropic Engineering RSS GitHub](https://github.com/conoro/anthropic-engineering-rss-feed)
- [Olshansk RSS Feeds](https://github.com/Olshansk/rss-feeds)
- [RSSHub Anthropic](https://rsshub.app/anthropic/news) (unreliable)

---

**Last Updated**: 2025-11-15
**Next Verification**: Recommended monthly or when collection issues occur
