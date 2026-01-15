# RCA Scenario Mode Enhancement - Work Plan

**Plan ID:** `rca-scenario-enhancement`
**Created:** 2026-01-16
**Estimated Duration:** 7-10 days
**Priority:** High

---

## Context

### Original Request
Implement TODO item #6: RCA Scenario Mode Enhancement
- Add 3 new scenario templates: "retention drop", "channel efficiency decline", "signup conversion drop"
- Define data patterns for each scenario
- Build RCA-specific dashboard layout
- Enhance step-by-step hint system
- Provide analysis report template

### Interview Summary

| Decision | User Choice |
|----------|-------------|
| Scenario Scope | All 3 scenarios |
| Dashboard Layout | Separate RCAWorkspace.tsx component |
| Hint System | 3-level progressive hints |
| Report Template | Hybrid (template + AI insights) |
| Infrastructure | Full schema migration with rca_anomaly_metadata table |
| Timeline | Full implementation (7-10 days acceptable) |

### Research Findings

**Current State:**
- RCA route exists at `/rca` in App.tsx, uses shared Workspace with `dataType="rca"`
- 5 anomaly types defined in `anomaly_injector.py`: CHANNEL_CONVERSION_DROP, DEVICE_ISSUE, TIME_BASED_ANOMALY, COUNTRY_BEHAVIOR_CHANGE, DATA_COLLECTION_GAP
- RCA scenarios defined per industry in `prompt_rca.py` (5 industries x 3 scenarios)
- Problem schema has single `hint` field (string)
- `rca_anomaly_metadata` table is referenced in code but NOT created in `sql/init.sql`

**Key Files:**
| File | Purpose |
|------|---------|
| `/mnt/z/GitHub/QueryCraft/problems/prompt_rca.py` | RCA scenario definitions |
| `/mnt/z/GitHub/QueryCraft/backend/generator/anomaly_injector.py` | Anomaly injection logic |
| `/mnt/z/GitHub/QueryCraft/backend/schemas/problem.py` | Problem Pydantic schema |
| `/mnt/z/GitHub/QueryCraft/frontend/src/pages/Workspace.tsx` | Current RCA UI (shared) |
| `/mnt/z/GitHub/QueryCraft/sql/init.sql` | PostgreSQL schema initialization |

---

## Work Objectives

### Core Objective
Transform RCA mode from a basic problem-solving interface into an immersive anomaly investigation experience with guided discovery and professional reporting.

### Deliverables
1. **3 New Scenario Templates** with distinct data patterns
2. **rca_anomaly_metadata Table** with full migration
3. **RCAWorkspace.tsx Component** (dedicated RCA UI)
4. **3-Level Progressive Hint System** (backend + frontend)
5. **Hybrid Analysis Report Template** (template + Gemini AI insights)

### Definition of Done
- [ ] All 3 scenarios generate problems correctly via admin panel
- [ ] rca_anomaly_metadata table exists and stores anomaly metadata
- [ ] RCAWorkspace shows investigation timeline, hint progression, and report generation
- [ ] Hint system reveals progressively (Level 1 -> 2 -> 3)
- [ ] Report template generates markdown with AI-enhanced insights
- [ ] All existing tests pass
- [ ] Frontend builds without errors

---

## Guardrails

### Must Have
- Backward compatibility with existing RCA problems
- Korean-first UI text (existing pattern)
- PostgreSQL-only (no DuckDB for RCA)
- Gemini API for AI-enhanced reports (existing pattern)
- Mobile-responsive layout

### Must NOT Have
- Breaking changes to PA/Stream workspace
- New npm dependencies without justification
- Direct database mutations in frontend
- Hardcoded API keys or credentials
- English-only UI text

---

## Task Flow and Dependencies

