from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, room_io
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from agent.voice_agent import DentalReceptionist

load_dotenv(".env.local")

server = AgentServer()


@server.rtc_session(agent_name="smileline-dental")
async def entrypoint(ctx: agents.JobContext):
    agent = DentalReceptionist()

    session = AgentSession(
        stt="deepgram/nova-3",
        llm="openai/gpt-4o-mini",
        tts=f"openai/tts-1:{agent.voice}",
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

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
