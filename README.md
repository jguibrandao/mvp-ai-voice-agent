# SmileLine Dental — AI Voice Receptionist

A voice AI agent that handles phone calls for a dental clinic. You can actually talk to it — schedule appointments, ask about services, or get transferred to the right department. Built with LiveKit Agents SDK and a React admin panel for real-time configuration.

This was built as a one-day engineering challenge. The focus was on making the voice experience feel natural (not like a chatbot reading text) and getting tool calling to work reliably during live conversation.

## Quick Start (< 5 minutes)

### Prerequisites

- Python 3.10+
- Node.js 18+
- A free [LiveKit Cloud](https://cloud.livekit.io) account
- An OpenAI API key

### 1. Clone and install

```bash
git clone https://github.com/jguibrandao/mvp-ai-voice-agent.git
cd mvp-ai-voice-agent

# Python
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt

# React admin UI
cd web && npm install && cd ..
```

### 2. Set up environment

Install the [LiveKit CLI](https://docs.livekit.io/home/cli/cli-setup/) and authenticate:

```bash
lk cloud auth
```

Generate your `.env.local`:

```bash
lk app env -w
```

Or manually create `.env.local` in the project root:

```
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
LIVEKIT_URL=wss://your-project.livekit.cloud
OPENAI_API_KEY=sk-...
```

### 3. Download model files

```bash
python main.py download-files
```

### 4. Run everything (3 terminals)

```bash
# Terminal 1 — Voice agent
python main.py dev

# Terminal 2 — Admin API
python api.py

# Terminal 3 — Admin UI
cd web && npm run dev
```

### 5. Talk to your agent

Open the [LiveKit Agents Playground](https://agents-playground.livekit.io/) and connect to your project. Start talking — the agent will greet you as Sarah, the dental receptionist.

Admin UI is at [http://localhost:5173](http://localhost:5173).

### Docker alternative

```bash
docker compose up
```

Then open the playground and admin UI as above.

---

## What I Built

### Voice Agent

A dental clinic receptionist ("Sarah") powered by LiveKit Agents SDK. She handles the kind of calls a real front desk would get:

**4 tools the agent can call mid-conversation:**

| Tool | What it does |
|------|-------------|
| `check_availability` | Looks up open appointment slots for a given date |
| `book_appointment` | Books an appointment (name, date, time, procedure) |
| `get_clinic_info` | Answers questions about hours, services, insurance, pricing |
| `transfer_call` | Routes the caller to a department (dentist, billing, manager) |

**Guardrail:** The system prompt explicitly instructs the agent to never give medical or dental advice. If someone asks "should I get a root canal?", Sarah redirects them to speak with the dentist directly.

### Admin UI

A React panel where you can:

- **Edit the system prompt** — change Sarah's personality, instructions, or boundaries
- **Configure persona** — change her name, greeting message, and TTS voice
- **Toggle tools** — enable or disable any of the 4 tools

Changes are saved to a JSON file and picked up on the next conversation. No restart needed.

### Bonus: Latency Tracking

I chose latency measurement because it's the single most important metric for voice UX. In a phone call, 200ms response time feels natural — it's within human conversational latency (200-500ms). At 800ms, it feels like the agent froze. At 1.5s, people start saying "hello? are you there?"

This is fundamentally different from chat, where users can wait 2-3 seconds without noticing because they're reading at their own pace.

The tracker measures end-to-end response time (user stops speaking → agent starts speaking) and exposes stats via `GET /api/metrics`.

---

## Why LiveKit over Pipecat

I went with **LiveKit Agents SDK** for these reasons:

1. **Built-in playground** — agents-playground.livekit.io lets you talk to the agent from any browser with zero client-side code. This saved hours.
2. **Plugin ecosystem** — Deepgram STT, OpenAI TTS, Silero VAD, noise cancellation — all plug-and-play. No custom audio pipeline needed.
3. **First-class tool calling** — The `@function_tool` decorator maps cleanly to Python functions. The framework handles serialization, interruptions, and error propagation.
4. **Production architecture** — LiveKit's room-based model (agent joins a room, participant joins the same room) mirrors how real telephony platforms work. This matters for Aloware's use case.

Pipecat is a great framework too, but it would have required more setup for browser-based voice (either a Daily account or a custom WebSocket transport), and LiveKit's playground was a huge time-saver for a one-day project.

---

## Decisions and Trade-offs

| Decision | Why |
|----------|-----|
| JSON file config (not DB) | Project spec says no database. JSON is readable, easy to debug, and sufficient for single-user. |
| Google Gemini 3 Flash for LLM | Latest and fastest Google model available through LiveKit inference. For voice, speed beats raw intelligence — every 100ms matters. Demonstrates multi-vendor thinking instead of defaulting to OpenAI for everything. |
| Deepgram Flux for STT | Deepgram's newest model, built specifically for voice agents with ultra-low latency. Runs through LiveKit Cloud inference. |
| OpenAI TTS-1 for voice | Multiple voice options, natural-sounding. Best-of-breed approach: each component uses the provider that excels at that specific task. |
| FastAPI for admin API | Lightweight, async, auto-generates OpenAPI docs. Overkill vs Flask for 2 endpoints, but it's what I'd use in production. |
| Vite + React for UI | Fast dev server, TypeScript support out of the box. No CSS framework — inline styles keep it simple for a functional UI. |
| Config reload per conversation | Agent reads JSON at session start. Simple, reliable, no hot-reload complexity. |
| Mock data for tools | Real database would violate the "no DB" constraint. In-memory mock data demonstrates the pattern. |

---

## What I'd Improve With More Time

- **Persistent storage** — Replace JSON + mock data with a real database (Postgres) for appointments and config
- **Streaming latency breakdown** — Track STT, LLM, and TTS latency separately to identify bottlenecks
- **Conversation history** — Log and display past conversations for debugging
- **Multi-agent handoff** — Instead of a fake "transfer_call", actually hand off to a specialized agent (billing agent, scheduling agent)
- **Better guardrails** — Add a classifier that detects off-topic requests before they reach the LLM, rather than relying on prompt engineering alone
- **Eval suite** — Automated tests that verify the agent calls the right tool with the right args for common scenarios
- **Production deployment** — Dockerize properly, add health checks, set up CI/CD

---

## Project Structure

```
├── agent/
│   ├── config_manager.py   # JSON config read/write
│   ├── metrics.py          # Latency tracking
│   ├── tools.py            # 4 function tools
│   └── voice_agent.py      # Agent class with dynamic config
├── web/src/
│   ├── App.tsx             # Main admin layout
│   ├── api.ts              # HTTP client for FastAPI
│   └── components/         # SystemPromptEditor, PersonaConfig, ToolsManager
├── main.py                 # LiveKit agent entry point
├── api.py                  # FastAPI admin server
├── agent_config.json       # Persisted agent configuration
├── Dockerfile
└── docker-compose.yml
```

---

## Loom Video

[Link to 5-minute demo video] — TODO

---

*Built with curiosity and too much coffee.*