```
Phase 1: Backend Foundation
    |
    +---> [1.1] Create rca_anomaly_metadata table migration
    |
    +---> [1.2] Define 3 new scenario types in AnomalyType enum
    |
    +---> [1.3] Implement scenario injection functions
    |
    +---> [1.4] Update Problem schema for multi-level hints
    |
    v
Phase 2: Scenario Implementation
    |
    +---> [2.1] RETENTION_DROP scenario (retention drop)
    |
    +---> [2.2] CHANNEL_EFFICIENCY_DECLINE scenario
    |
    +---> [2.3] SIGNUP_CONVERSION_DROP scenario
    |
    +---> [2.4] Update prompt_rca.py with new scenarios
    |
    v
Phase 3: Frontend - RCAWorkspace
    |
    +---> [3.1] Create RCAWorkspace.tsx component shell
    |
    +---> [3.2] Investigation timeline component
    |
    +---> [3.3] Progressive hint UI (3 levels)
    |
    +---> [3.4] Anomaly indicator badges
    |
    +---> [3.5] Wire up routing in App.tsx
    |
    v
Phase 4: Report System
    |
    +---> [4.1] Create report template structure
    |
    +---> [4.2] Backend API for report generation
    |
    +---> [4.3] AI enhancement integration (Gemini)
    |
    +---> [4.4] Report preview/export UI
    |
    v
Phase 5: Polish and Testing
    |
    +---> [5.1] RCA-specific CSS styling
    |
    +---> [5.2] End-to-end testing
    |
    +---> [5.3] Admin panel integration
    |
    +---> [5.4] Documentation update
```

---

## Detailed TODOs

### Phase 1: Backend Foundation (Days 1-2)

#### TODO 1.1: Create rca_anomaly_metadata Table Migration
**File:** `/mnt/z/GitHub/QueryCraft/sql/init.sql`

**Schema:**
```sql
CREATE TABLE IF NOT EXISTS rca_anomaly_metadata (
    id SERIAL PRIMARY KEY,
    problem_date DATE NOT NULL,
    product_type VARCHAR(50) NOT NULL,
    anomaly_type VARCHAR(100) NOT NULL,
    anomaly_params JSONB NOT NULL DEFAULT '{}',
    affected_scope TEXT,
    description TEXT,
    hints JSONB NOT NULL DEFAULT '[]',  -- Array of 3 progressive hints
    root_cause TEXT,                     -- Actual root cause for report generation
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rca_anomaly_date ON rca_anomaly_metadata(problem_date);
CREATE INDEX idx_rca_anomaly_type ON rca_anomaly_metadata(anomaly_type);
```

**Acceptance Criteria:**
- [ ] Table created successfully on fresh database
- [ ] Existing anomaly_injector.py functions work with new schema
- [ ] JSONB hints column supports array of strings

---

#### TODO 1.2: Define 3 New Scenario Types
**File:** `/mnt/z/GitHub/QueryCraft/backend/generator/anomaly_injector.py`

**New AnomalyType Enum Values:**
```python
class AnomalyType(Enum):
    # Existing
    CHANNEL_CONVERSION_DROP = "channel_conversion_drop"
    DEVICE_ISSUE = "device_issue"
    TIME_BASED_ANOMALY = "time_based_anomaly"
    COUNTRY_BEHAVIOR_CHANGE = "country_behavior_change"
    DATA_COLLECTION_GAP = "data_collection_gap"

    # NEW: TODO #6 Scenarios
    RETENTION_DROP = "retention_drop"                    # Retention drop
    CHANNEL_EFFICIENCY_DECLINE = "channel_efficiency_decline"  # Channel efficiency decline
    SIGNUP_CONVERSION_DROP = "signup_conversion_drop"    # Signup conversion drop
```

**Acceptance Criteria:**
- [ ] Enum values added without breaking existing code
- [ ] INDUSTRY_ANOMALY_MAP updated for each industry
- [ ] ANOMALY_DESCRIPTIONS dictionary updated with Korean descriptions

---

#### TODO 1.3: Implement Scenario Injection Functions
**File:** `/mnt/z/GitHub/QueryCraft/backend/generator/anomaly_injector.py`

**New Functions:**
1. `inject_retention_drop(pg_cur, ...)`
   - Pattern: Delete return visits for cohort from specific period
   - Affected tables: pa_sessions, pa_events

2. `inject_channel_efficiency_decline(pg_cur, ...)`
   - Pattern: Reduce conversion events for specific channel while maintaining traffic
   - Affected tables: pa_events, pa_orders

3. `inject_signup_conversion_drop(pg_cur, ...)`
   - Pattern: Delete signup completion events for specific funnel step
   - Affected tables: pa_users, pa_events

**Acceptance Criteria:**
- [ ] Each function returns metadata dict with type, params, description, hints (array of 3)
- [ ] Functions added to ANOMALY_INJECTORS mapping
- [ ] Each function has docstring explaining the pattern

---

#### TODO 1.4: Update Problem Schema for Multi-Level Hints
**File:** `/mnt/z/GitHub/QueryCraft/backend/schemas/problem.py`

