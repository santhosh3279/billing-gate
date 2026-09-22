import crypto from 'node:crypto';
import { promisify } from 'node:util';
import { getSecretKey } from './db.js';

const scryptAsync = promisify(crypto.scrypt);
const SESSION_DURATION_MS = 12 * 60 * 60 * 1000; // 12 hours
const COOKIE_NAME = 'ck_billing_gate';

// Rate limiting in-memory storage
const loginAttempts = new Map(); // ip -> { count, lockedUntil }
const MAX_ATTEMPTS = 5;
const LOCKOUT_DURATION_MS = 15 * 60 * 1000; // 15 minutes

/**
 * Hash a password using scrypt with a random or provided salt
 * @param {string} password
 * @param {string} [existingSaltHex]
 * @returns {Promise<{ hash: string, salt: string }>}
 */
export async function hashPassword(password, existingSaltHex = null) {
  const salt = existingSaltHex ? Buffer.from(existingSaltHex, 'hex') : crypto.randomBytes(16);
  const derivedKey = await scryptAsync(password, salt, 64);
  return {
    hash: derivedKey.toString('hex'),
    salt: salt.toString('hex'),
  };
}

/**
 * Verify a plaintext password against stored hash and salt
 * @param {string} password
 * @param {string} hashHex
 * @param {string} saltHex
 * @returns {Promise<boolean>}
 */
export async function verifyPassword(password, hashHex, saltHex) {
  try {
    const salt = Buffer.from(saltHex, 'hex');
    const expected = Buffer.from(hashHex, 'hex');
    const derived = await scryptAsync(password, salt, 64);
    if (derived.length !== expected.length) return false;
    return crypto.timingSafeEqual(derived, expected);
  } catch (_err) {
    return false;
  }
}

/**
 * Base64URL encode string or buffer
 */
function base64UrlEncode(input) {
  const buf = Buffer.isBuffer(input) ? input : Buffer.from(input, 'utf8');
  return buf.toString('base64url');
}

/**
 * Base64URL decode to string
 */
function base64UrlDecode(str) {
  return Buffer.from(str, 'base64url').toString('utf8');
}

/**
 * Create a cryptographically signed session token
 * @param {string} username
 * @param {number} [durationMs]
 * @returns {string}
 */
export function createSessionToken(username, durationMs = SESSION_DURATION_MS) {
  const now = Date.now();
  const payload = {
    u: username,
    iat: now,
    exp: now + durationMs,
    nonce: crypto.randomBytes(8).toString('hex'),
  };
  const payloadStr = base64UrlEncode(JSON.stringify(payload));
  const secret = getSecretKey();
  const sig = crypto.createHmac('sha256', secret).update(payloadStr).digest('base64url');
  return `${payloadStr}.${sig}`;
}

/**
 * Verify and decode a session token
 * @param {string} token
 * @returns {{ u: string, exp: number, iat: number } | null}
 */
export function verifySessionToken(token) {
  if (!token || typeof token !== 'string') return null;
  const parts = token.split('.');
  if (parts.length !== 2) return null;

  const [payloadStr, sig] = parts;
  const secret = getSecretKey();
  const expectedSig = crypto.createHmac('sha256', secret).update(payloadStr).digest('base64url');

  if (sig.length !== expectedSig.length) return null;
  if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expectedSig))) {
    return null;
  }

  try {
    const payload = JSON.parse(base64UrlDecode(payloadStr));
    if (!payload || !payload.exp || !payload.u) return null;
    if (Date.now() > payload.exp) return null; // Expired
    return payload;
  } catch (_err) {
    return null;
  }
}

/**
 * Generate Set-Cookie header for session token
 * @param {string} token
 * @param {boolean} [secure]
 * @param {number} [maxAgeSeconds]
 * @returns {string}
 */
export function buildCookieHeader(token, secure = true, maxAgeSeconds = Math.floor(SESSION_DURATION_MS / 1000)) {
  const secureFlag = secure ? '; Secure' : '';
  return `${COOKIE_NAME}=${token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${maxAgeSeconds}${secureFlag}`;
}

/**
 * Generate expired Set-Cookie header to clear session
 * @param {boolean} [secure]
 * @returns {string}
 */
export function buildClearCookieHeader(secure = true) {
  const secureFlag = secure ? '; Secure' : '';
  return `${COOKIE_NAME}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT${secureFlag}`;
}

/**
 * Extract session token from request Cookie header
 * @param {string} [cookieHeader]
 * @returns {string | null}
 */
export function extractTokenFromCookie(cookieHeader) {
  if (!cookieHeader) return null;
  const cookies = cookieHeader.split(';');
  for (const c of cookies) {
    const trimmed = c.trim();
    if (trimmed.startsWith(`${COOKIE_NAME}=`)) {
      return trimmed.substring(COOKIE_NAME.length + 1);
    }
  }
  return null;
}

/**
 * Check if IP is currently rate limited
 * @param {string} ip
 * @returns {{ limited: boolean, retryAfterSeconds?: number }}
 */
export function checkRateLimit(ip) {
  const now = Date.now();
  const record = loginAttempts.get(ip);
  if (!record) return { limited: false };

  if (record.lockedUntil && record.lockedUntil > now) {
    const retryAfter = Math.ceil((record.lockedUntil - now) / 1000);
    return { limited: true, retryAfterSeconds: retryAfter };
  }

  // If lockout expired, reset
  if (record.lockedUntil && record.lockedUntil <= now) {
    loginAttempts.delete(ip);
    return { limited: false };
  }

  return { limited: false };
}

/**
 * Record a failed authentication attempt for an IP
 * @param {string} ip
 */
export function recordFailedAttempt(ip) {
  const now = Date.now();
  let record = loginAttempts.get(ip) || { count: 0, firstAttempt: now };

  // Reset if older than lockout window
  if (now - record.firstAttempt > LOCKOUT_DURATION_MS) {
    record = { count: 0, firstAttempt: now };
  }

  record.count += 1;
  if (record.count >= MAX_ATTEMPTS) {
    record.lockedUntil = now + LOCKOUT_DURATION_MS;
  }
  loginAttempts.set(ip, record);
}

/**
 * Reset failed attempts upon successful login
 * @param {string} ip
 */
export function clearRateLimit(ip) {
  loginAttempts.delete(ip);
}
