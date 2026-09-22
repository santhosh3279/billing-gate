import crypto from 'node:crypto';
import QRCode from 'qrcode';

const BASE32_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';

/**
 * Encode a buffer to a Base32 string
 * @param {Buffer} buffer
 * @returns {string}
 */
export function base32Encode(buffer) {
  let bits = '';
  for (let i = 0; i < buffer.length; i++) {
    bits += buffer[i].toString(2).padStart(8, '0');
  }
  let base32 = '';
  for (let i = 0; i < bits.length; i += 5) {
    const chunk = bits.substring(i, i + 5);
    if (chunk.length < 5) {
      base32 += BASE32_ALPHABET[parseInt(chunk.padEnd(5, '0'), 2)];
      break;
    }
    base32 += BASE32_ALPHABET[parseInt(chunk, 2)];
  }
  return base32;
}

/**
 * Decode a Base32 string to a buffer
 * @param {string} str
 * @returns {Buffer}
 */
export function base32Decode(str) {
  const clean = str.replace(/[\s=-]/g, '').toUpperCase();
  let bits = '';
  for (let i = 0; i < clean.length; i++) {
    const val = BASE32_ALPHABET.indexOf(clean[i]);
    if (val === -1) {
      throw new Error(`Invalid Base32 character: ${clean[i]}`);
    }
    bits += val.toString(2).padStart(5, '0');
  }
  const bytes = [];
  for (let i = 0; i + 8 <= bits.length; i += 8) {
    bytes.push(parseInt(bits.substring(i, i + 8), 2));
  }
  return Buffer.from(bytes);
}

/**
 * Generate a cryptographically secure random Base32 secret for Google Authenticator (default 20 bytes = 160 bits)
 * @param {number} numBytes
 * @returns {string}
 */
export function generateSecret(numBytes = 20) {
  const randomBytes = crypto.randomBytes(numBytes);
  return base32Encode(randomBytes);
}

/**
 * Calculate the RFC 6238 TOTP code for a secret and time step counter
 * @param {string} secret
 * @param {number|bigint} counter
 * @returns {string} 6-digit code
 */
export function generateTotp(secret, counter) {
  const key = base32Decode(secret);
  const buf = Buffer.alloc(8);
  buf.writeBigUInt64BE(BigInt(counter));

  const hmac = crypto.createHmac('sha1', key).update(buf).digest();
  const offset = hmac[hmac.length - 1] & 0x0f;
  const code = (hmac.readUInt32BE(offset) & 0x7fffffff) % 1000000;
  return code.toString().padStart(6, '0');
}

/**
 * Verify a 6-digit TOTP code against a secret key
 * Allows +/- window steps (default 1 step = +/- 30s)
 * @param {string} code
 * @param {string} secret
 * @param {number} window
 * @returns {boolean}
 */
export function verifyTotp(code, secret, window = 1) {
  if (!code || typeof code !== 'string') return false;
  const cleanCode = code.replace(/[\s-]/g, '').trim();
  if (cleanCode.length !== 6 || !/^\d{6}$/.test(cleanCode)) return false;

  try {
    const currentStep = Math.floor(Date.now() / 1000 / 30);
    for (let offset = -window; offset <= window; offset++) {
      const step = currentStep + offset;
      const expected = generateTotp(secret, step);
      if (crypto.timingSafeEqual(Buffer.from(cleanCode), Buffer.from(expected))) {
        return true;
      }
    }
  } catch (_err) {
    return false;
  }
  return false;
}

/**
 * Build standard otpauth URL
 * @param {string} username
 * @param {string} secret
 * @param {string} issuer
 * @returns {string}
 */
export function getOtpauthUrl(username, secret, issuer = 'Chettiyar Kada Billing') {
  const encodedIssuer = encodeURIComponent(issuer);
  const encodedUser = encodeURIComponent(username);
  return `otpauth://totp/${encodedIssuer}:${encodedUser}?secret=${secret}&issuer=${encodedIssuer}&algorithm=SHA1&digits=6&period=30`;
}

/**
 * Generate QR code as Base64 Data URL
 * @param {string} otpauthUrl
 * @returns {Promise<string>}
 */
export async function generateQrCodeDataUrl(otpauthUrl) {
  return await QRCode.toDataURL(otpauthUrl, {
    errorCorrectionLevel: 'M',
    margin: 2,
    width: 260,
    color: {
      dark: '#0f172a',
      light: '#ffffff',
    },
  });
}
