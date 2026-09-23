import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable, PageBreak
)
from reportlab.pdfgen import canvas
import shutil

CONVERSATION_ID = "94f2a5f4-25b7-4c88-a8ed-72f1a6293ee9"
PDF_PATH = f"/root/.gemini/antigravity-cli/brain/{CONVERSATION_ID}/Chettiyar_Kada_Billing_2FA_Docker_Admin_Guide.pdf"
PREV_PDF_PATH = "/root/.gemini/antigravity-cli/brain/3c9e9f79-1dd6-49ab-b7a4-7811610449a4/billing_chettiyarkada_2fa_guide.pdf"
WEB_PDF_PATH = "/var/www/billing-gate/public/Chettiyar_Kada_Billing_2FA_Guide.pdf"
LOGO_PATH = "/var/www/billing-gate/public/logo.png"
QR_PATH = f"/root/.gemini/antigravity-cli/brain/{CONVERSATION_ID}/admin_totp_qr.png"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, 11 * inch - 30, "Chettiyar Kada Billing — 2FA Gate, Docker & Nginx Admin Operations Guide")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, 11 * inch - 34, 8.5 * inch - 40, 11 * inch - 34)
            
        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(40, 36, 8.5 * inch - 40, 36)
        
        self.drawString(40, 24, "CONFIDENTIAL  •  INTERNAL CHETTIYAR KADA BILLING INFRASTRUCTURE")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 40, 24, page_text)
        self.restoreState()

