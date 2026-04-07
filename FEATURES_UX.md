# Big Homie - UX & Intelligence Features

This document describes the advanced UX and intelligence features that make Big Homie a truly intelligent and user-friendly AI assistant.

## 🎨 User Experience Features

### 1. Progress Bars
**Location**: `progress_tracker.py`

During long-running tasks, Big Homie displays real-time progress indicators:

```
Searching... [||||||||||----------] 50% - Analyzing results
```

**Features**:
- Visual progress bar with percentage
- Current subtask description
- Elapsed time tracking
- Status updates (idle, running, completed, failed)

**Usage in GUI**:
- Status bar shows progress during LLM requests
- Progress updates at key stages:
  - 10% - Analyzing user input
  - 20% - Preparing context
  - 30% - Checking costs
  - 50% - Generating response
  - 70% - Fact-checking response
  - 80% - Tagging and categorizing
  - 90% - Saving to memory
  - 100% - Complete

### 2. Implicit Confirmation
**Behavior**: Big Homie automatically saves drafts and results, then informs you:

> "I've drafted this for you; let me know if you want changes."

Instead of asking "Should I save this?", it takes initiative while keeping you in control.

**Implementation**:
- Responses are automatically saved to memory with metadata
- Fact-check reports flag uncertain content
- Users can review and request corrections

### 3. Tone Mirroring
**Location**: `tone_preference.py` - `ToneAnalyzer` class

Big Homie analyzes your communication style and adapts its responses accordingly.

**Analyzed Metrics**:
- **Brevity Score** (0-1): Message length and conciseness
- **Formality Score** (0-1): Formal vs. casual language
- **Technical Score** (0-1): Use of technical terminology
- **Urgency Score** (0-1): Time-sensitive language

**Example**:
```python
# Short, casual message
"fix the bug asap"
→ Response: Brief, direct, focused on quick solution

# Detailed, formal request
"Could you please analyze the performance bottleneck and provide recommendations?"
→ Response: Comprehensive, structured analysis with detailed explanations
```

**How it Works**:
1. Each user message is analyzed for tone characteristics
2. Recent messages (last 20) are tracked
3. Average style is calculated
4. Response style guidance is added to system prompt

### 4. Smart Truncation
**Location**: `content_utils.py` - `SmartTruncator` class

Large code blocks and outputs are intelligently truncated:

**For Code**:
```python
# Only shows changed lines with context
Showing changed sections (total: 500 lines)
Lines marked with * were modified

   *  42 | def calculate_total(items):
      43 |     return sum(item.price for item in items)
   *  44 |     # Added discount logic
   *  45 |     discount = get_discount()
   *  46 |     return total * (1 - discount)

... [450 lines omitted] ...
```

**For Text**:
- Breaks at sentence boundaries
- Shows first 70% before truncation
- Indicates how many characters were truncated

**Usage**:
```python
from content_utils import smart_truncator

# Truncate code showing specific changed lines
truncated = smart_truncator.truncate_code(
    code_content,
    changed_lines=[42, 44, 45, 108, 109]
)

# Truncate text at sentence boundary
truncated = smart_truncator.truncate_text(long_text, max_length=500)
```

### 5. Markdown Export
**Location**: `content_utils.py` - `MarkdownExporter` class

One-click ability to export any content as clean markdown files.

**Features**:
- Export individual thoughts/analyses
- Export full conversations
- Export structured reports
- Automatic file naming with timestamps
- Safe filename sanitization

**Menu Options**:
- **File → Export History (JSON & Markdown)**: Export complete session history
- **Tools → Export Current Chat as Markdown**: Export current conversation

**Export Locations**:
```
~/.big_homie/
  └── markdown_exports/
      ├── 20260407_120000_conversation.md
      ├── 20260407_121500_research_analysis.md
      └── 20260407_130000_code_review.md
```

