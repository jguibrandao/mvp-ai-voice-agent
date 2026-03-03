from livekit.agents import Agent

from agent.config_manager import load_config
from agent.tools import (
    book_appointment,
    check_availability,
    get_clinic_info,
    transfer_call,
)

ALL_TOOLS = {
    "check_availability": check_availability,
    "book_appointment": book_appointment,
    "get_clinic_info": get_clinic_info,
    "transfer_call": transfer_call,
}


class DentalReceptionist(Agent):
    def __init__(self) -> None:
        config = load_config()
        enabled_tools = [
            ALL_TOOLS[name]
            for name, opts in config.get("tools", {}).items()
            if opts.get("enabled") and name in ALL_TOOLS
        ]
        super().__init__(
            instructions=config.get("system_prompt", "You are a helpful assistant."),
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
        return self._persona.get("voice", "alloy")
