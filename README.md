# ShopEase

ShopEase is a small multi-user e-commerce application. Users sign up, log in and manage their own products. Products can be shared in groups where every member has different permissions. Admins manage users, content and security from an admin dashboard.

CSE309 Final Project, Autumn 2026. Author: Ebrahim Sarwar, ID 2331040, section 06.

## Live links

- Frontend: https://shopease-brown-eight.vercel.app/
- API docs (Swagger): https://shopease-brown-eight.vercel.app/api/docs
- API base: https://shopease-brown-eight.vercel.app/api/v1

The app is deployed from the `main` branch on Vercel. The database is hosted on Supabase (PostgreSQL), so data persists.

## Tech stack

- Frontend: React + TypeScript (Vite)
- Backend: FastAPI (Python), SQLModel
- Database: Supabase PostgreSQL (SQLite for local development)
- Auth: JWT access tokens (PyJWT), passwords hashed with argon2 plus a server-side pepper
- Hosting: Vercel (frontend and backend)

## Test accounts for the instructor

The passwords are not in this file. They are in the submission form and in the PDF report.

| Username | Role | Email |
|---|---|---|
| `admin1` | admin | admin1@shopease.example |
| `admin2` | admin | admin2@shopease.example |
| `user1` | user | user1@shopease.example |
| `user2` | user | user2@shopease.example |
| `user3` | user | user3@shopease.example |

All demo accounts use demo data only.

### Sample data

- Each of `user1`, `user2` and `user3` owns two sample products.
- The products from the mid project are owned by `admin1`.

### Shared group with mixed permissions

Group **Demo Team**, owner `user1`.

| Member | create | edit | assign |
|---|---|---|---|
| `user1` (owner) | yes | yes | yes (and delete, rename, manage members) |
| `user2` | yes | yes | no |
| `user3` | no | no | yes |

Only the owner can delete the group or its products, rename the group and manage members.

## What is implemented

- Signup, login, logout, profile update and password change (current password required).
- Short-lived JWT access token (15 minutes) with the user id and role. Missing, invalid, tampered or expired tokens return 401.
- A banned user is rejected on the very next request (403).
- Brute-force protection: 5 failed logins for one username in 15 minutes lock that username for the rest of the window (429).
- Role based access control in one module (`backend/features/auth/rbac.py`), enforced on the server.
- Ownership rules: a normal user reads, changes and deletes only their own products (other users' products return 403).
- Groups with per-member permissions (create, edit, assign).
- Safety rules: an admin cannot change their own role, ban themselves or ban another admin.
- Admin dashboard: overview statistics, security view (failed logins by IP and account), users (search, filters, pagination, ban and unban with reason, role change, bulk ban and unban), product and group moderation (delete one or many), activity log (with IP address and browser) and CSV exports of users, products and activity.
- Frontend: login and signup pages, session restore without a guest flash, route guards, role based menu, logout and automatic logout when the server rejects the token.

## Not implemented

See section 6 of `docs/FINAL_REPORT.md`. In short: refresh tokens and session list or revoke, server-side token revocation before expiry, and automated pytest tests.

## Project structure

```
backend/
  main.py                  FastAPI app, error handler, startup
  core/                    config, database, errors, security (JWT, argon2)
  features/
    auth/                  signup, login, profile, RBAC module, seed data
    products/              product CRUD with ownership rules
    groups/                groups, members, group products
    admin/                 admin dashboard endpoints and CSV export
    audit/                 activity log
frontend/
  src/                     React app (pages, components, api.ts)
docs/FINAL_REPORT.md       PRD, SRS and TDD of the finished work
```

Each feature has the same layers: `router.py` (HTTP), `service.py` (rules), `repository.py` (database queries).

## Run locally

Backend (from the repository root):

```
cd backend
pip install -r requirements.txt
cp .env.example .env        # then set your own values
uvicorn main:app --reload
```

Frontend:

```
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

## Environment variables

Real values are never committed. Only `backend/.env.example` is in the repository. On Vercel they are set as project environment variables.

| Name | Purpose |
|---|---|
| `DATABASE_URL` | Supabase PostgreSQL connection string (empty means local SQLite) |
| `JWT_SECRET` | signs and verifies access tokens |
| `PASSWORD_PEPPER` | secret mixed into passwords before hashing |
| `ACCESS_TOKEN_MINUTES` | access token lifetime (default 15) |
| `SEED_PASSWORD` | password for the demo accounts (accounts are only created when it is set) |
