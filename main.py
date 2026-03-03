import logging

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import (
    AgentServer,
    AgentSession,
    AgentStateChangedEvent,
    UserStateChangedEvent,
    inference,
    room_io,
)
from livekit.plugins import noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from agent.metrics import tracker
from agent.voice_agent import DentalReceptionist

load_dotenv(".env.local")
logging.basicConfig(level=logging.INFO)

server = AgentServer()


@server.rtc_session(agent_name="smileline-dental")
async def entrypoint(ctx: agents.JobContext):
    agent = DentalReceptionist()

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=openai.LLM(model="gpt-4.1-nano"),
        tts=f"cartesia/sonic-turbo:{agent.voice}",
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        min_endpointing_delay=0.2,
        max_endpointing_delay=0.8,
    )

    @session.on("user_state_changed")
    def on_user_state_changed(event: UserStateChangedEvent):
        if event.old_state == "speaking" and event.new_state == "listening":
            tracker.mark_user_speech_end()

    @session.on("agent_state_changed")
    def on_agent_state_changed(event: AgentStateChangedEvent):
        if event.new_state == "thinking":
            tracker.mark_agent_thinking_start()
        elif event.new_state == "speaking":
            tracker.mark_agent_speech_start()

    await session.start(
        room=ctx.room,
        agent=agent,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    await session.generate_reply(instructions=f"Greet the user with: {agent.greeting}")


if __name__ == "__main__":
    agents.cli.run_app(server)
