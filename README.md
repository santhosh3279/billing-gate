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

---

## Repository Structure

```
billing-gate/
├── cli.js                         # Staff management command-line tool
├── server.js                      # Core HTTP authentication service
├── generate_pdf.py                # PDF documentation generator (ReportLab)
├── package.json                   # Node.js project & dependencies
├── lib/
│   ├── auth.js                    # Password hashing, token signing & rate limiting
│   ├── db.js                      # Atomic user storage & secret management
│   └── totp.js                    # RFC 6238 TOTP calculations & QR code generation
├── nginx/
│   └── billing.chettiyarkada.in.conf # Production Nginx reverse-proxy configuration
├── public/
│   ├── favicon.svg                # Portal favicon
│   └── logo.png                   # Official Chettiyar Kada brand logo
├── systemd/
│   └── billing-gate.service       # Systemd service unit definition
└── views/
    └── index.html                 # Responsive 2FA landing page template
```

---

## Quick Start & Installation

### 1. Prerequisites
- Node.js >= 18
- Nginx (compiled with `--with-http_auth_request_module`)

### 2. Install Dependencies
```bash
cd /var/www/billing-gate
npm install
```

### 3. Create First Administrator Account
Use the CLI to create an administrator and print the Google Authenticator QR code:
```bash
node cli.js add-user admin "YourSecurePassword123!"
```
*Scan the generated QR code in your Google Authenticator app.*

### 4. Enable and Start the Systemd Service
```bash
sudo cp systemd/billing-gate.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable billing-gate.service
sudo systemctl start billing-gate.service
sudo systemctl status billing-gate.service
```

### 5. Configure Nginx
Copy or merge the Nginx configuration:
```bash
sudo cp nginx/billing.chettiyarkada.in.conf /etc/nginx/sites-available/billing.chettiyarkada.in
sudo nginx -t
sudo systemctl reload nginx
```

---

## CLI Management Commands

All staff account management can be performed from the terminal:

| Action | Command |
|---|---|
| **Add Staff User** | `node cli.js add-user <username> <password>` |
| **List All Users** | `node cli.js list-users` |
| **Reset 2FA / Re-pair** | `node cli.js reset-totp <username>` |
| **Update Password** | `node cli.js set-password <username> <new-password>` |
| **Delete User** | `node cli.js delete-user <username>` |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `3100` | Port for the local auth gate server |
| `HOST` | `127.0.0.1` | Binding IP address |
| `DATA_DIR` | `/var/lib/billing-gate` | Path to persistent storage (`users.json`, `secret.key`) |
| `NODE_ENV` | `production` | Node runtime environment |

---

## License

Proprietary &bull; Internal staff software for Chettiyar Kada, Palakkad.