**Changes:**
```python
class Problem(BaseModel):
    # ... existing fields ...
    hint: Optional[str] = None           # Keep for backward compatibility
    hints: Optional[List[str]] = None    # NEW: Progressive hints array
    anomaly_metadata_id: Optional[int] = None  # NEW: Link to rca_anomaly_metadata
```

**Acceptance Criteria:**
- [ ] Both `hint` (legacy) and `hints` (new) supported
- [ ] Frontend can use either field
- [ ] API responses include hints array for RCA problems

---

### Phase 2: Scenario Implementation (Days 2-3)

#### TODO 2.1: RETENTION_DROP Scenario
**Affected Files:**
- `/mnt/z/GitHub/QueryCraft/backend/generator/anomaly_injector.py`

**Data Pattern:**
- Identify users who signed up 7-14 days ago
- Delete 60-80% of their return sessions
- Create clear week-over-week retention drop

**3-Level Hints:**
1. "Retention metrics look unusual. Compare this week to last week."
2. "Focus on users who signed up 1-2 weeks ago. What happened to them?"
3. "Calculate the return session rate by signup cohort. Which cohort dropped?"

**Acceptance Criteria:**
- [ ] Function creates measurable retention drop (>40%)
- [ ] Hints guide user to cohort-based analysis
- [ ] Metadata includes affected cohort info

---

#### TODO 2.2: CHANNEL_EFFICIENCY_DECLINE Scenario
**Affected Files:**
- `/mnt/z/GitHub/QueryCraft/backend/generator/anomaly_injector.py`

**Data Pattern:**
- Select one marketing channel (paid/social/referral)
- Keep session count stable
- Delete 50-70% of conversion events for that channel

**3-Level Hints:**
1. "Overall traffic looks normal, but something's off with conversions."
2. "Break down conversion rate by acquisition channel."
3. "Compare [affected_channel] channel's CVR to others. What's different?"

**Acceptance Criteria:**
- [ ] Function maintains traffic while dropping conversions
- [ ] Hints guide user to channel-level analysis
- [ ] Metadata includes affected channel name

---

#### TODO 2.3: SIGNUP_CONVERSION_DROP Scenario
**Affected Files:**
- `/mnt/z/GitHub/QueryCraft/backend/generator/anomaly_injector.py`

**Data Pattern:**
- Delete signup completion events at specific funnel step
- Keep earlier funnel steps intact
- Create clear funnel drop-off point

**3-Level Hints:**
1. "Signups are down. Build a funnel analysis to find the bottleneck."
2. "Compare step-by-step conversion rates. Where do users drop?"
3. "The [affected_step] step shows abnormal drop-off. Investigate timing and device."

**Acceptance Criteria:**
- [ ] Function creates identifiable funnel bottleneck
- [ ] Hints guide user through funnel analysis
- [ ] Metadata includes affected funnel step

---

#### TODO 2.4: Update prompt_rca.py with New Scenarios
**File:** `/mnt/z/GitHub/QueryCraft/problems/prompt_rca.py`

**Updates to RCA_SCENARIOS:**
```python
RCA_SCENARIOS = {
    "commerce": [
        # ... existing ...
        "Recent retention rate dropped by 25%. Find which user cohort is affected.",  # NEW
        "Paid channel shows stable traffic but conversion dropped 40%.",  # NEW
        "Signup funnel shows abnormal drop-off at checkout step.",  # NEW
    ],
    # ... other industries with similar additions ...
}
```

**Acceptance Criteria:**
- [ ] Each industry has 3 new scenario descriptions
- [ ] Descriptions match the data patterns we inject
- [ ] Korean text follows existing style

---

### Phase 3: Frontend - RCAWorkspace (Days 4-6)

#### TODO 3.1: Create RCAWorkspace.tsx Component Shell
**New File:** `/mnt/z/GitHub/QueryCraft/frontend/src/pages/RCAWorkspace.tsx`

**Structure:**
```
RCAWorkspace
├── InvestigationHeader (anomaly badge, timer, difficulty)
├── LeftPanel
│   ├── ProblemSelector
│   ├── AnomalyContext (urgent message style)
│   ├── InvestigationTimeline
│   └── HintProgression
├── RightPanel
│   ├── SQLEditor (reuse existing)
│   ├── ResultTable (reuse existing)
│   └── ReportGenerator
└── Footer (progress, submit)
```

**Acceptance Criteria:**
- [ ] Component renders without errors
- [ ] Reuses existing SQLEditor and ResultTable components
- [ ] Layout differs visually from PA Workspace

