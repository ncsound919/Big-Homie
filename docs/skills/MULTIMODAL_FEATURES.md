# 🎯 Big Homie - Advanced Multimodal Features

This document describes the advanced features added to Big Homie, focusing on vision capabilities, cost management, and observability.

## 🌟 Overview

Big Homie now includes five major feature categories:

1. **Multimodal "Eyes" (Vision & Screenshots)** - See and understand images
2. **Smart Throttling & Cost Guards** - Prevent runaway costs
3. **Observability & Thought Tracing** - Transparent AI reasoning
4. **Multi-Channel Sync** (Foundation) - Work across platforms
5. **Zero-Copy Data Architecture** (Foundation) - Live database queries

---

## 1. 👁️ Multimodal Vision Capabilities

### Overview
Big Homie can now "see" images, screenshots, and UI mockups using cost-effective vision models via OpenRouter.

### Features

#### Automatic Screenshot on Error
When tasks fail, Big Homie automatically:
- Captures a screenshot of the current state
- Analyzes it with vision AI
- Provides diagnosis and suggestions

```python
# Automatically enabled in heartbeat.py
# Configure in .env:
AUTO_SCREENSHOT_ON_ERROR=true
ENABLE_VISION=true
```

#### Vision Analysis Tools
Three new MCP tools available:

**1. `vision_analyze_image`** - General image analysis
```python
# Usage via LLM
"Analyze this screenshot and tell me what's wrong"
# Tool will be called automatically

# Direct usage
from vision_analysis import vision_analyzer

result = await vision_analyzer.analyze_image(
    image_path="screenshot.png",
    prompt="What's visible in this image?",
    quality="fast"  # fast, good, high, excellent
)
```

**2. `vision_extract_text`** - OCR text extraction
```python
# Tries local OCR first (free), falls back to API
result = await vision_analyzer.extract_text_from_image(
    image_path="document.png",
    use_local_ocr=True  # Try pytesseract first
)
print(result.extracted_text)
```

**3. `vision_audit_ui`** - UI/UX design audits
```python
result = await vision_analyzer.audit_ui_design(
    image_path="mockup.png",
    focus_areas=["accessibility", "consistency", "mobile"]
)
print(result.analysis)  # 3-5 actionable improvements
```

### Cost-Effective Vision Models

Vision models available via OpenRouter (sorted by cost):

| Model | Cost/1M Tokens | Best For |
|-------|----------------|----------|
| Gemini Flash 1.5 8B | $0.04 | Screenshots, quick analysis |
| Claude 3 Haiku | $0.25 | General vision tasks |
| Gemini Pro 1.5 | $1.25 | Detailed analysis |
| Claude 3.5 Sonnet | $3.00 | High-quality audits |

Default: **Gemini Flash 1.5 8B** (cheapest, good quality)

### Configuration

```bash
# .env settings
ENABLE_VISION=true
VISION_MODEL=google/gemini-flash-1.5-8b
AUTO_SCREENSHOT_ON_ERROR=true
OPTIMIZE_IMAGES_BEFORE_UPLOAD=true
USE_LOCAL_OCR=true  # Try local OCR before API
```

### Image Optimization
Images are automatically optimized before sending to API:
- Resized to max 1920x1080 if larger
- Quality reduced to 85% (nearly imperceptible)
- Saves ~70% on API costs

---

## 2. 💰 Smart Cost Guards

### Overview
Prevent runaway costs with intelligent budget management and pre-execution approval.

### Features

#### Pre-Execution Cost Estimation
Every LLM operation is estimated before execution:

```python
from cost_guards import cost_guard

estimate = cost_guard.estimate_cost(
    messages=messages,
    model="claude-opus-4-5",
    max_output_tokens=4096
)

print(f"Estimated: ${estimate.estimated_cost:.4f}")
print(f"Level: {estimate.cost_level}")  # LOW, MEDIUM, HIGH, VERY_HIGH
print(f"Requires approval: {estimate.requires_approval}")
```

