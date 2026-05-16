---
name: bot-delegate-recv
description: |
  接收来自其他 bot 的委派消息（群聊中被 @ 提及），处理任务后 @ 原始请求者回复结果。

  **何时使用:**
  - 本 bot 在群聊中被其他 bot @ 提及并收到任务委派
  - 消息包含明确的指令或待处理内容

  **何时不用:**
  - 用户直接对话（非 bot 委派）
  - 消息来自未知 bot 且无法识别任务内容
---

# Bot 委派接收

## 工作流程

### Step 1: 解析委派消息

从 inbound 消息中提取：
- **sender_open_id**：原始请求 bot（或用户）的 open_id
- **chat_id**：群聊 ID（从 inbound metadata 的 `chat_id` 字段，去掉 `chat:` 前缀）
- **消息内容**：提取具体的任务描述/指令

### Step 2: 处理任务

根据消息内容执行对应的处理逻辑。

### Step 3: 发送回执回复

处理完成后，使用脚本 `send_response.py` 发送带 @ 的富文本回执：

```bash
python3 ~/.openclaw/skills/bot-delegate-recv/send_response.py "<response_message>" "<chat_id>" "<sender_open_id>"
```

**成功示例：**
```bash
python3 ~/.openclaw/skills/bot-delegate-recv/send_response.py "任务已完成，请查看结果" "oc_xxx" "ou_xxx"
```

**失败示例：**
```bash
python3 ~/.openclaw/skills/bot-delegate-recv/send_response.py "处理失败: 具体错误原因" "oc_xxx" "ou_xxx"
```

### Step 4: 检查结果

- **成功** —— 退出码 0，stdout 包含 `OK message_id=om_xxx`
- **失败** —— 退出码 1，stderr 含错误描述

## 约束

- **回执必须 @ 原始发送者**，确保对方能收到通知
- **成功和失败都要发回执**，不要静默失败
- **每次调用都取新 token**（脚本内部处理）
- **不要在普通文本响应中手工 @ 任何用户/bot**
