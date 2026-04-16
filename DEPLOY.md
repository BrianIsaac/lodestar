# Deployment

Lodestar is deployed on **Alibaba Cloud ECS** (Ubuntu 22.04) using Docker Compose, with **Alibaba DashScope** (`qwen-plus`) as the LLM provider.

## Live instance

- **Frontend:** <http://43.98.179.20:3000>
- **Backend API:** <http://43.98.179.20:8000>

## Infrastructure

- **Host:** Alibaba Cloud ECS, Ubuntu 22.04, Docker Engine 29.4.0 (includes `docker compose`)
- **Open ports:** 22 (SSH), 3000 (frontend), 8000 (backend)
- **LLM:** Alibaba DashScope International (`https://dashscope-intl.aliyuncs.com/compatible-mode/v1`) using `qwen-plus`

## First-time deploy

```bash
ssh root@43.98.179.20   # password: ask admin

git clone https://github.com/BrianIsaac/lodestar.git
cd lodestar

cat > .env << 'EOF'
COACH_LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
COACH_LLM_MODEL=qwen-plus
COACH_LLM_API_KEY=<ask-admin-for-key>
EOF

docker compose build --build-arg NEXT_PUBLIC_API_URL=http://43.98.179.20:8000 frontend
docker compose up --build -d
```

## Update after code changes

```bash
ssh root@43.98.179.20
cd lodestar
git pull
docker compose build --build-arg NEXT_PUBLIC_API_URL=http://43.98.179.20:8000 frontend
docker compose up --build -d
```

## LLM configuration

Lodestar reads LLM settings from environment variables (prefix `COACH_`). See [`.env.example`](.env.example) for the template.

**Alibaba DashScope (production):**

```
COACH_LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
COACH_LLM_MODEL=qwen-plus
COACH_LLM_API_KEY=<your-key>
```

Verify a DashScope key:

```bash
curl -s $COACH_LLM_BASE_URL/chat/completions \
  -H "Authorization: Bearer $COACH_LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-plus","messages":[{"role":"user","content":"hello"}]}'
```

**Local Ollama (development):**

```
COACH_LLM_BASE_URL=http://localhost:11434/v1
COACH_LLM_MODEL=qwen3:14b
COACH_LLM_API_KEY=not-needed
```

## Operations

```bash
docker compose logs -f          # follow all logs
docker compose logs backend     # backend only
docker compose logs frontend    # frontend only
docker compose down             # stop everything
docker compose restart backend  # restart one service
```

## Security notes

- Never commit `.env` — it is gitignored. Create it directly on the server.
- Rotate the DashScope API key via the Alibaba Cloud console.
- SSH password should be rotated to key-based auth for anything beyond the PoC.