#### Automatic Approval Thresholds
- Operations under $0.10: Auto-approved
- Operations $0.10-$0.50: Warning logged
- Operations over $0.50: Requires explicit approval

```bash
# Configure thresholds in .env
COST_APPROVAL_THRESHOLD=0.50
AUTO_APPROVE_UNDER=0.10
```

#### Daily Budget Enforcement
```python
# Set daily budget
MAX_AUTONOMOUS_COST=5.0  # $5/day

# Budget is checked before every operation
# Operations denied if budget would be exceeded
```

#### Budget Status Tracking
```python
from cost_guards import cost_guard

status = cost_guard.get_budget_status()
print(f"Daily: ${status.daily_spent:.2f} / ${status.daily_limit:.2f}")
print(f"Remaining: ${status.daily_remaining:.2f}")
print(f"Over budget: {status.is_over_budget}")
```

#### Token Counting
Accurate token counting using `tiktoken`:

```python
tokens = cost_guard.count_tokens(
    "Your text here",
    model="gpt-4"
)
```

#### Context Pruning Suggestions
When conversations get long and costly:

```python
suggestions = cost_guard.suggest_context_pruning(
    messages=conversation_history,
    target_reduction=0.5  # 50% reduction
)

# Returns strategies:
# - Keep only recent messages
# - Summarize old messages
# - Remove system messages
```

### Cost Levels

| Level | Range | Action |
|-------|-------|--------|
| LOW | < $0.10 | Auto-approve |
| MEDIUM | $0.10 - $0.50 | Log warning |
| HIGH | $0.50 - $2.00 | Require approval |
| VERY HIGH | > $2.00 | Require approval + extra warning |

---

## 3. 🔍 Observability & Thought Tracing

### Overview
Transparent AI reasoning with detailed thought logs and beautiful terminal output.

### Features

#### Structured Thought Logging
Every decision is logged with context:

```python
from thoughts_logger import thoughts_logger

# Log different types of thoughts
thoughts_logger.log_reasoning("Analyzing user request...")
thoughts_logger.log_decision("Use Claude Opus", rationale="Complex reasoning required")
thoughts_logger.log_model_selection("claude-opus-4-5", "Best for strategic planning")
thoughts_logger.log_cost_analysis("API call", 0.25, "Within budget")
```

#### Thought Types
- **REASONING**: Analytical thoughts
- **DECISION**: Choices made with rationale
- **OBSERVATION**: Things noticed
- **PLANNING**: Task breakdown
- **REFLECTION**: Learning from outcomes
- **COST_ANALYSIS**: Budget considerations
- **MODEL_SELECTION**: Why a model was chosen

#### Beautiful Terminal Output
With Rich library integration:
```
┌─ DECISION ────────────────────────────────────┐
│ Route to architect role using anthropic/     │
│ claude-opus-4-5                               │
│                                               │
│ Rationale: Selected for high-level reasoning │
│ and strategic planning. Using anthropic/     │
│ claude-opus-4-5 as the optimal model.        │
│                                               │
│ Metadata:                                     │
│   estimated_cost: $0.0125                     │
│   complexity: 0.75                            │
└───────────────────────────────────────────────┘
```

#### Detail Levels
Control verbosity:
- **0**: Off (no logging)
- **1**: Minimal (critical decisions only)
- **2**: Normal (recommended)
- **3**: Verbose (everything)

```python
thoughts_logger.set_detail_level(2)
```

#### Export Thought Traces
Save reasoning traces for analysis:

```python
path = thoughts_logger.export_trace()
# Exports to: ~/.big_homie/logs/thought_trace_20260407_123456.json
```

#### Daily Thought Logs
Automatic logging to file:
```
~/.big_homie/logs/THOUGHTS_2026-04-07.log
```

Each line is a JSON object:
```json
{
  "timestamp": "2026-04-07T12:34:56",
  "type": "model_selection",
  "content": "Selected: claude-opus-4-5\n\nReason: Complex reasoning task",
  "metadata": {"estimated_cost": "$0.0125"}
}
```

