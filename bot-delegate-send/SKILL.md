---
name: bot-delegate-send
description: |
  向群内的其他 bot 分发任务（多 bot 路由）。根据用户需求，智能匹配并分发到对应的 bot，支持单 bot 分发和多 bot 协同。

  **何时使用:**
  - 用户在群聊中提出需要某个 bot 处理的任务
  - 路由表(ROUTES.md)中有匹配的任务类型

  **何时不用:**
  - 用户只是聊天，不需要其他 bot 处理
---

# Bot 任务分发（路由模式）

## 核心原则

飞书 bot 的普通文本输出通道不解析 `<at>` 标签。必须通过 `send_delegation.py` 脚本调飞书 API 发送 post 富文本消息。

## 工作流程

### Step 1: 读取路由表

读取 `~/.openclaw/skills/bot-delegate-send/ROUTES.md`，获取任务类型与 bot 的映射关系。

### Step 2: 匹配任务类型

从用户消息中提取需求，对照 ROUTES.md 的 **触发关键词** 和 **任务类型** 列，判断涉及哪些任务类型。

### Step 3: 路由决策

根据匹配结果决定分发策略：

**情况 A — 单 bot 处理**（一个 bot 覆盖所有任务类型）
- 例：用户请求"翻译这段文字"，只匹配到 translate，对应 bot A
- 决策：一条消息发给 bot A

**情况 B — 多 bot 协同**（多个 bot 各负责一部分）
- 例：用户请求"翻译并配图"，匹配到 translate(→bot A) + image(→bot B)
- 决策：分别给 bot A 和 bot B 发送消息，各自处理对应的子任务

**情况 C — 无匹配路由**
- 例：用户请求"帮我写首歌"，路由表中没有匹配的类型
- 回复用户："不确定该交给哪个 bot，请告诉我具体需要什么类型的服务。"

### Step 4: 构造各 bot 的消息内容

为每个目标 bot 构造专属消息，只包含与该 bot 能力相关的指令：

| 场景 | 消息构造 |
|---|---|
| 单 bot | 完整用户需求 |
| 多 bot | 拆分任务，每只 bot 只收到属于自己的部分 |

### Step 5: 发送委派消息

逐个调用脚本：

```bash
python3 ~/.openclaw/skills/bot-delegate-send/send_delegation.py "<target_open_id>" "<message>" "<chat_id>" "<sender_open_id>"
```

参数：
- `<target_open_id>` —— 从 ROUTES.md 获取的目标 bot open_id
- `<message>` —— 为该 bot 构造的消息内容
- `<chat_id>` —— 从 inbound 消息 metadata 提取（去掉 `chat:` 前缀）
- `<sender_open_id>` —— 可选，原始请求者的 open_id

**注意 shell 转义：** 如果消息包含双引号、反引号、`$` 等特殊字符，使用单引号包裹或 bash `$'...'` 形式。

### Step 6: 观察脚本输出

- **成功** —— 退出码 0，stdout 包含 `OK message_id=om_xxx`
- **失败** —— 退出码 1，stderr 含错误描述。如实告知用户。

### Step 7: 给用户简短确认

**单 bot：**
```
已派发给图片生成 bot 处理，稍等。
```

**多 bot：**
```
已分发给翻译 bot 和图片生成 bot，稍等片刻。
```

## 约束

- **必须先调脚本，后说话**
- **不要在文本响应里手工 @ 任何 bot**
- **多 bot 分发时，每个 bot 的消息内容要专属化，不要发重复的完整需求**
- **脚本失败时不要假装成功**
- **每次调用都取新 token**（脚本内部处理）

## 获取目标 bot 的 open_id

如果不知道目标 bot 的 open_id：

```bash
node ~/.openclaw/skills/bot-delegate-send/get-bot-openid.js <app_id> <app_secret>
```

然后把结果写入 ROUTES.md。
