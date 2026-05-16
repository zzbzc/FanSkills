---
name: routes
---

# 路由表

每行代表「任务类型 → 某个 bot」的映射。一个 bot 可以有多行（多能力），一个任务类型也可以对应多个 bot。

| 任务类型 | bot 名称 | open_id | 触发关键词 |
|---|---|---|---|
| image | 图片生成 | ou_xxx_imagegen_bot | 生成图片,画一张,配图,做图 |
| translate | 翻译 | ou_xxx_translate_bot | 翻译,translate |

## 编辑说明

1. **添加新 bot**：新增一行，填写任务类型、bot 名称、open_id、触发关键词
2. **一个 bot 多个能力**：添加多行，同一 bot 名称 + open_id，不同任务类型
3. **同类型多个 bot**：添加多行，同一任务类型，不同 bot
4. **获取 open_id**：运行 `node ~/.openclaw/skills/bot-delegate-send/get-bot-openid.js <app_id> <app_secret>`
