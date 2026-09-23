import fs from 'node:fs';
import path from 'node:path';
import { exec } from 'node:child_process';
import { promisify } from 'node:util';

const execAsync = promisify(exec);

const NGINX_SITES_AVAILABLE = process.env.NGINX_SITES_AVAILABLE || '/etc/nginx/sites-available';
const NGINX_SITES_ENABLED = process.env.NGINX_SITES_ENABLED || '/etc/nginx/sites-enabled';
const NGINX_PID_FILE = process.env.NGINX_PID_FILE || '/run/nginx.pid';
const BACKUP_DIR = path.join(NGINX_SITES_AVAILABLE, '.backups');

function isRoot() {
  return typeof process.getuid === 'function' && process.getuid() === 0;
}

function getNginxTestCmd() {
  return isRoot() ? '/usr/sbin/nginx -t' : 'sudo /usr/sbin/nginx -t';
}

function getNginxReloadCmd() {
  return isRoot() 
    ? '/usr/bin/systemctl reload nginx 2>&1 || /usr/sbin/nginx -s reload 2>&1'
    : 'sudo /usr/bin/systemctl reload nginx 2>&1 || sudo /usr/sbin/nginx -s reload 2>&1';
}

function validateSiteName(name) {
  if (!name || typeof name !== 'string') {
    throw new Error('Site name is required.');
  }
  const trimmed = name.trim();
  if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]{1,63}$/.test(trimmed)) {
    throw new Error('Invalid site name. Use alphanumeric characters, dots, hyphens, and underscores (max 64 chars).');
  }
  if (trimmed.includes('..') || trimmed.includes('/') || trimmed.includes('\\')) {
    throw new Error('Invalid characters in site name.');
  }
  return trimmed;
}

/**
 * Execute nginx -t to test syntax
 * @returns {Promise<{ success: boolean, output: string }>}
 */
export async function testNginx() {
  const cmd = getNginxTestCmd();
  try {
    const { stdout, stderr } = await execAsync(cmd);
    const output = (stderr || stdout || '').trim();
    return { success: true, output: output || 'Syntax test passed.' };
  } catch (err) {
    const output = (err.stderr || err.stdout || err.message || '').trim();
    return { success: false, output };
  }
}

/**
 * Reload Nginx configuration
 * @returns {Promise<{ success: boolean, output: string }>}
 */
export async function reloadNginx() {
  const testRes = await testNginx();
  if (!testRes.success) {
    return {
      success: false,
      output: `Cannot reload: Nginx syntax test failed!\n\n${testRes.output}`
    };
  }

  const reloadCmd = getNginxReloadCmd();
  try {
    const { stdout, stderr } = await execAsync(reloadCmd);
    const output = (stderr || stdout || '').trim();
    return { success: true, output: output || 'Nginx reloaded successfully.' };
  } catch (err) {
    const output = (err.stderr || err.stdout || err.message || '').trim();
    return { success: false, output: `Reload failed: ${output}` };
  }
}

/**
 * Get current status of Nginx daemon
 */
export async function getNginxStatus() {
  let isRunning = false;
  let pid = null;

  try {
    if (fs.existsSync(NGINX_PID_FILE)) {
      const pidStr = fs.readFileSync(NGINX_PID_FILE, 'utf8').trim();
      pid = parseInt(pidStr, 10);
      if (!isNaN(pid)) {
        isRunning = fs.existsSync(`/proc/${pid}`);
      }
    }
  } catch (_e) {
    isRunning = false;
  }

  let version = 'nginx';
  try {
    const { stderr, stdout } = await execAsync('/usr/sbin/nginx -v');
    version = (stderr || stdout || '').trim();
  } catch (_e) {}

  const test = await testNginx();
  const sites = listSites();

  return {
    isRunning,
    pid,
    version,
    syntaxOk: test.success,
    syntaxOutput: test.output,
    sitesCount: sites.length,
    enabledCount: sites.filter(s => s.enabled).length
  };
}

/**
 * Parse metadata from Nginx server block configuration text
 */
