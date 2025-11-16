# .gitignore Assessment - Research Agent Project

**Date**: 2025-11-15
**Purpose**: Identify files that should/shouldn't be in git for a clean, reusable repository

---

## Executive Summary

**Current Issues**:
1. ❌ **User-specific plist tracked** - `com.leegonzales.research-agent.plist` contains hardcoded paths
2. ❌ **User-specific prompts tracked** - `prompts/*.md` contain "Lee Gonzales", "BetterUp", etc.
3. ❌ **Prompts are outdated** - Repo prompts don't match actual runtime prompts in `~/.research-agent/`
4. ✅ **Good examples exist** - `.env.example`, `config.yaml.example` are properly templated

**Recommendation**:
- Remove user-specific files from tracking
- Add `.example` versions with placeholders
- Update .gitignore to prevent future commits

---

## Current .gitignore Analysis

### ✅ What's Working Well

```gitignore
# Python artifacts
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/

# Virtual environments
venv/
ENV/
env/

# Environment variables
.env
!.env.example        # ← Good: Forces .example to be tracked

# Research Agent specific
state.db             # ← Good: User data should not be tracked
*.log                # ← Good: Logs are runtime artifacts

# macOS
.DS_Store            # ← Good: OS-specific files ignored
```

### ❌ What's Missing

**Files that SHOULD be ignored but aren't**:

1. **User-specific launchd plist**
   ```gitignore
   # Missing: macOS launchd plist with user paths
   *.plist
   !com.leegonzales.research-agent.plist.example
   ```

2. **Runtime prompts directory** (if users customize)
   ```gitignore
   # Missing: User-customized prompts
   prompts/*.md
   !prompts/*.example.md
   ```

3. **User data directory** (if created in repo)
   ```gitignore
   # Missing: Local data directory
   .research-agent/
   ```

4. **Generated digests** (if output to repo)
   ```gitignore
   # Missing: Output files
   digests/
   output/
   *.md
   !README.md
   !CLAUDE.md
   # ... (allow specific docs)
   ```

