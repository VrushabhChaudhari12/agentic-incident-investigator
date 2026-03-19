# Agentic AI Incident Investigator

A production-grade AI agent that autonomously investigates AWS
incidents using a ReAct loop (Reason, Act, Observe).

## How it works

When a CloudWatch alarm fires, the agent does not just fetch logs
and guess. It loops up to 5 times, deciding what information it
needs, fetching it using tools, and only concluding when it has
enough to give a confirmed root cause.

## Tools available to the agent

- fetch_logs: pulls recent ERROR lines from CloudWatch log groups
- fetch_metrics: fetches CPU, memory, disk metrics for EC2 instances
- search_past_incidents: searches historical incidents using keyword match
- post_slack: posts structured root cause analysis to Slack

## Output format

Every investigation produces:
- WHAT: what is happening
- WHY: confirmed root cause
- ACTION: numbered fix steps
- SAFE: whether the action is safe to run without human review

## Stack

- Python 3.12
- Ollama (local LLM, completely free)
- llama3.2 model
- OpenAI-compatible API via Ollama

## Run locally
```cmd
pip install openai
python agent.py
```

## Real-world impact

Based on a system built at Concentrix that reduced incident triage
time from 45 minutes to 2 minutes by replacing manual log reading
with LLM-powered root cause analysis.