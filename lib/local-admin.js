import { isIP } from 'node:net';

function isLoopback(address) {
  return address === '::1' ||
    (isIP(address || '') === 4 && address.startsWith('127.')) ||
    (address?.startsWith('::ffff:') && isLoopback(address.slice(7)));
}

// Nginx also connects over loopback: reject proxies, rebinding and cross-origin requests.
export function isLocalAdminRequest(req) {
  if (!isLoopback(req.socket.remoteAddress)) return false;
  if (Object.keys(req.headers).some(name =>
    name === 'forwarded' || name === 'x-real-ip' || name.startsWith('x-forwarded-')
  )) return false;
  try {
    const host = req.headers.host;
    if (!host || !/^(localhost|127(?:\.\d{1,3}){3}|\[::1\])(?::\d+)?$/i.test(host)) return false;
    const url = new URL(`http://${host}`);
    if (url.hostname !== 'localhost' && url.hostname !== '[::1]' && !isLoopback(url.hostname)) return false;
    if (req.headers.origin && req.headers.origin !== url.origin) return false;
    if (req.headers['sec-fetch-site'] && !['same-origin', 'none'].includes(req.headers['sec-fetch-site'])) return false;
    return true;
  } catch {
    return false;
  }
}
