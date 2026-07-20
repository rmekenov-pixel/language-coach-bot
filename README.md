# Language Coach Bot 🎓

AI-powered English language coach for WhatsApp. Built with FastAPI, PostgreSQL, Groq (Llama 3), and WhatsApp Cloud API.

## What It Does

- 💬 **Conversational coaching** — natural dialogue in English at A1-A2 level
- 🔧 **Error correction** — gently corrects grammar mistakes, one at a time
- 📚 **Course recommendations** — suggests free learning resources from a curated catalog (23 materials: Stepik, BBC, Duolingo, British Council and more)
- 📈 **Progress tracking** — evaluates student level every 10 messages, promotes A1 → A2 → B1
- 🧠 **Persistent memory** — conversation history and student profile saved in PostgreSQL
- 🎯 **Topic detection** — matches course recommendations to the topic of the conversation

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI, uvicorn |
| LLM | Groq API (llama-3.1-8b-instant) |
| Database | PostgreSQL + SQLAlchemy async + asyncpg |
| Messaging | WhatsApp Cloud API (Meta) |
| Hosting | Railway |

## Commands

| Command | Description |
|---|---|
| `/reset` | Clear conversation history |
| `/progress` | Show current level and message count |

## Project Structure

```
app/
├── main.py                  # FastAPI app, lifespan (DB init + content seeding)
├── config.py                # Settings from environment variables
├── db/
│   ├── database.py          # Async PostgreSQL connection (asyncpg)
│   └── models.py            # SQLAlchemy models: User, Message, ContentItem
├── routers/
│   └── webhook.py           # WhatsApp webhook: verification + message handling
└── services/
    ├── coach.py             # LLM coach logic + system prompt
    ├── memory.py            # Conversation history (read/write PostgreSQL)
    ├── user_service.py      # Student profile management
    ├── content_service.py   # Course catalog queries
    └── progress_service.py  # Topic detection + level evaluation
scripts/
└── seed_content.py          # Initial content catalog data (22 learning materials)
```

## Environment Variables

```env
WHATSAPP_TOKEN=             # Meta permanent system user token
WHATSAPP_PHONE_NUMBER_ID=   # WhatsApp Business phone number ID
WHATSAPP_VERIFY_TOKEN=      # Webhook verification token (your choice)
WHATSAPP_API_VERSION=v22.0  # Graph API version
GROQ_API_KEY=               # Groq API key (console.groq.com)
DATABASE_URL=               # PostgreSQL connection string (auto-set by Railway)
```

## Setup & Deployment

### 1. Meta for Developers
- Create a Meta App → add WhatsApp product
- Get `Phone Number ID` and generate a permanent token via System User
- Configure webhook URL: `https://your-app.up.railway.app/webhook`
- Subscribe to `messages` field

### 2. Railway
- Create new project → Deploy from GitHub
- Add PostgreSQL database → connect `DATABASE_URL` via reference variable
- Set all environment variables
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 3. First Run
On startup, the app automatically:
1. Creates database tables (`users`, `messages`, `content_items`)
2. Seeds the content catalog with 22 learning materials

## Privacy Policy

Available at: https://rmekenov-pixel.github.io/language-coach-bot/privacy-policy.html

## Author

Ratmir Mekenov — [LinkedIn](https://linkedin.com/in/mekenovratmir) | [GitHub](https://github.com/rmekenov-pixel)