5. **Poetry lock file** (debatable - some projects include, some don't)
   ```gitignore
   # Missing: Poetry lock (optional)
   poetry.lock
   ```

---

## Files Currently Tracked That Shouldn't Be

### 1. com.leegonzales.research-agent.plist ❌

**Current state**: Tracked in repo
**Problem**: Contains user-specific paths
```xml
<string>/Users/leegonzales/Projects/miniconda/bin/python3</string>
<string>/Users/leegonzales/Projects/leegonzales/Intelbot</string>
<string>/Users/leegonzales/.research-agent/logs/launchd-stdout.log</string>
```

**Solution**:
1. Rename to `com.leegonzales.research-agent.plist.example`
2. Replace user paths with placeholders:
   ```xml
   <string>{{PYTHON_PATH}}</string>
   <string>{{PROJECT_PATH}}</string>
   <string>{{HOME}}/.research-agent/logs/launchd-stdout.log</string>
   ```
3. Update schedule.sh to create actual plist from example
4. Add `*.plist` to .gitignore

### 2. prompts/system.md ❌

**Current state**: Tracked in repo, **OUTDATED** (2355 bytes repo vs 3514 bytes runtime)
**Problem**: Contains user-specific content
```markdown
You are an AI research analyst working for Lee Gonzales,
Director of AI Transformation at BetterUp and Founder of
Catalyst AI Services.
```

**Solution**:
1. Rename to `prompts/system.example.md`
2. Replace with placeholders:
   ```markdown
   You are an AI research analyst working for {{USER_NAME}},
   {{USER_TITLE}} at {{USER_COMPANY}}.

   ## Your Mission

   Track and synthesize developments in AI research and practice, with focus on:
   {{USER_FOCUS_AREAS}}

   ## Your Expertise

   You understand {{USER_NAME}}'s background:
   {{USER_BACKGROUND}}
   ```
3. Add `prompts/*.md` to .gitignore
4. Document in README how to customize prompts

### 3. prompts/synthesis.md ❌

**Current state**: Tracked in repo, **OUTDATED** (3223 bytes repo vs 9491 bytes runtime)
**Problem**: Contains user-specific references
```markdown
5. Validate that "Why it matters" connects to Lee's work context
```

**Solution**:
1. Rename to `prompts/synthesis.example.md`
2. The synthesis template is mostly generic, just needs:
   ```markdown
   5. Validate that "Why it matters" connects to {{USER_NAME}}'s work context
   ```
3. Copy updated version from `~/.research-agent/prompts/synthesis.md` (with HARD DIVERSITY REQUIREMENTS)
4. Add `prompts/*.md` to .gitignore

### 4. prompts/sources.md ✅

**Current state**: Tracked in repo (2154 bytes both locations)
**Problem**: None - appears to be generic documentation
**Action**: Keep as-is, but verify no user-specific content

---

## Files That Should Be Tracked (Are Currently)

### ✅ Example/Template Files

1. **`.env.example`** ✅
   - Generic template without actual API key
   - Shows required environment variables

2. **`config.yaml.example`** ✅
   - Generic configuration template
   - Has placeholder paths like `~/Notes/Research`

3. **`schedule.sh`** ✅
   - Generic script
   - Dynamically finds paths

4. **Documentation**
   - README.md ✅
   - CLAUDE.md ✅ (project context for AI)
   - BUG_REPORT.md ✅
   - TASK_LIST.md ✅
   - VALIDATION_SUMMARY.md ✅
   - SCHEDULING.md ✅
   - DIGEST_ASSESSMENT.md ✅
   - IMPROVEMENTS_IMPLEMENTED.md ✅

5. **Source Code**
   - research_agent/ ✅
   - tests/ ✅
   - pyproject.toml ✅

---

## Recommended .gitignore Updates

### Add These Patterns

```gitignore
# User-specific configuration
*.plist
!*.plist.example
config.yaml
prompts/*.md
!prompts/*.example.md

# User data directory (if created in repo)
.research-agent/

# Generated digests (if output to repo)
digests/
output/
*-research-digest.md

# Poetry lock file (optional - team preference)
# poetry.lock

# macOS launchd logs
~/Library/LaunchAgents/com.*.research-agent.plist

# IDE - additional
.cursor/
*.code-workspace

# Temporary analysis files
*_ASSESSMENT.md
*_IMPLEMENTED.md
GITIGNORE_ASSESSMENT.md
```

### Remove These Patterns (Already Covered)

None - current .gitignore is well-structured

---

## Migration Steps

### Step 1: Create Template Files

```bash
# Create plist template
cp com.leegonzales.research-agent.plist com.leegonzales.research-agent.plist.example
# Edit to replace user paths with placeholders

# Create prompt templates (with updated content from ~/.research-agent/)
cp ~/.research-agent/prompts/system.md prompts/system.example.md
cp ~/.research-agent/prompts/synthesis.md prompts/synthesis.example.md
cp ~/.research-agent/prompts/sources.md prompts/sources.example.md
# Edit to replace user-specific content with placeholders
```

### Step 2: Update .gitignore

```bash
cat >> .gitignore << 'EOF'

# User-specific launchd configuration
*.plist
!*.plist.example

# User-customized prompts (use examples as templates)
prompts/*.md
!prompts/*.example.md

# User data directory
.research-agent/

# Generated digests
*-research-digest.md

# Temporary assessment files
*_ASSESSMENT.md
*_IMPLEMENTED.md
GITIGNORE_ASSESSMENT.md
EOF
```

### Step 3: Remove User-Specific Files from Tracking

```bash
# Remove from git but keep locally
git rm --cached com.leegonzales.research-agent.plist
git rm --cached prompts/system.md
git rm --cached prompts/synthesis.md
git rm --cached prompts/sources.md

# Add template files
git add com.leegonzales.research-agent.plist.example
git add prompts/*.example.md
git add .gitignore
```

### Step 4: Update schedule.sh

Add function to create plist from example:

```bash
create_plist_from_example() {
    local PYTHON_PATH=$(which python3)
    local PROJECT_PATH=$(pwd)
    local HOME_DIR="$HOME"

    # Replace placeholders in example
    sed -e "s|{{PYTHON_PATH}}|$PYTHON_PATH|g" \
        -e "s|{{PROJECT_PATH}}|$PROJECT_PATH|g" \
        -e "s|{{HOME}}|$HOME_DIR|g" \
        com.leegonzales.research-agent.plist.example > \
        com.leegonzales.research-agent.plist
}

# Call in install_schedule()
create_plist_from_example
```

### Step 5: Update README

Add "First Time Setup" section:

```markdown
## First Time Setup

1. **Copy configuration examples**:
   ```bash
   cp .env.example .env
   cp config.yaml.example config.yaml
   ```

2. **Configure environment**:
   - Edit `.env` and add your `ANTHROPIC_API_KEY`
   - Edit `config.yaml` and update paths for your system

3. **Customize prompts** (optional):
   ```bash
   mkdir -p ~/.research-agent/prompts
   cp prompts/system.example.md ~/.research-agent/prompts/system.md
   cp prompts/synthesis.example.md ~/.research-agent/prompts/synthesis.md
   cp prompts/sources.example.md ~/.research-agent/prompts/sources.md
   ```

   Edit the prompts to customize for your use case:
   - Replace `{{USER_NAME}}` with your name
   - Replace `{{USER_COMPANY}}` with your organization
   - Update focus areas and background
```

---

## File Categorization

### 🟢 Should Be Tracked (Generic/Reusable)

**Source Code**:
- `research_agent/**/*.py` - All Python source
- `tests/**/*.py` - All test files
- `scripts/**/*` - Utility scripts

**Configuration Templates**:
- `.env.example` - Environment variable template
- `config.yaml.example` - Config template
- `prompts/*.example.md` - Prompt templates
- `com.leegonzales.research-agent.plist.example` - Launchd template

**Documentation**:
- `README.md` - User documentation
- `CLAUDE.md` - AI context (should be template)
- `docs/**/*.md` - All documentation
- `SCHEDULING.md` - Scheduling guide
- `BUG_REPORT.md`, `TASK_LIST.md`, etc.

**Project Files**:
- `pyproject.toml` - Python dependencies
- `schedule.sh` - Generic scheduler script
- `.github/**/*` - GitHub workflows/templates
- `.gitignore` - This file

### 🔴 Should NOT Be Tracked (User-Specific)

**User Configuration**:
- `.env` - Contains API keys (SECRETS!)
- `config.yaml` - User-specific paths
- `*.plist` - User-specific launchd config
- `prompts/*.md` - User-customized prompts

**Runtime Data**:
- `state.db` - SQLite database with collected items
- `*.log` - Log files
- `.research-agent/` - User data directory
- `*-research-digest.md` - Generated output files

**IDE/OS Files**:
- `.vscode/`, `.idea/`, `.cursor/` - IDE settings
- `.DS_Store` - macOS metadata
- `__pycache__/`, `*.pyc` - Python cache
- `venv/`, `env/` - Virtual environments

**Temporary Files**:
- `*.tmp`, `*.bak` - Temp files
- `*_ASSESSMENT.md` - Analysis docs (this file!)
- `GITIGNORE_ASSESSMENT.md` - This file

### ⚠️ Debatable (Team Decision)

**Poetry Lock**:
- `poetry.lock` - Some teams track for reproducibility, others don't
- **Recommendation**: TRACK IT (ensures consistent dependencies across installations)

**CLAUDE.md**:
- Currently contains project context
- Should be templated for reusability
- **Recommendation**: Create `CLAUDE.example.md` with placeholders

---

## Security Concerns

### 🔒 Critical - Never Commit

1. **API Keys**: `.env` file
   - Currently: ✅ Properly ignored
   - Contains: `ANTHROPIC_API_KEY=sk-...`

2. **User Paths**: `*.plist` files
   - Currently: ❌ TRACKED (PROBLEM!)
   - Reveals: Home directory structure, usernames

3. **Database**: `state.db`
   - Currently: ✅ Properly ignored
   - Contains: Collected research items, URLs, content

4. **Logs**: `*.log` files
   - Currently: ✅ Properly ignored
   - May contain: API responses, debug info

### 🔓 Safe to Commit

1. **Example Files**: `*.example`
   - Contains: Placeholders, no secrets

2. **Source Code**: `*.py`
   - No hardcoded secrets (verified)

3. **Documentation**: `*.md`
   - Generic guides and context

---

## Impact Analysis

### If We Don't Fix This

**Security Risks**:
- ❌ User paths revealed (`/Users/leegonzales/`)
- ❌ Personal context exposed ("Lee Gonzales, BetterUp")
- ⚠️ Could accidentally commit API keys if .gitignore fails

**Usability Issues**:
- ❌ New users can't use the repo without manual edits
- ❌ Clone → Edit all files to remove "Lee Gonzales"
- ❌ Prompts in repo are outdated vs runtime

**Maintenance Problems**:
- ❌ User-specific files may conflict in PRs
- ❌ Updates to prompts won't be reflected in repo
- ❌ No clear "install from scratch" workflow

### If We Fix This

**Benefits**:
- ✅ Clean, professional open-source repo
- ✅ Easy onboarding: `cp *.example` → edit → run
- ✅ No accidental secret commits
- ✅ Clear separation: templates vs user config
- ✅ Prompts stay in sync (runtime is source of truth)

**Effort Required**:
- ~30 minutes to create templates
- ~10 minutes to update .gitignore
- ~20 minutes to update README/docs
- **Total**: ~1 hour

---

## Recommended .gitignore (Complete)

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
.cursor/
*.swp
*.swo
*~
*.code-workspace

# Environment variables
.env
!.env.example

# User configuration
config.yaml
!config.yaml.example

# User-specific launchd plist
*.plist
!*.plist.example

# User-customized prompts
prompts/*.md
!prompts/*.example.md

# Testing
.pytest_cache/
.coverage
htmlcov/

# Research Agent - User Data
.research-agent/
state.db
*.log

# Research Agent - Generated Output
*-research-digest.md
digests/
output/

# Temporary assessment files
*_ASSESSMENT.md
*_IMPLEMENTED.md
GITIGNORE_ASSESSMENT.md

# macOS
.DS_Store
.AppleDouble
.LSOverride

# Temporary files
*.tmp
*.bak
~*

# Poetry (optional - recommend tracking)
# poetry.lock
```

---

## Checklist for Clean Repository

### Immediate Actions Required

- [ ] Create `com.leegonzales.research-agent.plist.example` with placeholders
- [ ] Create `prompts/system.example.md` with placeholders (from `~/.research-agent/` version)
- [ ] Create `prompts/synthesis.example.md` with placeholders (from `~/.research-agent/` version)
- [ ] Create `prompts/sources.example.md` (verify it's generic)
- [ ] Update `.gitignore` with new patterns
- [ ] Remove tracked user-specific files: `git rm --cached`
- [ ] Add template files: `git add *.example`
- [ ] Update `schedule.sh` to generate plist from template
- [ ] Update README with "First Time Setup" section
- [ ] Consider templating CLAUDE.md

### Verification Steps

- [ ] Clone repo to fresh directory
- [ ] Verify no user-specific content in tracked files
- [ ] Test setup flow: copy examples → edit → run
- [ ] Verify `.env` not tracked: `git ls-files | grep "\.env$"` (should be empty)
- [ ] Verify plist not tracked: `git ls-files | grep "\.plist$"` (should only show .example)
- [ ] Run `git status` - should be clean

---

## Example Template Content

### com.leegonzales.research-agent.plist.example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{{USERNAME}}.research-agent</string>

    <key>ProgramArguments</key>
    <array>
        <string>{{PYTHON_PATH}}</string>
        <string>-m</string>
        <string>research_agent.cli.main</string>
        <string>run</string>
    </array>

    <key>WorkingDirectory</key>
    <string>{{PROJECT_PATH}}</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>{{PYTHON_PATH_DIR}}:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>PYTHONPATH</key>
        <string>{{PROJECT_PATH}}</string>
    </dict>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>{{HOME}}/.research-agent/logs/launchd-stdout.log</string>

    <key>StandardErrorPath</key>
    <string>{{HOME}}/.research-agent/logs/launchd-stderr.log</string>

    <key>RunAtLoad</key>
    <false/>

    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
```

### prompts/system.example.md

```markdown
# Research Analyst System Prompt

You are an AI research analyst working for {{USER_NAME}}, {{USER_TITLE}} at {{USER_COMPANY}}.

## Your Mission

Track and synthesize developments in AI research and practice, with focus on:
{{USER_FOCUS_AREAS}}
<!-- Example focus areas:
- AI transformation frameworks
- Agent architectures
- Prompt engineering
- RLHF and alignment
- Practical deployment
-->

## Your Expertise

You understand {{USER_NAME}}'s background:
{{USER_BACKGROUND}}
<!-- Example:
- 20+ years engineering leadership
- Builds AI transformation programs
- Uses frameworks: OODA loops, Wardley Mapping
- Values: justice, dignity, human flourishing
-->

## Selection Criteria

### INCLUDE
- Novel techniques or frameworks (not incremental improvements)
- Practitioner discourse and production lessons
- Benchmark results from reputable sources
- Framework/library releases with adoption potential
- Debates and contradictions in the field
- Strategic implications for transformation work

[... rest of template ...]
```

---

## Conclusion

**Priority**: 🔴 **HIGH** - Should fix before sharing repository publicly

**Effort**: Low (~1 hour)

**Impact**: High (security, usability, professionalism)

**Next Steps**:
1. Review this assessment
2. Decide: Fix now or later?
3. If now: Follow migration steps
4. If later: Add to project backlog as P1 task

**Recommendation**: **Fix immediately** - takes minimal time and prevents:
- Accidental secret exposure
- User confusion
- Maintenance burden

---

**Assessment Date**: 2025-11-15
**Assessor**: Claude (Research Agent Analysis)
**Status**: Ready for implementation
