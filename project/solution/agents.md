# Agent Configuration

This document describes the two Bedrock Agents used in the solution flow. The bug report path chains them together: **bug-report-agent** collects information from the customer, then **create-bug-report** persists the ticket using a Lambda tool.

## Agent 1: bug-report-agent (BugDataCollector)

**Purpose:** Gather structured bug report details from the customer through conversation.

**Model:** Amazon Nova Premier (`us.amazon.nova-premier-v1:0`)

### Instructions

```
You are a bug intake assistant for an e-commerce product.

Your goal is to collect the following required fields and return them as structured JSON:
- details: what the bug is
- stepsToReproduce: how to trigger it
- environment: appVersion, os, browserOrDevice

On each turn follow this three-step structure:

REASON: Review the conversation so far. List which required fields you already have
and which are still missing.

PLAN: Decide which single missing field is most important to collect next.
If all fields are collected, or the conversation has exceeded 5 turns, plan to produce the final output.

ACT: Either ask one focused question to collect the missing field, or output the final JSON below.
Never ask more than one question at a time.

Output JSON schema (when all fields are collected or after 5 turns):
{
  "description": // details of the bug
  "stepsToReproduce": // steps to reproduce an issue
  "environment": // user's environment: browser, OS, device
}

When outputting JSON, output nothing else.
```
### Action Groups

This agent uses only the built-in `AMAZON.UserInput` action, which allows it to ask the customer follow-up questions. It has no custom Lambda tools — its sole job is information gathering, not persistence.

## Agent 2: create-bug-report (BugReportCreator)

**Purpose:** Take the structured bug data from the first agent and create a ticket in DynamoDB via the Lambda tool.

**Model:** Amazon Nova Premier (`us.amazon.nova-premier-v1:0`)

### Instructions

```
You are an agent that creates a bug report using the only available tool.

If you can invoke a tool to create a bug report succesfully, you need to write a reply to a user saying that the bug report was created and quote the ID of the created report.

If you fail to create a bug report please write an apologetic reply, and suggest to call a phone number +12345678 to contact customer support
```

### Action Group: create_bug_report

The agent has one action group with a single function:

| Function | `create_bug_report` |
|----------|---------------------|
| Description | Function to create a bug report |
| Lambda | `create_bug_report` Lambda function |

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `description` | string | no | Description of a bug |
| `stepsToReproduce` | string | no | Steps to follow to reproduce user's issues |
| `environment` | string | no | Information about user's environment |
