# Restaurant Ordering System (Django)

A table-based restaurant ordering website. Customers scan a table QR code, open the food menu, add items to their cart, and submit orders. Staff and kitchen use password-protected dashboards.

## Features

- Public customer menu and cart, with a separate URL for each table.
- Manual menu pricing controlled by the administrator.
- Staff and kitchen order dashboards with table-wise audio notification settings.
- Separate Admin Login and Kitchen Login buttons on the public landing page.
- Admin-only menu, notification, and payment configuration.
- Nepal NPR billing and Fonepay merchant QR display.

## Install and run

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Staff accounts and login

- **Admin:** use the Admin Login button. Admin-only pages require a Django superuser account. Create one with `python manage.py createsuperuser`.
- **Kitchen:** use the Kitchen Login button. Create a separate Django user in Django Admin and enable `is_staff` for that account.
- Admin menu/payment settings are not accessible to kitchen-only accounts. Both login forms require a username and password.

## Customer ordering and table QR

A table QR should open `/t/<table-token>/` or the direct menu URL `/table/1/menu/`. The QR URL must use the server's LAN/public IP or domain when scanned from a phone; `127.0.0.1` only works on the computer running the server. The customer menu does not show admin or kitchen controls.

## Configure Fonepay QR (Nepal)

1. Register the restaurant as a Fonepay merchant through your bank or Fonepay.
2. Download the official merchant QR image from the Fonepay merchant service.
3. Sign in using Admin Login.
4. Open `/manage/payment/` and upload the official Fonepay QR image. Enter the merchant display name and payment instructions, then save.
5. The bill page displays this official Fonepay QR and the exact amount in NPR. Customers enter the amount shown on the bill and pay using a supported Nepali banking or wallet app. Staff must verify the payment in the merchant/bank app before marking the bill paid.

**Important:** This version uses the restaurant's issued static Fonepay merchant QR image. It does not fabricate a QR code or claim automatic payment confirmation. A unique dynamic QR for every bill and automatic payment verification require Fonepay's separate Dynamic QR merchant integration and credentials. Contact Fonepay or your acquiring bank to request this access. Fonepay explains the difference between static and dynamic QR on its [business page](https://fonepay.com/public/business) and provides [merchant enrollment](https://fonepay.com/business/merchant-enrollment).

## Production notes

- Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, and `DJANGO_ALLOWED_HOSTS` before deployment.
- Use HTTPS and a production database such as PostgreSQL.
- Configure static and media file hosting for uploaded menu images, notification audio, and the Fonepay QR image.
- Install dependencies before running Django checks: `pip install -r requirements.txt`.
