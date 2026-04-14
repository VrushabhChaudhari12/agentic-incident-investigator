# ---------------------------------------------------------------------------
# System prompt - kept compact to reduce token cost per iteration.
# Tool descriptions are included once here, not repeated per call.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a Senior AWS SRE investigating production incidents on Kubernetes and AWS.

TOOLS (call exactly one per response):
- fetch_logs(log_group, minutes): Returns JSON with recent CloudWatch log entries.
- fetch_metrics(instance_id, metric): Returns JSON with a metric value (cpu/memory/disk/connections/response_time).
- search_past_incidents(query): Returns JSON with up to 2 similar historical incidents.
- post_slack(message): Posts the final formatted report to #incidents-prod. Call this last.

RULES:
1. Always use at least 2 tools before concluding.
2. Tool results are returned as JSON - read the 'data' field for content.
3. One tool call per response, using EXACTLY this format on its own line:
   TOOL_CALL: tool_name(param1, param2)
4. When ready to conclude, output EXACTLY this block (all 4 fields required):
   FINAL_ANSWER:
   WHAT: <one sentence - what is happening>
   WHY: <one sentence - root cause>
   ACTION:
   1. <step>
   2. <step>
   3. <step>
   SAFE: <yes or no>
5. Never guess. Fetch data first. Never call the same tool with the same params twice."""


# ---------------------------------------------------------------------------
# Message builder
# ---------------------------------------------------------------------------
def build_messages(alarm: str, history: list) -> list:
    """
    Construct the full message array for the LLM.

    Args:
        alarm: The incident alarm string.
        history: List of {assistant, tool_result} dicts from prior iterations.

    Returns:
        List of {role, content} message dicts.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({
        "role": "user",
        "content": f"INCIDENT ALERT: {alarm}\n\nInvestigate this incident.",
    })
    for entry in history:
        messages.append({"role": "assistant", "content": entry["assistant"]})
        if "tool_result" in entry:
            messages.append({
                "role": "user",
                "content": f"Tool result:\n{entry['tool_result']}",
            })
    return messages
