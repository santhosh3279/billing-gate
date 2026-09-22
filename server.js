import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  hashPassword,
  verifyPassword,
  createSessionToken,
  verifySessionToken,
  buildCookieHeader,
  buildClearCookieHeader,
  extractTokenFromCookie,
  checkRateLimit,
  recordFailedAttempt,
  clearRateLimit
} from './lib/auth.js';
import {
  generateSecret,
  verifyTotp,
  getOtpauthUrl,
  generateQrCodeDataUrl
} from './lib/totp.js';
import {
  getUser,
  saveUser,
  needsInitialSetup
} from './lib/db.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT || 3100);
const HOST = process.env.HOST || '127.0.0.1';

// Pre-read index.html
const INDEX_HTML_PATH = path.join(__dirname, 'views', 'index.html');
const PUBLIC_DIR = path.join(__dirname, 'public');

/**
 * Helper to read JSON request body safely
 */
function readJsonBody(req, maxSize = 8192) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > maxSize) {
        reject(new Error('Payload too large'));
      } else {
        chunks.push(chunk);
      }
    });
    req.on('end', () => {
      try {
        const bodyStr = Buffer.concat(chunks).toString('utf8');
        if (!bodyStr) return resolve({});
        resolve(JSON.parse(bodyStr));
      } catch (err) {
        reject(new Error('Invalid JSON'));
      }
    });
    req.on('error', reject);
  });
}

/**
 * Get client IP address from request headers or socket
 */
function getClientIp(req) {
  const forwarded = req.headers['x-forwarded-for'];
  if (forwarded) {
    const ips = forwarded.split(',');
    return ips[0].trim();
  }
  return req.headers['x-real-ip'] || req.socket.remoteAddress || '127.0.0.1';
}

/**
 * Send JSON response
 */
function sendJson(res, statusCode, data, headers = {}) {
  const json = JSON.stringify(data);
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(json),
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Cache-Control': 'no-store, no-cache, must-revalidate',
    ...headers
  });
  res.end(json);
}

/**
 * Main HTTP request handler
 */
