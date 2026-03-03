import logging

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, room_io
from livekit.plugins import noise_cancellation, silero
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
        stt="deepgram/flux",
        llm="google/gemini-3-flash",
        tts=f"openai/tts-1:{agent.voice}",
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    @session.on("user_speech_committed")
    def on_user_speech_committed(*args):
        tracker.mark_user_speech_end()

    @session.on("agent_speech_started")
    def on_agent_speech_started(*args):
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
