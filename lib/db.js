import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const DATA_DIR = process.env.DATA_DIR || '/var/lib/billing-gate';
const USERS_FILE = path.join(DATA_DIR, 'users.json');
const SECRET_FILE = path.join(DATA_DIR, 'secret.key');

// Ensure data directory exists
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true, mode: 0o700 });
}

/**
 * Get or initialize server signing secret key
 * @returns {string}
 */
export function getSecretKey() {
  if (fs.existsSync(SECRET_FILE)) {
    try {
      const key = fs.readFileSync(SECRET_FILE, 'utf8').trim();
      if (key && key.length >= 32) return key;
    } catch (_err) {}
  }
  const newKey = crypto.randomBytes(32).toString('hex');
  fs.writeFileSync(SECRET_FILE, newKey, { mode: 0o600 });
  return newKey;
}

/**
 * Load all users from disk
 * @returns {Record<string, any>}
 */
export function getUsers() {
  if (!fs.existsSync(USERS_FILE)) {
    return {};
  }
  try {
    const data = fs.readFileSync(USERS_FILE, 'utf8');
    const users = JSON.parse(data) || {};
    // Ensure every user has a role
    for (const [k, u] of Object.entries(users)) {
      if (!u.role) {
        u.role = (k.toLowerCase() === 'admin' || u.username?.toLowerCase() === 'admin') ? 'admin' : 'staff';
      }
    }
    return users;
  } catch (_err) {
    return {};
  }
}

/**
 * Save users map atomically
 * @param {Record<string, any>} users
 */
export function saveUsers(users) {
  const tmpFile = `${USERS_FILE}.tmp.${Date.now()}`;
  fs.writeFileSync(tmpFile, JSON.stringify(users, null, 2), { mode: 0o600 });
  fs.renameSync(tmpFile, USERS_FILE);
}

/**
 * Get single user by username (case-insensitive)
 * @param {string} username
 * @returns {any | null}
 */
export function getUser(username) {
  if (!username) return null;
  const users = getUsers();
  const lower = username.toLowerCase().trim();
  for (const [k, u] of Object.entries(users)) {
    if (k.toLowerCase() === lower || u.username?.toLowerCase() === lower) {
      if (!u.role) {
        u.role = (u.username?.toLowerCase() === 'admin') ? 'admin' : 'staff';
      }
      return u;
    }
  }
  return null;
}

/**
 * Get sanitized users list for API (omitting passwordHash, salt, totpSecret)
 */
export function getSanitizedUsers() {
  const users = getUsers();
  return Object.values(users).map(u => ({
    username: u.username,
    role: u.role || (u.username.toLowerCase() === 'admin' ? 'admin' : 'staff'),
    enrolled: !!u.enrolled,
    createdAt: u.createdAt || null,
    updatedAt: u.updatedAt || null,
    lastLoginAt: u.lastLoginAt || null
  }));
}

/**
 * Count current number of active admin users
 */
export function countAdmins() {
  const users = getUsers();
  return Object.values(users).filter(u => u.role === 'admin' || u.username.toLowerCase() === 'admin').length;
}

/**
 * Add or update user
 * @param {any} user
 */
export function saveUser(user) {
  if (!user || !user.username) throw new Error('Username required');
  const users = getUsers();
  const role = user.role || (user.username.toLowerCase() === 'admin' ? 'admin' : 'staff');
  users[user.username] = {
    ...users[user.username],
    ...user,
    role,
    updatedAt: new Date().toISOString(),
  };
  saveUsers(users);
}

/**
 * Remove user
 * @param {string} username
 */
export function deleteUser(username) {
  const users = getUsers();
  const lower = username.toLowerCase().trim();
  let foundKey = null;
  for (const [k, u] of Object.entries(users)) {
    if (k.toLowerCase() === lower || u.username?.toLowerCase() === lower) {
      foundKey = k;
      break;
    }
  }
  if (foundKey) {
    delete users[foundKey];
    saveUsers(users);
    return true;
  }
  return false;
}

/**
 * Check if initial setup is needed (i.e. zero users registered)
 * @returns {boolean}
 */
export function needsInitialSetup() {
  const users = getUsers();
  return Object.keys(users).length === 0;
}
