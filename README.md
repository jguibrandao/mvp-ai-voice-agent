# SmileLine Dental — AI Voice Receptionist

A voice AI agent that handles phone calls for a dental clinic. You can actually talk to it — schedule appointments, ask about services, or get transferred to the right department. Built with LiveKit Agents SDK and a React admin panel for real-time configuration.

This was built as a one-day engineering challenge. The focus was on making the voice experience feel natural (not like a chatbot reading text) and getting tool calling to work reliably during live conversation.

## Quick Start (< 5 minutes)

### Prerequisites

- Python 3.10+
- Node.js 18+
- A free [LiveKit Cloud](https://cloud.livekit.io) account
- An OpenAI API key (for LLM; TTS uses Cartesia via LiveKit Inference)

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

# Terminal 2 — Admin API (runs on port 8001)
python api.py

# Terminal 3 — Admin UI
cd web && npm run dev
```

### 5. Talk to your agent

Open the [LiveKit Agents Playground](https://agents-playground.livekit.io/) and connect to your project. In the sidebar, set the **Agent name** field to `smileline-dental` (this enables explicit dispatch). Click connect and start talking — the agent will greet you as Sarah, the dental receptionist.

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

**5 tools the agent can call mid-conversation:**

| Tool | What it does |
|------|-------------|
| `check_availability` | Looks up open appointment slots for a given date |
| `book_appointment` | Books an appointment (name, date, time, procedure) |
| `get_clinic_info` | Answers questions about hours, services, insurance, pricing |
| `transfer_call` | Routes the caller to a department (dentist, billing, manager) |
| `end_call` | Ends the call politely when the caller is done |

**Note on transfers:** `transfer_call` is simulated — there's no SIP trunk or PBX behind it. When triggered, the agent says a warm farewell and the session ends automatically after ~10 seconds. In production, this would integrate with LiveKit SIP to route the call to a real extension.

**Guardrail:** The system prompt explicitly instructs the agent to never give medical or dental advice. If someone asks "should I get a root canal?", Sarah redirects them to speak with the dentist directly.

### Admin UI

A React panel where you can:

- **Edit the system prompt** — change Sarah's personality, instructions, or boundaries
- **Configure persona** — change her name, greeting message, and TTS voice (the voice field accepts a [Cartesia voice ID](https://play.cartesia.ai/); default is "Jacqueline", a young American female voice)
- **Toggle tools** — enable or disable any of the 5 tools
- **Latency dashboard** — real-time metrics with bar chart visualization and color-coded thresholds

Changes are saved to a JSON file and picked up on the next conversation. No restart needed.

### Bonus: Latency Measurement & Optimization

I chose latency because it's the single most important metric for voice UX — and it's fundamentally different from chat.

**Why 200ms vs 800ms matters more for voice than chat:**

In a text chat, a 2-second delay is barely noticeable — the user is reading the previous message, scrolling, or typing. The interaction is asynchronous by nature; there's no expectation of instant feedback. Voice is the opposite. The user's mental model is a phone call with another human. Humans take turns in conversation with gaps of 200-300ms — that's the natural rhythm our brains expect. Research in conversational analysis (Stivers et al., 2009) shows that inter-turn silence beyond ~700ms is perceived as a social signal: the other person is hesitating, confused, or disengaged.

For a voice AI agent, this means:
- **< 300ms** — feels instantaneous, indistinguishable from human turn-taking
- **300-500ms** — natural, comfortable pause
- **500-800ms** — noticeable but tolerable; the user starts to feel "something is processing"
- **800ms-1.5s** — awkward silence; callers start repeating themselves or saying "hello?"
- **> 1.5s** — callers assume the line is dead and hang up

This is why every millisecond matters in voice but not in chat. A chat user waits 3 seconds and doesn't care. A phone caller waits 3 seconds and hangs up. For a platform like Aloware handling real phone calls at scale, the difference between 500ms and 1.2s is the difference between callers staying on the line and callers dropping.

**What I measure — two separate metrics:**

The system tracks two distinct latency metrics, as the pipeline has a natural split point:

| Metric | What it measures | How |
|--------|-----------------|-----|
| **TTFT (Time-to-First-Token)** | User stops speaking → LLM starts generating | Captures STT processing + turn detection + inference routing overhead |
| **End-to-End** | User stops speaking → Agent audio starts playing | The full pipeline: STT → LLM → TTS. This is the silence the caller actually hears. |

The difference between the two (End-to-End minus TTFT) gives us the **Processing time** — how long the LLM generation + TTS synthesis takes. This decomposition is critical because it tells you *where* to optimize: if TTFT is high, the bottleneck is in STT/turn detection; if processing is high, it's in LLM/TTS.

All metrics are persisted to a JSON file, exposed via `GET /api/metrics`, and visualized in a real-time dashboard with stacked bar charts showing the TTFT vs Processing breakdown per response, plus avg/min/max stats for each metric. Color-coded thresholds (green < 500ms, yellow 500-800ms, red > 800ms) make it easy to spot regressions.

**What I optimized:**

| Optimization | Before | After | Impact |
|-------------|--------|-------|--------|
| Turn detection timing | 0.5-3.0s delay | 0.2-0.8s delay | -2.2s worst case |
| STT language tag | Missing (degraded turn detection) | Explicit `en` (proper detection) | -0.5s avg |
| LLM model | Gemini 3 Flash (via gateway) | GPT-4.1 Nano (direct OpenAI plugin) | -0.5s avg |
| LLM connection | Via LiveKit inference gateway | Direct API (bypass gateway) | -100-200ms per call |
| STT model | Deepgram Flux (no language output) | Deepgram Nova-3 (language-aware) | Better turn detection |
| TTS model | Cartesia Sonic 3 | Cartesia Sonic Turbo (latency-optimized) | -100-200ms first audio |
| System prompt | Verbose instructions | Concise, structured rules | Fewer tokens for LLM to process |

**Current results and honest assessment:**

Running from Brazil (South America) against US-based providers:
- **Simple responses:** ~800-1200ms end-to-end
- **Tool-calling responses:** ~1.5-2s (requires two LLM passes: one to decide which tool, one to formulate the answer)

This is above the ideal 300-500ms range. Here's why, and what would fix it:

| Bottleneck | Cause | Fix |
|-----------|-------|-----|
| Geographic latency | Agent runs in Brazil, providers are in US-East/West. Every API call adds ~150-200ms round-trip. | Deploy agent in US-East (same region as OpenAI/Deepgram). This alone would save ~300-400ms. |
| STT/TTS via inference gateway | Deepgram and Cartesia calls are routed through LiveKit's inference gateway, adding a hop. | Use direct plugins with provider API keys (like we did for the LLM). Saves ~100-200ms per provider. |
| No response caching | Common questions ("what are your hours?") hit the full pipeline every time. | Semantic cache for frequent queries — skip LLM entirely for known answers. |
| TTS cold start | First response in a session has higher TTS latency. | Pre-warm TTS connection during the greeting. |
| No speculative execution | System waits for STT to finalize before starting LLM. | Partial transcript streaming — start LLM inference on interim STT results. |

The key insight from measuring TTFT separately: most of our latency budget is spent *before* the LLM even starts (STT finalization + turn detection + routing). This means even switching to a faster LLM has diminishing returns — the real wins are in infrastructure (co-location, direct connections) and pipeline architecture (speculative execution).

---

## Why LiveKit over Pipecat

I went with **LiveKit Agents SDK** for these reasons:

1. **Built-in playground** — agents-playground.livekit.io lets you talk to the agent from any browser with zero client-side code. This saved hours.
2. **Plugin ecosystem** — Deepgram STT, Cartesia TTS, Silero VAD, noise cancellation — all plug-and-play. No custom audio pipeline needed.
3. **First-class tool calling** — The `@function_tool` decorator maps cleanly to Python functions. The framework handles serialization, interruptions, and error propagation.
4. **Production architecture** — LiveKit's room-based model (agent joins a room, participant joins the same room) mirrors how real telephony platforms work. This matters for Aloware's use case.

Pipecat is a great framework too, but it would have required more setup for browser-based voice (either a Daily account or a custom WebSocket transport), and LiveKit's playground was a huge time-saver for a one-day project.

---

## Decisions and Trade-offs

| Decision | Why |
|----------|-----|
| JSON file config (not DB) | Project spec says no database. JSON is readable, easy to debug, and sufficient for single-user. |
| OpenAI GPT-4.1 Nano for LLM (direct plugin) | Fastest OpenAI model via direct API connection (bypasses LiveKit inference gateway). Initially tried Gemini 3 Flash (multi-vendor) then GPT-4.1 Mini via gateway — switched to Nano with direct plugin after profiling showed the LLM + gateway routing was the biggest latency contributor. |
| Deepgram Nova-3 for STT | Fast, accurate, and reports language codes the turn detector needs. Initially tried Deepgram Flux (newer), but it doesn't output language tags, degrading turn detection and adding latency. |
| Cartesia Sonic Turbo for TTS | Cartesia's latency-optimized model, trades marginal quality for significantly faster time-to-first-audio. Initially tried OpenAI TTS-1 (unsupported by gateway), then Sonic 3 — switched to Sonic Turbo to minimize the TTS segment of the pipeline. |
| FastAPI for admin API | Lightweight, async, auto-generates OpenAPI docs. Overkill vs Flask for 2 endpoints, but it's what I'd use in production. |
| Vite + React for UI | Fast dev server, TypeScript support out of the box. No CSS framework — inline styles keep it simple for a functional UI. |
| Config reload per conversation | Agent reads JSON at session start. Simple, reliable, no hot-reload complexity. |
| Mock data for tools | Real database would violate the "no DB" constraint. In-memory mock data demonstrates the pattern. |

---

## What I'd Improve With More Time

- **Persistent storage** — Replace JSON + mock data with a real database (Postgres) for appointments and config
- **Per-component latency** — Track STT, LLM, and TTS as three separate measurements (currently split into TTFT and Processing)
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
│   ├── tools.py            # 5 function tools
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
