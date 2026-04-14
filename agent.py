import re
import logging
from openai import OpenAI
from prompts import build_messages
from tools import execute_tool
from models import AlarmEvent, FinalAnswer, InvestigationStep, ToolCall
import config

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("agent")

# ---------------------------------------------------------------------------
# LLM client (shared, single instance)
# ---------------------------------------------------------------------------
client = OpenAI(
    base_url=config.LLM_BASE_URL,
    api_key=config.LLM_API_KEY,
)

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------
TOOL_PATTERN = re.compile(r"TOOL_CALL:\s*(\w+)\(([^)]*)\)")


def parse_tool_call(response_text: str):
    """Extract tool name and params from a TOOL_CALL line."""
    match = TOOL_PATTERN.search(response_text)
    if not match:
        return None, None
    tool_name = match.group(1).strip()
    params_str = match.group(2).strip()
    params = []
    if params_str:
        for p in params_str.split(","):
            p = p.strip().strip('"').strip("'")
            if "=" in p:
                p = p.split("=", 1)[1].strip().strip('"').strip("'")
            params.append(p)
    return tool_name, params


def parse_final_answer(response_text: str):
    """Return the FINAL_ANSWER block if present, else None."""
    if "FINAL_ANSWER:" in response_text:
        return response_text[response_text.index("FINAL_ANSWER:"):]
    return None


# ---------------------------------------------------------------------------
# Tool result cache (keyed by (tool_name, tuple(params)))
# ---------------------------------------------------------------------------
_tool_cache: dict = {}


def cached_execute_tool(tool_name: str, params: list) -> str:
    """Execute a tool but skip the call if an identical one was already made."""
    cache_key = (tool_name, tuple(params))
    if cache_key in _tool_cache:
        logger.debug("Cache hit for %s%s", tool_name, params)
        return _tool_cache[cache_key]
    result = execute_tool(tool_name, params)
    _tool_cache[cache_key] = result
    return result


# ---------------------------------------------------------------------------
# Main agent loop
# ---------------------------------------------------------------------------
def run_agent(alarm_input) -> str:
    """
    Run the ReAct investigation loop for an alarm.

    Args:
        alarm_input: str or AlarmEvent

    Returns:
        Raw final answer text (or warning string on timeout).
    """
    # Normalise input
    if isinstance(alarm_input, str):
        event = AlarmEvent(alarm=alarm_input)
    else:
        event = alarm_input

    _tool_cache.clear()  # fresh cache per incident
    logger.info("[%s] Incident received: %s", event.trace_id, event.alarm)
    print(f"\n{'='*60}")
    print(f"INCIDENT [{event.trace_id}]: {event.alarm}")
    print(f"{'='*60}\n")

    history = []
    tools_used = 0

    for iteration in range(1, config.MAX_ITERATIONS + 1):
        logger.info("[%s] Iteration %d/%d", event.trace_id, iteration, config.MAX_ITERATIONS)
        print(f"[AGENT] Iteration {iteration}/{config.MAX_ITERATIONS}")

        messages = build_messages(event.alarm, history)

        try:
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
            )
            response_text = response.choices[0].message.content
            logger.debug("[%s] LLM: %s", event.trace_id, response_text[:120])
            print(f"[AGENT] LLM response: {response_text[:100]}...")
        except Exception as exc:
            logger.error("[%s] LLM call failed: %s", event.trace_id, exc)
            break

        # --- Check for final answer ---
        raw_answer = parse_final_answer(response_text)
        if raw_answer and tools_used >= config.MIN_TOOLS_BEFORE_ANSWER:
            final = FinalAnswer.from_text(raw_answer)
            if final and final.is_valid():
                logger.info("[%s] Valid FinalAnswer after %d iterations", event.trace_id, iteration)
                print(f"\n[AGENT] Investigation complete after {iteration} iteration(s)")
                print(f"\n{raw_answer}")
                _post_final(event, final)
                return raw_answer
            else:
                logger.warning("[%s] FinalAnswer schema invalid, continuing...", event.trace_id)
                history.append({
                    "assistant": response_text,
                    "tool_result": (
                        "Your FINAL_ANSWER is missing required fields (WHAT/WHY/ACTION/SAFE). "
                        "Please include all four fields."
                    ),
                })
                continue

        # --- Check for a tool call ---
        tool_name, params = parse_tool_call(response_text)
        if tool_name:
            print(f"[AGENT] Calling tool: {tool_name}({params})")
            tool_result = cached_execute_tool(tool_name, params)
            print(f"[AGENT] Tool result: {str(tool_result)[:100]}...")
            tools_used += 1
            history.append({
                "assistant": response_text,
                "tool_result": tool_result,
            })
        else:
            logger.warning("[%s] No tool call or final answer on iteration %d", event.trace_id, iteration)
            history.append({
                "assistant": response_text,
                "tool_result": "Please call a tool (TOOL_CALL: ...) or provide FINAL_ANSWER.",
            })

    # --- Timeout / fallback ---
    warning_msg = (
        f"WARNING: Agent reached max iterations ({config.MAX_ITERATIONS}) "
        "without a conclusion. Manual investigation required."
    )
    logger.error("[%s] %s", event.trace_id, warning_msg)
    print(f"[AGENT] {warning_msg}")
    from tools import post_slack
    post_slack(f"Incident [{event.trace_id}]: {event.alarm}\n\n{warning_msg}")
    return warning_msg


def _post_final(event: AlarmEvent, final: FinalAnswer) -> None:
    """Validate schema then post to Slack."""
    from tools import post_slack
    slack_body = final.to_slack_text()
    header = f"Incident [{event.trace_id}]: {event.alarm}"
    post_slack(f"{header}\n\n{slack_body}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    alarm = "CPU at 95% on instance i-0abc123 in ap-south-1"
    run_agent(alarm)
