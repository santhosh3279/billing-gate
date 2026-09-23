# Chettiyar Kada Billing — 2FA Landing Gate

A high-performance, lightweight **Two-Factor Authentication (2FA) Reverse-Proxy Access Gate** with **Google Authenticator (RFC 6238 TOTP)**, Username & Password authentication, dynamic QR code enrollment, brute-force protection, and seamless **Nginx `auth_request`** integration.

Designed specifically to protect internal ERPNext / Frappe billing and POS systems while keeping public customer pages (such as `/frontend/catalogueviewer`) accessible without authentication.

---

## Architecture Overview

```
                      +---------------------------------------+
                      |   Client Browser / Smartphone         |
                      +---------------------------------------+
                                          |
                                          | (HTTPS :443)
                                          v
                      +---------------------------------------+
                      |      Nginx Reverse Proxy              |
                      +---------------------------------------+
                                   |              |
         Public Routes             |              |  Protected Routes
    (/frontend/catalogueviewer,    |              |  (/, /app, /desk,
     /assets/, /files/, etc.)      |              |   /cashier, etc.)
                                   |              v
                                   |       auth_request /_gate/verify
                                   |              |
                                   |              v
                                   |     +-------------------------+
                                   |     | 2FA Auth Gate (:3100)   |
                                   |     | (Node.js Service)       |
                                   |     | - Google Authenticator  |
                                   |     | - Username & Password   |
                                   |     | - Signed HMAC Cookies   |
                                   |     | - Rate Limiter Guard    |
                                   |     +-------------------------+
                                   |              |
                                   |              | 200 OK (Authenticated)
                                   v              v
                      +---------------------------------------+
                      |   ERPNext / Frappe Billing VM         |
                      |   (http://192.168.225.135)            |
                      +---------------------------------------+
```

---

## Features

- **Google Authenticator 2FA (RFC 6238)**: Standard Time-based One-Time Passwords compatible with Google Authenticator, Microsoft Authenticator, Apple Passwords, and Authy (with ±30s clock drift tolerance).
- **Dual-Mode Modern Landing UI**: Clean dark theme inspired by Chettiyar Kada branding with **Sign In** and **Enroll 2FA** tabs.
- **On-Screen QR Code Enrollment**: Generates standard `otpauth://` QR codes on the fly with copyable secret keys for easy pairing.
- **Terminal Management CLI (`cli.js`)**: Add, list, reset, or remove staff accounts directly from the server terminal with terminal ASCII QR codes.
- **Defense-in-Depth Security**:
  - Passwords hashed using salted `scrypt`.
  - Cryptographically signed HMAC-SHA256 session cookies (`HttpOnly; Secure; SameSite=Lax`).
  - Brute-force protection: automatic IP-based lockout after 5 failed attempts for 15 minutes.
  - Constant-time comparison preventing timing attacks.
- **Selective Public Exemptions**: Supports public customer-facing routes (`/frontend/catalogueviewer`, `/files/`, `/assets/`) without prompting for staff authentication.
- **One-Click Logout**: Revokes gate session tokens via `/gate/logout`.
- **Web Admin Control Center (`/gate/admin`)**: Complete browser-based management dashboard for managing Nginx sites (edit configs, toggle enable/disable, syntax check, safe reload) and managing staff 2FA users (add, reset TOTP with instant QR codes, change passwords, roles).

---

## Repository Structure

```
billing-gate/
├── Dockerfile                     # Production multi-stage Alpine container image
├── docker-compose.yml             # Production Docker Compose orchestration
├── docker-entrypoint.sh           # Safe privilege-drop & permission initialization
├── gate-cli.sh                    # Helper script for containerized CLI management
├── .dockerignore                  # Docker build context exclusions
├── .env.example                   # Environment configuration template
├── cli.js                         # Staff management command-line tool
├── server.js                      # Core HTTP authentication service
├── generate_pdf.py                # PDF documentation generator (ReportLab)
├── package.json                   # Node.js project & dependencies
├── lib/
│   ├── auth.js                    # Password hashing, token signing & rate limiting
│   ├── db.js                      # Atomic user storage, role & secret management
│   ├── nginx.js                   # Nginx sites parser, syntax tester & reload controller
│   └── totp.js                    # RFC 6238 TOTP calculations & QR code generation
├── nginx/
│   └── billing.chettiyarkada.in.conf # Production Nginx reverse-proxy configuration
├── public/
│   ├── favicon.svg                # Portal favicon
│   └── logo.png                   # Official Chettiyar Kada brand logo
├── systemd/
│   ├── billing-gate-docker.service# Systemd service for Docker Compose mode
│   └── billing-gate.service       # Systemd service for bare-metal Node.js
└── views/
    ├── admin.html                 # Complete Nginx & User Management Control Center
    └── index.html                 # Responsive 2FA landing page template
```

---

## Production Docker Deployment (Recommended)

### 1. Prerequisites
- Docker (>= 20.10) & Docker Compose (v2 or `docker compose`)
- Nginx reverse proxy on the host (with `auth_request` support)

