import random
from mock_data import PAST_INCIDENTS

def fetch_logs(log_group, minutes=30):
    mock_logs = [
        f"[ERROR] java.lang.OutOfMemoryError: Java heap space at com.app.Service.process(Service.java:142)",
        f"[ERROR] Connection refused: Unable to connect to RDS endpoint after 3 retries",
        f"[WARN]  Response time 28450ms exceeds threshold of 3000ms for /api/payment",
        f"[ERROR] GC overhead limit exceeded - JVM spending 98% time in garbage collection",
        f"[ERROR] Too many connections - MySQL connection pool exhausted (max=100, active=100)",
        f"[WARN]  Memory usage at 94% - heap dump triggered automatically",
        f"[ERROR] Health check failed for target i-0abc123 - removing from load balancer",
    ]
    print(f"[TOOL] fetch_logs called: log_group={log_group}, minutes={minutes}")
    return "\n".join(random.sample(mock_logs, min(4, len(mock_logs))))

def fetch_metrics(instance_id, metric):
    mock_metrics = {
        "cpu": random.randint(88, 98),
        "memory": random.randint(85, 95),
        "disk": random.randint(40, 60),
        "connections": random.randint(95, 100),
        "response_time": random.randint(15000, 35000),
    }
    metric_key = metric.lower().replace(" ", "_").replace("-", "_")
    for key in mock_metrics:
        if key in metric_key:
            value = mock_metrics[key]
            print(f"[TOOL] fetch_metrics called: instance={instance_id}, metric={metric}")
            return f"{metric} for {instance_id}: {value}%"
    print(f"[TOOL] fetch_metrics called: instance={instance_id}, metric={metric}")
    return f"{metric} for {instance_id}: {random.randint(70, 99)}%"

def search_past_incidents(query):
    """
    Structured tool call: searches historical incident store by keyword
    relevance scoring. Returns top 2 most relevant past incidents.
    """
    print(f"[TOOL] search_past_incidents called: query={query}")
    query_words = query.lower().split()
    scored = []
    for incident in PAST_INCIDENTS:
        score = 0
        text = (incident["alarm"] + " " + incident["root_cause"]).lower()
        for word in query_words:
            if word in text:
                score += 1
        if score > 0:
            scored.append((score, incident))
    scored.sort(reverse=True, key=lambda x: x[0])
    if not scored:
        return "No similar past incidents found."
    output = []
    for score, r in scored[:2]:
        output.append(f"Past incident: {r['alarm']}")
        output.append(f"Root cause: {r['root_cause']}")
        output.append(f"Fix applied: {r['fix']}")
        output.append("---")
    return "\n".join(output)

def post_slack(message):
    print("\n" + "="*60)
    print("SLACK NOTIFICATION - #incidents-prod")
    print("="*60)
    print(message)
    print("="*60 + "\n")
    return "Slack message posted successfully."

def execute_tool(tool_name, params):
    tools = {
        "fetch_logs": fetch_logs,
        "fetch_metrics": fetch_metrics,
        "search_past_incidents": search_past_incidents,
        "post_slack": post_slack,
    }
    if tool_name not in tools:
        return f"Unknown tool: {tool_name}. Available tools: {list(tools.keys())}"
    try:
        if len(params) == 0:
            return tools[tool_name]()
        elif len(params) == 1:
            return tools[tool_name](params[0])
        else:
            return tools[tool_name](*params)
    except Exception as e:
        return f"Tool error: {str(e)}"