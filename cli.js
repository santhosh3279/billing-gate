#!/usr/bin/env node
import QRCode from 'qrcode';
import { getUser, getUsers, saveUser, deleteUser } from './lib/db.js';
import { hashPassword } from './lib/auth.js';
import { generateSecret, getOtpauthUrl } from './lib/totp.js';

const [,, cmd, arg1, arg2] = process.argv;

async function main() {
  switch (cmd) {
    case 'add-user': {
      const username = arg1;
      const password = arg2;
      if (!username || !password) {
        console.error('Usage: node cli.js add-user <username> <password>');
        process.exit(1);
      }
      const existing = getUser(username);
      if (existing) {
        console.error(`Error: User "${username}" already exists. Use set-password or reset-totp.`);
        process.exit(1);
      }
      const { hash, salt } = await hashPassword(password);
      const secret = generateSecret();
      const otpauth = getOtpauthUrl(username, secret);

      saveUser({
        username,
        passwordHash: hash,
        salt,
        totpSecret: secret,
        enrolled: true,
        createdAt: new Date().toISOString(),
      });

      console.log(`\n=== User "${username}" successfully created ===\n`);
      console.log(`Username:    ${username}`);
      console.log(`TOTP Secret: ${secret}\n`);
      console.log('Scan this QR code in Google Authenticator:\n');
      console.log(await QRCode.toString(otpauth, { type: 'terminal', small: true }));
      console.log(`\nManual entry code: ${secret}`);
      console.log(`OTP URL: ${otpauth}\n`);
      break;
    }

    case 'list-users': {
      const users = getUsers();
      const entries = Object.values(users);
      if (entries.length === 0) {
        console.log('No users configured yet.');
        return;
      }
      console.log('\nConfigured Gate Users:');
      console.log('------------------------------------------------------------');
      for (const u of entries) {
        console.log(`User: ${u.username.padEnd(16)} | Enrolled: ${u.enrolled ? 'Yes' : 'No'} | Created: ${u.createdAt || 'N/A'}`);
      }
      console.log('------------------------------------------------------------\n');
      break;
    }

    case 'reset-totp': {
      const username = arg1;
      if (!username) {
        console.error('Usage: node cli.js reset-totp <username>');
        process.exit(1);
      }
      const user = getUser(username);
      if (!user) {
        console.error(`Error: User "${username}" not found.`);
        process.exit(1);
      }
      const secret = generateSecret();
      user.totpSecret = secret;
      user.enrolled = true;
      saveUser(user);

      const otpauth = getOtpauthUrl(user.username, secret);
      console.log(`\n=== TOTP Reset for "${user.username}" ===\n`);
      console.log(`New TOTP Secret: ${secret}\n`);
      console.log('Scan this QR code in Google Authenticator:\n');
      console.log(await QRCode.toString(otpauth, { type: 'terminal', small: true }));
      console.log(`\nManual entry key: ${secret}\n`);
      break;
    }

    case 'set-password': {
      const username = arg1;
      const newPass = arg2;
      if (!username || !newPass) {
        console.error('Usage: node cli.js set-password <username> <new-password>');
        process.exit(1);
      }
      const user = getUser(username);
      if (!user) {
        console.error(`Error: User "${username}" not found.`);
        process.exit(1);
      }
      const { hash, salt } = await hashPassword(newPass);
      user.passwordHash = hash;
      user.salt = salt;
      saveUser(user);
      console.log(`Password updated successfully for "${user.username}".`);
      break;
    }

    case 'delete-user': {
      const username = arg1;
      if (!username) {
        console.error('Usage: node cli.js delete-user <username>');
        process.exit(1);
      }
      const ok = deleteUser(username);
      if (ok) {
        console.log(`User "${username}" deleted.`);
      } else {
        console.error(`User "${username}" not found.`);
      }
      break;
    }

    default:
      console.log(`
Chettiyar Kada Billing Gate CLI Tool

Usage:
  node cli.js add-user <username> <password>     Create a new staff user and show Google Authenticator QR
  node cli.js list-users                         List all configured staff users
  node cli.js reset-totp <username>              Generate a new Google Authenticator QR for a user
  node cli.js set-password <username> <password> Update password for a user
  node cli.js delete-user <username>             Remove a user
      `);
      break;
  }
}

main().catch((err) => {
  console.error('CLI Error:', err);
  process.exit(1);
});
