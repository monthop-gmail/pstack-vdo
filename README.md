# pstack app template

แม่แบบสำหรับสร้าง app ใหม่บนฐาน [pstack](https://github.com/monthop-gmail/pstack) —
app repo เก็บเฉพาะ addons ของตัวเอง แล้ว **pin pstack เป็น tag** (`PSTACK_REF`)

## เริ่ม app ใหม่

1. กด **Use this template** บน GitHub → ตั้งชื่อ repo เช่น `pstack-lms`
2. clone ลงเครื่อง แล้วเปลี่ยนชื่อโฟลเดอร์ addons ให้เป็นของ app ตัวเอง (ห้ามใช้ชื่อ `addons` เพราะชนกับของ pstack):

```bash
NEW=lms_addons   # ตั้งตามชื่อ app
git mv app_addons $NEW
grep -rl app_addons --exclude-dir=.git . | xargs sed -i "s/app_addons/$NEW/g"
```

3. เปลี่ยนชื่อโมดูลตัวอย่าง `demo` เป็นโมดูลจริงของคุณ (ดูวิธีเขียนโมดูลใน
   [MODULE_GUIDE](https://github.com/monthop-gmail/pstack/blob/main/docs/MODULE_GUIDE.md))
4. `cp .env.example .env` แล้วตั้งค่า

## Dev บนเครื่อง

ต้องมี pstack checkout ไว้ข้างๆ (pin tag เดียวกับ `PSTACK_REF` ใน .env.example):

```bash
git clone --branch v0.1.0 https://github.com/monthop-gmail/pstack.git ../pstack
python3 -m venv .venv && .venv/bin/pip install -e "../pstack[dev]"

export PSTACK_ADDONS_PATHS=../pstack/addons,app_addons
.venv/bin/uvicorn main:app --reload          # dev server
.venv/bin/python -m pytest tests/            # เทส (sqlite)
```

สร้าง migration ของโมดูล: `.venv/bin/python ../pstack/cli.py makemigration <module> -m "..."`
(รันจาก root ของ repo นี้ โดยตั้ง PSTACK_ADDONS_PATHS ตามด้านบน)

## Docker

```bash
docker compose up -d --build
```

Dockerfile จะ clone pstack ตาม `PSTACK_REF` ใน `.env` — ถ้า pstack ยังเป็น private repo
ให้ใส่ `GIT_TOKEN` (fine-grained PAT ที่อ่าน repo pstack ได้) ใน `.env` ด้วย

## CI

workflow จะ clone pstack ตาม `PSTACK_REF` ใน `.env.example` — สำหรับ private repo
ต้องเพิ่ม secret ชื่อ **`PSTACK_CLONE_TOKEN`** (PAT อ่าน pstack ได้) ใน Settings → Secrets

## กติกาสำคัญ

- **ห้ามแก้โค้ด pstack ใน repo นี้** — อยากได้อะไรจาก kernel ให้ไปทำฝั่ง pstack แล้วออก tag ใหม่
- อัปเกรด `PSTACK_REF` เป็นรอบๆ ใน PR เดียว อ่าน breaking changes จาก
  [CHANGELOG ของ pstack](https://github.com/monthop-gmail/pstack/blob/main/CHANGELOG.md) ก่อนเสมอ
- deploy บนเซิร์ฟเวอร์รวม: เปิด network `odoo-public` ใน docker-compose.yml เพื่ออยู่หลัง Caddy กลาง
