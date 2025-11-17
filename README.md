# Savannah Coffee — Full-Stack Django Café Backend  
**From the golden African savannah to Canada’s winter streets — one perfect cup at a time**

```
   ███████╗ █████╗ ██╗   ██╗ █████╗ ███╗   ██╗███╗   ██╗ █████╗ ██╗  ██╗
   ██╔════╝██╔══██╗██║   ██║██╔══██╗████╗  ██║████╗  ██║██╔══██╗██║  ██║
   ███████╗███████║██║   ██║███████║██╔██╗ ██║██╔██╗ ██║███████║███████║
   ╚════██║██╔══██║╚██╗ ██╔╝██╔══██║██║╚██╗██║██║╚██╗██║██╔══██║██╔══██║
   ███████║██║  ██║ ╚████╔╝ ██║  ██║██║ ╚████║██║ ╚████║██║  ██║██║  ██║
   ╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝
                Where African coffee meets Canadian warmth
```

Live • Production-Ready • November 17, 2025  
GitHub: https://github.com/yourname/savannah-coffee

### The Savannah Vision
Coffee was born under the African sun on the vast savannah.  
Today it warms hands through Canadian winters.  
This backend connects both worlds — with love, oat milk, and perfect code.

### Live Endpoints (ready right now)
Base URL: `https://yourdomain.com/api/`

| Method | Endpoint                            | Purpose                                  |
|-------|-------------------------------------|------------------------------------------|
| POST  | `/auth/register/`                   | Join the Savannah family                 |
| POST  | `/auth/login/`                      | Login → fresh JWT                        |
| GET   | `/auth/me/`                         | Your profile + loyalty points            |
| GET   | `/products/`                        | Full menu (single-origin + merch)        |
| POST  | `/orders/`                          | Guest or logged-in ordering              |
| GET   | `/orders/active/`                   | Real-time barista iPad dashboard         |
| PATCH | `/orders/20251117-0001/status/`     | Barista marks Ready → Completed          |

### Features That Actually Matter
- Guest checkout (no account needed)  
- Loyalty points built-in (10 = 1 free)  
- Barista / Manager / Owner roles  
- Atomic order numbers: `20251117-0042` (never duplicates)  
- Real-time `/orders/active/` with late-order alerts  
- Google one-tap login  
- Historical pricing (price changes don’t break old orders)  
- Out-of-stock protection  
- Ready for Toronto winters and Nairobi summers

### Tech Stack — African Roots + Canadian Reliability
- Django 5.2 + Django REST Framework  
- PostgreSQL (production-ready)  
- JWT + Google OAuth2  
- Whitenoise + mobile-ready CORS  
- Deployable in 5 minutes (Render, Railway, Fly.io, or your own server)

### Run Locally in 30 Seconds
```bash
git clone https://github.com/yourname/savannah-coffee.git
cd savannah-coffee
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser   # becomes Owner
python manage.py runserver
```

Visit → http://127.0.0.1:8000/api/orders/active/  
Your barista screen is live instantly.

### Production Ready
- `.env` based secrets (never committed)  
- Whitenoise static serving  
- Secure headers (HSTS, etc.)  
- JWT blacklist enabled  
- Canada-compliant time zone (`America/Toronto`)

### From the Savannah With Love
Every line of code carries respect for the farmers who grow coffee under the African sun…  
and gratitude for the baristas who serve it with a smile through Canadian snow.

Karibu. Welcome. Bienvenue.

Made with single-origin beans, oat milk, and pure passion  
Toronto & the African Savannah — November 17, 2025

**Savannah Coffee. Where coffee finds home.**
