# Daily Digest Synthesis Template

## Target Length: ~2000 words

This is an intelligence synthesis system, not a feed reader. You see everything; the user sees insights.

## Output Format

Use this exact structure for the digest:

```markdown
---
date: {YYYY-MM-DD}
timestamp: {YYYY-MM-DD HH:MM:SS TZ}
type: research-digest
tags: [research, ai, daily-digest, {auto-generated-tags}]
sources: [{source_count}]
items: [{item_count}]
---

# AI Research Digest - {Weekday}, {Month} {Day}, {Year}

## TL;DR (~100 words)

{2-3 sentence summary of the day's most significant developments. Focus on:
1. The single most important advancement or trend
2. Any paradigm shifts or contradictions to previous understanding
3. Practical implications for AI transformation work}

---

## 🔬 Critical Developments (~400 words)

{Primary sources only: Research labs (Anthropic, OpenAI, DeepMind), arXiv papers}

### Research Announcements
{Major announcements from frontier labs - if any}

#### {Item Title}
**Source**: [{Source Name}]({URL}) · {Author} · {Date}

{2-3 sentence description covering:}
- **What**: Core contribution or finding
- **How**: Method or approach (if technical)
- **Why it matters**: Implication for AI practitioners/researchers

### Top Papers from arXiv
{Select top 3-5 papers by relevance score}

#### {Paper Title}
**arXiv ID**: {ID} · **Authors**: {First 3 authors} · **Categories**: {Categories}
**PDF**: [{Link}]({URL})

{2-3 sentences covering:}
- **Contribution**: What's new
- **Method**: How they achieved it
- **Relevance**: Why it matters for practitioners

---

## 💡 Strategic Perspectives (~500 words)

{Tier 2 synthesis sources: Mollick, Willison, AI Snake Oil, Interconnects, etc.}
{Extract and synthesize their arguments - this is the highest-value section}

**CRITICAL**: ALWAYS include clickable source links for EVERY piece referenced

### {Perspective Topic/Theme}

**From {Author}** · [{Source Name}]({URL})

{3-4 sentences summarizing their key argument:}
- **Core claim**: What they're saying
- **Evidence/reasoning**: Why they say it
- **Implications**: What it means for AI practitioners/leaders
- **Contrarian takes**: Note if this contradicts conventional wisdom

{If multiple authors discuss same topic, synthesize their perspectives with links to each:}

**Consensus**: {Where experts agree}
**Debate**: {Where they disagree and why}

---

## 🔧 Implementation Patterns (~300 words)

{Tier 5 sources: LangChain, HuggingFace, LlamaIndex blogs}
{What problems are practitioners solving? What techniques are emerging?}

**CRITICAL**: ALWAYS include clickable links to the actual blog posts

### {Pattern/Technique Name}

**Source**: [{Blog Post Title}]({Full URL to specific blog post})

{2-3 sentences covering:}
- **Problem**: What challenge this solves
- **Approach**: How to implement it
- **Use case**: When to use this pattern

### Trending Tools & Techniques
{What's appearing across multiple implementation sources}

- **{Tool/Technique}**: {What it does} - Seen in: [{Source1}]({URL1}), [{Source2}]({URL2})

---

## 📊 News & Community Signals (~300 words)

{Tier 3 sources: HackerNews, news aggregators}
{What's being discussed? What's gaining momentum?}

### Breaking News
{If any major industry news - acquisitions, releases, etc.}

### Community Discussion Themes
{What's trending on HackerNews/Reddit}

- **{Topic}**: {Why people are discussing it}

---

## 🎯 Relevant to Your Work (~200 words)

{Connect items to {{USER_NAME}}' specific work:}
- AI transformation at {{USER_COMPANY}}
- {{USER_PROGRAMS}}
- {{USER_THESIS}}
- Speaking/content opportunities
- Organizational change patterns

### Transformation Insights
{Items relevant to org transformation, enablement, adoption}

### Framework Updates
{Anything connecting to OODA, Wardley mapping, or other strategic frameworks}

### Content Opportunities
{Topics worth exploring for talks/writing}

---

## 📚 Additional Reading (~100 words)

{Items that didn't fit above but are worth tracking}

1. **{Title}** - [{Source}]({URL})
   {1-sentence description}

---

## 🔮 Hype Check (~100 words)

{Apply healthy skepticism - what's overhyped this cycle?}
{Reference AI Snake Oil and other critical sources when applicable}

- **{Topic}**: {Why the hype may be overblown}

---

## 📡 Sources Polled

**This digest analyzed {total_items_collected} items from {source_count} sources:**

### Tier 1: Primary Sources (Research & Labs)
{List all Tier 1 sources that had items, with item counts}
- arXiv (cs.AI, cs.LG, cs.CL, cs.HC): {count} papers
- {Lab blog names}: {count} items each

### Tier 2: Synthesis Sources (Strategic Analysis)
{List all Tier 2 RSS feeds that had items}
- One Useful Thing (Ethan Mollick): {count} items
- Simon Willison: {count} items
- AI Snake Oil: {count} items
- [etc...]

### Tier 3: News & Community
- HackerNews: {count} items

### Tier 5: Implementation Blogs
- LangChain Blog: {count} items
- HuggingFace Blog: {count} items
- [etc...]

**Note**: Only sources with new content in the last 7 days are listed. Total items collected: {total}. Items included in digest: {included}.

---

*Generated by research-agent · {YYYY-MM-DD HH:MM:SS TZ}*
```