### Configuration

```bash
# .env settings
ENABLE_THOUGHT_LOGGING=true
THOUGHT_LOG_DETAIL_LEVEL=2  # 0-3
LOG_MODEL_SELECTIONS=true
LOG_COST_DECISIONS=true
```

---

## 4. 📡 Multi-Channel Synchronization (Foundation)

### Overview
Foundation for working across Discord, Slack, Telegram, and more.

### Current Status
Configuration placeholders added:

```bash
# Discord
ENABLE_DISCORD=false
DISCORD_WEBHOOK_URL=

# Slack
ENABLE_SLACK=false
SLACK_WEBHOOK_URL=
```

### Future Implementation
Full implementation coming in Phase 3:
- Unified task queue (Redis/SQLite)
- Channel-aware memory
- Result delivery across channels
- "Follow me" workflow

---

## 5. 🗄️ Zero-Copy Data Architecture (Foundation)

### Overview
Foundation for live database queries without copying data.

### Current Status
Configuration placeholders added:

```bash
# PostgreSQL
POSTGRES_URL=

# Supabase
SUPABASE_URL=
SUPABASE_KEY=
```

### Future Implementation
Full implementation coming in Phase 3:
- PostgreSQL live queries
- Supabase integration
- Real-time file system monitoring
- Memory-mapped file access

---

## 📊 Usage Examples

### Example 1: Automatic Error Diagnosis
```python
# Error occurs during autonomous task
# Big Homie automatically:
# 1. Captures screenshot
# 2. Analyzes with vision AI
# 3. Provides diagnosis

# No manual intervention needed!
```

### Example 2: Cost-Aware Operation
```python
from llm_gateway import llm
from cost_guards import cost_guard

# Cost guard automatically checks before execution
messages = [{"role": "user", "content": "Long prompt..."}]

# If cost > threshold, user is prompted for approval
# If over budget, operation is denied
result = await llm.complete(messages)
```

### Example 3: Transparent Decision Making
```python
from router import router

# Router logs its decision-making process
decision, result = await router.execute_with_routing(
    task="Design a microservices architecture",
    context={"requires_reasoning": True}
)

# Check thought logs to see why Claude Opus was selected
# See cost estimates and complexity analysis
```

### Example 4: UI/UX Audit
```python
from vision_analysis import vision_analyzer

result = await vision_analyzer.audit_ui_design(
    image_path="mockup.png",
    focus_areas=["accessibility", "mobile responsiveness"]
)

print(result.analysis)
# Output:
# 1. Increase contrast ratio to meet WCAG AA standards
# 2. Add mobile breakpoint at 768px
# 3. Enlarge tap targets to minimum 44x44px
# 4. Use system fonts for better mobile performance
# 5. Add loading states for async operations
```

---

## 🛠️ Installation

### Dependencies
```bash
pip install -r requirements.txt
```

New dependencies added:
- `tiktoken>=0.5.0` - Token counting
- `pytesseract>=0.3.10` - Local OCR
- `rich>=13.0.0` - Terminal formatting
- `discord.py>=2.3.0` - Discord integration
- `slack-sdk>=3.23.0` - Slack integration
- `psycopg2-binary>=2.9.0` - PostgreSQL
- `supabase>=2.0.0` - Supabase client
- `watchdog>=3.0.0` - File monitoring

### Local OCR Setup (Optional but Recommended)
For free local text extraction:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

---

## 🔧 Configuration Reference