**Example Export**:
```markdown
# Chat Session session_20260407_120000

Exported: 2026-04-07 12:00:00

---

## User - 2026-04-07T12:00:15

How do I implement caching in Python?

---

## Assistant - 2026-04-07T12:00:25

There are several ways to implement caching in Python...
```

## 🧠 Intelligence Features

### 1. Correction Ledger
**Location**: `correction_ledger.py`

Big Homie learns from your corrections and never makes the same mistake twice.

**How It Works**:
1. When you correct Big Homie, the correction is logged
2. Similar corrections are grouped and tracked
3. Common mistakes are identified
4. Context from past corrections is injected into future prompts

**Data Structure**:
```json
{
  "id": 1,
  "timestamp": "2026-04-07T12:00:00",
  "mistake": "Used 'var' instead of 'let' in JavaScript",
  "correction": "Always use 'let' or 'const', never 'var'",
  "category": "coding",
  "context": "JavaScript ES6+ code",
  "occurrences": 3
}
```

**API**:
```python
from correction_ledger import correction_ledger

# Record a correction
correction_ledger.add_correction(
    mistake="Suggested MongoDB for SQL use case",
    correction="Use PostgreSQL for relational data with complex queries",
    category="database",
    context="E-commerce application architecture"
)

# View learning summary
summary = correction_ledger.get_learnings_summary()
```

**Storage**: `~/.big_homie/correction_ledger.json`

**Menu Access**: **Tools → View Correction Ledger**

### 2. Metadata Tagging
**Location**: `fact_metadata.py` - `MetadataTagger` class

Automatically tags logs and content for fast filtering.

**Auto-Detected Tags**:
- `#coding` - Code, functions, bugs, implementations
- `#research` - Analysis, investigations, comparisons
- `#finance` - Trading, investments, markets
- `#marketing` - Campaigns, content, SEO
- `#web` - Websites, scraping, browser automation
- `#data` - Analytics, datasets, visualizations
- `#system` - Errors, warnings, performance
- `#question` - Contains a question mark
- `#error` - Contains error messages
- `#urgent` - Time-sensitive content

**Usage**:
```python
from fact_metadata import metadata_tagger

# Auto-tag content
tags = metadata_tagger.tag_content(
    "I need to debug this Python function that's causing a timeout error"
)
# Returns: {'coding', 'error', 'system'}

# Tag and categorize logs
metadata = metadata_tagger.tag_log_entry(
    log_text="API request failed with 500 error",
    level="ERROR"
)
```

**Benefits**:
- Quick filtering: "Show me all coding errors from yesterday"
- Pattern recognition: "80% of urgent tasks are finance-related"
- Automatic organization of logs and conversations

### 3. Fact Checking
**Location**: `fact_metadata.py` - `FactChecker` class

Self-reflection system that flags uncertain claims.

**Uncertainty Markers Detected**:
- "might", "maybe", "possibly", "probably", "likely"
- "I think", "I believe", "it seems", "appears to"
- "approximately", "roughly", "about"

**Confidence Score Calculation**:
```
confidence_score = confident_markers / (confident_markers + uncertain_markers)

< 60% = Low confidence (flagged)
60-80% = Medium confidence
> 80% = High confidence
```

**Example Report**:
```markdown
## Fact-Check Report

**Overall Confidence**: 45%

⚠️ The following sections may need verification:

1. **"The API might be rate-limited, possibly at 100 requests per hour"**
   - Contains uncertainty markers: might, possibly

2. **"This should probably work, but I'm not entirely sure about the authentication"**
   - Contains uncertainty markers: probably, not sure
```

**Integration**:
- Automatically runs after each LLM response
- Displays fact-check report in chat if confidence < 60%
- Metadata stored with each message for future reference

### 4. Time Awareness
**Location**: `time_awareness.py`

Contextual understanding of dates, times, and temporal references.

