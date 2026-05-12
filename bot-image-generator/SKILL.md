---
name: bot-image-generator
description: |
  图片生成 bot。当收到图片生成委托请求时，直接调用 image_generate MCP 工具生图，
  然后通过飞书 API 将图片发送到群聊。

  **何时使用:**
  - 收到图片生成委托消息（来自 bot-delegate-image 或其他触发源）
  - 消息包含生图提示词和任务编号

  **何时不用:**
  - 处理图片 bot 回执（含 [REQ-...] ✅/❌ 标记）—— 那是 bot-image-followup 的职责
---

# 图片生成

## 工作流程

### Step 1: 解析请求

从消息中提取:
- 任务编号 `[REQ-YYYYMMDD-HHMMSS-XXX]`
- 生图提示词（prompt）
- 可选参数（尺寸、风格等）
- 发送者的 open_id（用于回执消息中 @ 提对方）
- 群聊 chat_id（从 inbound metadata 的 `chat_id` 字段获取，去掉 `chat:` 前缀）

### Step 2: 调用 image_generate 工具

使用 `image_generate({...})` 工具直接生图:

```json
{
  "model": "openai/gpt-image-2",
  "prompt": "<生图提示词>",
  "size": "1024x1024",
  "quality": "high",
  "outputFormat": "png",
  "filename": "<任务编号>.png",
  "count": 1,
  "timeoutMs": 120000
}
```

- **model**: 优先 `openai/gpt-image-2`，没有则回退到 `gpt-image-1.5`
- **prompt**: 根据用户请求构造，可融合风格描述
- **filename**: 用任务编号命名

工具返回 MEDIA 路径（本地文件），类似:
```
MEDIA:/root/.openclaw/media/tool-image-generation/xxx.png
```

### Step 3: 获取 token、上传图片、发送回执（合并为一步）

**关键点：** 不能直接回复消息（reply 不支持图片），必须用主动发送方式。
也不能依赖环境变量，飞书凭据从 gateway 配置（openclaw.json 的 `channels.feishu`）中读取。

三个子步骤合并在一个 Python 脚本中完成:

```python
import json, urllib.request

# 配置
IMAGE_BOT_APP_ID = "cli_xxx"
IMAGE_BOT_APP_SECRET = "xxx"
chat_id = "oc_xxx"  # 从 inbound metadata chat_id 去掉 "chat:" 前缀
image_path = "/root/.../output.png"  # Step 2 返回的本地文件路径
req_id = "REQ-xxx-xxx"
sender_id = "ou_xxx"  # 发起请求者的 open_id

# 1. 获取 tenant_access_token
req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=json.dumps({"app_id": IMAGE_BOT_APP_ID, "app_secret": IMAGE_BOT_APP_SECRET}).encode(),
    headers={"Content-Type": "application/json"}
)
TOKEN = json.loads(urllib.request.urlopen(req).read())["tenant_access_token"]

# 2. 上传图片获取 image_key
import subprocess
result = subprocess.run([
    "curl", "-s", "-X", "POST",
    "https://open.feishu.cn/open-apis/im/v1/images",
    "-H", f"Authorization: Bearer {TOKEN}",
    "-F", "image_type=message",
    "-F", f"image=@{image_path}"
], capture_output=True, text=True)
IMAGE_KEY = json.loads(result.stdout)["data"]["image_key"]

# 3. 发送回执消息（@at + 任务编号 + 图片）
content_obj = {
    "zh_cn": {
        "title": "",
        "content": [[
            {"tag": "at", "user_id": sender_id},
            {"tag": "text", "text": f" [{req_id}] ✅"},
            {"tag": "img", "image_key": IMAGE_KEY}
        ]]
    }
}

body = {
    "receive_id": chat_id,
    "msg_type": "post",
    "content": json.dumps(content_obj, ensure_ascii=False)
}

req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
    data=json.dumps(body).encode("utf-8"),
    headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}
)
urllib.request.urlopen(req)
```

### 失败处理

如果生图失败（内容安全、超时等），发送带 @ 提的失败回执:

```python
content_obj = {
    "zh_cn": {
        "title": "",
        "content": [[
            {"tag": "at", "user_id": sender_id},
            {"tag": "text", "text": f" [{req_id}] ❌\n生成失败: {错误原因}"}
        ]]
    }
}
```

## 约束

- **只处理图片生成委托**，不处理其他消息
- **失败也要发送回执**，让委托方知道结果
- **回执消息必须 @ 提原始发送者**，成功失败都要
- **不要在群聊中发送裸 URL**，图片通过 img tag 发送
- **不要重新描述图片内容**，回执保持简洁
- **每次调用都取新 token**（不要复用过期 token）