### 2. Configure Environment
Copy the example environment file:
```bash
cd /var/www/billing-gate
cp .env.example .env
```
Default settings in `.env`:
```env
BIND_IP=0.0.0.0
PORT=3100
DATA_DIR_PATH=/var/lib/billing-gate
```
*Note: Pointing `DATA_DIR_PATH` to `/var/lib/billing-gate` preserves existing production accounts and signing keys without re-enrollment.*

### 3. Build & Start the Container
```bash
docker compose up -d --build
```
Verify the container is healthy:
```bash
docker compose ps
curl http://127.0.0.1:3100/gate/health
# {"status":"ok","timestamp":"..."}
```

### 4. Enable Systemd Auto-Start for Docker (Optional)
To manage the Docker Compose service via `systemctl`:
```bash
sudo cp systemd/billing-gate-docker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable billing-gate-docker.service
```

---

## Web Admin Control Center (`/gate/admin`)

Access the management dashboard in your browser:
**`https://billing.chettiyarkada.in/gate/admin`**

*(Requires login with an administrator account)*

### Key Capabilities

1. **Nginx Reverse-Proxy Management**:
   - **Live Daemon Monitoring**: Real-time status of Nginx daemon PID, version, and active syntax test.
   - **Sites Overview**: Inspect domain names (`server_name`), listen ports, SSL encryption, and 2FA protection flags across all sites in `/etc/nginx/sites-available`.
   - **Interactive Switch Toggle**: One-click enable/disable sites (automatically creates/removes symlinks in `/etc/nginx/sites-enabled` with syntax testing).
   - **In-Browser Configuration Editor**: Edit site configurations with syntax highlighting, automatic timestamped backups, and safe rollback if `nginx -t` fails.
   - **Create New Sites**: Start from predefined templates:
     - *Reverse Proxy with 2FA Gate Protection*
     - *Standard Reverse Proxy*
     - *Static Website*
   - **Global Nginx Actions**: One-click **Test Syntax (`nginx -t`)** and zero-downtime **Reload Daemon (`systemctl reload nginx`)**.

2. **Staff & 2FA User Management**:
   - View all registered staff accounts, roles (`Administrator` or `Staff`), enrollment status, and last login timestamps.
   - **Add Staff User**: Form with instant on-screen Google Authenticator QR Code and copyable secret key.
   - **Reset 2FA / Re-pair**: Re-generate TOTP secrets with instant QR display for staff onboarding.
   - **Change Passwords**: Securely re-hash passwords with `scrypt`.
   - **Delete Users**: Safe removal preventing self-deletion or leaving zero administrators.

3. **Security & Brute-Force Monitoring**:
   - Real-time display of IP addresses flagged or locked out by the rate limiter guard.
   - One-click manual **Unblock IP** button.

---

## Staff Account Management (CLI)

Use the `./gate-cli.sh` helper to run commands directly inside the Docker container:

| Action | Docker Command | Bare-Metal Command |
|---|---|---|
| **Add Staff User** | `./gate-cli.sh add-user <username> <password>` | `node cli.js add-user <username> <password>` |
| **List All Users** | `./gate-cli.sh list-users` | `node cli.js list-users` |
| **Reset 2FA / Re-pair** | `./gate-cli.sh reset-totp <username>` | `node cli.js reset-totp <username>` |
| **Update Password** | `./gate-cli.sh set-password <username> <new-password>` | `node cli.js set-password <username> <new-password>` |
| **Delete User** | `./gate-cli.sh delete-user <username>` | `node cli.js delete-user <username>` |

*(Alternatively, you can run `docker compose exec billing-gate node cli.js <command>`)*

---

## Switching From Bare-Metal (Systemd) to Docker

If you currently have `billing-gate.service` running directly on the host and wish to switch to Docker:

1. Stop and disable the bare-metal service:
   ```bash
   sudo systemctl stop billing-gate.service
   sudo systemctl disable billing-gate.service
   ```
2. Start the Docker container:
   ```bash
   docker compose up -d
   ```
3. Test authentication at `https://billing.chettiyarkada.in/gate/login`.

Host Nginx requires zero changes because the Docker container binds to port 3100 (`0.0.0.0:3100:3100`), matching the existing reverse proxy configuration.

---

## Alternative: Bare-Metal Installation (Node.js & Systemd)

1. **Install Dependencies**:
   ```bash
   npm install --omit=dev
   ```
2. **Setup First Administrator**:
   ```bash
   node cli.js add-user admin "YourSecurePassword123!"
   ```
3. **Start Systemd Service**:
   ```bash
   sudo cp systemd/billing-gate.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now billing-gate.service
   ```

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `BIND_IP` | `0.0.0.0` | Host IP interface binding in `docker-compose.yml` (`0.0.0.0` for all interfaces) |
| `PORT` | `3100` | Port for the local auth gate server |
| `HOST` | `0.0.0.0` (Docker) / `127.0.0.1` (Host) | Binding IP address |
| `DATA_DIR` | `/var/lib/billing-gate` | Path inside container/host to persistent storage (`users.json`, `secret.key`) |
| `DATA_DIR_PATH` | `/var/lib/billing-gate` | Host volume mount path in `docker-compose.yml` |
| `NODE_ENV` | `production` | Node runtime environment |

---

## License

Proprietary &bull; Internal staff software for Chettiyar Kada, Palakkad.
