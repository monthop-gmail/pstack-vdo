# pstack-vdo

Video streaming server บนฐาน [pstack](https://github.com/monthop-gmail/pstack) (pin `PSTACK_REF=v0.1.0`)
— สร้างจาก [pstack-app-template](https://github.com/monthop-gmail/pstack-app-template)

## โมดูล `vdo`

- **อัปโหลดวิดีโอ** — `POST /api/vdo/videos` (ต่อยอดโมดูล `storage` ของ pstack)
- **Transcode เป็น HLS** ด้วย ffmpeg ผ่าน ARQ worker (งานหนัก CPU แยกโปรเซส):
  `uploaded → processing → ready | error`
- **เสิร์ฟ HLS** — dev: `/hls/{video_id}/index.m3u8`; production ให้ Caddy/nginx
  เสิร์ฟโฟลเดอร์ `hls/` ตรงๆ ไม่ผ่าน FastAPI
- **AI tools** — `search_videos` (สาธารณะ — ถามผ่าน LINE/MCP ได้),
  `video_pipeline_status` (ต้องมีสิทธิ์ `vdo.manage`)

## Dev บนเครื่อง

ต้องมี pstack checkout ไว้ข้างๆ (tag ตรงกับ `PSTACK_REF` ใน .env.example):

```bash
git clone --branch v0.1.0 https://github.com/monthop-gmail/pstack.git ../pstack
python3 -m venv .venv && .venv/bin/pip install -e "../pstack[dev]"

export PSTACK_ADDONS_PATHS=../pstack/addons,vdo_addons
.venv/bin/python -m pytest tests/            # เทส (sqlite ไม่ต้องมี DB/redis/ffmpeg)
.venv/bin/uvicorn main:app --reload          # dev server
```

สร้าง migration เมื่อแก้ models: `.venv/bin/python ../pstack/cli.py makemigration vdo -m "..."`

## Docker

```bash
cp .env.example .env    # ตั้ง PSTACK_REF และรหัสต่างๆ
docker compose up -d --build
```

image ติดตั้ง **ffmpeg** ให้แล้ว — worker เป็นคนรัน transcode
(ไม่มี worker/redis วิดีโอจะค้างสถานะ `uploaded`)

## CI

workflow จะ clone pstack ตาม `PSTACK_REF` ใน `.env.example` แล้วรันเทสอัตโนมัติ

## กติกา

- ห้ามแก้โค้ด pstack ใน repo นี้ — อยากได้อะไรจาก kernel ไปทำฝั่ง pstack แล้วออก tag ใหม่
- อัปเกรด `PSTACK_REF` เป็นรอบๆ ใน PR เดียว อ่าน
  [CHANGELOG ของ pstack](https://github.com/monthop-gmail/pstack/blob/main/CHANGELOG.md) ก่อน
