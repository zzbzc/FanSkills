#!/usr/bin/env node
// 用法: node get-bot-openid.js <app_id> <app_secret>
// 输出: bot 的 open_id

const https = require('https');
const [,, appId, appSecret] = process.argv;
if (!appId || !appSecret) {
  console.error('用法: node get-bot-openid.js <app_id> <app_secret>');
  process.exit(1);
}

function postJson(hostname, path, body, headers = {}) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = https.request({
      hostname, path, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data), ...headers }
    }, res => {
      let buf = '';
      res.on('data', c => buf += c);
      res.on('end', () => { try { resolve(JSON.parse(buf)); } catch(e) { reject(e); } });
    });
    req.on('error', reject);
    req.write(data); req.end();
  });
}

function getJson(hostname, path, headers = {}) {
  return new Promise((resolve, reject) => {
    https.request({ hostname, path, method: 'GET', headers }, res => {
      let buf = '';
      res.on('data', c => buf += c);
      res.on('end', () => { try { resolve(JSON.parse(buf)); } catch(e) { reject(e); } });
    }).on('error', reject).end();
  });
}

(async () => {
  const tokenRes = await postJson('open.feishu.cn', '/open-apis/auth/v3/tenant_access_token/internal',
    { app_id: appId, app_secret: appSecret });
  if (tokenRes.code !== 0) { console.error('取 token 失败:', tokenRes); process.exit(1); }

  const infoRes = await getJson('open.feishu.cn', '/open-apis/bot/v3/info',
    { Authorization: `Bearer ${tokenRes.tenant_access_token}` });
  if (infoRes.code !== 0) { console.error('查 bot info 失败:', infoRes); process.exit(1); }

  console.log('open_id:', infoRes.bot.open_id);
  console.log('app_name:', infoRes.bot.app_name);
})();