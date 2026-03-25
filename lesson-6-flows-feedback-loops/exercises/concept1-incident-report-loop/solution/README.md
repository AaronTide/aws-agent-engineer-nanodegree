# Exercise Solution – Incident Report Completion with an Agent Node

## Flow Structure

```
Flow Input (incident_report)
    │
    ▼
[Agent: IncidentReviewAgent]  ←→  asks follow-up questions (multi-turn)
    │  (when agent has collected all missing details)
    ▼
[ReportFinalizer]
    │
    ▼
Flow Output
```

---

## Bedrock Agent: IncidentReviewAgent

**Agent instructions:**
```
You are an incident response coordinator. When an engineer submits an incident report, your job is to review it and collect any missing information before the report can be escalated or handed off.

A complete incident report must cover all six of these fields:
- Affected systems: which services, components, or regions were impacted
- Severity: P1 / P2 / P3 / P4
- Root cause: what caused the incident
- Impact: who or what was affected and to what extent

Review the submitted report and identify which fields are missing or too vague to act on. Ask focused follow-up questions — one to three at a time — until you have specific answers for every field. Do not fabricate or assume any details.

When all six fields are covered, respond with:
REPORT COMPLETE
- Affected systems: ...
- Severity: ...
- Root cause hypothesis: ...
- Impact: ...
```

**Model:** Claude 3 Sonnet

**Additional settings:** User input — enabled

---

## Node: ReportFinalizer

**Prompt template:**
```
You are an incident report formatter. Given the information collected during an incident review, produce a clean, standardized incident report ready for escalation, handoff, or post-incident review.

Format your output exactly as follows:

## Incident Report

**Affected systems:** [value]
**Severity:** [value]
**Timeline:** [value]
**Root cause hypothesis:** [value]
**Impact:** [value]
**Remediation steps taken:** [value]

Collected information:
<info>
{{collected_info}}
</info>

Generate the formatted incident report now.
```

**Input variable:** `collected_info` (String)

---

## Connection Map

| From | To | Mapping |
|------|----|---------|
| Flow input | IncidentReviewAgent | `incident_report` → agent input |
| IncidentReviewAgent (output) | ReportFinalizer | agent response → `collected_info` |
| ReportFinalizer (output) | Flow output | model response → output |

---

## Expected Outputs

### Test Case 1 – Minimal report

Input: `Database went down around 3pm. Fixed it.`

The agent asks several rounds of questions. Example exchange:

> **Agent:** Which database was affected, and which services or teams depend on it?
>
> **User:** The primary Postgres database. The API and the background job processor both depend on it.
>
> **Agent:** How severe was the impact — were end users affected, or was this limited to internal systems? And approximately how long was the outage?
>
> **User:** End users got errors for about 25 minutes. Severity P2.
>
> **Agent:** What caused the outage, and what steps were taken to restore the database?
>
> **User:** Disk filled up due to unrotated logs. We cleared the logs and restarted the service.

Agent then outputs `REPORT COMPLETE` with all six fields populated. `ReportFinalizer` formats it:

```
## Incident Report

**Affected systems:** Primary Postgres database; API service and background job processor
**Severity:** P2
**Timeline:** Started approximately 15:00 local time; resolved after ~25 minutes
**Root cause hypothesis:** Disk exhaustion caused by unrotated log files
**Impact:** End users received errors for approximately 25 minutes
**Remediation steps taken:** Cleared log files, restarted the database service
```

### Test Case 2 – Partially complete report

Input includes timeline, affected system, root cause, and remediation — but severity and impact are missing.

The agent asks only about the missing fields:

> **Agent:** What severity level would you assign to this incident? And approximately how many users or transactions were affected during the outage window?

After receiving answers, it outputs `REPORT COMPLETE` and the flow produces the formatted report.

### Test Case 3 – Already complete report

The agent outputs `REPORT COMPLETE` immediately without asking any follow-up questions. The flow produces a formatted report in one pass.

---

## Why This Design Works

**The agent instructions list exactly six required fields.** This gives the agent a concrete checklist to evaluate the submitted report against, rather than making a vague judgment about whether the report is "good enough". The agent asks only about what is missing — it does not re-ask for information already provided.

**`ReportFinalizer` is a separate node from the agent.** The agent's job is to collect information through conversation. The formatting job belongs to a dedicated prompt node with a fixed output template. Separating these concerns means the final report format is consistent regardless of how many turns the conversation took.

**User input is enabled on the agent.** Without this setting, the agent cannot pause mid-execution to ask the user a question. It is required for any agent that needs multi-turn conversation.
