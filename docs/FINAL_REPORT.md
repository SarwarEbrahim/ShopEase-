# ShopEase Final Report

Course CSE309, Autumn 2026. Student: Ebrahim Sarwar, ID 2331040, section 06.
Repository: https://github.com/SarwarEbrahim/ShopEase-
Live app: https://shopease-brown-eight.vercel.app/ , API docs: https://shopease-brown-eight.vercel.app/api/docs

This report describes the finished work, in three parts: PRD (what and why), SRS (what the system must do) and TDD (how it is built).

---

# Part 1. PRD (Product Requirements)

## 1.1 Problem

The mid project (ShopEase) let anybody create, change and delete products without logging in. A real shop needs to know who is acting, let people work only with their own data, let small teams share work, and give the owners of the system tools to control abuse.

## 1.2 Users

| User | Needs |
|---|---|
| Visitor | Create an account and log in. |
| User | Manage their own products, join groups, keep their profile and password safe. |
| Group member | Work on a shared group's products within the permissions the group owner gave. |
| Admin | See how the system is used, manage users, remove bad content, review activity and security. |

## 1.3 Goals

1. Secure login with JWT.
2. Server-enforced roles (user, admin), ownership and group permissions.
3. An admin dashboard for users, content, activity and security.
4. Everything live on Vercel with persistent data and demo accounts.

## 1.4 Scope

In scope: signup, login, logout, profile, password change, products with ownership, groups with member permissions, admin dashboard (statistics, users, moderation, activity log, security view, exports), brute-force lockout.

Out of scope (not built): refresh tokens and session management, email verification and password reset by email, payments and orders, automated test suite.

## 1.5 Success criteria

- A normal user cannot read or change another user's product, and cannot call an admin endpoint (403).
- A tampered or expired token is rejected (401).
- A banned user is blocked on the next request.
- A group member can do only what the owner allowed.
- The instructor can log in with the demo accounts on the live URL.

---

# Part 2. SRS (Software Requirements)

## 2.1 Functional requirements

### Authentication

| ID | Requirement |
|---|---|
| FR-A1 | A visitor can sign up with username (3 to 30 letters, digits or underscore), email, full name and a password of at least 8 characters with a letter and a digit. Username and email are unique. Everybody who signs up gets the role `user`. |
| FR-A2 | A user can log in with username and password and receives an access token that expires in 15 minutes. |
| FR-A3 | A wrong username and a wrong password give the same error (401), so a visitor cannot find out which usernames exist. |
| FR-A4 | After 5 failed logins for a username within 15 minutes, further logins for it are refused with 429 until the window passes. |
| FR-A5 | A banned user cannot log in (403) and any request with an old token is rejected (403). |
| FR-A6 | A logged-in user can read and update their profile (name, email) and change their password. Changing the password needs the current password. A wrong current password is recorded as a failed attempt. |
| FR-A7 | Logout is recorded in the activity log and the browser forgets the token. |

### Authorization (RBAC)

| ID | Requirement |
|---|---|
| FR-R1 | Every endpoint except signup and login needs a valid token. Missing, invalid, tampered or expired tokens return 401. |
| FR-R2 | Roles are `user` and `admin`, stored in the database and checked on the server on every request. |
| FR-R3 | A normal user lists, reads, changes and deletes only their own products. Another user's product returns 403. |
| FR-R4 | An admin can see and moderate all products and groups. |
| FR-R5 | An admin cannot change their own role, ban themselves or ban another admin. |
| FR-R6 | Admin endpoints return 403 to a normal user. |

### Groups

| ID | Requirement |
|---|---|
| FR-G1 | Any user can create a group and becomes its owner. |
| FR-G2 | The owner adds members by username and gives each member any of three permissions: create, edit, assign. |
| FR-G3 | A member with create can add products to the group. With edit can change them. With assign can assign a product to the owner or a member. |
| FR-G4 | Only the owner can rename or delete the group, delete group products and manage members. |
| FR-G5 | A user who is not in the group cannot see it (403). |

### Admin dashboard

| ID | Requirement |
|---|---|
| FR-D1 | Overview: users, banned users, admins, products, groups, new users and products in the last 7 days, failed logins in 24 hours. |
| FR-D2 | Users: search, filter by role and status, pagination, ban and unban with a reason, role change, bulk ban and unban. |
| FR-D3 | Moderation: list all products and groups, delete one or many products, delete a group. |
| FR-D4 | Activity log: login, failed login, blocked login, logout, password change (and failed attempts), profile update, role change, ban, unban, delete and export, each with user, IP address, browser and time. Filter by event and search. |
| FR-D5 | Security view: failed logins in the last 24 hours grouped by IP address and by account. |
| FR-D6 | CSV export of users, products and the activity log, using the same filters as the lists. |

## 2.2 Non-functional requirements

