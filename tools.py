import json
import logging
import random
from mock_data import PAST_INCIDENTS

logger = logging.getLogger("tools")


# ---------------------------------------------------------------------------
# Internal helper: wrap every tool result in a consistent JSON envelope
# ---------------------------------------------------------------------------
def _ok(tool: str, data: dict) -> str:
    """Return a JSON-serialised success envelope."""
    return json.dumps({"tool": tool, "status": "ok", "data": data}, indent=2)


def _err(tool: str, message: str) -> str:
    """Return a JSON-serialised error envelope."""
    return json.dumps({"tool": tool, "status": "error", "message": message}, indent=2)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
def fetch_logs(log_group: str, minutes: int = 30) -> str:
    """Fetch recent error logs from CloudWatch (mocked)."""
    mock_logs = [
        "[ERROR] java.lang.OutOfMemoryError: Java heap space at com.app.Service.process(Service.java:142)",
        "[ERROR] Connection refused: Unable to connect to RDS endpoint after 3 retries",
        "[WARN]  Response time 28450ms exceeds threshold of 3000ms for /api/payment",
        "[ERROR] GC overhead limit exceeded - JVM spending 98% time in garbage collection",
        "[ERROR] Too many connections - MySQL connection pool exhausted (max=100, active=100)",
        "[WARN]  Memory usage at 94% - heap dump triggered automatically",
        "[ERROR] Health check failed for target i-0abc123 - removing from load balancer",
    ]
    logger.info("fetch_logs called: log_group=%s, minutes=%s", log_group, minutes)
    sampled = random.sample(mock_logs, min(4, len(mock_logs)))
    return _ok("fetch_logs", {
        "log_group": log_group,
        "window_minutes": minutes,
        "entries": sampled,
    })


def fetch_metrics(instance_id: str, metric: str) -> str:
    """Fetch CPU, memory, disk or other metrics for an EC2/EKS instance (mocked)."""
    mock_metrics = {
        "cpu": random.randint(88, 98),
        "memory": random.randint(85, 95),
        "disk": random.randint(40, 60),
        "connections": random.randint(95, 100),
        "response_time": random.randint(15000, 35000),
    }
    logger.info("fetch_metrics called: instance=%s, metric=%s", instance_id, metric)
    metric_key = metric.lower().replace(" ", "_").replace("-", "_")
    value = next(
        (mock_metrics[k] for k in mock_metrics if k in metric_key),
        random.randint(70, 99),
    )
    unit = "ms" if "response" in metric_key else "%"
    return _ok("fetch_metrics", {
        "instance_id": instance_id,
        "metric": metric,
        "value": value,
        "unit": unit,
    })


def search_past_incidents(query: str) -> str:
    """
    Search the historical incident store by keyword relevance.
    Returns the top-2 most similar past incidents.
    """
    logger.info("search_past_incidents called: query=%s", query)
    query_words = query.lower().split()
    scored = []
    for incident in PAST_INCIDENTS:
        score = sum(
            1 for w in query_words
            if w in (incident["alarm"] + " " + incident["root_cause"]).lower()
        )
        if score > 0:
            scored.append((score, incident))
    scored.sort(reverse=True, key=lambda x: x[0])

    if not scored:
        return _ok("search_past_incidents", {"query": query, "results": []})

    results = [
        {
            "alarm": r["alarm"],
            "root_cause": r["root_cause"],
            "fix": r["fix"],
            "relevance_score": s,
        }
        for s, r in scored[:2]
    ]
    return _ok("search_past_incidents", {"query": query, "results": results})


def post_slack(message: str) -> str:
    """Post a formatted incident report to the #incidents-prod Slack channel."""
    logger.info("post_slack called")
    print("\n" + "="*60)
    print("SLACK NOTIFICATION - #incidents-prod")
    print("="*60)
    print(message)
    print("="*60 + "\n")
    return _ok("post_slack", {"delivered": True})


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
_REGISTRY = {
    "fetch_logs": fetch_logs,
    "fetch_metrics": fetch_metrics,
    "search_past_incidents": search_past_incidents,
    "post_slack": post_slack,
}


def execute_tool(tool_name: str, params: list) -> str:
    """Dispatch a tool call by name with positional params."""
    if tool_name not in _REGISTRY:
        return _err("execute_tool", f"Unknown tool '{tool_name}'. Available: {list(_REGISTRY.keys())}")
    try:
        fn = _REGISTRY[tool_name]
        if len(params) == 0:
            return fn()
        elif len(params) == 1:
            return fn(params[0])
        else:
            return fn(*params)
    except Exception as exc:
        logger.exception("Tool '%s' raised an exception", tool_name)
        return _err(tool_name, str(exc))