---

#### TODO 3.2: Investigation Timeline Component
**New File:** `/mnt/z/GitHub/QueryCraft/frontend/src/components/InvestigationTimeline.tsx`

**Features:**
- Shows investigation progress as vertical timeline
- Tracks queries executed, hints revealed, attempts made
- Visual indicators for each investigation step

**Acceptance Criteria:**
- [ ] Timeline updates in real-time as user works
- [ ] Each step has icon, timestamp, and description
- [ ] Collapsible for space efficiency

---

#### TODO 3.3: Progressive Hint UI (3 Levels)
**File:** `/mnt/z/GitHub/QueryCraft/frontend/src/pages/RCAWorkspace.tsx`

**UX Flow:**
1. Level 1 hint available immediately (free)
2. Level 2 hint unlocks after 1 SQL execution
3. Level 3 hint unlocks after 3 SQL executions or 5 minutes

**UI Components:**
- HintCard with lock/unlock state
- Reveal animation
- XP penalty indicator (if applicable)

**Acceptance Criteria:**
- [ ] Hints reveal progressively based on user actions
- [ ] Visual feedback when hint unlocks
- [ ] State persists across page refresh (localStorage)

---

#### TODO 3.4: Anomaly Indicator Badges
**File:** `/mnt/z/GitHub/QueryCraft/frontend/src/pages/RCAWorkspace.tsx`

**Badge Types:**
- Anomaly type badge (e.g., "RETENTION_DROP")
- Severity badge (based on drop percentage)
- Affected scope badge (channel, device, cohort)

**Acceptance Criteria:**
- [ ] Badges display anomaly metadata from API
- [ ] Color-coded by severity
- [ ] Tooltips explain each badge

---

#### TODO 3.5: Wire Up Routing in App.tsx
**File:** `/mnt/z/GitHub/QueryCraft/frontend/src/App.tsx`

**Changes:**
```tsx
// Change from:
<Route path="/rca" element={<Workspace dataType="rca" />} />

// Change to:
<Route path="/rca" element={<RCAWorkspace />} />
```

**Acceptance Criteria:**
- [ ] /rca route renders RCAWorkspace
- [ ] No breaking changes to other routes
- [ ] Navigation menu works correctly

---

### Phase 4: Report System (Days 6-7)

#### TODO 4.1: Create Report Template Structure
**New File:** `/mnt/z/GitHub/QueryCraft/backend/templates/rca_report.py`

**Template Structure:**
```markdown
# Root Cause Analysis Report

## Executive Summary
{ai_generated_summary}

## Investigation Overview
- **Anomaly Type:** {anomaly_type}
- **Affected Scope:** {affected_scope}
- **Severity:** {severity}
- **Investigation Duration:** {duration}

## Findings
{user_findings}

## Root Cause
{root_cause_explanation}

## Recommendations
{ai_generated_recommendations}

## Appendix: Queries Used
{sql_queries}
```

**Acceptance Criteria:**
- [ ] Template renders as valid markdown
- [ ] Placeholders clearly documented
- [ ] Supports both Korean and English sections

---

#### TODO 4.2: Backend API for Report Generation
**File:** `/mnt/z/GitHub/QueryCraft/backend/api/rca.py` (new or extend existing)

**Endpoint:** `POST /api/rca/report`

**Request:**
```json
{
  "problem_id": "rca_sql_001",
  "user_findings": "Channel X showed 40% drop...",
  "queries_used": ["SELECT ...", "SELECT ..."],
  "investigation_duration_sec": 300
}
```

**Response:**
```json
{
  "report_markdown": "# Root Cause Analysis Report\n...",
  "ai_insights": {
    "summary": "...",
    "recommendations": ["...", "..."]
  }
}
```

**Acceptance Criteria:**
- [ ] Endpoint generates complete report
- [ ] AI insights are optional (graceful fallback)
- [ ] Report includes all user-provided data

---

#### TODO 4.3: AI Enhancement Integration (Gemini)
**File:** `/mnt/z/GitHub/QueryCraft/backend/services/ai_service.py`

**New Function:** `generate_rca_insights(anomaly_metadata, user_findings, queries)`

**Prompt Template:**
```
You are a senior data analyst reviewing an RCA investigation.

Anomaly: {anomaly_type} - {description}
User's Findings: {user_findings}
Queries Used: {queries}

Generate:
1. Executive summary (2-3 sentences)
2. 3 actionable recommendations
3. Potential follow-up questions
```

