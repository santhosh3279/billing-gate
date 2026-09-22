import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
import shutil

PDF_PATH = "/root/.gemini/antigravity-cli/brain/3c9e9f79-1dd6-49ab-b7a4-7811610449a4/billing_chettiyarkada_2fa_guide.pdf"
WEB_PDF_PATH = "/var/www/billing-gate/public/Chettiyar_Kada_Billing_2FA_Guide.pdf"
LOGO_PATH = "/var/www/billing-gate/public/logo.png"
QR_PATH = "/root/.gemini/antigravity-cli/brain/3c9e9f79-1dd6-49ab-b7a4-7811610449a4/admin_totp_qr.png"

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
            self.drawString(40, 11 * inch - 30, "Chettiyar Kada Billing — 2FA Security & Operations Guide")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, 11 * inch - 34, 8.5 * inch - 40, 11 * inch - 34)
            
        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(40, 36, 8.5 * inch - 40, 36)
        
        self.drawString(40, 24, "CONFIDENTIAL  •  FOR AUTHORISED CHETTIYAR KADA STAFF ONLY")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 40, 24, page_text)
        self.restoreState()

def build_pdf():
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
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=gold_color,
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=5
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=text_dark,
        spaceAfter=5
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
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
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#92400e")
    )

    story = []

    # Top Header Table with Logo and Title
    logo_img = Image(LOGO_PATH, width=1.05 * inch, height=1.05 * inch)
    header_text = [
        Paragraph("CHETTIYAR KADA &bull; PALAKKAD", ParagraphStyle('Super', fontName='Helvetica-Bold', fontSize=9, textColor=accent_bar_color, leading=11)),
        Paragraph("Enterprise Billing Portal: 2FA Access & Setup Guide", title_style),
        Paragraph("Multi-Factor Authentication (TOTP) & Gateway Security Operations", subtitle_style),
        Paragraph("<b>Domain:</b> <font color='#0284c7'>https://billing.chettiyarkada.in</font> &nbsp;|&nbsp; <b>Auth Standard:</b> Google Authenticator (RFC 6238 TOTP)", body_style)
    ]

    header_table = Table([[logo_img, header_text]], colWidths=[1.25 * inch, 5.75 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (1,0), (1,0), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_bar_color, spaceAfter=8))

    # Section 1: Executive Overview
    story.append(Paragraph("1. System Overview & Security Architecture", h1_style))
    story.append(Paragraph(
        "To protect Chettiyar Kada's financial, invoicing, and POS infrastructure, an enterprise <b>Two-Factor Authentication (2FA) Reverse-Proxy Access Gate</b> "
        "has been deployed for <b>https://billing.chettiyarkada.in</b>. Any unauthenticated browser attempting to connect to the billing system is intercepted "
        "at the network perimeter and prompted for staff credentials and a synchronized <b>Google Authenticator (TOTP)</b> 6-digit passcode before being proxied to "
        "the internal ERPNext application.<br/><br/>"
        "<b>Public Access Exemption:</b> The shared product catalogue viewer (<font color='#0284c7'>https://billing.chettiyarkada.in/frontend/catalogueviewer</font>), "
        "catalogue media (<font face='Courier'>/files/</font>), and frontend styling assets are kept completely public and excluded from the 2FA gate so retail customers "
        "can browse store offers without requiring an authenticator.",
        body_style
    ))

    # Section 2: Initial Admin Credentials
    story.append(Paragraph("2. Provisioned Administrator Credentials", h1_style))
    
    cred_data = [
        [Paragraph("Parameter", table_header_style), Paragraph("Configuration Details", table_header_style)],
        [Paragraph("<b>Portal URL</b>", table_cell_style), Paragraph("<font color='#0284c7'>https://billing.chettiyarkada.in</font> (redirects to /gate/login)", table_cell_style)],
        [Paragraph("<b>Public Catalogue</b>", table_cell_style), Paragraph("<font color='#0284c7'>https://billing.chettiyarkada.in/frontend/catalogueviewer</font> (Public - No 2FA)", table_cell_style)],
        [Paragraph("<b>Username</b>", table_cell_style), Paragraph("<b>admin</b>", table_cell_style)],
        [Paragraph("<b>Initial Password</b>", table_cell_style), Paragraph("<b>ChettiyarAdmin2026!</b>", table_cell_style)],
        [Paragraph("<b>TOTP Secret Key</b>", table_cell_style), Paragraph("<font face='Courier'>WG56VR7SCCFAI3TQUB2O5OKCCO6CXGWW</font> (Base32, 160-bit)", table_cell_style)],
        [Paragraph("<b>Session Lifetime</b>", table_cell_style), Paragraph("12 Hours &bull; Signed HMAC-SHA256 Token (Secure, HttpOnly, SameSite=Lax)", table_cell_style)],
        [Paragraph("<b>Brute-Force Guard</b>", table_cell_style), Paragraph("5 failed attempts maximum &rarr; 15-minute automatic IP lockout", table_cell_style)],
    ]
    cred_table = Table(cred_data, colWidths=[2.1 * inch, 4.9 * inch])
    cred_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8fafc"), colors.white]),
    ]))
    story.append(cred_table)
    story.append(Spacer(1, 6))

    # Section 3: Google Authenticator Setup & QR Code
    story.append(Paragraph("3. Google Authenticator Pairing Instructions", h1_style))
    
    qr_img = Image(QR_PATH, width=1.6 * inch, height=1.6 * inch)
    
    instructions_text = [
        Paragraph("<b>How to pair your smartphone:</b>", ParagraphStyle('B1', fontName='Helvetica-Bold', fontSize=8.5, textColor=primary_color, leading=11)),
        Paragraph("1. Open the <b>Google Authenticator</b> app on your iOS or Android smartphone.", body_style),
        Paragraph("2. Tap the <b>+</b> button (bottom-right) and select <b>Scan a QR code</b>.", body_style),
        Paragraph("3. Point your camera at the QR code displayed to the left.", body_style),
        Paragraph("4. <i>Manual Entry Alternative:</i> Choose <b>Enter a setup key</b>, set Account Name to <b>Chettiyar Kada Billing:admin</b>, enter Key <b><font face='Courier'>WG56VR7SCCFAI3TQUB2O5OKCCO6CXGWW</font></b>, and select <b>Time-based</b>.", body_style),
        Paragraph("5. Your phone will now display a rolling 6-digit passcode that changes every 30 seconds.", body_style),
    ]

    qr_table = Table([[qr_img, instructions_text]], colWidths=[1.85 * inch, 5.15 * inch])
    qr_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (1,0), (1,0), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(qr_table)
    story.append(Spacer(1, 6))

    # Callout box for security tip
    callout_data = [[
        Paragraph(
            "<b>CONFIDENTIALITY NOTICE:</b> Anyone with access to this QR code and password can authenticate into the billing portal. "
            "Store this document securely and update the default password upon initial login.",
            callout_style
        )
    ]]
    callout_table = Table(callout_data, colWidths=[7.0 * inch])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef3c7")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#f59e0b")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 12))

    # PAGE 2 ITEMS (Kept together cleanly)
    page2_elements = []

    # Section 4: Daily Staff Login Flow
    page2_elements.append(Paragraph("4. Daily Staff Login Workflow", h1_style))
    page2_elements.append(Paragraph(
        "&bull; <b>Step 1:</b> Navigate to <b>https://billing.chettiyarkada.in</b> from any browser. The system will automatically direct you to <b>/gate/login</b>.<br/>"
        "&bull; <b>Step 2:</b> Enter your assigned staff <b>Username</b> and <b>Password</b>.<br/>"
        "&bull; <b>Step 3:</b> Open <b>Google Authenticator</b> on your phone, read the current 6-digit code for <i>Chettiyar Kada Billing</i>, and enter it into the OTP box.<br/>"
        "&bull; <b>Step 4:</b> Click <b>Verify & Access Billing</b>. Upon verification, the gate issues an encrypted session cookie and seamlessly opens the ERPNext billing dashboard.<br/>"
        "&bull; <b>Step 5 (Sign Out):</b> When finished, visit <b>https://billing.chettiyarkada.in/gate/logout</b> to immediately terminate the session.",
        body_style
    ))
    page2_elements.append(Spacer(1, 10))

    # Section 5: Staff User Management CLI
    page2_elements.append(Paragraph("5. Server Management CLI (Adding & Managing Staff)", h1_style))
    page2_elements.append(Paragraph(
        "System administrators can manage staff accounts directly from the server terminal using the built-in management script:",
        body_style
    ))

    cli_data = [
        [Paragraph("Task", table_header_style), Paragraph("Terminal Command Line", table_header_style), Paragraph("Description", table_header_style)],
        [
            Paragraph("<b>Create User</b>", table_cell_style),
            Paragraph("node /var/www/billing-gate/cli.js add-user &lt;user&gt; &lt;pass&gt;", code_style),
            Paragraph("Creates account & prints terminal QR code", table_cell_style)
        ],
        [
            Paragraph("<b>List Users</b>", table_cell_style),
            Paragraph("node /var/www/billing-gate/cli.js list-users", code_style),
            Paragraph("Displays all accounts & 2FA status", table_cell_style)
        ],
        [
            Paragraph("<b>Reset 2FA</b>", table_cell_style),
            Paragraph("node /var/www/billing-gate/cli.js reset-totp &lt;user&gt;", code_style),
            Paragraph("Generates fresh QR code for a staff member", table_cell_style)
        ],
        [
            Paragraph("<b>Change Password</b>", table_cell_style),
            Paragraph("node /var/www/billing-gate/cli.js set-password &lt;user&gt; &lt;newpass&gt;", code_style),
            Paragraph("Updates staff login password", table_cell_style)
        ],
        [
            Paragraph("<b>Delete User</b>", table_cell_style),
            Paragraph("node /var/www/billing-gate/cli.js delete-user &lt;user&gt;", code_style),
            Paragraph("Revokes staff access immediately", table_cell_style)
        ],
    ]
    cli_table = Table(cli_data, colWidths=[1.3 * inch, 3.8 * inch, 1.9 * inch])
    cli_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8fafc"), colors.white]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    page2_elements.append(cli_table)
    page2_elements.append(Spacer(1, 10))

    # Section 6: Technical Service Architecture
    page2_elements.append(Paragraph("6. Service & Infrastructure Reference", h1_style))
    page2_elements.append(Paragraph(
        "&bull; <b>Daemon Service:</b> <font face='Courier'>billing-gate.service</font> (Node.js on 127.0.0.1:3100, managed via systemd)<br/>"
        "&bull; <b>Reverse Proxy:</b> Nginx 1.24 with <font face='Courier'>auth_request /_gate/verify</font> subrequest authentication<br/>"
        "&bull; <b>Persistent Data Directory:</b> <font face='Courier'>/var/lib/billing-gate/users.json</font> &amp; <font face='Courier'>secret.key</font><br/>"
        "&bull; <b>Service Status Command:</b> <font face='Courier'>systemctl status billing-gate.service</font><br/>"
        "&bull; <b>Live Logs Command:</b> <font face='Courier'>journalctl -u billing-gate.service -f</font>",
        body_style
    ))

    story.append(KeepTogether(page2_elements))

    doc.build(story, canvasmaker=NumberedCanvas)
    shutil.copyfile(PDF_PATH, WEB_PDF_PATH)
    print(f"PDF successfully built: {PDF_PATH} ({os.path.getsize(PDF_PATH)} bytes)")

if __name__ == '__main__':
    build_pdf()
