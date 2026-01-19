# AI Portal MVP

A containerized AI chat portal with authentication, multiple LLM support, and audit logging.

## Architecture

- **Frontend**: Next.js (React)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Gateway**: Nginx (reverse proxy)

## Prerequisites

- Docker Desktop installed and running
- OpenAI API key (or Azure OpenAI credentials)

## Quick Start

1. **Clone and setup environment**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values (especially OPENAI_API_KEY)
   ```

2. **Run the stack**
   ```bash
   docker compose up --build
   ```

3. **Access the portal**
   - Open http://localhost:8080 in your browser

## Project Structure

```
/
├── docker-compose.yml      # Multi-service orchestration
├── .env.example            # Environment template
├── gateway/
│   └── nginx.conf          # Reverse proxy config
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py         # FastAPI app
│       ├── auth.py         # Authentication
│       ├── llm.py          # LLM provider wrapper
│       ├── db.py           # Database connection
│       ├── models.py       # SQLAlchemy models
│       ├── schemas.py      # Pydantic schemas
│       └── settings.py     # Configuration
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── app/
│       ├── page.tsx        # Main page
│       └── components/
│           ├── Chat.tsx    # Chat interface
│           └── Login.tsx   # Login form
└── db/
    └── init.sql            # DB initialization
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/login | Login and get JWT |
| POST | /api/chat | Send prompt to LLM |
| GET | /api/healthz | Health check |

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| POSTGRES_USER | Database user | Yes |
| POSTGRES_PASSWORD | Database password | Yes |
| POSTGRES_DB | Database name | Yes |
| DATABASE_URL | Full connection string | Yes |
| JWT_SECRET | Secret for JWT signing | Yes |
| JWT_EXPIRE_MINUTES | Token expiration | Yes |
| LLM_PROVIDER | openai or azure_openai | Yes |
| OPENAI_API_KEY | OpenAI API key | If using OpenAI |
| OPENAI_MODEL | Model to use | Yes |

## Development Status

- [x] Task 1: Project scaffolding
- [ ] Task 2: Backend MVP (auth + chat endpoints)
- [ ] Task 3: Frontend MVP (login + chat UI)
- [ ] Task 4: Testing & validation
- [ ] Task 5: Hardening (rate limiting, PII guard)

## Troubleshooting

- **Port 8080 in use**: Change gateway port in docker-compose.yml
- **DB connection refused**: Wait for healthcheck or add retry logic
- **Slow on Windows**: Use WSL2 with repo in Linux filesystem
