FROM python:3.12-slim

ARG PSTACK_REF=v0.1.0
ARG GIT_TOKEN=

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# ดึง pstack ตาม tag ที่ pin — GIT_TOKEN จำเป็นเฉพาะตอน pstack ยังเป็น private repo
RUN if [ -n "$GIT_TOKEN" ]; then \
        CLONE_URL="https://oauth2:${GIT_TOKEN}@github.com/monthop-gmail/pstack.git"; \
    else \
        CLONE_URL="https://github.com/monthop-gmail/pstack.git"; \
    fi \
    && git clone --depth 1 --branch "${PSTACK_REF}" "$CLONE_URL" /app \
    && rm -rf /app/.git

WORKDIR /app
RUN pip install --no-cache-dir .

# addons ของ app นี้ (PSTACK_ADDONS_PATHS=addons,app_addons)
COPY app_addons /app/app_addons

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
