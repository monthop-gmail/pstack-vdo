FROM python:3.12-slim

ARG PSTACK_REF=v0.1.0

RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ดึง pstack ตาม tag ที่ pin
RUN git clone --depth 1 --branch "${PSTACK_REF}" \
        https://github.com/monthop-gmail/pstack.git /app \
    && rm -rf /app/.git

WORKDIR /app
RUN pip install --no-cache-dir .

# addons ของ app นี้ (PSTACK_ADDONS_PATHS=addons,vdo_addons)
COPY vdo_addons /app/vdo_addons

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
