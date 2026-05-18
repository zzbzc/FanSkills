# FanSkills

OpenClaw 飞书 Bot 技能集 —— Bot-to-Bot 协作调度基础设施。

## 架构

主 Bot 和其他能力 Bot 各自部署独立的 OpenClaw 实例，在同一个群聊中通过**真实 @ 提及**的富文本消息互相委派任务、回复结果。

```
用户 ──@──> 主 Bot ──路由匹配──> 目标 Bot(s)
                                    │
                              (处理任务)
                                    │
                         send_response.py ──@──> 原始请求者
```

## Skills

### 1. bot-delegate-send（任务分发）

主 Bot 侧使用。根据用户需求，智能匹配路由表，将任务分发给对应的能力 Bot。

**能力：**
- 单 Bot 分发：一个 Bot 覆盖所有需求
- 多 Bot 协同：拆分任务，分别发给不同专长的 Bot
- 无匹配兜底：回复用户"不确定该交给哪个 Bot"

**文件：**
| 文件 | 说明 |
|---|---|
| `SKILL.md` | 主说明文档，教 LLM 如何读取路由表、匹配任务、分发请求 |
| `ROUTES.md` | 路由配置表，维护任务类型 ↔ Bot open_id ↔ 触发关键词 |
| `send_delegation.py` | 发送脚本，调飞书 API 发 post 富文本（含真实 @） |
| `get-bot-openid.js` | 工具脚本，查询目标 Bot 的 open_id |

**使用方法：**

1. 将 `bot-delegate-send/` 目录放到 `~/.openclaw/skills/bot-delegate-send/`
2. 复制 `.env.example` 为 `.env`，填入你的飞书应用凭据：
   ```
   BOT_APP_ID=cli_xxx
   BOT_APP_SECRET=xxx
   ```
3. 编辑 `ROUTES.md`，配置你的 Bot 路由表：
   ```markdown
   | 任务类型 | bot 名称 | open_id | 触发关键词 |
   |---|---|---|---|
   | image | 图片生成 | ou_xxx_imagegen_bot | 生成图片,画一张,配图,做图 |
   | translate | 翻译 | ou_xxx_translate_bot | 翻译,translate |
   ```
4. 如需查询某个 Bot 的 open_id：
   ```bash
   node ~/.openclaw/skills/bot-delegate-send/get-bot-openid.js <app_id> <app_secret>
   ```

### 2. bot-delegate-recv（任务接收 & 回执）

能力 Bot 侧使用。接收被 @ 的委派消息，处理完成后 @ 原始请求者回复结果。

**文件：**
| 文件 | 说明 |
|---|---|
| `SKILL.md` | 主说明文档，教 LLM 如何解析委派、发送回执 |
| `send_response.py` | 回执脚本，调飞书 API 发 post 富文本（含真实 @） |

**使用方法：**

1. 将 `bot-delegate-recv/` 目录放到 `~/.openclaw/skills/bot-delegate-recv/`
2. 复制 `.env.example` 为 `.env`，填入你的飞书应用凭据：
   ```
   BOT_APP_ID=cli_xxx
   BOT_APP_SECRET=xxx
   ```
3. 在你的能力 Bot 的 OpenClaw 配置中启用 `bot-delegate-recv` skill

## 为什么需要这套 Skill

飞书 Bot 的普通文本回复通道**不支持解析 `<at>` 标签**，会原样显示为字符串。本套 Skill 通过飞书 API 直接发送 `post` 类型富文本消息，实现真正的 @ 提及。

## 快速上手

### 场景：用户在群里说 "帮我翻译这段文字并配图"

1. 主 Bot 匹配到 `translate` + `image` 两种任务类型
2. 查路由表发现翻译 → bot A，生图 → bot B（两个不同 Bot）
3. 分别调用 `send_delegation.py` 给 A 发翻译指令，给 B 发生图指令
4. A 和 B 各自处理完后，调用 `send_response.py` @ 原始请求者回复结果

### 场景：用户在群里说 "翻译这段文字"

1. 主 Bot 只匹配到 `translate` 类型
2. 一条委派消息发给翻译 Bot
3. 翻译完成后 @ 原始请求者回复

## 添加新能力 Bot

1. 获取新 Bot 的 open_id：
   ```bash
   node ~/.openclaw/skills/bot-delegate-send/get-bot-openid.js <app_id> <app_secret>
   ```
2. 在 `ROUTES.md` 新增一行路由配置
3. 在新 Bot 的 OpenClaw 实例中启用 `bot-delegate-recv` skill
4. （可选）为新 Bot 编写专属的接收端 skill，定义具体处理逻辑
