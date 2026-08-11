# Voice Agent Starter — Powered by Murf Falcon

Build a production voice AI agent in 5 minutes. Powered by the fastest TTS on the market - swap the system prompt to build anything from customer support to language tutors.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Murf Falcon](https://img.shields.io/badge/TTS-Murf%20Falcon-6366F1)](https://murf.ai/api/docs/text-to-speech/streaming) [![LiveKit](https://img.shields.io/badge/Transport-LiveKit-002cf2)](https://docs.livekit.io) [![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/) [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

---

## Why Murf Falcon

- **55ms model latency** - fastest production TTS
- **130ms time-to-first-audio** across 10+ global regions
- **$0.01/1000 characters** - up to 10x cheaper than alternatives
- **150+ voices** across 35+ languages
- **99.38% pronunciation accuracy**

---

## Architecture

```mermaid
flowchart LR
    A[🎙️ User speaks] -->|audio| B[Deepgram STT]
    B -->|text| C[LLM]
    C -->|response text| D[Murf Falcon TTS]
    D -->|audio| E[LiveKit]
    E -->|stream| F[🔊 User hears]

    style A fill:#444441,stroke:#888780,color:#fff
    style B fill:#185FA5,stroke:#85B7EB,color:#fff
    style C fill:#534AB7,stroke:#AFA9EC,color:#fff
    style D fill:#0F6E56,stroke:#5DCAA5,color:#fff
    style E fill:#D85A30,stroke:#F0997B,color:#fff
    style F fill:#444441,stroke:#888780,color:#fff
```

---

## Quickstart

### Prerequisites

- **Python** 3.10+
- **[uv](https://docs.astral.sh/uv/)** - fast Python package manager
  ```bash
  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Node.js** 18+
- **pnpm** — fast Node package manager
  ```bash
  npm install -g pnpm
  ```
- A [LiveKit](https://cloud.livekit.io/) project (free tier available)

### Step 1: Clone the repo

```bash
git clone https://github.com/murf-ai/murf-livekit-starter.git
cd murf-livekit-starter
```

### Step 2: Set up environment variables

Create `.env.local` in both `backend/` and `frontend/` (copy from `.env.example` in each). You need:

| Variable                               | Where to get it                                        | Required |
| -------------------------------------- | ------------------------------------------------------ | -------- |
| `LIVEKIT_URL`                          | LiveKit Cloud dashboard                                | Yes      |
| `LIVEKIT_API_KEY`                      | LiveKit Cloud dashboard                                | Yes      |
| `LIVEKIT_API_SECRET`                   | LiveKit Cloud dashboard                                | Yes      |
| `MURF_API_KEY`                         | [murf.ai/api/dashboard](https://murf.ai/api/dashboard) | Yes      |
| `DEEPGRAM_API_KEY`                     | [deepgram.com](https://deepgram.com)                   | Yes      |
| `GOOGLE_API_KEY` (or `OPENAI_API_KEY`) | Depends on LLM choice                                  | Yes      |

### Step 3: Install backend dependencies

```bash
cd backend
uv sync
uv run python src/agent.py download-files
```

### Step 4: Install frontend dependencies

```bash
cd frontend
pnpm install
```

### Step 5: Run it

**Option A - All-in-one (from repo root):**

```bash
# macOS/Linux
chmod +x start_app.sh
./start_app.sh

# Windows (PowerShell)
.\start_app.ps1
```

**Option B - Separate terminals:**

```bash
# Terminal 1 — LiveKit Server
livekit-server --dev

# Terminal 2 — Backend agent
cd backend && uv run python src/agent.py dev

# Terminal 3 — Frontend
cd frontend && pnpm dev
```

Then open **http://localhost:3000** in your browser.

You should now see the voice agent UI. Click **Start talking**, allow microphone access, and speak — the agent will respond with Murf Falcon TTS. Ensure your backend and (if using Option B) LiveKit server are running.

---

## Deploy

Want to deploy this beyond localhost? You'll need to deploy **two services**: the backend agent and the frontend. Both must use the same LiveKit project.

> This is a two-service app — the backend agent and the frontend UI deploy separately. You'll need both running and connected to the same LiveKit project.

### Backend (Python agent) — Deploy to Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/tIVCF1?referralCode=cNjn2P&utm_medium=integration&utm_source=template&utm_campaign=generic)

Set these environment variables in Railway:

- `MURF_API_KEY`
- `DEEPGRAM_API_KEY`
- `GOOGLE_API_KEY` or `OPENAI_API_KEY`
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`

The backend runs as a long-lived Python process that connects to LiveKit as an agent. Railway handles this well.

### Frontend (Next.js) — Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/murf-ai/murf-livekit-starter&root-directory=frontend&env=LIVEKIT_URL,LIVEKIT_API_KEY,LIVEKIT_API_SECRET&project-name=murf-voice-agent&repository-name=murf-voice-agent)

Set these environment variables in Vercel:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `AGENT_NAME` (optional — for explicit agent dispatch)

The frontend is a standard Next.js app. Point it at the same LiveKit instance your backend agent is connected to.

### Connecting them

The frontend and backend don't call each other directly — they both connect to **LiveKit**, which handles the real-time audio transport.

1. Use the **same** `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` on both Railway and Vercel
2. Set `AGENT_NAME=my-agent` on Vercel — this matches the `agent_name="my-agent"` registered in `backend/src/agent.py`
3. Verify: Railway logs should show the agent connected to LiveKit. Open your Vercel URL, click **Start talking** — the agent should respond

If the agent doesn't connect, double-check that both services point to the same LiveKit project and that the backend is running (check Railway logs).

---

## Change the Use Case

The default system prompt makes this a **customer support agent**. You can change the agent’s behavior by editing the prompt.

**Where the prompt lives:** `backend/src/agent.py`- the `SYSTEM_PROMPT` constant (near the top of the file, after the imports). Change that string to change what your voice agent does.

### Example prompts (copy-paste)

**Customer Support (default):**

```
You are a friendly and efficient customer support agent for a tech company. Help users with account issues, billing questions, and product troubleshooting. Be concise, empathetic, and solution-oriented. If you don't know something, say so honestly and offer to escalate.
```

**Language Tutor:**

```
You are a patient and encouraging language tutor helping the user practice conversational Spanish. Speak primarily in Spanish but switch to English to explain grammar or vocabulary when needed. Correct mistakes gently and suggest better phrasing. Keep conversations natural and fun.
```

**AI Receptionist:**

```
You are a professional receptionist for a medical clinic. Help callers schedule appointments, answer questions about office hours and services, and take messages for doctors. Be warm but efficient. Ask for the caller's name and reason for calling upfront.
```

See the Configuration section below for voice, STT, and LLM options.

---

## Configuration

### Murf voice

Edit the `tts=murf.TTS(...)` call in `backend/src/agent.py`. Set the `voice` argument to any Murf voice ID. Examples:

- `Anisha` — Indian English (female, default in this starter)
- `Pooja` — Indian English (female)
- `Samar` — Indian English (male)
- `Amara` — US English (female)
- `Gordon` — US English (male)
- `Hazel` — UK English (female)
- `Bertie` — UK English (male)

Browse all voices: [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library).

### STT provider

STT is configured in `backend/src/agent.py` in the `AgentSession(stt=...)` call. The default is Deepgram (`deepgram.STT(model="nova-3")`). You can swap to another LiveKit-compatible STT plugin if needed.

### LLM (Gemini vs OpenAI)

- **Gemini (default):** Set `GOOGLE_API_KEY` and use `llm=google.LLM(model="gemini-3.5-flash-lite")` in `agent.py`.
- **OpenAI:** Set `OPENAI_API_KEY`, add the OpenAI plugin, and use the corresponding `llm=openai.LLM(...)` in `agent.py`.

### Audio format

Murf Falcon and LiveKit handle audio format internally. For advanced options, see [Murf API docs](https://murf.ai/api/docs) and [LiveKit docs](https://docs.livekit.io).

---

## Project Structure

```
murf-livekit-starter/
├── backend/                 # Python voice agent (LiveKit Agents + Murf Falcon)
│   ├── src/
│   │   └── agent.py         # Agent entrypoint, pipeline (STT/LLM/TTS), system prompt
│   ├── tests/               # Agent tests
│   ├── .env.example         # Backend env template
│   ├── pyproject.toml       # Python deps (uv)
│   └── railway.toml         # Railway deploy config
├── frontend/                # Next.js UI for voice sessions
│   ├── app/
│   │   ├── page.tsx         # Main page
│   │   └── api/token/       # LiveKit token endpoint (dev)
│   ├── components/          # UI (agents-ui, app config, theme)
│   ├── app-config.ts        # Branding, title, button text, accent
│   ├── .env.example         # Frontend env template
│   └── package.json         # Node deps (pnpm)
├── start_app.sh             # Start LiveKit + backend + frontend (macOS/Linux)
├── start_app.ps1            # Start LiveKit + backend + frontend (Windows)
├── README.md                # This file
```

For deeper documentation on each part, see:

- [Backend Documentation](./backend/README.md) — agent pipeline, voice/LLM/STT configuration, testing, deployment
- [Frontend Documentation](./frontend/README.md) — UI customization, visualizers, theming, component architecture

---

## Links

- [Murf API Docs](https://murf.ai/api/docs)
- [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
- [LiveKit Docs](https://docs.livekit.io)
- [Deepgram Docs](https://developers.deepgram.com)
- [Murf Falcon Benchmarks](https://murf.ai/falcon/benchmarks)
- [TTS Latency Benchmarker](https://github.com/sahilsgupta/tts-latency-benchmarker) — run your own p50/p95 tests across providers
- [Murf Discord](https://discord.gg/FbKAy96Sz7)
- [Murf Startup Incubator](https://murf.ai/api) — 50M free characters for startups

---

## License

MIT

---

## Day 5 — Scheme Document Checklist Tool

### What it does

A `get_scheme_document_checklist` function tool is now connected to
the FinAssist voice agent. When the user asks what documents,
certificates, proofs, or paperwork are required for an Indian
government financial scheme, the agent automatically calls this
tool and reads the checklist back in natural spoken language.

Supported schemes:

- PM-KISAN
- PMJJBY (Pradhan Mantri Jeevan Jyoti Bima Yojana)
- PMSBY (Pradhan Mantri Suraksha Bima Yojana)
- MUDRA Loan
- Sukanya Samriddhi Yojana
- Atal Pension Yojana
- Jan Dhan Yojana
- Kisan Credit Card (KCC)
- Ayushman Bharat (AB-PMJAY)

### Data source

Local dataset compiled from publicly available scheme guidelines
and official ministry notifications. This is **not** live data.

**Last updated:** 2026-08-10

### Failure handling

If the tool cannot find a scheme or encounters an error, it
returns a clear failure message. The agent then tells the user:

> "I'm unable to access the scheme information right now, so I
> don't want to give you inaccurate information."

The agent does **not** hallucinate document lists when the tool
fails.

### Example user question

> "What documents do I need for a Mudra loan?"

### Example tool response (internal, not spoken)

```
Scheme: MUDRA (Micro Units Development and Refinance Agency) Loan
Objective: Provides loans up to ten lakh rupees to non-corporate,
non-farm small or micro enterprises.
Required documents:
- Identity proof (Aadhaar, PAN, or voter ID)
- Address proof (utility bill, Aadhaar, or rental agreement)
- Passport-size photograph
- Business plan or project report
- Proof of business existence (registration, licence, or shop act certificate)
- Bank account statements for the last six months
- Quotation for machinery or equipment (if applicable)
- Category certificate (SC/ST/OBC) if applicable
Data source: Local dataset compiled from publicly available scheme guidelines.
Data last updated: 2026-08-10
Data type: Local dataset (not live data)
```

### Files changed for Day 5

- `backend/src/scheme_data.py` — new local dataset
- `backend/src/agent.py` — added `get_scheme_document_checklist`
  tool and updated system prompt
- `README.md` — this section

---

## Day 6 — Outbound Phone Calls

### What it does

The FinAssist agent can now place outbound phone calls to a
phone number you control. When the agent receives a dispatch
with `"outbound": true` in the metadata, it:

1. Reads the destination phone number from metadata
2. Creates a SIP participant via LiveKit's SIP API
3. Places the call through your configured Twilio SIP trunk
4. Uses a phone-appropriate greeting that:
   - Identifies the agent as FinAssist
   - Explains the purpose of the call
   - Clearly states this is an automated/AI call
   - Gives the user a way to opt out ("say stop at any time")
5. Offers an `end_call` tool so the agent can hang up when
   the conversation is finished

### Architecture

```
dispatch_call.py
  → LiveKit Agent Dispatch API
    → my_agent entrypoint
      → detects "outbound: true" in metadata
      → ctx.add_sip_participant(trunk_id, phone_number)
      → Twilio SIP trunk → PSTN → your phone rings
      → FinAssist answers and starts conversation
```

### New environment variables

| Variable | Where to get it |
|---|---|
| `SIP_OUTBOUND_TRUNK_ID` | LiveKit Cloud → Telephony → SIP Trunks → your outbound trunk ID |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number (e.g. `+15105550123`) |

### External configuration (outside the code)

You must set up three things before outbound calling works:

**1. Twilio Console**

- Purchase a phone number (if you don't have one)
- Create an Elastic SIP Trunk
- Under **Termination**, set a domain like `finassist.pstn.twilio.com`
- Create a **Credential List** (username + password) and attach
  it to the trunk
- Associate your phone number with the trunk

**2. LiveKit Cloud Dashboard**

- Go to **Telephony → SIP Trunks → Create new trunk**
- Select **Outbound** direction
- Set:
  - **Name:** `Twilio outbound`
  - **Address:** `finassist.pstn.twilio.com`
  - **Numbers:** `["+15105550123"]` (your Twilio number)
  - **Auth username/password:** match your Twilio credential list
- Copy the trunk ID → set as `SIP_OUTBOUND_TRUNK_ID`

**3. Start the agent**

```bash
cd backend
uv run python src/agent.py dev
```

### How to trigger an outbound call

In a separate terminal:

```bash
cd backend
python src/dispatch_call.py +919876543210
```

Replace `+919876543210` with your actual phone number (must
include country code with `+` prefix).

### What to expect

1. Your phone rings
2. You hear FinAssist introduce itself as an AI assistant
3. The agent explains it is an automated call
4. You can say "stop" at any time to end the call
5. You can ask about financial services, schemes, etc.
6. The agent has the `end_call` tool to hang up when done

### Failure handling

- **Invalid phone number:** SIP returns an error, logged in agent
- **Busy/no answer:** SIP timeout, agent logs the failure and shuts down
- **Call disconnected:** Room is deleted, agent exits cleanly
- **Missing trunk ID:** Agent logs an error and refuses to dial

### Files changed for Day 6

- `backend/src/agent.py` — added outbound detection, SIP call
  logic, phone greeting, and `end_call` tool
- `backend/src/dispatch_call.py` — new script to trigger calls
- `backend/.env.local` — added `SIP_OUTBOUND_TRUNK_ID` and
  `TWILIO_PHONE_NUMBER`
- `README.md` — this section
