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

### Step 2: 调用 image_generate 工具

使用 `image_generate({...})` 工具直接生图，参数格式:

```json
{
  "model": "openai/gpt-image-1-mini",
  "prompt": "<生图提示词>",
  "size": "1024x1024",
  "quality": "low",
  "outputFormat": "png",
  "filename": "<有意义的文件名>.png",
  "count": 1,
  "timeoutMs": 120000
}
```

- **model**: 固定使用 `openai/gpt-image-1-mini`
- **prompt**: 根据用户请求构造，可融合风格描述
- **size**: 默认 `1024x1024`，按需调整
- **quality**: 预览用 `low`，高质量用 `high`
- **filename**: 用任务编号或有意义的英文短词命名

工具返回的是**本地文件路径**（不是 URL），例如:
```
/path/to/output/test-blue-cube---uuid.png
```

### Step 3: 上传图片到飞书，获取 image_key

使用飞书 API 上传本地图片文件:

```bash
# 获取 tenant_access_token
TOKEN=$(curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d "{\"app_id\":\"$IMAGE_BOT_APP_ID\",\"app_secret\":\"$IMAGE_BOT_APP_SECRET\"}" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['tenant_access_token'])")

# 上传图片获取 image_key
IMAGE_KEY=$(curl -s -X POST 'https://open.feishu.cn/open-apis/im/v1/images' \
  -H "Authorization: Bearer $TOKEN" \
  -F 'image_type=message' \
  -F "image=@<本地文件路径>" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['image_key'])")
```

输出 `IMAGE_KEY` 供下一步使用。

### Step 4: 发送结果到群聊

使用飞书消息 API 发送包含图片的消息:

```bash
curl -s -X POST 'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{
    \"receive_id\": \"$DEMO_GROUP_CHAT_ID\",
    \"msg_type\": \"post\",
    \"content\": \"{\\\"zh_cn\\\":{\\\"title\\\":\\\"\\\",\\\"content\\\":[[{\\\"tag\\\":\\\"text\\\",\\\"text\\\":\\\"[REQ-任务编号] ✅\\\"},{\\\"tag\\\":\\\"img\\\",\\\"image_key\\\":\\\"$IMAGE_KEY\\\"}]]}}\"
  }"
}
```

### 失败处理

如果生图失败（内容安全、超时等），发送失败回执:

```json
{
  "zh_cn": {
    "title": "",
    "content": [
      [{"tag": "text", "text": "[REQ-任务编号] ❌\n生成失败: <错误原因>"}]
    ]
  }
}
```

## 环境变量

| 变量 | 用途 |
|------|------|
| `IMAGE_BOT_APP_ID` | 飞书 Bot App ID |
| `IMAGE_BOT_APP_SECRET` | 飞书 Bot App Secret |
| `DEMO_GROUP_CHAT_ID` | 目标群聊 chat_id |

## 约束

- **只处理图片生成委托**，不处理其他消息
- **失败也要发送回执**，让委托方知道结果
- **不要在群聊中发送裸 URL**，图片通过 img tag 发送
- **不要重新描述图片内容**，回执保持简洁
