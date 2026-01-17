# QueryCraft Analytics Guide

> Last updated: 2026-01-17

## Overview

QueryCraft uses a dual-analytics system with **Mixpanel** and **GA4** (via GTM) to track user behavior and platform usage. This guide documents all tracked events, properties, and implementation patterns.

## Analytics Stack

- **Mixpanel**: Primary analytics platform for detailed user behavior analysis
- **GA4**: Google Analytics 4 via Google Tag Manager for web analytics
- **PostHog** (optional): Alternative analytics platform

## Event Naming Convention

- Format: **Title Case** (e.g., "Problem Solved", "Login Success")
- Pattern: **Verb + Object** (action-oriented)
- GA4 Conversion: Automatically converted to snake_case (e.g., `problem_solved`)

## Core Events

### 🎯 Core Action

| Event | Description | When to Track |
|-------|-------------|---------------|
| **Problem Solved** | User successfully solved a problem | Only when submission is marked as correct |

### 👤 User Authentication

| Event | Description | Properties |
|-------|-------------|------------|
| Sign Up Completed | User completed registration | `user_id`, `auth_provider`, `is_new_user` |
| Login Success | User logged in successfully | `user_id`, `auth_provider` |
| Logout Completed | User logged out | - |

### 📊 Problem-Solving Funnel

Complete funnel from viewing to solving a problem:

| Event | Description | When to Track |
|-------|-------------|---------------|
| Problem Viewed | User opened a problem | On problem page load |
| Problem Attempted | User started working on problem | First typing or execution |
| SQL Executed | User ran SQL query | Every query execution |
| SQL Error Occurred | SQL execution failed | When query returns error |
| Problem Submitted | User submitted solution | On submission |
| Problem Solved | Submission was correct | When `is_correct = true` |
| Problem Failed | Submission was incorrect | When `is_correct = false` |

### 💡 Help & Hints

| Event | Description | Properties |
|-------|-------------|------------|
| Hint Requested | User requested a hint | `problem_id`, `difficulty_level`, `data_type` |
| AI Help Requested | User requested AI assistance | `help_type` (hint/solution), `attempts_before`, `time_before_help` |

### 🤖 AI Lab Events (NEW)

| Event | Description | Properties | Added |
|-------|-------------|------------|-------|
| **Text to SQL Requested** | Natural language → SQL conversion | `prompt_version`, `experiment_group`, `prompt_length` | 2026-01 |
| **AI Insight Requested** | Request insights from SQL results | `problem_id`, `data_type`, `result` | 2026-01 |
| **AI Suggestion Applied** | User applied AI suggestion | `suggestion_type` (query/insight/hint) | 2026-01 |

### 🎓 Onboarding

| Event | Description | Properties |
|-------|-------------|------------|
| Onboarding Started | User began onboarding flow | `total_steps` |
| Onboarding Completed | User finished onboarding | - |
| Onboarding Skipped | User skipped onboarding | `step_skipped_at` |

### 📱 Navigation & Interaction

| Event | Description | Properties |
|-------|-------------|------------|
| Page Viewed | User viewed a page | `page` (pathname) |
| Tab Changed | User switched tabs | `tab_name`, `data_type` |
| Schema Viewed | User viewed schema documentation | `data_type` |
| Contact Clicked | User clicked contact button | - |

## Event Properties

### Common Properties (Auto-added)

| Property | Type | Description |
|----------|------|-------------|
| `timestamp` | string (ISO) | Event occurrence time |
| `page` | string | Current page pathname |
| `env` | enum | Environment: `local`, `staging`, `prod` |

### Problem-Related Properties

| Property | Type | Description | Required For |
|----------|------|-------------|--------------|
| `problem_id` | string | Unique problem identifier | All problem events |
| `difficulty_level` | enum | `easy`, `medium`, `hard` | Problem events |
| `data_type` | string | `pa`, `stream`, `practice`, `rca` | Problem events |
| `is_daily_problem` | boolean | Is this a daily challenge? | Problem Viewed |
| `daily_issue_date` | string (YYYY-MM-DD) | Date of daily challenge | Daily challenges |
| `topic_tags` | string/array | Problem topics | Problem Viewed |

### Attempt & Performance Tracking

| Property | Type | Description |
|----------|------|-------------|
| `attempt_count` | number | How many times submitted this problem |
| `execution_count` | number | How many times executed SQL for this problem |
| `time_spent_sec` | number | Seconds from view to solve |
| `result` | enum | `success` or `fail` |

### SQL-Related Properties

| Property | Type | Description |
|----------|------|-------------|
| `sql_text` | string | The SQL query executed/submitted |
| `sql_length` | number | Character count of SQL query |
| `db_engine` | string | `postgres` or `duckdb` |
| `error_type` | string | `syntax`, `runtime`, `timeout`, etc. |
| `error_message` | string | Detailed error message |
| `used_hint_before` | boolean | Did user request hint before solving? |

### AI & Help Properties

| Property | Type | Description |
|----------|------|-------------|
| `help_type` | enum | `hint` or `solution` |
| `attempts_before` | number | Attempts before requesting help |
| `time_before_help` | number | Seconds before requesting help |
| `prompt_version` | string | Text-to-SQL prompt version (e.g., "v1") |
| `experiment_group` | string | A/B test group identifier |
| `prompt_length` | number | Length of natural language query |
| `suggestion_type` | enum | `query`, `insight`, or `hint` |

### Authentication Properties

| Property | Type | Description |
|----------|------|-------------|
| `user_id` | string | Unique user identifier |
| `auth_provider` | enum | `google`, `kakao`, `email` |
| `is_new_user` | boolean | Is this a new signup? |