**Current Time Context**:
```python
{
  "datetime": "2026-04-07T14:30:00",
  "date": "2026-04-07",
  "day_of_week": "Monday",
  "time_of_day": "afternoon",
  "is_weekend": False,
  "is_business_hours": True,
  "season": "spring"
}
```

**Temporal Reference Parsing**:
```python
from time_awareness import time_awareness

# Parse natural language time references
time_awareness.parse_temporal_reference("tomorrow")
# → datetime for tomorrow

time_awareness.parse_temporal_reference("last Friday")
# → datetime for the most recent Friday

time_awareness.parse_temporal_reference("3 days ago")
# → datetime for 3 days ago
```

**Relative Time Formatting**:
```python
time_awareness.format_relative_time(some_datetime)
# → "2 hours ago"
# → "yesterday"
# → "3 weeks ago"
```

**Features**:
- Understands "this morning", "this afternoon", "tonight"
- Recognizes weekday names with "last", "next", "this"
- Detects quiet hours for autonomous operations
- Provides seasonal context
- Business hours awareness

**System Prompt Integration**:
Every request includes current time context:
```
Current Time Context:
- Date: Monday, 2026-04-07
- Time: 14:30:00 (afternoon)
- Season: spring
- Business Hours: Yes
- Weekend: No
```

### 5. Preference Weights
**Location**: `tone_preference.py` - `PreferenceTracker` class

Big Homie remembers your preferences and defaults to them automatically.

**Preference Types**:
- Programming languages: "Python over JavaScript"
- Frameworks: "React over Vue"
- Tools: "PostgreSQL over MySQL"
- Coding style: "Functional over OOP"
- Communication: "Detailed explanations preferred"
- Response format: "Code examples required"

**Data Structure**:
```python
{
  "preferred_language": {
    "value": "Python",
    "confidence": 0.9,
    "occurrences": 15
  },
  "code_style": {
    "value": "Type hints required",
    "confidence": 0.7,
    "occurrences": 8
  }
}
```

**Learning Process**:
1. Preferences are extracted from user corrections and explicit statements
2. Confidence increases with repeated observations
3. High-confidence preferences (>50%) are injected into system prompts
4. Preferences are stored in long-term memory

**Example**:
```
User: "I prefer using FastAPI for Python web services"

[Preference recorded]
Key: api_framework_python
Value: FastAPI
Confidence: 1.0

Next time:
User: "Help me build a REST API"
Assistant: [Automatically suggests FastAPI without asking]
```

**Menu Access**: **Tools → View Learned Preferences**

## 🔗 Integration Points

### System Prompt Enhancement
Every request includes:
1. **Time Context**: Current date, time, day of week, season
2. **Correction Ledger**: Past mistakes to avoid
3. **User Preferences**: Learned preferences to apply
4. **Tone Guidance**: Suggested response style based on user's tone

### Response Processing Pipeline
1. **Input Analysis**: Tone analysis, preference detection
2. **Context Building**: Time + corrections + preferences
3. **LLM Request**: With enhanced system prompt
4. **Fact Checking**: Confidence analysis
5. **Metadata Tagging**: Auto-categorization
6. **Memory Storage**: With all metadata

### Memory Integration
All features integrate with the existing memory system:
- **Session Memory**: Recent messages with tone analysis
- **Long-term Memory**: Preferences stored as facts
- **Skills**: Workflows tagged with metadata
- **Task History**: Tagged with categories

## 📊 Data Storage

```
~/.big_homie/
├── memory.db                    # SQLite database (preferences, history)
├── correction_ledger.json       # Learned corrections
├── markdown_exports/            # Exported markdown files
│   ├── YYYYMMDD_HHMMSS_*.md
└── logs/                        # Tagged log files
```

## 🚀 Usage Examples

### Example 1: Adaptive Responses

**Brief User Style**:
```
User: "fix npm error"
Assistant: "Run: npm install --legacy-peer-deps"
```

