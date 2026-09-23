import test from 'node:test';
import assert from 'node:assert/strict';
import { isLocalAdminRequest } from '../lib/local-admin.js';
const request = (remoteAddress, headers = {}) => ({ socket: { remoteAddress }, headers: { host: '127.0.0.1:3100', ...headers } });
test('allows direct loopback access', () => {
  for (const ip of ['127.0.0.1', '::1', '::ffff:127.0.0.1']) assert.equal(isLocalAdminRequest(request(ip)), true);
  for (const host of ['localhost:3100', '[::1]:3100', '127.0.0.1:3100']) {
    assert.equal(isLocalAdminRequest(request('::1', { host, origin: `http://${host}`, 'sec-fetch-site': 'same-origin' })), true);
  }
});
test('rejects remote and missing addresses', () => {
  for (const ip of ['192.168.1.1', '203.0.113.2', '::ffff:192.168.1.1', undefined]) assert.equal(isLocalAdminRequest(request(ip)), false);
});
test('rejects proxy headers including spoofed loopback', () => {
  for (const header of ['forwarded', 'x-forwarded-for', 'x-forwarded-proto', 'x-real-ip', 'x-forwarded-host']) {
    for (const value of ['', '127.0.0.1']) assert.equal(isLocalAdminRequest(request('127.0.0.1', { [header]: value })), false);
  }
});
test('rejects DNS rebinding and cross-origin requests', () => {
  for (const host of ['evil.example', 'localhost.evil.example', 'localhost@evil.example', '', '127.999.0.1']) assert.equal(isLocalAdminRequest(request('::1', { host })), false);
  for (const origin of ['https://evil.example', 'null', 'http://127.0.0.1:9999']) assert.equal(isLocalAdminRequest(request('::1', { origin })), false);
  for (const site of ['cross-site', 'same-site']) assert.equal(isLocalAdminRequest(request('::1', { 'sec-fetch-site': site })), false);
});
