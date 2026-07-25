# MI Logistics — Django REST API Backend

Full Django 4.2 + DRF + MySQL backend for the MI Logistics admin dashboard.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2 LTS |
| REST API | Django REST Framework 3.17 |
| Auth | JWT via djangorestframework-simplejwt |
| Database | MySQL (via mysqlclient) |
| CORS | django-cors-headers |
| Filtering | django-filter |
| Config | python-decouple (.env) |

---

## Project Structure

```
mi-logistics-backend/
├── authentication/          # Custom User model, JWT login, /me/, change-password
│   ├── models.py            # User (email login, role field)
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── core/                    # Business models and API
│   ├── models.py            # Customer, Staff, Shipment, TrackingEvent, Notification
│   ├── serializers.py       # List + Detail serializers, public tracking serializer
│   ├── views.py             # ViewSets + DashboardStatsView + PublicTrackingView
│   ├── urls.py
│   ├── admin.py
│   └── management/
│       └── commands/
│           └── seed_data.py # python manage.py seed_data
├── milogistics_backend/
│   ├── settings.py
│   └── urls.py
├── .env.example             # Copy to .env and fill in your values
├── requirements.txt
└── README.md
```

---

## Setup (Step by Step)

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

> On Windows you may need to install the MySQL C connector first:
> `pip install mysqlclient` requires MySQL to be installed and on PATH.
> If `mysqlclient` fails to install, set `USE_MYSQL=False` in your `.env`
> to use SQLite while you sort it out.

### 2. Create the MySQL database

Open MySQL Workbench or your terminal:

```sql
CREATE DATABASE milogistics_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Configure .env

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
SECRET_KEY=your-random-secret-key-here
DEBUG=True
USE_MYSQL=True

DB_NAME=milogistics_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Seed sample data

```bash
python manage.py seed_data
```

This creates:
- **Superuser**: `admin@milogistics.in` / `admin123`
- 10 customers (Chennai, Coimbatore, Mumbai, Madurai, etc.)
- 6 staff members (Delivery Manager, Drivers, Warehouse, Support)
- 10 shipments with various statuses (pending, in-transit, delivered, cancelled)
- Tracking events for MIL-2024-001 and MIL-2024-002
- 5 sample notifications

To reset and re-seed:

```bash
python manage.py seed_data --flush
```

### 6. Start the dev server

```bash
python manage.py runserver
```

Backend runs at **http://localhost:8000**

---

## API Endpoints

### Auth

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/auth/login/` | Login → returns `access`, `refresh`, `user` |
| POST | `/api/auth/refresh/` | Refresh access token |
| GET | `/api/auth/me/` | Current user profile (🔒) |
| PATCH | `/api/auth/me/` | Update own profile (🔒) |
| POST | `/api/auth/change-password/` | Change password (🔒) |

### Shipments (🔒 all require JWT)

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/shipments/` | List with filter/search/pagination |
| POST | `/api/shipments/` | Create new shipment |
| GET | `/api/shipments/{code}/` | Detail by shipment code (SHP001) |
| PATCH | `/api/shipments/{code}/` | Update shipment |
| DELETE | `/api/shipments/{code}/` | Delete shipment |
| GET | `/api/shipments/by-tracking-number/{tn}/` | Lookup by tracking number |
| POST | `/api/shipments/{code}/add_event/` | Append a tracking event |

### Customers (🔒)

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/customers/` | List with filter/search |
| POST | `/api/customers/` | Create customer |
| GET | `/api/customers/{code}/` | Detail (C001) |
| PATCH | `/api/customers/{code}/` | Update |
| DELETE | `/api/customers/{code}/` | Delete |

### Staff (🔒)

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/staff/` | List |
| POST | `/api/staff/` | Create |
| GET | `/api/staff/{code}/` | Detail (ST001) |
| PATCH | `/api/staff/{code}/` | Update |
| DELETE | `/api/staff/{code}/` | Delete |

### Other

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/api/dashboard/stats/` | 🔒 | Aggregate stat cards for dashboard |
| GET | `/api/track/{tracking_number}/` | Public | Customer-facing parcel tracker |
| GET | `/api/notifications/` | 🔒 | List notifications |
| POST | `/api/notifications/{id}/mark_read/` | 🔒 | Mark notification as read |

### Filtering & Search

Shipments: `?status=pending`, `?priority=express`, `?search=Chennai`
Customers: `?status=active`, `?city=Chennai`, `?search=Arjun`
Staff: `?department=Delivery`, `?status=active`, `?search=Ramesh`
Pagination: `?page=2&page_size=20`

---

## User Roles

| Role value | Display label | Django `is_staff` |
|---|---|---|
| `super_admin` | Super Admin | Yes |
| `admin` | Admin | No |
| `dispatch_manager` | Dispatch Manager | No |
| `staff` | Staff | No |

Create additional users via Django admin at `/admin/` or the API.

---

## Django Admin

Available at **http://localhost:8000/admin/**

Login with `admin@milogistics.in` / `admin123` after running `seed_data`.

---

## Notes

- `Shipment.code` (e.g. `SHP001`) is the URL lookup key for the admin API.
  `Shipment.tracking_number` (e.g. `MIL-2024-001`) is what customers see.
- Staff `deliveries` count reflects actual shipments in the database marked
  as delivered and assigned to that staff member — it will be low with just
  the seed data (10 shipments total).
- The monthly revenue chart on the Reports/Dashboard page uses static
  placeholder data from the frontend (`sampleData.js`) — historical
  reporting endpoints are not included in this version.