def build_pdf():
    os.makedirs(os.path.dirname(PDF_PATH), exist_ok=True)

    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=44
    )

    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#0f172a")
    gold_color = colors.HexColor("#b45309")
    accent_bar_color = colors.HexColor("#d97706")
    text_dark = colors.HexColor("#1e293b")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=21,
        textColor=primary_color,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=gold_color,
        spaceAfter=8
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14.5,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=11.8,
        textColor=text_dark,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.8,
        leading=10,
        textColor=colors.HexColor("#0f172a")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=text_dark
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=11,
        textColor=colors.HexColor("#92400e")
    )

    story = []

    # =========================================================================
    # PAGE 1: Perimeter Architecture, Admin Credentials & Google Authenticator
    # =========================================================================

    logo_img = Image(LOGO_PATH, width=1.0 * inch, height=1.0 * inch)
    header_text = [
        Paragraph("CHETTIYAR KADA &bull; PALAKKAD", ParagraphStyle('Super', fontName='Helvetica-Bold', fontSize=8.5, textColor=accent_bar_color, leading=10.5)),
        Paragraph("Enterprise Billing Portal: 2FA & Infrastructure Guide", title_style),
        Paragraph("Multi-Factor Authentication (TOTP), Web Admin Control Center & Production Docker Deployment", subtitle_style),
        Paragraph("<b>Portal URL:</b> <font color='#0284c7'>https://billing.chettiyarkada.in</font> &nbsp;|&nbsp; <b>Admin URL:</b> <font color='#0284c7'>https://billing.chettiyarkada.in/gate/admin</font>", body_style)
    ]

    header_table = Table([[logo_img, header_text]], colWidths=[1.15 * inch, 5.85 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (1,0), (1,0), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_bar_color, spaceAfter=6))

    # Section 1: Overview & Architecture
    story.append(Paragraph("1. System Overview & Perimeter Security Architecture", h1_style))
    story.append(Paragraph(
        "To protect Chettiyar Kada's financial, invoicing, and POS infrastructure, an enterprise <b>Two-Factor Authentication (2FA) Reverse-Proxy Access Gate</b> "
        "is deployed for <b>https://billing.chettiyarkada.in</b>. Unauthenticated browsers attempting to access billing or administrative routes "
        "are intercepted at the Nginx edge and challenged for staff credentials and a synchronized <b>Google Authenticator (RFC 6238 TOTP)</b> 6-digit passcode "
        "before receiving access to the internal ERPNext application.<br/><br/>"
        "<b>Customer Exemption:</b> The product catalogue (<font color='#0284c7'>/frontend/catalogueviewer</font>), "
        "catalogue media (<font face='Courier'>/files/</font>), and frontend styling assets are kept completely public and excluded from 2FA so retail shoppers "
        "can browse store offers without barriers.",
        body_style
    ))

    # Section 2: Administrator Credentials
    story.append(Paragraph("2. Provisioned Administrator Credentials", h1_style))
    cred_data = [
        [Paragraph("Parameter", table_header_style), Paragraph("Configuration Details", table_header_style)],
        [Paragraph("<b>Portal Login</b>", table_cell_style), Paragraph("<font color='#0284c7'>https://billing.chettiyarkada.in</font> &rarr; <font face='Courier'>/gate/login</font>", table_cell_style)],
        [Paragraph("<b>Admin Control Center</b>", table_cell_style), Paragraph("<font color='#0284c7'>https://billing.chettiyarkada.in/gate/admin</font> (Requires Admin role)", table_cell_style)],
        [Paragraph("<b>Public Catalogue</b>", table_cell_style), Paragraph("<font color='#0284c7'>https://billing.chettiyarkada.in/frontend/catalogueviewer</font> (No 2FA required)", table_cell_style)],
        [Paragraph("<b>Initial Administrator</b>", table_cell_style), Paragraph("Username: <b>admin</b> &nbsp;|&nbsp; Role: <b>ADMIN</b>", table_cell_style)],
        [Paragraph("<b>Initial Password</b>", table_cell_style), Paragraph("<b>ChettiyarAdmin2026!</b>", table_cell_style)],
        [Paragraph("<b>TOTP Secret Key</b>", table_cell_style), Paragraph("<font face='Courier'>WG56VR7SCCFAI3TQUB2O5OKCCO6CXGWW</font> (RFC 6238 Base32)", table_cell_style)],
        [Paragraph("<b>Session Duration</b>", table_cell_style), Paragraph("12 Hours &bull; Signed HMAC-SHA256 Token (<font face='Courier'>HttpOnly; Secure; SameSite=Lax</font>)", table_cell_style)],
        [Paragraph("<b>Brute-Force Guard</b>", table_cell_style), Paragraph("Automatic IP lockout after 5 failed attempts for 15 minutes", table_cell_style)],
    ]
    cred_table = Table(cred_data, colWidths=[2.0 * inch, 5.0 * inch])
    cred_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8fafc"), colors.white]),
    ]))
    story.append(cred_table)
    story.append(Spacer(1, 6))

    # Section 3: Google Authenticator Pairing
    story.append(Paragraph("3. Google Authenticator Smartphone Pairing", h1_style))
    qr_img = Image(QR_PATH, width=1.5 * inch, height=1.5 * inch)
    instructions_text = [
        Paragraph("<b>Scan with Google Authenticator:</b>", ParagraphStyle('B1', fontName='Helvetica-Bold', fontSize=8.5, textColor=primary_color, leading=11)),
        Paragraph("1. Open the <b>Google Authenticator</b> app on your iOS or Android mobile phone.", body_style),
        Paragraph("2. Tap the <b>+</b> button (bottom-right) and select <b>Scan a QR code</b>.", body_style),
        Paragraph("3. Point your camera at the QR code displayed to the left to enroll.", body_style),
        Paragraph("4. <i>Manual Entry Key:</i> Enter account <b>Chettiyar Kada:admin</b>, Key: <b><font face='Courier'>WG56VR7SCCFAI3TQUB2O5OKCCO6CXGWW</font></b>, Type: <b>Time-based</b>.", body_style),
        Paragraph("5. The authenticator will generate a rolling 6-digit passcode refreshed every 30 seconds.", body_style),
    ]
    qr_table = Table([[qr_img, instructions_text]], colWidths=[1.7 * inch, 5.3 * inch])
    qr_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (1,0), (1,0), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(qr_table)
    story.append(Spacer(1, 4))

    callout_data = [[
        Paragraph(
            "<b>CONFIDENTIALITY NOTICE:</b> Anyone with access to this QR code and password can authenticate into the billing portal. "
            "Keep this document confidential and change default passwords immediately after initial setup.",
            callout_style
        )
    ]]
    callout_table = Table(callout_data, colWidths=[7.0 * inch])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef3c7")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#f59e0b")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(callout_table)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: Web Admin Control Center & Nginx Management
    # =========================================================================

    story.append(Paragraph("4. Web Admin Control Center (/gate/admin)", h1_style))
    story.append(Paragraph(
        "A dedicated, browser-based management dashboard is hosted at <b>https://billing.chettiyarkada.in/gate/admin</b>. "
        "It provides full administrative control over both the <b>reverse-proxy routing tier (Nginx)</b> and <b>staff authentication &amp; 2FA credentials</b> "
        "without requiring terminal or SSH access. Restricted exclusively to accounts with the <b>Administrator</b> role.",
        body_style
    ))

    admin_features_data = [
        [Paragraph("Feature Area", table_header_style), Paragraph("Capabilities & Operations", table_header_style), Paragraph("Safety / Safeguards", table_header_style)],
        [
            Paragraph("<b>🌐 Nginx Site Management</b>", table_cell_style),
            Paragraph("• List all configuration files in <font face='Courier'>/etc/nginx/sites-available</font><br/>"
                      "• Real-time Nginx daemon PID and running state indicator<br/>"
                      "• One-click toggle switch to Enable or Disable sites<br/>"
                      "• Parsed display of domains, listen ports, SSL, and 2FA status", table_cell_style),
            Paragraph("Symlinks in <font face='Courier'>sites-enabled</font> are tested automatically with <font face='Courier'>nginx -t</font> before applying.", table_cell_style)
        ],
        [
            Paragraph("<b>✏️ In-Browser Config Editor</b>", table_cell_style),
            Paragraph("• Full code editor with syntax indentation and monospace font<br/>"
                      "• Predefined site templates (2FA Reverse Proxy, Standard Proxy, Static Site)<br/>"
                      "• One-click <b>Test Syntax</b> button runs <font face='Courier'>nginx -t</font><br/>"
                      "• <b>Save &amp; Reload Nginx</b> applies changes without dropping active clients", table_cell_style),
            Paragraph("<b>Automatic Rollback:</b> If syntax validation fails, changes are reverted immediately from backup.", table_cell_style)
        ],
        [
            Paragraph("<b>👥 Staff &amp; 2FA Management</b>", table_cell_style),
            Paragraph("• Add new staff with role assignment (<b>Staff</b> vs <b>Administrator</b>)<br/>"
                      "• Instant on-screen Google Authenticator QR code with copyable secret<br/>"
                      "• Re-pair / Reset 2FA with new QR generation on mobile changes<br/>"
                      "• Update staff passwords with salted <font face='Courier'>scrypt</font> hashing", table_cell_style),
            Paragraph("Safeguards prevent administrators from deleting their own account or removing the last admin.", table_cell_style)
        ],
        [
            Paragraph("<b>🛡️ Brute-Force Monitoring</b>", table_cell_style),
            Paragraph("• Live monitor of rate-limited and locked-out client IPs<br/>"
                      "• Displays failed attempt counts and remaining lockout seconds<br/>"
                      "• One-click <b>Unblock IP</b> button to immediately restore access", table_cell_style),
            Paragraph("Configured with 5 max failed attempts and a 15-minute sliding lockout window.", table_cell_style)
        ],
    ]
    admin_features_table = Table(admin_features_data, colWidths=[1.8 * inch, 3.4 * inch, 1.8 * inch])
    admin_features_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8fafc"), colors.white]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(admin_features_table)
    story.append(Spacer(1, 8))

    # Section 5: Staff Workflow & Access Control
    story.append(Paragraph("5. Role-Based Access Control & Daily Staff Login Workflow", h1_style))
    story.append(Paragraph(
        "The access gate enforces strict Role-Based Access Control (RBAC):<br/>"
        "&bull; <b>Staff Role:</b> Authorized to authenticate into ERPNext / Frappe billing and POS interfaces. Access to <font face='Courier'>/gate/admin</font> is blocked with a 403 Forbidden page.<br/>"
        "&bull; <b>Administrator Role:</b> Full access to both the Billing Portal and the Gate &amp; Nginx Control Center.<br/><br/>"
        "<b>Staff Login Workflow:</b><br/>"
        "1. Open <b>https://billing.chettiyarkada.in</b> in any web browser (redirects automatically to <font face='Courier'>/gate/login</font>).<br/>"
        "2. Enter registered staff <b>Username</b> and <b>Password</b>.<br/>"
        "3. Open <b>Google Authenticator</b>, read the 6-digit rolling code, and submit the form.<br/>"
        "4. Upon verification, an encrypted HMAC cookie is issued and the user is redirected to the billing dashboard.<br/>"
        "5. To log out, navigate to <b>https://billing.chettiyarkada.in/gate/logout</b> to revoke session cookies.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: Production Docker Deployment & Container Operations
    # =========================================================================

    story.append(Paragraph("6. Production Docker Containerization & Deployment", h1_style))
    story.append(Paragraph(
        "For enterprise production deployment, <b>Billing Gate</b> is packaged as a high-security, lightweight <b>Docker container</b>. "
        "This containerizes the Node.js authentication service while seamlessly integrating with the host's existing Nginx reverse proxy.",
        body_style
    ))

    docker_arch_data = [
        [Paragraph("Architectural Component", table_header_style), Paragraph("Production Specification & Implementation Details", table_header_style)],
        [Paragraph("<b>Base Container Image</b>", table_cell_style), Paragraph("<b>Node.js 20 LTS on Alpine Linux</b> (<font face='Courier'>node:20-alpine</font>). Total image size is ~51 MB.", table_cell_style)],
        [Paragraph("<b>Security Hardening</b>", table_cell_style), Paragraph("Runs as an unprivileged non-root user (<font face='Courier'>node</font>, UID 1000). The entrypoint script verifies data permissions and drops privileges using <font face='Courier'>su-exec</font>.", table_cell_style)],
        [Paragraph("<b>Network Isolation</b>", table_cell_style), Paragraph("Port binding: <font face='Courier'>127.0.0.1:3100:3100</font>. The service is bound strictly to the local loopback interface on the host, ensuring it is only accessible via the Nginx reverse proxy.", table_cell_style)],
        [Paragraph("<b>Data Persistence</b>", table_cell_style), Paragraph("Host volume mount: <font face='Courier'>/var/lib/billing-gate:/var/lib/billing-gate</font>. Stores <font face='Courier'>users.json</font> and HMAC <font face='Courier'>secret.key</font> persistently across restarts.", table_cell_style)],
        [Paragraph("<b>Nginx Management Mounts</b>", table_cell_style), Paragraph("Mounted volumes: <font face='Courier'>/etc/nginx:/etc/nginx</font>, <font face='Courier'>/etc/letsencrypt:/etc/letsencrypt:ro</font>, and shared host PID (<font face='Courier'>pid: host</font>) allowing in-container Nginx syntax checks and reloads.", table_cell_style)],
        [Paragraph("<b>Container Health Check</b>", table_cell_style), Paragraph("Native Node.js fetch healthcheck polling <font face='Courier'>http://127.0.0.1:3100/gate/health</font> every 30s.", table_cell_style)],
        [Paragraph("<b>Logging &amp; Rotation</b>", table_cell_style), Paragraph("JSON-file logging driver with automatic log rotation (<font face='Courier'>max-size: 10m, max-file: 3</font>).", table_cell_style)],
    ]
    docker_arch_table = Table(docker_arch_data, colWidths=[2.2 * inch, 4.8 * inch])
    docker_arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8fafc"), colors.white]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(docker_arch_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("7. Docker Operations & Systemd Switchover", h1_style))
    story.append(Paragraph(
        "<b>A. Quick Start via Docker Compose:</b><br/>"
        "<font face='Courier'>cd /var/www/billing-gate &amp;&amp; docker compose up -d --build</font><br/><br/>"
        "<b>B. Zero-Disruption Switchover from Bare-Metal to Docker:</b><br/>"
        "Because both the host Node.js service and the Docker container publish to <font face='Courier'>127.0.0.1:3100</font>, "
        "switching from bare-metal to Docker requires <b>zero changes</b> to Nginx configuration files:<br/>"
        "1. Stop bare-metal service: <font face='Courier'>sudo systemctl stop billing-gate.service &amp;&amp; sudo systemctl disable billing-gate.service</font><br/>"
        "2. Launch Docker Compose: <font face='Courier'>docker compose up -d</font><br/>"
        "3. Enable Systemd Docker unit: <font face='Courier'>sudo cp systemd/billing-gate-docker.service /etc/systemd/system/ &amp;&amp; sudo systemctl daemon-reload &amp;&amp; sudo systemctl enable billing-gate-docker.service</font><br/><br/>"
        "<b>C. Container Management CLI Helper (<font face='Courier'>./gate-cli.sh</font>):</b><br/>"
        "To manage accounts inside the running Docker container with interactive terminal QR codes:<br/>"
        "&bull; Add staff user: <font face='Courier'>./gate-cli.sh add-user &lt;username&gt; &lt;password&gt; [admin|staff]</font><br/>"
        "&bull; List all users: <font face='Courier'>./gate-cli.sh list-users</font><br/>"
        "&bull; Reset TOTP / Re-pair: <font face='Courier'>./gate-cli.sh reset-totp &lt;username&gt;</font><br/>"
        "&bull; Update password: <font face='Courier'>./gate-cli.sh set-password &lt;username&gt; &lt;newpass&gt;</font><br/>"
        "&bull; Delete account: <font face='Courier'>./gate-cli.sh delete-user &lt;username&gt;</font>",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: Complete CLI & Infrastructure Reference Table
    # =========================================================================

    story.append(Paragraph("8. Complete Command & Infrastructure Reference", h1_style))
    story.append(Paragraph(
        "Reference sheet for system administrators managing Chettiyar Kada's 2FA access gate across bare-metal and Docker environments:",
        body_style
    ))

    ref_data = [
        [Paragraph("Operational Task", table_header_style), Paragraph("Docker Compose Mode", table_header_style), Paragraph("Bare-Metal Systemd Mode", table_header_style)],
        [
            Paragraph("<b>Start Service</b>", table_cell_style),
            Paragraph("<font face='Courier'>docker compose up -d</font>", code_style),
            Paragraph("<font face='Courier'>systemctl start billing-gate</font>", code_style)
        ],
        [
            Paragraph("<b>Stop Service</b>", table_cell_style),
            Paragraph("<font face='Courier'>docker compose down</font>", code_style),
            Paragraph("<font face='Courier'>systemctl stop billing-gate</font>", code_style)
        ],
        [
            Paragraph("<b>Service Status</b>", table_cell_style),
            Paragraph("<font face='Courier'>docker compose ps</font>", code_style),
            Paragraph("<font face='Courier'>systemctl status billing-gate</font>", code_style)
        ],
        [
            Paragraph("<b>Live Logs</b>", table_cell_style),
            Paragraph("<font face='Courier'>docker compose logs -f</font>", code_style),
            Paragraph("<font face='Courier'>journalctl -u billing-gate -f</font>", code_style)
        ],
        [
            Paragraph("<b>Health Probe</b>", table_cell_style),
            Paragraph("<font face='Courier'>curl http://127.0.0.1:3100/gate/health</font>", code_style),
            Paragraph("<font face='Courier'>curl http://127.0.0.1:3100/gate/health</font>", code_style)
        ],
        [
            Paragraph("<b>Add Admin User</b>", table_cell_style),
            Paragraph("<font face='Courier'>./gate-cli.sh add-user u p admin</font>", code_style),
            Paragraph("<font face='Courier'>node cli.js add-user u p admin</font>", code_style)
        ],
        [
            Paragraph("<b>Add Staff User</b>", table_cell_style),
            Paragraph("<font face='Courier'>./gate-cli.sh add-user u p staff</font>", code_style),
            Paragraph("<font face='Courier'>node cli.js add-user u p staff</font>", code_style)
        ],
        [
            Paragraph("<b>List Users &amp; Roles</b>", table_cell_style),
            Paragraph("<font face='Courier'>./gate-cli.sh list-users</font>", code_style),
            Paragraph("<font face='Courier'>node cli.js list-users</font>", code_style)
        ],
        [
            Paragraph("<b>Reset TOTP QR</b>", table_cell_style),
            Paragraph("<font face='Courier'>./gate-cli.sh reset-totp &lt;user&gt;</font>", code_style),
            Paragraph("<font face='Courier'>node cli.js reset-totp &lt;user&gt;</font>", code_style)
        ],
        [
            Paragraph("<b>Update Password</b>", table_cell_style),
            Paragraph("<font face='Courier'>./gate-cli.sh set-password u p</font>", code_style),
            Paragraph("<font face='Courier'>node cli.js set-password u p</font>", code_style)
        ],
        [
            Paragraph("<b>Nginx Syntax Test</b>", table_cell_style),
            Paragraph("Via <font face='Courier'>/gate/admin</font> or <font face='Courier'>nginx -t</font>", code_style),
            Paragraph("<font face='Courier'>sudo nginx -t</font>", code_style)
        ],
        [
            Paragraph("<b>Nginx Reload</b>", table_cell_style),
            Paragraph("Via <font face='Courier'>/gate/admin</font> or <font face='Courier'>nginx -s reload</font>", code_style),
            Paragraph("<font face='Courier'>sudo systemctl reload nginx</font>", code_style)
        ],
    ]
    ref_table = Table(ref_data, colWidths=[1.5 * inch, 2.75 * inch, 2.75 * inch])
    ref_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8fafc"), colors.white]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(ref_table)
    story.append(Spacer(1, 8))

    # Section 9: File System & Directory Map
    story.append(Paragraph("9. Key File Paths & Repository Architecture Map", h1_style))
    paths_data = [
        [Paragraph("Path / Location", table_header_style), Paragraph("Purpose / Description", table_header_style)],
        [Paragraph("<font face='Courier'>/var/www/billing-gate/Dockerfile</font>", code_style), Paragraph("Production multi-stage Alpine Linux container build definition", table_cell_style)],
        [Paragraph("<font face='Courier'>/var/www/billing-gate/docker-compose.yml</font>", code_style), Paragraph("Container orchestration specification, volume mappings, and loopback port bindings", table_cell_style)],
        [Paragraph("<font face='Courier'>/var/www/billing-gate/views/admin.html</font>", code_style), Paragraph("Interactive Web Admin Control Center (Nginx &amp; user management)", table_cell_style)],
        [Paragraph("<font face='Courier'>/var/www/billing-gate/lib/nginx.js</font>", code_style), Paragraph("Backend engine for Nginx directive parsing, syntax testing (<font face='Courier'>nginx -t</font>), and safe reload", table_cell_style)],
        [Paragraph("<font face='Courier'>/var/www/billing-gate/gate-cli.sh</font>", code_style), Paragraph("Interactive CLI wrapper script executing commands inside the Docker container", table_cell_style)],
        [Paragraph("<font face='Courier'>/var/lib/billing-gate/users.json</font>", code_style), Paragraph("Persistent atomic JSON database storing staff credentials, roles, and TOTP secrets", table_cell_style)],
        [Paragraph("<font face='Courier'>/var/lib/billing-gate/secret.key</font>", code_style), Paragraph("High-entropy 256-bit cryptographically random signing key for session HMAC cookies", table_cell_style)],
        [Paragraph("<font face='Courier'>/etc/nginx/sites-available/billing.chettiyarkada.in</font>", code_style), Paragraph("Production Nginx reverse-proxy configuration with 2FA subrequest verification", table_cell_style)],
    ]
    paths_table = Table(paths_data, colWidths=[3.2 * inch, 3.8 * inch])
    paths_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8fafc"), colors.white]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(paths_table)

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    
    # Copy to web path and previous conversation artifact path if exists
    shutil.copyfile(PDF_PATH, WEB_PDF_PATH)
    try:
        shutil.copyfile(PDF_PATH, PREV_PDF_PATH)
    except Exception:
        pass

    file_size = os.path.getsize(PDF_PATH)
    print(f"PDF successfully generated: {PDF_PATH} ({file_size} bytes)")
    return PDF_PATH

if __name__ == '__main__':
    build_pdf()
