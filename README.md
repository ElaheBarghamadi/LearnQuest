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

## **مرحله 5: فایل .env**

فایل `.env` بساز و این رو بذار:

```env
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=True
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
# روش 1 - با runscript (پیشنهادی)
python manage.py runscript seed_airport_chapter

# روش 2 - با shell
python manage.py shell
>>> exec(open('seed_airport_chapter.py', encoding='utf-8').read())
>>> exit()

# روش 3 - با redirect
python manage.py shell < seed_airport_chapter.py
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
daphne -p 8000 learnquest.asgi:application
```

### **ترمینال ۲ - اجرای Celery (اختیاری):**
```bash
celery -A learnquest worker --loglevel=info --pool=solo
```

---

## **دسترسی به پروژه**

| بخش | آدرس |
|-----|------|
| پنل ادمین کلی | `http://127.0.0.1:8000/admin/` |
| پنل ادمین Academy | `http://127.0.0.1:8000/admin-panel/` |
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
python manage.py runscript seed_airport_chapter
python manage.py collectstatic
daphne -p 8000 learnquest.asgi:application
```