- **Security:** passwords are never stored in plain text (argon2 with a pepper). Secrets come from environment variables. Responses never include password hashes or stack traces.
- **Input validation:** every request body is validated (types, lengths, patterns). Invalid input returns 422 with the field and the reason.
- **Consistent errors:** every application error has the form `{"error_code": "...", "message": "..."}`.
- **Persistence:** data is stored in a hosted PostgreSQL database.
- **Usability:** responsive layout, loading, error and empty states.

## 2.3 Error codes

| HTTP | error_code | When |
|---|---|---|
| 400 | WRONG_PASSWORD | wrong current password on password change |
| 400 | PASSWORD_UNCHANGED | new password equals the current one |
| 400 | NOT_A_MEMBER | assigning to someone outside the group |
| 401 | NOT_AUTHENTICATED | no token |
| 401 | TOKEN_INVALID | malformed or tampered token |
| 401 | TOKEN_EXPIRED | token lifetime is over |
| 401 | INVALID_CREDENTIALS | wrong username or password |
| 403 | FORBIDDEN | not allowed (role or ownership) |
| 403 | USER_BANNED | account is banned |
| 403 | CANNOT_MODIFY_SELF | admin acts on own account |
| 403 | CANNOT_MODIFY_ADMIN | admin tries to ban an admin |
| 403 | NOT_GROUP_OWNER | owner-only group action |
| 403 | GROUP_PERMISSION_DENIED | member lacks the group permission |
| 404 | USER_NOT_FOUND, GROUP_NOT_FOUND, PRODUCT_NOT_FOUND | missing record |
| 409 | USERNAME_TAKEN, EMAIL_TAKEN, ALREADY_MEMBER | duplicate |
| 429 | TOO_MANY_ATTEMPTS | login lockout |

## 2.4 API summary (all under `/api/v1`)

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/signup`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`, `PATCH /auth/me`, `POST /auth/change-password` |
| Products | `GET /products`, `POST /products`, `GET /products/{id}`, `PUT /products/{id}`, `DELETE /products/{id}` |
| Groups | `GET /groups`, `POST /groups`, `GET /groups/{id}`, `PATCH /groups/{id}`, `DELETE /groups/{id}`, `POST /groups/{id}/members`, `PATCH /groups/{id}/members/{user_id}`, `DELETE /groups/{id}/members/{user_id}`, `GET` and `POST /groups/{id}/products`, `PUT` and `DELETE /groups/{id}/products/{product_id}`, `PUT /groups/{id}/products/{product_id}/assign` |
| Admin | `GET /admin/stats`, `GET /admin/users`, `GET /admin/users/{id}`, `POST /admin/users/{id}/ban`, `POST /admin/users/{id}/unban`, `PATCH /admin/users/{id}/role`, `POST /admin/users/bulk-ban`, `POST /admin/users/bulk-unban`, `GET /admin/products`, `DELETE /admin/products/{id}`, `POST /admin/products/bulk-delete`, `GET /admin/groups`, `DELETE /admin/groups/{id}`, `GET /admin/audit`, `GET /admin/security`, `GET /admin/export/users.csv`, `GET /admin/export/products.csv`, `GET /admin/export/audit.csv` |

---

# Part 3. TDD (Technical Design)

## 3.1 Architecture

```
Browser (React + TypeScript)
   |  fetch  /api/v1/...   Authorization: Bearer <access token>
   v
Vercel  --- /api/*  ---> FastAPI backend ---> Supabase PostgreSQL
        --- other  ---> React static files
```

The frontend and the API are served from the same Vercel domain, so the browser makes only same-origin requests and no cross-origin (CORS) access is opened.

Each backend feature is split into layers:

- `router.py`: HTTP only (parse request, call the service, return JSON).
- `service.py`: business rules, no HTTP and no SQL.
- `repository.py`: the only place that talks to the database.

## 3.2 Data model

| Table | Main columns |
|---|---|
| `users` | id, username (unique), email (unique), full_name, password_hash, role, is_banned, ban_reason, created_at, updated_at |
| `products` | id, name, description, price, stock, category, owner_id, group_id, assignee_id, created_at, updated_at |
| `groups` | id, name, owner_id, created_at, updated_at |
| `group_members` | id, group_id, user_id, can_create, can_edit, can_assign (unique on group_id and user_id) |
| `audit_logs` | id, event, user_id, username, ip_address, user_agent, detail, created_at |

New columns added to an existing table are added on startup by a small migration step in `core/database.py`.

## 3.3 Password storage

`password -> HMAC-SHA256 with the pepper -> argon2 hash -> users.password_hash`

- The pepper is a secret from the `PASSWORD_PEPPER` environment variable. It is not in the database, so a stolen database alone is not enough to guess passwords.
- Argon2 is deliberately slow and adds a random salt, so two identical passwords have different hashes.
- When the username does not exist, login still verifies against a dummy hash so the response time does not show which usernames exist.

## 3.4 JWT flow

