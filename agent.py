import re
from openai import OpenAI
from prompts import build_messages
from tools import execute_tool

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

MODEL = "llama3.2"
MAX_ITERATIONS = 5

def parse_tool_call(response_text):
    pattern = r"TOOL_CALL:\s*(\w+)\(([^)]*)\)"
    match = re.search(pattern, response_text)
    if match:
        tool_name = match.group(1).strip()
        params_str = match.group(2).strip()
        if params_str:
            params = []
            for p in params_str.split(","):
                p = p.strip().strip('"').strip("'")
                if "=" in p:
                    p = p.split("=", 1)[1].strip().strip('"').strip("'")
                params.append(p)
        else:
            params = []
        return tool_name, params
    return None, None

def parse_final_answer(response_text):
    if "FINAL_ANSWER:" in response_text:
        return response_text[response_text.index("FINAL_ANSWER:"):]
    return None

def run_agent(alarm):
    print(f"\n{'='*60}")
    print(f"INCIDENT RECEIVED: {alarm}")
    print(f"{'='*60}\n")
    
    history = []
    
    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"[AGENT] Iteration {iteration}/{MAX_ITERATIONS}")
        
        messages = build_messages(alarm, history)
        
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=500
            )
            response_text = response.choices[0].message.content
            print(f"[AGENT] LLM response: {response_text[:100]}...")
        except Exception as e:
            print(f"[ERROR] LLM call failed: {e}")
            break
        
        final_answer = parse_final_answer(response_text)
        if final_answer:
            print(f"\n[AGENT] Investigation complete after {iteration} iterations")
            print(f"\n{final_answer}")
            
            from tools import post_slack
            slack_message = f"Incident: {alarm}\n\n{final_answer}"
            post_slack(slack_message)
            return final_answer
        
        tool_name, params = parse_tool_call(response_text)
        if tool_name:
            print(f"[AGENT] Calling tool: {tool_name}({params})")
            tool_result = execute_tool(tool_name, params)
            print(f"[AGENT] Tool result: {str(tool_result)[:100]}...")
            
            history.append({
                "assistant": response_text,
                "tool_result": tool_result
            })
        else:
            print("[AGENT] No tool call or final answer found. Retrying...")
            history.append({
                "assistant": response_text,
                "tool_result": "Please use a tool or provide FINAL_ANSWER."
            })
    
    print("[AGENT] Max iterations reached. Forcing conclusion.")
    from tools import post_slack
    post_slack(f"Incident: {alarm}\n\nWARNING: Agent reached max iterations without conclusion. Manual investigation required.")

if __name__ == "__main__":
    alarm = "CPU at 95% on instance i-0abc123 in ap-south-1"
    run_agent(alarm)