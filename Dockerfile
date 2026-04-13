# --- Backend stage ---
FROM python:3.11-slim AS backend

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev
COPY src/ src/

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "lodestar.api:app", "--host", "0.0.0.0", "--port", "8000"]

# --- Frontend stage ---
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:20-slim AS frontend

WORKDIR /app/frontend
COPY --from=frontend-build /app/frontend/.next .next
COPY --from=frontend-build /app/frontend/public public
COPY --from=frontend-build /app/frontend/package.json .
COPY --from=frontend-build /app/frontend/node_modules node_modules

EXPOSE 3000
CMD ["npm", "start"]