## User Properties (Profile)

These properties are set once per user and updated over time:

| Property | Type | Description |
|----------|------|-------------|
| `user_id` | string | Unique identifier |
| `email` | string | User email |
| `user_type` | enum | `free` or `admin` |
| `signup_date` | string (ISO) | Registration timestamp |
| `signup_cohort_date` | string (YYYY-MM-DD) | Cohort for analysis |
| `total_problems_solved` | number | Lifetime solved count |
| `current_level` | string | User level (e.g., "🌱 Beginner") |
| `current_xp` | number | Experience points |
| `experience_level` | string | "초보", "중수", "고수" (based on XP) |

### Experience Level Calculation

- **초보 (Beginner)**: 0-299 XP
- **중수 (Intermediate)**: 300-999 XP
- **고수 (Advanced)**: 1000+ XP

## Usage Examples

### Basic Event Tracking

```typescript
import { analytics } from '@/services/analytics';

// Problem viewed
analytics.problemViewed('pa_001', {
  difficulty: 'medium',
  dataType: 'pa',
  isDaily: true,
  topic: 'joins'
});

// SQL execution
analytics.sqlExecuted('pa_001', {
  sql: 'SELECT * FROM users',
  hasError: false,
  dbEngine: 'postgres'
});

// Submission
analytics.problemSubmitted('pa_001', {
  isCorrect: true,
  difficulty: 'medium',
  dataType: 'pa'
});
```

### AI Lab Events

```typescript
// Text-to-SQL request
analytics.textToSQLRequested(
  "Find users who signed up last week",
  {
    problemId: 'pa_001',
    dataType: 'pa',
    experimentGroup: 'variant_a'
  }
);

// AI Insight request
analytics.aiInsightRequested('pa_001', {
  dataType: 'pa',
  resultCount: 42
});

// Apply AI suggestion
analytics.aiSuggestionApplied('query', {
  problemId: 'pa_001',
  dataType: 'pa'
});
```

### User Identification

```typescript
// On login
analytics.identify('user_123', {
  user_type: 'free',
  signup_date: '2026-01-15T09:00:00Z',
  total_problems_solved: 15,
  current_xp: 450,
  current_level: '🌿 Apprentice'
});

// Increment problem count (automatic on solve)
// Mixpanel: window.mixpanel!.people.increment('total_problems_solved', 1);
```

## Debugging

Enable debug mode to see console logs:

```typescript
import { analytics } from '@/services/analytics';

analytics.setDebugMode(true); // Enable verbose logging
```

Debug logs show:
- `[Mixpanel] Track: {event} {properties}`
- `[PostHog] Capture: {event} {properties}`
- `[GA4/GTM] Push: {event} {properties}`

## Environment Configuration

### Environment Detection

| Hostname | Environment |
|----------|-------------|
| `localhost`, `127.0.0.1` | `local` |
| Contains `staging` or `test` | `staging` |
| All others | `prod` |

### Required Environment Variables

```bash
# .env
VITE_MIXPANEL_TOKEN=your_mixpanel_project_token
```

## Analytics Platforms

### Mixpanel

- **Purpose**: Detailed user behavior, funnel analysis, retention
- **Features**: User profiles, people properties, increments
- **Auto-capture**: Enabled (clicks, page views)
- **Session recording**: 100% of sessions

### Google Analytics 4 (GA4)

- **Purpose**: Web traffic, acquisition, basic metrics
- **Integration**: Via Google Tag Manager (GTM)
- **Event Format**: Converted to snake_case (e.g., `problem_solved`)
- **Configuration**: Via GTM container

## Best Practices

1. **Always track the full funnel**: View → Attempt → Submit → Solve
2. **Include context**: Always pass `difficulty_level` and `data_type` for problem events
3. **Track errors**: Use `SQL Error Occurred` to identify friction points
4. **User identification**: Call `analytics.identify()` on login
5. **Debug mode**: Use in development to verify event tracking
6. **Reset on logout**: Automatic via `analytics.logoutCompleted()`

## Tracking Plan Compliance

This implementation follows industry-standard tracking plan principles:

- ✅ Consistent event naming (Title Case)
- ✅ Clear event hierarchy (Core Action → Supporting events)
- ✅ Required vs. optional properties documented
- ✅ User properties for profile enrichment
- ✅ Environment-aware tracking
- ✅ Auto-increment for cumulative metrics

## Dashboard Recommendations

### Key Metrics

1. **Core Conversion**: Problem Viewed → Problem Solved rate
2. **Engagement**: Daily Active Users (DAU), problems per session
3. **Retention**: Day 1, Day 7, Day 30 retention
4. **Friction**: SQL Error rate, attempts per problem
5. **AI Usage**: Text-to-SQL requests, AI Help requests

### Recommended Funnels

**Problem-Solving Funnel**:
```
Problem Viewed
  → Problem Attempted
    → Problem Submitted
      → Problem Solved
```

**AI Lab Funnel** (NEW):
```
Text to SQL Requested
  → AI Suggestion Applied
    → Problem Solved
```

## Changelog

### 2026-01-17
- ✨ Added AI Lab events: `Text to SQL Requested`, `AI Insight Requested`, `AI Suggestion Applied`
- 📝 Added properties: `prompt_version`, `experiment_group`, `prompt_length`, `suggestion_type`
- 🔧 Created comprehensive analytics documentation

---

**Questions?** Contact the analytics team or check Mixpanel/GA4 for live event data.