function parseSiteMeta(content) {
  const serverNames = [];
  const listenPorts = [];
  const proxyPasses = [];
  let hasSSL = false;
  let has2FA = false;

  const lines = content.split('\n');
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (line.startsWith('#')) continue;

    // server_name
    const snMatch = line.match(/^server_name\s+([^;]+);/);
    if (snMatch) {
      const names = snMatch[1].trim().split(/\s+/);
      for (const n of names) {
        if (!serverNames.includes(n) && n !== '_') serverNames.push(n);
      }
    }

    // listen
    const listenMatch = line.match(/^listen\s+([^;]+);/);
    if (listenMatch) {
      const portSpec = listenMatch[1].trim();
      if (!listenPorts.includes(portSpec)) listenPorts.push(portSpec);
      if (portSpec.includes('443') || portSpec.includes('ssl')) hasSSL = true;
    }

    // proxy_pass
    const ppMatch = line.match(/^proxy_pass\s+([^;]+);/);
    if (ppMatch) {
      const target = ppMatch[1].trim();
      if (!proxyPasses.includes(target)) proxyPasses.push(target);
    }

    // auth_request (2FA Gate)
    if (line.includes('auth_request') || line.includes('_gate/verify')) {
      has2FA = true;
    }
    if (line.includes('ssl_certificate')) {
      hasSSL = true;
    }
  }

  return {
    serverNames,
    listenPorts,
    proxyPasses,
    hasSSL,
    has2FA
  };
}

/**
 * List all sites in sites-available
 */
export function listSites() {
  if (!fs.existsSync(NGINX_SITES_AVAILABLE)) {
    return [];
  }

  let enabledLinks = [];
  if (fs.existsSync(NGINX_SITES_ENABLED)) {
    enabledLinks = fs.readdirSync(NGINX_SITES_ENABLED);
  }

  const files = fs.readdirSync(NGINX_SITES_AVAILABLE);
  const sites = [];

  for (const filename of files) {
    if (filename.startsWith('.') || filename.endsWith('~') || filename.endsWith('.bak')) {
      continue;
    }

    const filePath = path.join(NGINX_SITES_AVAILABLE, filename);
    let stat;
    try {
      stat = fs.statSync(filePath);
      if (!stat.isFile()) continue;
    } catch (_e) {
      continue;
    }

    const enabled = enabledLinks.includes(filename);
    let meta = { serverNames: [], listenPorts: [], proxyPasses: [], hasSSL: false, has2FA: false };

    try {
      const content = fs.readFileSync(filePath, 'utf8');
      meta = parseSiteMeta(content);
    } catch (_e) {}

    sites.push({
      name: filename,
      enabled,
      serverNames: meta.serverNames,
      listenPorts: meta.listenPorts,
      proxyPasses: meta.proxyPasses,
      hasSSL: meta.hasSSL,
      has2FA: meta.has2FA,
      sizeBytes: stat.size,
      updatedAt: stat.mtime.toISOString(),
      isProtected: filename === 'billing.chettiyarkada.in'
    });
  }

  // Sort: enabled first, then alphabetically
  sites.sort((a, b) => {
    if (a.enabled && !b.enabled) return -1;
    if (!a.enabled && b.enabled) return 1;
    return a.name.localeCompare(b.name);
  });

  return sites;
}

/**
 * Get site details and configuration contents
 */
export function getSite(name) {
  const cleanName = validateSiteName(name);
  const filePath = path.join(NGINX_SITES_AVAILABLE, cleanName);

  if (!fs.existsSync(filePath)) {
    throw new Error(`Site "${cleanName}" does not exist in sites-available.`);
  }

  const content = fs.readFileSync(filePath, 'utf8');
  const enabled = fs.existsSync(path.join(NGINX_SITES_ENABLED, cleanName));
  const meta = parseSiteMeta(content);

  // List backups
  const backups = [];
  if (fs.existsSync(BACKUP_DIR)) {
    const backupFiles = fs.readdirSync(BACKUP_DIR);
    for (const b of backupFiles) {
      if (b.startsWith(`${cleanName}.`)) {
        try {
          const bStat = fs.statSync(path.join(BACKUP_DIR, b));
          backups.push({
            filename: b,
            timestamp: bStat.mtime.toISOString(),
            sizeBytes: bStat.size
          });
        } catch (_e) {}
      }
    }
    backups.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
  }

  return {
    name: cleanName,
    content,
    enabled,
    ...meta,
    backups
  };
}

/**
 * Save site configuration with automatic backup and syntax rollback safety
 */
