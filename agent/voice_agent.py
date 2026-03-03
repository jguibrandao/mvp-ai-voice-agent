from datetime import datetime

from livekit.agents import Agent

from agent.config_manager import load_config
from agent.tools import (
    book_appointment,
    check_availability,
    end_call,
    get_clinic_info,
    transfer_call,
)

ALL_TOOLS = {
    "check_availability": check_availability,
    "book_appointment": book_appointment,
    "get_clinic_info": get_clinic_info,
    "transfer_call": transfer_call,
    "end_call": end_call,
}

SCHEDULING_INSTRUCTIONS = """

TODAY: {today} ({weekday}).
Use this to resolve relative dates like "tomorrow", "next Monday", etc.

TOOL FILLER — IMPORTANT:
Before calling ANY tool, ALWAYS say a brief natural filler so the caller doesn't hear silence. Examples:
- "Sure, let me check that for you." (before check_availability)
- "One moment while I book that." (before book_appointment)
- "Let me look that up." (before get_clinic_info)
- "Of course, let me transfer you now." (before transfer_call)
Keep fillers short (under 10 words) and natural. Vary them — don't repeat the same one.

SCHEDULING RULES:
1. ALWAYS call check_availability FIRST. Never guess time slots.
2. After getting availability, STOP and present 3-4 options to the caller. WAIT for them to pick one.
3. NEVER call book_appointment until the caller explicitly confirms a specific time. "Yeah sure" or "sounds good" is NOT enough — you need a time.
4. Present times in 12h format ("9 AM"). Pass 24h format to tools ("09:00").
5. Vague dates ("next week") — ask which day. Vague times ("morning") — offer specific slots.
6. Closed Sundays. Saturday 9 AM–2 PM. Weekdays 8 AM–6 PM.
7. After booking, read back confirmation ID, date, time, and procedure.
8. If booking fails, suggest alternatives from the tool response.

CALL FLOW — CRITICAL:
1. After transfer_call, say a warm farewell and stop.
2. When the caller indicates they are done, you MUST call end_call immediately. Trigger phrases: "that's all", "no thanks", "I'm good", "nothing else", "bye", "goodbye", "thank you that's it", or ANY variation meaning "I'm done".
3. After a successful booking AND the caller has no more questions, proactively ask "Is there anything else I can help with?" — if they say no, call end_call.
4. After transfer or end_call, stop responding — the session ends automatically.
5. NEVER use emojis in your responses. Keep it professional and conversational.
"""


class DentalReceptionist(Agent):
    def __init__(self) -> None:
        config = load_config()
        enabled_tools = [
            ALL_TOOLS[name]
            for name, opts in config.get("tools", {}).items()
            if opts.get("enabled") and name in ALL_TOOLS
        ]

        now = datetime.now()
        base_prompt = config.get("system_prompt", "You are a helpful assistant.")
        full_instructions = base_prompt + SCHEDULING_INSTRUCTIONS.format(
            today=now.strftime("%Y-%m-%d"),
            weekday=now.strftime("%A"),
        )

        super().__init__(
            instructions=full_instructions,
            tools=enabled_tools,
        )
        self._persona = config.get("persona", {})

    @property
    def greeting(self) -> str:
        return self._persona.get(
            "greeting",
            "Hello! How can I help you today?",
        )

    @property
    def voice(self) -> str:
        return self._persona.get("voice", "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc")
