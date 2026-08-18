# 🚀 راهنمای اجرای پروژه LearnQuest

---

## **مرحله 1: اکسترکت فایل**
```bash
unzip learnquest.zip
cd learnquest
```

---

## **مرحله 2: نصب Python**

اگر Python نصب نیست: [python.org](https://www.python.org/downloads/)

```bash
python --version
```

---

## **مرحله 3: محیط مجازی**

```bash
python -m venv venv

# فعال کردن:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

---

## **مرحله 4: نصب پکیج‌ها**

```bash
pip install -r requirements.txt
```

---

## **مرحله 5: تنظیمات (اختیاری)**

پروژه به‌صورت پیش‌فرض با `DEBUG=True` و یک `SECRET_KEY` پیش‌فرض کار می‌کند و نیازی به فایل `.env` ندارد.
برای تغییر، متغیرهای محیطی را ست کنید (یا فایل `.env` بسازید و مقدارش را در ترمینال export کنید):

```bash
export DJANGO_SECRET_KEY=your-secret-key-here
```

---

## **مرحله 6: ساخت دیتابیس**

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## **مرحله 7: ساخت ادمین**

```bash
python manage.py createsuperuser
```

---

## **مرحله 8: اضافه کردن محتوا**

```bash
# روش 1 - اجرای اسکریپت کامل دیتا (پیشنهادی)
python seed_data.py

# روش 2 - دستور اختصاصی آکادمی
python manage.py init_worlds

# روش 3 - دیتای اقتصاد و فروشگاه
python manage.py seed_economy
python manage.py seed_shop

# روش 4 - مقالات نمونه بلاگ
python scripts/seed_blog.py
```

---

## **مرحله 9: جمع‌آوری استاتیک**

```bash
python manage.py collectstatic
```
`yes` رو بزن

---

## **مرحله 10: اجرا**

### **ترمینال ۱ - اجرا با WebSocket:**
```bash
daphne -p 8000 Config.asgi:application
```

### **ترمینال ۲ - اجرای Celery (اختیاری):**
```bash
celery -A Config worker --loglevel=info --pool=solo
```

---

## **دسترسی به پروژه**

| بخش | آدرس |
|-----|------|
| پنل ادمین کلی | `http://127.0.0.1:8000/admin/` |
| پنل ادمین Academy | `http://127.0.0.1:8000/academy/manage/` |
| صفحه اصلی | `http://127.0.0.1:8000/` |

---

## **خلاصه یک‌جا**

```bash
cd learnquest
python -m venv venv
venv\Scripts\activate  # یا source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python seed_data.py
python manage.py collectstatic
daphne -p 8000 Config.asgi:application
```