1. **Create:** after a correct password, `create_access_token` signs a payload with `JWT_SECRET` (HS256): `sub` (user id), `role`, `iat`, `exp` (now + 15 minutes).
2. **Send:** the browser keeps the token and sends `Authorization: Bearer <token>` on every request.
3. **Verify:** `get_current_user` runs on every protected request. `decode_access_token` checks the signature, the allowed algorithm (only HS256) and the expiry (`exp` and `sub` are required). A bad signature or a malformed token gives `TOKEN_INVALID`, an old token gives `TOKEN_EXPIRED`, both 401.
4. **Load the user:** the user is read from the database by the id in `sub`. A missing user gives 401, a banned user 403. The role used for authorization is the one in the database, not the one in the token, so a role change or ban works on the next request.
5. **Expire:** after 15 minutes the token is rejected with 401 and the frontend returns the user to the login page.

The access token is stateless: the server does not store it. This is why its lifetime is short.

## 3.5 RBAC design

All rules live in `backend/features/auth/rbac.py` and `dependencies.py`:

- Role to permission map (`ROLE_PERMISSIONS`) and helpers `has_permission`, `can_access_record`, `ensure_can_access_record`.
- `AdminUser` dependency: an endpoint with `admin: AdminUser` is admin-only (403 for others).
- `CurrentUser` dependency: an endpoint with `user: CurrentUser` needs a valid token.
- Ownership rule: the owner of a record, or a user with permission to manage all records (admin).
- Group permissions: `group_permissions(owner_id, user_id, member)` returns what a user may do in a group. The owner gets all; a member gets the flags the owner set; anybody else gets nothing.

Group permission matrix:

| Action | Owner | Member with create | with edit | with assign | Other user |
|---|---|---|---|---|---|
| View group and products | yes | yes | yes | yes | no |
| Add product | yes | yes | no | no | no |
| Edit product | yes | no | yes | no | no |
| Assign product | yes | no | no | yes | no |
| Delete product | yes | no | no | no | no |
| Rename or delete group, manage members | yes | no | no | no | no |

Safety rules (`features/admin/service.py`): `check_can_ban` (not yourself, not an admin) and `check_can_change_role` (not yourself).

## 3.6 Activity log and brute-force protection

- `features/audit/service.py` writes one row per event with the client IP (from `X-Forwarded-For` on Vercel) and the browser (`User-Agent`).
- Login failures are counted per username in the last 15 minutes. At 5, `login` raises 429 before checking the password. Banned and locked attempts are logged as `login_blocked` and do not extend the lockout.

## 3.7 Frontend design

- `AuthContext` holds the user. On start, if a token is saved, it asks `/auth/me` before showing anything, so a logged-in user never sees a guest flash.
- `api.ts` adds the token to every request. When the server answers 401 to a request that had a token, it clears the token and the app shows the login page with "Your session has expired".
- The page is kept in the URL hash (`#/products`, `#/groups/3`, `#/admin`), so reloads and deep links work.
- Route guards and menus follow the server rules: guests see only login and signup, the Admin link is shown only to admins, and a normal user who opens `#/admin` sees a 403 message. The server enforces the same rules.

## 3.8 Deployment

- Vercel builds from the `main` branch. `vercel.json` sends `/api/*` to the FastAPI service and everything else to the Vite frontend.
- Environment variables on Vercel: `DATABASE_URL` (Supabase transaction pooler), `JWT_SECRET`, `PASSWORD_PEPPER`, `SEED_PASSWORD`. No secret is in the repository; only `backend/.env.example` is.
- On startup the backend creates the tables, applies the small column migration and, if `SEED_PASSWORD` is set, creates the demo accounts, sample products and the shared group once.

## 3.9 Testing done

Tested by hand on the live deployment (Swagger and the web app):

| Test | Result |
|---|---|
| Signup with valid data | 201, role `user`, no password in the response |
| Login with correct credentials | 200 with token |
| `GET /auth/me` with token | 200 |
| `GET /auth/me` without token | 401 NOT_AUTHENTICATED |
| Admin login (`admin1`) | 200, role `admin` |
| `GET /admin/users` as admin | 200, user list |
| `GET /admin/users` as normal user (`user1`) | 403 FORBIDDEN |
| Web app login, role menu, admin users page | works |

The logic of the ownership rule, group permission rule, safety rules, CSV escaping and the password rules was also checked with a small script during development.

## 3.10 Known limitations

- No refresh token, no session list and no server-side revoke. A stolen access token works until it expires (at most 15 minutes). Logout is recorded and the browser forgets the token, but the server cannot cancel a token before it expires. A banned user is still stopped, because the database is checked on every request.
- No automated pytest suite.
- The admin user detail endpoint exists, but the dashboard does not have a separate detail screen with the user's records, groups and sessions.
- Moderation can delete products and groups but has no "hide" state.
- The lockout is per username, so an attacker can lock a known username for 15 minutes.
