# AIVOA — AI Complaint Management

An AI-first pharmaceutical complaint management demo. Complaint data is entered through the AIVOA Copilot, never manually in the QMS form.

## Stack

- React + Redux Toolkit + Inter
- Python FastAPI + SQLAlchemy with Supabase Postgres
- LangGraph orchestration with Groq (`gemma2-9b-it`)

## Run locally

## Backend

```powershell
cd backend
Copy-Item .env.example .env
# Set GROQ_API_KEY in .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the address printed by Vite (usually `http://localhost:5173`).

## Demo prompts

1. `Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg, batch AMX240602, manufactured March 2026, expiry February 2028. 12 capsules were affected in a sealed bottle. Please log this complaint.`
2. `Sorry, the batch number is BMX240602 and the affected quantity is 48 capsules.`

You can also upload `sample-data/customer-complaint-email.txt`. The API accepts PDF, TXT, and EML files. Without a Groq key, AIVOA runs a deterministic offline extraction fallback so the demo remains usable.

## Environment

## Supabase database

Create a Supabase project, then copy its **Session pooler** connection string from **Settings → Database → Connect**. First run the supplied SQL schema in the Supabase SQL Editor. Then create `backend/.env` from `backend/.env.example` and set its connection string in SQLAlchemy form:

```env
DATABASE_URL=postgresql+psycopg://postgres.PROJECT_REF:YOUR_PASSWORD@aws-0-YOUR_REGION.pooler.supabase.com:6543/postgres?sslmode=require
```

The backend requires this Supabase URL, uses a `NullPool` client configuration behind Supabase's own connection pooler, and validates stale connections before using them. Keep the URL server-side only; never put it in the React app.