async function handleRequest(req, res) {
  const clientIp = getClientIp(req);
  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = parsedUrl.pathname;
  const isSecure = (req.headers['x-forwarded-proto'] === 'https') || req.socket.encrypted;

  // 1. Static Assets (/gate/assets/*)
  if (pathname.startsWith('/gate/assets/')) {
    const filename = pathname.replace('/gate/assets/', '');
    // Prevent directory traversal
    if (filename.includes('..') || filename.includes('/')) {
      res.writeHead(403);
      return res.end('Forbidden');
    }
    const filePath = path.join(PUBLIC_DIR, filename);
    if (!fs.existsSync(filePath)) {
      res.writeHead(404);
      return res.end('Asset not found');
    }
    const ext = path.extname(filePath).toLowerCase();
    const mimeTypes = {
      '.png': 'image/png',
      '.svg': 'image/svg+xml',
      '.ico': 'image/x-icon',
      '.css': 'text/css',
      '.js': 'application/javascript',
      '.pdf': 'application/pdf'
    };
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    res.writeHead(200, {
      'Content-Type': contentType,
      'Cache-Control': 'public, max-age=86400',
      'X-Content-Type-Options': 'nosniff'
    });
    fs.createReadStream(filePath).pipe(res);
    return;
  }

  // 2. Auth Request Verification (Used by Nginx auth_request /_gate/verify)
  if (pathname === '/gate/api/verify' || pathname === '/_gate/verify') {
    const token = extractTokenFromCookie(req.headers.cookie);
    const session = verifySessionToken(token);
    if (session && session.u) {
      res.writeHead(200, {
        'X-Gate-User': session.u,
        'Cache-Control': 'no-store, no-cache, must-revalidate',
        'X-Content-Type-Options': 'nosniff'
      });
      return res.end('OK');
    } else {
      res.writeHead(401, {
        'Cache-Control': 'no-store, no-cache, must-revalidate',
        'X-Content-Type-Options': 'nosniff'
      });
      return res.end('Unauthorized');
    }
  }

  // 3. Health check
  if (pathname === '/gate/health') {
    return sendJson(res, 200, { status: 'ok', timestamp: new Date().toISOString() });
  }

  // 4. Check Setup Status API
  if (pathname === '/gate/api/setup-status' && req.method === 'GET') {
    return sendJson(res, 200, {
      needsInitialSetup: needsInitialSetup()
    });
  }

  // 5. Initial Admin Setup API (only active when zero users registered)
  if (pathname === '/gate/api/setup-init' && req.method === 'POST') {
    if (!needsInitialSetup()) {
      return sendJson(res, 403, { status: 'error', message: 'System is already initialized.' });
    }

    try {
      const body = await readJsonBody(req);
      const username = (body.username || '').trim();
      const password = body.password || '';

      if (!username || !password || username.length < 3 || password.length < 6) {
        return sendJson(res, 400, {
          status: 'error',
          message: 'Username must be at least 3 characters and password at least 6 characters.'
        });
      }

      const { hash, salt } = await hashPassword(password);
      const secret = generateSecret();
      const otpauth = getOtpauthUrl(username, secret);
      const qrDataUrl = await generateQrCodeDataUrl(otpauth);

      // Save user temporarily as pending enrollment
      saveUser({
        username,
        passwordHash: hash,
        salt,
        totpSecret: secret,
        enrolled: false,
        createdAt: new Date().toISOString()
      });

      return sendJson(res, 200, {
        status: 'success',
        secret,
        qrDataUrl
      });
    } catch (err) {
      return sendJson(res, 400, { status: 'error', message: err.message });
    }
  }

  // 6. Enroll 2FA Step 1: Verify credentials and issue QR code
  if (pathname === '/gate/api/setup-enroll' && req.method === 'POST') {
    const rateStatus = checkRateLimit(clientIp);
    if (rateStatus.limited) {
      return sendJson(res, 429, {
        status: 'error',
        message: `Too many failed attempts. Please wait ${rateStatus.retryAfterSeconds} seconds.`,
        retryAfter: rateStatus.retryAfterSeconds
      });
    }

    try {
      const body = await readJsonBody(req);
      const username = (body.username || '').trim();
      const password = body.password || '';

      const user = getUser(username);
      if (!user) {
        recordFailedAttempt(clientIp);
        return sendJson(res, 401, { status: 'error', message: 'Invalid username or password.' });
      }

      const validPassword = await verifyPassword(password, user.passwordHash, user.salt);
      if (!validPassword) {
        recordFailedAttempt(clientIp);
        return sendJson(res, 401, { status: 'error', message: 'Invalid username or password.' });
      }

      const secret = generateSecret();
      const otpauth = getOtpauthUrl(user.username, secret);
      const qrDataUrl = await generateQrCodeDataUrl(otpauth);

      return sendJson(res, 200, {
        status: 'success',
        secret,
        qrDataUrl
      });
    } catch (err) {
      return sendJson(res, 400, { status: 'error', message: err.message });
    }
  }

  // 7. Enroll 2FA Step 2: Confirm code and activate
  if (pathname === '/gate/api/setup-verify' && req.method === 'POST') {
    try {
      const body = await readJsonBody(req);
      const username = (body.username || '').trim();
      const secret = (body.secret || '').trim();
      const totpCode = (body.totpCode || '').trim();

      const user = getUser(username);
      if (!user) {
        return sendJson(res, 404, { status: 'error', message: 'User not found.' });
      }

      const validTotp = verifyTotp(totpCode, secret);
      if (!validTotp) {
        return sendJson(res, 400, { status: 'error', message: 'Invalid 6-digit code. Please verify time in Google Authenticator.' });
      }

      // Activate user
      user.totpSecret = secret;
      user.enrolled = true;
      user.lastLoginAt = new Date().toISOString();
      saveUser(user);

      // Issue session token
      const token = createSessionToken(user.username);
      const cookieHeader = buildCookieHeader(token, isSecure);

      clearRateLimit(clientIp);
      return sendJson(res, 200, { status: 'success', message: '2FA enrolled and session activated.' }, {
        'Set-Cookie': cookieHeader
      });
    } catch (err) {
      return sendJson(res, 400, { status: 'error', message: err.message });
    }
  }

  // 8. Primary Login API
  if (pathname === '/gate/api/login' && req.method === 'POST') {
    const rateStatus = checkRateLimit(clientIp);
    if (rateStatus.limited) {
      return sendJson(res, 429, {
        status: 'error',
        message: `Too many failed attempts. Please wait ${rateStatus.retryAfterSeconds} seconds.`,
        retryAfter: rateStatus.retryAfterSeconds
      });
    }

    try {
      const body = await readJsonBody(req);
      const username = (body.username || '').trim();
      const password = body.password || '';
      const totpCode = (body.totpCode || '').trim();

      const user = getUser(username);
      if (!user || !user.enrolled || !user.totpSecret) {
        recordFailedAttempt(clientIp);
        return sendJson(res, 401, { status: 'error', message: 'Invalid username, password, or un-enrolled 2FA.' });
      }

      const validPassword = await verifyPassword(password, user.passwordHash, user.salt);
      if (!validPassword) {
        recordFailedAttempt(clientIp);
        return sendJson(res, 401, { status: 'error', message: 'Invalid credentials.' });
      }

      const validTotp = verifyTotp(totpCode, user.totpSecret);
      if (!validTotp) {
        recordFailedAttempt(clientIp);
        return sendJson(res, 401, { status: 'error', message: 'Invalid Google Authenticator code. Check clock synchronization.' });
      }

      // Success
      clearRateLimit(clientIp);
      user.lastLoginAt = new Date().toISOString();
      saveUser(user);

      const token = createSessionToken(user.username);
      const cookieHeader = buildCookieHeader(token, isSecure);

      return sendJson(res, 200, {
        status: 'success',
        message: 'Authentication successful',
        redirect: '/'
      }, {
        'Set-Cookie': cookieHeader
      });
    } catch (err) {
      return sendJson(res, 400, { status: 'error', message: err.message });
    }
  }

  // 9. Logout
  if (pathname === '/gate/logout') {
    const clearCookie = buildClearCookieHeader(isSecure);
    res.writeHead(302, {
      'Location': '/gate/login?logged_out=1',
      'Set-Cookie': clearCookie,
      'Cache-Control': 'no-store, no-cache, must-revalidate'
    });
    return res.end();
  }

  // 10. Landing Page (/gate/login or /gate or /gate/)
  if (pathname === '/gate/login' || pathname === '/gate' || pathname === '/gate/') {
    // If already authenticated, redirect to destination
    const existingToken = extractTokenFromCookie(req.headers.cookie);
    const existingSession = verifySessionToken(existingToken);
    const returnTo = parsedUrl.searchParams.get('return_to') || '/';

    if (existingSession && existingSession.u && !parsedUrl.searchParams.get('logged_out')) {
      res.writeHead(302, {
        'Location': returnTo,
        'Cache-Control': 'no-store, no-cache, must-revalidate'
      });
      return res.end();
    }

    try {
      const html = fs.readFileSync(INDEX_HTML_PATH, 'utf8');
      res.writeHead(200, {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-store, no-cache, must-revalidate',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN'
      });
      return res.end(html);
    } catch (_err) {
      res.writeHead(500);
      return res.end('Error loading landing page');
    }
  }

  // 404 for anything else under /gate/
  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not Found');
}

const server = http.createServer((req, res) => {
  handleRequest(req, res).catch((err) => {
    console.error('Unhandled server error:', err);
    if (!res.headersSent) {
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('Internal Server Error');
    }
  });
});

server.listen(PORT, HOST, () => {
  console.log(`Billing Auth Gate service listening on http://${HOST}:${PORT}`);
});