**Acceptance Criteria:**
- [ ] Function calls Gemini API with structured prompt
- [ ] Response parsed into structured format
- [ ] Error handling for API failures
- [ ] Token usage logged

---

#### TODO 4.4: Report Preview/Export UI
**File:** `/mnt/z/GitHub/QueryCraft/frontend/src/components/RCAReportModal.tsx` (new)

**Features:**
- Markdown preview with syntax highlighting
- Copy to clipboard button
- Download as .md file
- Share link generation (future)

**Acceptance Criteria:**
- [ ] Modal displays formatted report
- [ ] Copy and download work correctly
- [ ] Loading state while generating

---

### Phase 5: Polish and Testing (Days 8-10)

#### TODO 5.1: RCA-Specific CSS Styling
**File:** `/mnt/z/GitHub/QueryCraft/frontend/src/pages/RCAWorkspace.css` (new)

**Design Goals:**
- Dark, urgent color scheme (reds, oranges for anomaly indicators)
- Timeline visual styling
- Hint card animations
- Report modal styling

**Acceptance Criteria:**
- [ ] Consistent with existing theme system (light/dark)
- [ ] Mobile responsive
- [ ] Animations performant

---

#### TODO 5.2: End-to-End Testing
**File:** `/mnt/z/GitHub/QueryCraft/tests/test_rca_scenarios.py` (new)

**Test Cases:**
1. Each anomaly injection function creates expected data pattern
2. API returns correct hints array
3. Report generation produces valid markdown
4. Frontend state management for hint progression

**Acceptance Criteria:**
- [ ] All new scenarios have test coverage
- [ ] Tests pass in CI
- [ ] Edge cases covered (empty data, missing fields)

---

#### TODO 5.3: Admin Panel Integration
**File:** `/mnt/z/GitHub/QueryCraft/frontend/src/App.tsx` (AdminPage section)

**Updates:**
- Add "RCA Scenario Test" button
- Show rca_anomaly_metadata table status
- Display last generated RCA problem info

**Acceptance Criteria:**
- [ ] Admin can generate RCA problems manually
- [ ] Metadata visible in admin panel
- [ ] Error states handled gracefully

---

#### TODO 5.4: Documentation Update
**Files:**
- `/mnt/z/GitHub/QueryCraft/CLAUDE.md`
- `/mnt/z/GitHub/QueryCraft/README.md` (if exists)

**Updates:**
- Document new RCA scenarios
- Update architecture section
- Add RCA-specific API documentation

**Acceptance Criteria:**
- [ ] CLAUDE.md reflects new RCA capabilities
- [ ] API endpoints documented
- [ ] Scenario descriptions clear

---

## Commit Strategy

| Phase | Commit Message Pattern |
|-------|------------------------|
| Phase 1 | `feat(rca): add rca_anomaly_metadata table and schema updates` |
| Phase 2 | `feat(rca): implement {scenario_name} anomaly injection` |
| Phase 3 | `feat(rca): create RCAWorkspace component with {feature}` |
| Phase 4 | `feat(rca): add report generation with AI insights` |
| Phase 5 | `test(rca): add end-to-end tests for RCA scenarios` |

**Branch Strategy:** Create feature branch `feature/rca-scenario-enhancement`

---

## Success Criteria

### Functional
- [ ] 3 new scenarios generate distinct, identifiable anomalies
- [ ] Progressive hints guide users effectively
- [ ] Reports provide actionable insights

### Technical
- [ ] All existing tests pass
- [ ] Frontend builds without TypeScript errors
- [ ] No console errors in browser

### User Experience
- [ ] Investigation feels immersive and educational
- [ ] Hints unlock at appropriate difficulty levels
- [ ] Reports are professionally formatted

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Gemini API rate limits | Implement caching, fallback to template-only reports |
| Anomaly injection breaks PA data | Use separate RCA data generation, not shared tables |
| Complex UI increases bundle size | Code-split RCAWorkspace as separate chunk |
| Hint timing frustrates users | A/B test unlock thresholds, add skip option |

---

## Handoff

To begin implementation, run:
```
/ralph-loop "Implement RCA Scenario Enhancement per .sisyphus/plans/rca-scenario-enhancement.md"
```

Or manually start with Phase 1, TODO 1.1 (database migration).

---

*Plan generated by Prometheus | 2026-01-16*
