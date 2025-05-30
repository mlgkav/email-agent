📬 Building a Full-Stack Email Agent Dashboard

This guide walks you through building a secure, scalable, and powerful email agent dashboard using a modern full-stack setup. It includes email ingestion, classification, and frontend visualization. We’ll use Next.js + shadcn/ui for the frontend, and FastAPI + PostgreSQL + pgvector for the backend, with background processing and AI support.

⸻

🔧 Tech Stack Overview

Frontend
	•	Next.js – React framework with built-in SSR and API routes
	•	shadcn/ui – Tailwind-based accessible UI components
	•	Tailwind CSS – Utility-first styling
	•	React Query – API caching and background refresh
	•	Zod – Schema validation for frontend + backend sync
	•	Vercel – Hosting and CI/CD for the frontend

Backend
	•	FastAPI – High-performance async backend
	•	PostgreSQL + pgvector – For structured data and vector search
	•	Redis + RQ/Celery – Background task processing
	•	Docker – Containerization
	•	OpenAI / HuggingFace – Embedding + RAG/LLM integration
	•	imap-tools – Python library for IMAP email fetching

⸻

📁 1. Project Structure

email-agent-dashboard/
├── frontend/            # Next.js app
│   ├── components/      # UI components (shadcn/ui)
│   ├── pages/           # Route pages
│   ├── utils/           # Fetchers, helpers
│   └── ...
├── backend/             # FastAPI app
│   ├── app/
│   │   ├── api/         # Endpoints
│   │   ├── workers/     # Background tasks
│   │   ├── models/      # ORM models
│   │   └── core/        # DB, logging, config
│   └── main.py
├── docker-compose.yml   # Dev environment
└── .env


⸻

⚙️ 2. Backend Setup (FastAPI)

🔹 Step 1: Initialize FastAPI project

mkdir backend && cd backend
python3 -m venv venv && source venv/bin/activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary
pip install imap-tools celery redis openai pgvector

🔹 Step 2: Configure PostgreSQL + pgvector

Install the pgvector extension in PostgreSQL:

CREATE EXTENSION IF NOT EXISTS vector;

Create models:

from sqlalchemy import Column, Integer, String, DateTime
from pgvector.sqlalchemy import Vector

class Email(Base):
    __tablename__ = 'emails'

    id = Column(Integer, primary_key=True)
    sender = Column(String)
    subject = Column(String)
    date = Column(DateTime)
    body = Column(String)
    embedding = Column(Vector(1536))

🔹 Step 3: Background email fetching

Use imap-tools in a task:

from imap_tools import MailBox

def fetch_emails():
    with MailBox('imap.gmail.com').login(user, password, 'INBOX') as mailbox:
        for msg in mailbox.fetch():
            # store to DB and trigger embedding/classification

Use Redis + Celery to run async:

@celery.task
def process_email(msg):
    # Clean text, get embedding, classify, store


⸻

🧠 3. Embedding + Classification

🔹 Step 1: Get OpenAI embedding

import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_embedding(text):
    return openai.Embedding.create(input=text, model="text-embedding-3-small")['data'][0]['embedding']

🔹 Step 2: Store vector in pgvector

email.embedding = get_embedding(text)
session.add(email)
session.commit()

🔹 Step 3: Classify emails

Use regex or a lightweight model to detect spam/marketing:

if "unsubscribe" in body.lower() or re.search(r'<img[^>]+1x1', body):
    email.label = "marketing"
else:
    email.label = "personal"


⸻

💻 4. Frontend Setup (Next.js)

🔹 Step 1: Scaffold app

npx create-next-app@latest frontend -e with-tailwindcss
cd frontend
npx shadcn-ui@latest init

🔹 Step 2: Add shadcn component

npx shadcn-ui@latest add button card table

Use like this:

import { Card } from '@/components/ui/card'

<Card className="p-4">Email from John Doe</Card>

🔹 Step 3: Fetch emails

Use React Query:

import { useQuery } from '@tanstack/react-query'

const { data } = useQuery(['emails'], async () => {
  const res = await fetch('/api/emails')
  return res.json()
})

🔹 Step 4: Build Dashboard UI

Use Table, Card, Badge, and DropdownMenu to allow:
	•	Viewing emails
	•	Filtering by label
	•	Quick summaries with AI

⸻

🔐 5. Auth + Roles

🔹 Option A: Clerk/Auth0

Use Clerk or Auth0 to protect routes:

import { useUser } from '@clerk/nextjs'

if (!user) return <SignIn />

Protect API routes:

export default withAuth(async (req, res) => {
  if (!req.auth.userId) return res.status(401).end()
})


⸻

📡 6. API Integration

🔹 Create API route in Next.js

// pages/api/emails.ts
export default async function handler(req, res) {
  const emails = await fetch("http://localhost:8000/emails")
  const data = await emails.json()
  res.status(200).json(data)
}

Use Zod to validate on both ends:

const Email = z.object({
  sender: z.string(),
  subject: z.string(),
  date: z.string(),
  label: z.string()
})


⸻

🐳 7. Docker Dev Environment

🔹 docker-compose.yml

version: '3.9'
services:
  db:
    image: postgres
    environment:
      POSTGRES_DB: emails
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
  backend:
    build: ./backend
    ports:
      - "8000:8000"
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"


⸻

🚀 8. Deployment

🔹 Vercel (Frontend)
	•	Connect your GitHub repo
	•	Set environment variables (e.g. API_URL, AUTH_KEY)
	•	Vercel auto-detects Next.js

🔹 Railway / Render (Backend)
	•	Deploy your FastAPI server + Postgres
	•	Add background workers as services

⸻

🧪 9. Bonus Features

🔹 Email Search

SELECT * FROM emails WHERE embedding <#> $1 LIMIT 5;

Use cosine distance to find similar emails.

🔹 Summarize with OpenAI

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": f"Summarize this: {body}"}]
)

🔹 User feedback or tagging system

Allow agents to tag or reclassify emails in the UI.

⸻

✅ Summary

By following this guide, you’ve created:
	•	A secure, scalable backend with async email processing
	•	A clean, customizable frontend with Next.js + shadcn
	•	A vector-searchable email database with classification
	•	Real-time, agent-ready dashboards for email triage

Let me know if you want:
	•	RAG integration
	•	Multi-user access
	•	AI-suggested responses
	•	Admin analytics dashboard

Happy building! 🚀
