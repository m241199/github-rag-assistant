# GitHub RAG Assistant

A retrieval-augmented generation assistant for understanding GitHub repositories.

## Tech Stack

- Frontend: Next.js + TypeScript
- Backend: FastAPI + Python
- Database: PostgreSQL
- Embeddings: local sentence-transformers
- LLM: Gemini

## Setup

Create a local environment file:

```bash
cp .env.example .env
```

Set at least:

```env
DATABASE_URL=postgresql://...
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSIONS=384
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
CHAT_MODEL=gemini-2.5-flash-lite
```

`GITHUB_TOKEN` is optional, but recommended if you index more than a few public repositories.

`GEMINI_API_KEY` is only required for generated answers. Repository indexing and retrieval work with local embeddings without any paid OpenAI API calls.

## Database Options

### Option A: Hosted Postgres, Recommended for Local Development

Use Supabase or Neon so you can run the backend without Docker on your machine.

For Supabase:

1. Create a Supabase project.
2. Open the SQL Editor.
3. Run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

4. Copy the Postgres connection string into `.env`:

```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
```

If your machine cannot reach the direct Supabase database host, use Supabase's pooler connection string instead. In Supabase, open Project Settings -> Database -> Connection string, choose a pooler mode, and copy that URL into `DATABASE_URL`.

Some hosted providers require SSL. If your provider gives you an SSL connection string, keep the query parameter, for example:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require
```

When the backend starts, it creates the application tables automatically.

### Option B: Docker Postgres for Local Development

If Docker is available and you only want the database in Docker, start the local pgvector database:

```bash
docker compose up -d db
```

Then use the default local database URL from `.env.example`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/github_rag
```

The database will be available on `localhost:5432`.

## Run Locally

Use this path when you want to run the backend and frontend directly on your machine.

### Backend

From the project root:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On macOS or Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

When the backend starts, it creates the application tables automatically.

The first local embedding request downloads `sentence-transformers/all-MiniLM-L6-v2` from Hugging Face and caches it on your machine.

The API will run at:

```text
http://localhost:8000
```

You can check the FastAPI docs at:

```text
http://localhost:8000/docs
```

### Frontend

Open a second terminal from the project root:

```bash
cd frontend
npm install
npm run dev
```

The frontend will run at:

```text
http://localhost:3000
```

Keep the backend and frontend terminals running at the same time. The frontend calls the backend through `NEXT_PUBLIC_API_BASE_URL`, which defaults to `http://localhost:8000`.

If Next.js prints a network URL such as `http://192.168.x.x:3000`, prefer `http://localhost:3000` when testing on the same machine.

## Run with Docker

Use this path when you want Docker to run Postgres, the FastAPI backend, and the Next.js frontend together.

Make sure `.env` exists and contains your API keys, then start the stack from the project root:

```bash
docker compose up --build
```

The services will be available at:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000
API docs: http://localhost:8000/docs
Database: localhost:5432
```

In Docker, the backend uses the Compose database host:

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/github_rag
```

This is set automatically in `docker-compose.yml`, so your local `.env` can keep using `localhost` for non-Docker development.

To stop the Docker stack:

```bash
docker compose down
```

To also remove the local database volume:

```bash
docker compose down -v
```

## Index a Repository

Create a repository record:

```bash
curl -X POST http://localhost:8000/repos/ \
  -H "Content-Type: application/json" \
  -d "{\"github_url\":\"https://github.com/octocat/Hello-World\"}"
```

Then index the returned `id`:

```bash
curl -X POST http://localhost:8000/indexing/REPO_ID
```

## Current Status

Early end-to-end scaffold:
- frontend pages and components
- backend routes and services
- GitHub zipball loading for public repositories
- database persistence for repositories, files, chunks, and query logs
- docs chunking by headers
- code chunking by classes, functions, methods, and related symbols
- hybrid retrieval using lexical BM25-style scoring plus embedding similarity
- local embeddings by default, with optional OpenAI fallback in code
- Gemini chat responses when `GEMINI_API_KEY` is set