export async function saveSite(name, content, autoReload = false) {
  const cleanName = validateSiteName(name);
  if (typeof content !== 'string' || content.trim().length === 0) {
    throw new Error('Configuration content cannot be empty.');
  }

  const filePath = path.join(NGINX_SITES_AVAILABLE, cleanName);
  if (!fs.existsSync(filePath)) {
    throw new Error(`Site "${cleanName}" does not exist.`);
  }

  // Ensure backup directory
  if (!fs.existsSync(BACKUP_DIR)) {
    fs.mkdirSync(BACKUP_DIR, { recursive: true, mode: 0o755 });
  }

  const originalContent = fs.readFileSync(filePath, 'utf8');
  const backupPath = path.join(BACKUP_DIR, `${cleanName}.${Date.now()}.bak`);
  fs.writeFileSync(backupPath, originalContent, 'utf8');

  // Write new content
  fs.writeFileSync(filePath, content, 'utf8');

  // Test syntax
  const test = await testNginx();
  if (!test.success) {
    // Revert immediately!
    fs.writeFileSync(filePath, originalContent, 'utf8');
    return {
      success: false,
      error: `Syntax test failed. Changes were automatically reverted to prevent downtime!\n\n${test.output}`,
      reverted: true
    };
  }

  let reloadResult = null;
  if (autoReload) {
    reloadResult = await reloadNginx();
  }

  return {
    success: true,
    message: autoReload 
      ? 'Configuration saved, verified, and Nginx reloaded successfully.' 
      : 'Configuration saved and syntax verified successfully.',
    reloaded: autoReload && reloadResult ? reloadResult.success : false,
    reloadError: reloadResult && !reloadResult.success ? reloadResult.output : null
  };
}

/**
 * Toggle site enabled/disabled state
 */
export async function toggleSite(name, enable, autoReload = true) {
  const cleanName = validateSiteName(name);
  const availablePath = path.join(NGINX_SITES_AVAILABLE, cleanName);
  const enabledPath = path.join(NGINX_SITES_ENABLED, cleanName);

  if (!fs.existsSync(availablePath)) {
    throw new Error(`Site "${cleanName}" not found in sites-available.`);
  }

  const wasEnabled = fs.existsSync(enabledPath);
  if (enable === wasEnabled) {
    return { success: true, enabled: enable, message: `Site is already ${enable ? 'enabled' : 'disabled'}.` };
  }

  if (enable) {
    fs.symlinkSync(availablePath, enabledPath);
  } else {
    fs.unlinkSync(enabledPath);
  }

  // Test syntax
  const test = await testNginx();
  if (!test.success) {
    // Revert symlink state
    if (enable) {
      try { fs.unlinkSync(enabledPath); } catch (_e) {}
    } else {
      try { fs.symlinkSync(availablePath, enabledPath); } catch (_e) {}
    }
    return {
      success: false,
      error: `Cannot ${enable ? 'enable' : 'disable'} site: syntax validation failed!\n\n${test.output}`,
      reverted: true
    };
  }

  let reloadRes = null;
  if (autoReload) {
    reloadRes = await reloadNginx();
  }

  return {
    success: true,
    enabled: enable,
    message: `Site "${cleanName}" ${enable ? 'enabled' : 'disabled'} successfully.`,
    reloaded: autoReload && reloadRes ? reloadRes.success : false
  };
}

/**
 * Create a new site configuration in sites-available
 */
export async function createSite(name, content, enableImmediately = false) {
  const cleanName = validateSiteName(name);
  if (typeof content !== 'string' || content.trim().length === 0) {
    throw new Error('Configuration content cannot be empty.');
  }

  const filePath = path.join(NGINX_SITES_AVAILABLE, cleanName);
  if (fs.existsSync(filePath)) {
    throw new Error(`Site "${cleanName}" already exists.`);
  }

  fs.writeFileSync(filePath, content, 'utf8');

  // Test syntax
  const test = await testNginx();
  if (!test.success) {
    try { fs.unlinkSync(filePath); } catch (_e) {}
    return {
      success: false,
      error: `Invalid Nginx configuration syntax:\n\n${test.output}`
    };
  }

  if (enableImmediately) {
    return toggleSite(cleanName, true, true);
  }

  return {
    success: true,
    message: `Site "${cleanName}" created successfully in sites-available.`
  };
}

/**
 * Delete a site configuration
 */
export async function deleteSite(name) {
  const cleanName = validateSiteName(name);
  if (cleanName === 'billing.chettiyarkada.in') {
    throw new Error('Cannot delete the active primary billing gate site.');
  }

  const availablePath = path.join(NGINX_SITES_AVAILABLE, cleanName);
  const enabledPath = path.join(NGINX_SITES_ENABLED, cleanName);

  if (!fs.existsSync(availablePath)) {
    throw new Error(`Site "${cleanName}" does not exist.`);
  }

  // Disable first if enabled
  if (fs.existsSync(enabledPath)) {
    fs.unlinkSync(enabledPath);
  }

  // Move to backups
  if (!fs.existsSync(BACKUP_DIR)) {
    fs.mkdirSync(BACKUP_DIR, { recursive: true, mode: 0o755 });
  }
  const backupPath = path.join(BACKUP_DIR, `${cleanName}.deleted.${Date.now()}.bak`);
  fs.renameSync(availablePath, backupPath);

  // Reload nginx
  await reloadNginx();

  return {
    success: true,
    message: `Site "${cleanName}" deleted and backed up to .backups/.`
  };
}