### Complete .env Example
```bash
# Vision & Multimodal
ENABLE_VISION=true
VISION_MODEL=google/gemini-flash-1.5-8b
AUTO_SCREENSHOT_ON_ERROR=true
OPTIMIZE_IMAGES_BEFORE_UPLOAD=true
USE_LOCAL_OCR=true

# Cost Guards
ENABLE_COST_GUARDS=true
COST_APPROVAL_THRESHOLD=0.50
DAILY_TOKEN_CAP=1000000
COST_WARNING_THRESHOLD=0.75
AUTO_APPROVE_UNDER=0.10

# Thought Logging
ENABLE_THOUGHT_LOGGING=true
THOUGHT_LOG_DETAIL_LEVEL=2
LOG_MODEL_SELECTIONS=true
LOG_COST_DECISIONS=true

# Multi-Channel (Future)
ENABLE_DISCORD=false
DISCORD_WEBHOOK_URL=
ENABLE_SLACK=false
SLACK_WEBHOOK_URL=

# Database Connectors (Future)
POSTGRES_URL=
SUPABASE_URL=
SUPABASE_KEY=
```

---

## 📈 Performance & Costs

### Vision API Costs (Estimated)
Based on 1000 token average per image:

| Model | Cost per Image | Cost per 1000 Images |
|-------|----------------|----------------------|
| Gemini Flash 1.5 8B | $0.00004 | $0.04 |
| Claude 3 Haiku | $0.00025 | $0.25 |
| Gemini Pro 1.5 | $0.00125 | $1.25 |

**Local OCR**: $0 (free, unlimited)

### Cost Savings Tips
1. **Use local OCR** for text extraction (free)
2. **Optimize images** before sending (70% cost reduction)
3. **Use cheapest model** that meets quality needs
4. **Set daily budgets** to prevent overspending
5. **Enable auto-approval** for small operations

---

## 🧪 Testing

### Test Vision Capabilities
```python
# Test with a sample image
import asyncio
from vision_analysis import vision_analyzer

async def test_vision():
    # Create test image or use existing screenshot
    result = await vision_analyzer.analyze_image(
        image_path="test_screenshot.png",
        prompt="What do you see in this image?",
        quality="fast"
    )

    print(f"Analysis: {result.analysis}")
    print(f"Cost: ${result.cost:.4f}")
    print(f"Model: {result.model_used}")

asyncio.run(test_vision())
```

### Test Cost Guards
```python
from cost_guards import cost_guard

# Test estimation
estimate = cost_guard.estimate_cost(
    messages=[{"role": "user", "content": "Hello" * 1000}],
    model="claude-opus-4-5"
)

print(f"Estimated: ${estimate.estimated_cost:.4f}")
print(f"Requires approval: {estimate.requires_approval}")
```

### Test Thought Logging
```python
from thoughts_logger import thoughts_logger

thoughts_logger.log_reasoning("Testing thought logging system")
thoughts_logger.log_decision("Use test mode", "For validation purposes")

# Export for inspection
path = thoughts_logger.export_trace()
print(f"Trace exported to: {path}")
```

---

## 🚀 Next Steps

### Phase 3 Implementation (Future)
1. **Multi-Channel Sync**
   - Discord bot integration
   - Slack app integration
   - Unified message queue
   - Cross-channel memory

2. **Zero-Copy Data**
   - Live PostgreSQL queries
   - Supabase real-time subscriptions
   - File system monitoring
   - Streaming large datasets

3. **Enhanced Vision**
   - Video analysis (frame extraction)
   - Multi-image comparison
   - Visual change detection
   - Screenshot diffing

---

## 📚 Additional Resources

- **Vision Analysis**: See `vision_analysis.py` for implementation
- **Cost Guards**: See `cost_guards.py` for details
- **Thought Logging**: See `thoughts_logger.py` for API
- **Configuration**: See `config.py` for all settings
- **Integration**: See `mcp_integration.py` for tools

---

## 🤝 Contributing

To add new vision capabilities:
1. Add handler to `vision_analysis.py`
2. Register tool in `mcp_integration.py`
3. Update this documentation

To enhance cost guards:
1. Modify `cost_guards.py`
2. Update pricing in `_calculate_model_cost()`
3. Test with various models

---

## 📝 License

MIT License - Same as Big Homie

---

**Big Homie** - Now with eyes to see, brains to think, and wisdom to save money. 🏠👁️💰
