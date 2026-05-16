#!/usr/bin/env python3
"""
send_delegation.py — 向群内其他 bot 发送带真实 @ 的富文本消息

用法:
  python3 send_delegation.py <target_bot_open_id> <message_content> <chat_id> [sender_open_id]

参数:
  target_bot_open_id  —— 目标 bot 的 open_id (ou_xxx)
  message_content     —— 要传达给目标 bot 的内容
  chat_id             —— 群聊 ID (oc_xxx)
  sender_open_id      —— 可选,原始请求者的 open_id,用于回执时 @ 回来

环境变量(从脚本同目录的 .env 文件读取):
  BOT_APP_ID       —— 本 bot 飞书应用 App ID
  BOT_APP_SECRET   —— 本 bot 飞书应用 App Secret

退出码:
  0 —— 成功
  1 —— 失败
"""

import sys
import os
import json
from pathlib import Path

# 从脚本同目录下的 .env 文件读取环境变量
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            value = value.split('#', 1)[0].strip()
            os.environ.setdefault(key.strip(), value)

APP_ID = os.environ.get('BOT_APP_ID')
APP_SECRET = os.environ.get('BOT_APP_SECRET')

TARGET_OPEN_ID = sys.argv[1] if len(sys.argv) > 1 else None
MESSAGE = sys.argv[2] if len(sys.argv) > 2 else None
CHAT_ID = sys.argv[3] if len(sys.argv) > 3 else None
SENDER_OPEN_ID = sys.argv[4] if len(sys.argv) > 4 else ''

def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

if not TARGET_OPEN_ID:
    die('用法: python3 send_delegation.py <target_bot_open_id> <message> <chat_id> [sender_open_id]')
if not MESSAGE:
    die('message_content 不能为空')
if not CHAT_ID:
    die('chat_id 不能为空')
if not APP_ID:
    die('环境变量 BOT_APP_ID 未设置(请在 .env 文件中配置)')
if not APP_SECRET:
    die('环境变量 BOT_APP_SECRET 未设置(请在 .env 文件中配置)')

import urllib.request
import urllib.error

def feishu_request(url, body, headers=None):
    req = urllib.request.Request(url, data=body.encode() if isinstance(body, str) else body, method='POST')
    req.add_header('Content-Type', 'application/json')
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            return resp.status, data
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            pass
        return e.code, body

def main():
    # Step 1: 获取 tenant_access_token
    token_body = json.dumps({'app_id': APP_ID, 'app_secret': APP_SECRET})
    status, token_res = feishu_request(
        'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
        token_body
    )
    if status != 200 or token_res.get('code') != 0:
        die(f'获取 tenant_access_token 失败: {json.dumps(token_res)}')
    token = token_res['tenant_access_token']

    # Step 2: 构造富文本消息
    paragraphs = [
        [{'tag': 'at', 'user_id': TARGET_OPEN_ID}, {'tag': 'text', 'text': f' {MESSAGE}'}]
    ]

    if SENDER_OPEN_ID:
        paragraphs.append([
            {'tag': 'at', 'user_id': SENDER_OPEN_ID},
            {'tag': 'text', 'text': ' 请关注下方处理结果'}
        ])

    content = {'zh_cn': {'title': '', 'content': paragraphs}}
    message_body = json.dumps({
        'receive_id': CHAT_ID,
        'msg_type': 'post',
        'content': json.dumps(content),
    })

    # Step 3: 发送消息
    headers = {'Authorization': f'Bearer {token}'}
    status, msg_res = feishu_request(
        'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id',
        message_body,
        headers
    )

    if status != 200 or msg_res.get('code') != 0:
        die(f'发送消息失败: {json.dumps(msg_res)}')

    message_id = msg_res.get('data', {}).get('message_id', '')
    print(f'OK message_id={message_id}')

if __name__ == '__main__':
    main()