**Detailed User Style**:
```
User: "I'm encountering an npm peer dependency conflict. Could you explain what's happening and how to resolve it?"
Assistant: "This error occurs when npm detects incompatible peer dependencies...
[Detailed explanation with multiple solutions]"
```

### Example 2: Learning from Corrections

**First Time**:
```
User: "Create a user model in Django"
Assistant: [Creates model without email validation]
User: "Always add email validation with Django's EmailField"
[Correction logged]
```

**Next Time**:
```
User: "Create a profile model"
Assistant: [Automatically includes proper email validation]
```

### Example 3: Fact-Checking

**Response Generated**:
```
"The API might support up to 1000 requests per hour, but I'm not entirely sure.
You should probably check the documentation."

[Fact-Check Report]
Overall Confidence: 35%
⚠️ Uncertain claims detected:
- "might support" - uncertainty marker
- "not entirely sure" - low confidence statement
- "should probably" - hedging language
```

## 🎯 Benefits

1. **Reduced Friction**: Less back-and-forth, more implicit understanding
2. **Continuous Learning**: Gets better with every interaction
3. **Personalization**: Adapts to your unique communication style
4. **Transparency**: Flags uncertain information automatically
5. **Efficiency**: Smart truncation keeps displays clean
6. **Documentation**: Easy export of important conversations
7. **Accountability**: Correction ledger ensures mistakes aren't repeated

## 🔧 Configuration

New settings in `.env`:

```bash
# Enable/disable features
ENABLE_TONE_MIRRORING=true
ENABLE_FACT_CHECKING=true
ENABLE_SMART_TRUNCATION=true
ENABLE_AUTO_TAGGING=true
ENABLE_CORRECTION_LEARNING=true

# Thresholds
FACT_CHECK_CONFIDENCE_THRESHOLD=0.6  # Flag if below 60%
SMART_TRUNCATE_MAX_LINES=50
PREFERENCE_CONFIDENCE_THRESHOLD=0.5  # Apply if above 50%
```

## 📖 API Reference

### Progress Tracker
```python
from progress_tracker import progress_tracker

progress_tracker.start("Research task", callback=update_ui)
progress_tracker.update(50, "Analyzing results")
progress_tracker.complete()
```

### Correction Ledger
```python
from correction_ledger import correction_ledger

correction_ledger.add_correction(mistake, correction, category, context)
common_mistakes = correction_ledger.get_common_mistakes(limit=10)
context = correction_ledger.apply_corrections_to_context()
```

### Tone Analyzer
```python
from tone_preference import tone_analyzer

analysis = tone_analyzer.analyze_message(user_input)
style = tone_analyzer.get_average_style()
guidance = tone_analyzer.suggest_response_style()
```

### Smart Truncator
```python
from content_utils import smart_truncator

truncated = smart_truncator.truncate_code(code, changed_lines=[10, 20])
truncated = smart_truncator.truncate_text(text, max_length=500)
```

### Markdown Exporter
```python
from content_utils import markdown_exporter

path = markdown_exporter.export_thought(title, content, category)
path = markdown_exporter.export_conversation(messages)
path = markdown_exporter.export_analysis(title, sections)
```

### Fact Checker
```python
from fact_metadata import fact_checker

analysis = fact_checker.analyze_confidence(response)
report = fact_checker.format_fact_check_report(analysis)
```

### Metadata Tagger
```python
from fact_metadata import metadata_tagger

tags = metadata_tagger.tag_content(content)
metadata = metadata_tagger.tag_log_entry(log_text, level)
filtered = metadata_tagger.filter_logs_by_tags(logs, {'error', 'coding'})
```

### Time Awareness
```python
from time_awareness import time_awareness

context = time_awareness.get_current_context()
dt = time_awareness.parse_temporal_reference("last Friday")
relative = time_awareness.format_relative_time(some_datetime)
is_quiet = time_awareness.is_quiet_hours("23:00", "06:00")
```

---

**Big Homie** - An AI assistant that truly understands and adapts to you. 🏠
