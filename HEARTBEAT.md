# Big Homie Heartbeat
## Autonomous Wake-Up & Proactive Execution System

### Overview

The Heartbeat system enables Big Homie to wake up autonomously every 30-60 minutes to:
- Scan for new opportunities to help
- Process pending tasks
- Monitor systems and alerts
- Execute scheduled actions
- Self-improve through log review

### Heartbeat Cycle

```
┌─────────────────────────────────────────┐
│  HEARTBEAT EVERY 30-60 MINUTES          │
└─────────────────────────────────────────┘
           │
           ▼
    ┌──────────────┐
    │   Wake Up    │
    └──────────────┘
           │
           ▼
    ┌──────────────────────────────────┐
    │  1. System Health Check          │
    │     - Check API connectivity     │
    │     - Verify memory system       │
    │     - Review cost budget         │
    └──────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────┐
    │  2. Scan Action Items            │
    │     - Unread emails/messages     │
    │     - Pending tasks              │
    │     - Scheduled reminders        │
    │     - Market alerts              │
    └──────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────┐
    │  3. Process Autonomous Tasks     │
    │     - Data aggregation           │
    │     - Report generation          │
    │     - System monitoring          │
    │     - Skill refinement           │
    └──────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────┐
    │  4. Log Review (Daily)           │
    │     - Analyze error patterns     │
    │     - Identify improvements      │
    │     - Update skills              │
    │     - Clean old data             │
    └──────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────┐
    │  5. Notify User (If Needed)      │
    │     - Actionable insights        │
    │     - Completed tasks            │
    │     - Alerts & warnings          │
    └──────────────────────────────────┘
           │
           ▼
    ┌──────────────┐
    │  Sleep Again │
    └──────────────┘
```

### Autonomous Tasks

#### 1. Information Aggregation
- **Market Watch** (if configured)
  - Check watchlist symbols
  - Identify significant price movements
  - Scan for news affecting holdings

- **Email/Message Scan** (if authorized)
  - Check for urgent items
  - Categorize by priority
  - Draft replies to common requests

- **News Monitoring**
  - Track topics of interest
  - Summarize important developments
  - Alert on breaking news in your domains

#### 2. Proactive Execution
- **Daily Reports**
  - Cost summary
  - Task completion stats
  - Skill improvement metrics
  - System health status

- **Data Processing**
  - Aggregate logs
  - Generate analytics
  - Update dashboards
  - Clean temporary data

- **Maintenance Tasks**
  - Archive old sessions
  - Optimize database
  - Refresh skills cache
  - Update model availability

#### 3. Self-Improvement
- **Log Analysis** (Daily at 3 AM)
  - Review error logs
  - Identify failure patterns
  - Propose code fixes
  - Update skill success rates

- **Skill Refinement**
  - Test alternative workflows
  - Benchmark performance
  - Remove obsolete skills
  - Document best practices

- **Cost Optimization**
  - Analyze model usage
  - Identify expensive queries
  - Suggest cheaper alternatives
  - Update routing logic

### Heartbeat Schedule

```yaml
# Default schedule (configurable)
heartbeat_interval: 45 minutes
active_hours:
  start: 06:00
  end: 23:00
  timezone: local

special_tasks:
  - task: "log_review"
    schedule: "daily at 03:00"

  - task: "cost_report"
    schedule: "daily at 08:00"

  - task: "skill_optimization"
    schedule: "weekly on Sunday at 02:00"

  - task: "memory_cleanup"
    schedule: "monthly on 1st at 01:00"
```

### Notification Criteria

**Always Notify:**
- Critical errors detected
- Cost threshold exceeded
- Urgent action items found
- Security alerts
- Task completion (if requested)

**Notify if Configured:**
- Market alerts triggered
- New high-priority emails
- Scheduled reports ready
- System maintenance completed
- Skill improvements available

**Never Notify During:**
- Quiet hours (23:00 - 06:00 by default)
- When user is in active session
- For routine maintenance
- For self-improvement tasks

### Safety Mechanisms

#### Rate Limiting
- Maximum 1 heartbeat per 30 minutes
- Maximum 3 autonomous actions per hour
- Budget check before each action
- Pause if cost limit reached

#### Permission Levels
- **Level 0**: Read-only operations (always allowed)
- **Level 1**: Data processing and analysis (allowed during heartbeat)
- **Level 2**: Draft creation (allowed with review flag)
- **Level 3**: External communication (requires explicit permission)
- **Level 4**: Financial/destructive (always requires confirmation)

#### Failure Handling
- If 3 consecutive heartbeats fail → pause system
- If cost spike detected → alert and pause
- If API errors → exponential backoff
- All failures logged for review

### Configuration

```python
# In .env or config
HEARTBEAT_ENABLED=true
HEARTBEAT_INTERVAL=45  # minutes
AUTONOMOUS_ACTIONS=true
QUIET_HOURS_START=23:00
QUIET_HOURS_END=06:00
MAX_AUTONOMOUS_COST=5.00  # USD per day
NOTIFICATION_METHOD=ui  # ui, email, webhook
```

### Action Items Discovery

When scanning for action items, Big Homie looks for:

1. **Email Patterns** (if connected)
   - Unread with "urgent" in subject
   - From VIPs in contacts
   - Containing keywords like "deadline", "asap", "important"

2. **Task Management** (if connected)
   - Overdue tasks
   - Tasks due today
   - High-priority flagged items

3. **System Monitoring**
   - Error spikes in logs
   - Performance degradation
   - Quota limits approaching

4. **Market Signals** (if configured)
   - Watchlist price alerts
   - News about holdings
   - Economic indicators

### Example Heartbeat Output

```
🫀 Heartbeat #142 - 2026-04-07 14:30:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ System Health: All systems operational
💰 Session Cost: $2.34 / $10.00 daily budget
🧠 Memory: 1,247 long-term facts, 42 active skills

📥 Action Items Found:
  • 3 new emails requiring response
  • 1 high-priority task due today
  • NVDA up 8% (watchlist alert)

🤖 Autonomous Actions Taken:
  ✓ Drafted replies to 2 routine emails (queued for review)
  ✓ Aggregated market news summary
  ✓ Updated skill success rates

📊 Ready to Notify:
  → Market update available (NVDA)
  → 2 draft emails ready for review

⏭️  Next heartbeat in 45 minutes
```

### Implementation Notes

- Heartbeat runs in background thread
- All actions logged to audit trail
- Cost tracked separately for autonomous vs interactive
- Can be paused/resumed via UI
- Status displayed in dashboard

### Evolution

The heartbeat system learns:
- Optimal times for different task types
- Which autonomous actions are most valuable
- When to be proactive vs. wait for prompts
- How to balance helpfulness with cost

---

*This heartbeat keeps Big Homie alive and proactive, not just reactive.*

**Last Updated**: 2026-04-07
**Version**: 1.0
