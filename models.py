from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ToolCall:
    """Represents a single tool invocation and its result."""
    tool_name: str
    params: List[str]
    result: str


@dataclass
class InvestigationStep:
    """One iteration of the ReAct loop."""
    iteration: int
    llm_response: str
    tool_call: Optional[ToolCall] = None


@dataclass
class FinalAnswer:
    """Structured root-cause report validated before posting to Slack."""
    what: str
    why: str
    action: List[str]
    safe: bool

    @classmethod
    def from_text(cls, text: str) -> Optional["FinalAnswer"]:
        """
        Parse FINAL_ANSWER block into a FinalAnswer dataclass.
        Returns None if required fields are missing.
        """
        lines = text.splitlines()
        what, why, action_lines, safe = "", "", [], None
        capturing_action = False

        for line in lines:
            line = line.strip()
            if line.startswith("WHAT:"):
                what = line[5:].strip()
                capturing_action = False
            elif line.startswith("WHY:"):
                why = line[4:].strip()
                capturing_action = False
            elif line.startswith("ACTION:"):
                raw = line[7:].strip()
                if raw:
                    action_lines.append(raw)
                capturing_action = True
            elif line.startswith("SAFE:"):
                safe = line[5:].strip().lower() == "yes"
                capturing_action = False
            elif capturing_action and line:
                action_lines.append(line)

        if not (what and why and action_lines and safe is not None):
            return None

        return cls(what=what, why=why, action=action_lines, safe=safe)

    def is_valid(self) -> bool:
        return bool(self.what and self.why and self.action)

    def to_slack_text(self) -> str:
        action_str = "\n".join(f"  {i+1}. {a}" for i, a in enumerate(self.action))
        safe_label = "YES - safe to auto-remediate" if self.safe else "NO - requires human approval"
        return (
            f"*WHAT:* {self.what}\n"
            f"*WHY:* {self.why}\n"
            f"*ACTION:*\n{action_str}\n"
            f"*SAFE:* {safe_label}"
        )


@dataclass
class AlarmEvent:
    """Represents an incoming incident alarm."""
    alarm: str
    region: str = "ap-south-1"
    trace_id: str = ""

    def __post_init__(self):
        if not self.trace_id:
            import uuid
            self.trace_id = str(uuid.uuid4())[:8]