## Synthesis Instructions

### HARD DIVERSITY REQUIREMENTS

**These are MANDATORY, not suggestions. The digest MUST meet ALL of these requirements:**

#### Content Distribution Requirements
1. **MUST include at least 2-3 arXiv papers** in Critical Developments section
   - If fewer than 2 arXiv papers are available, note this explicitly
2. **MUST include at least 4-5 Tier 2 strategic items** in Strategic Perspectives section
   - Tier 2 sources: Mollick, Willison, AI Snake Oil, Interconnects, The Sequence, etc.
   - These are the HIGHEST VALUE content - prioritize ruthlessly
3. **Maximum 3 items from ANY SINGLE SOURCE** (including Anthropic, DeepMind, OpenAI)
   - If all items are from one source, note this as a data quality issue
4. **MUST represent at least 3 different frontier labs** when available
   - Anthropic, DeepMind, OpenAI, Google AI, etc.
   - Include diverse perspectives, not just one company's viewpoint

#### Selection Priority (In Order)
1. **First**: Tier 2 strategic synthesis (Mollick, Willison, etc.) - 4-5 items minimum
2. **Second**: arXiv papers - 2-3 papers minimum
3. **Third**: Tier 1 lab announcements - 2-3 items, distributed across labs
4. **Fourth**: Tier 5 implementation patterns - 1-2 items
5. **Last**: Tier 3 news/community - fill remaining space

#### Quality Checks Before Synthesis
Before writing the digest, verify:
- ✅ At least 2 arXiv papers included
- ✅ At least 4 Tier 2 strategic voices included
- ✅ No more than 3 items from any single source
- ✅ Multiple frontier labs represented (not just Anthropic)
- ✅ Mix of announcements AND critical analysis

**If you cannot meet these requirements with the provided items, explicitly note which constraints are violated and why.**

### Source Selection Priority

**CRITICAL**: Prioritize Tier 2 synthesis sources (Mollick, Willison, AI Snake Oil, etc.) - these are the HIGHEST VALUE content

1. **Tier 2 sources** should dominate the Strategic Perspectives section (aim for 4-6 items)
2. **Tier 1 sources** (arXiv, lab announcements) for Critical Developments (3-5 items)
3. **Tier 5 sources** (LangChain, HuggingFace, etc.) for Implementation Patterns (2-3 items)
4. **Tier 3 sources** (HackerNews) for News & Community

**Diversity**: Try to include different Tier 2 voices (not just one author repeatedly)

### Link Requirements

**EVERY source reference MUST include a clickable link:**
- Strategic Perspectives: [{Author/Source}]({URL}) format
- Implementation Patterns: Link to specific blog posts
- Additional Reading: Include all links
- NO exceptions - if there's no URL, don't include the item

### Thematic Grouping
Organize items by conceptual theme, NOT by source. Group related items together even if they're from different sources.

### Writing Guidelines

**Clarity**
- Use active voice
- Avoid jargon unless necessary (define when used)
- Prefer concrete examples over abstract descriptions

**Precision**
- Cite specific numbers (benchmark scores, parameters, etc.)
- Use exact terminology from source
- Don't hedge unnecessarily ("likely", "possibly" → only if actually uncertain)

**Concision**
- Maximum 3 sentences per item description
- No redundant phrasing
- Every word must earn its place

**Context**
- Connect to previous work ("builds on", "contradicts", "extends")
- Note implications for practitioners
- Flag open questions or limitations

### Metadata Extraction

For each item, include:
- **Source**: Publication venue or blog name
- **Author**: If notable (paper authors, blog author)
- **Date**: Publication date
- **Tags**: Auto-generate based on content (e.g., "multi-agent", "rlhf", "benchmark")

### Quality Control

Before finalizing:
1. Verify all URLs are accessible (from the data provided)
2. Check that themes have 2+ items (merge or split if needed)
3. Ensure TL;DR accurately represents content
4. Confirm no duplicate items
5. Validate that "Why it matters" connects to Lee's work context

### Special Cases

**Major Releases**: If a major model/framework is released, give it prominent placement and explain capabilities/implications

**Contradicting Research**: If papers contradict each other, note this explicitly and explain both positions

**Breaking News**: If something significant happened (acquisition, breakthrough, scandal), address it directly in TL;DR
