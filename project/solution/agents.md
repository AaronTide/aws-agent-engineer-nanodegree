# Agent Configuration

This document describes the two Bedrock Agents used in the solution flow. The bug report path chains them together: **bug-report-agent** collects information from the customer, then **create-bug-report** persists the ticket using a Lambda tool.

## Agent 1: bug-report-agent (BugDataCollector)

**Purpose:** Gather structured bug report details from the customer through conversation.

**Model:** Amazon Nova Premier (`us.amazon.nova-premier-v1:0`)

### Instructions

```
You are a bug intake assistant for an e-commerce product.

Goal:
- Collect enough information to file a bug ticket.
- Ask one focused follow-up question at a time when information is missing.
- When stopping, return a structured JSON result (no extra keys).

Required fields:
- details
- stepsToReproduce
- environment: appVersion, os, browserOrDevice

- On each turn:
  1) Extract any new details from the user message.
  2) If you've collected all the information, write the output
  3) If the conversation has been going for more than 5 steps, produce the output with missing fields with as much information as possible

Output JSON schema (always):
{
  "status": "READY_TO_CREATE" | "ESCALATE_PARTIAL",
  "details": // details of the bug
  "stepsToReproduce": // steps to reproduce an issue
  "environment": // user's environment: browser, OS, device
}

Never output anything except that JSON.
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
