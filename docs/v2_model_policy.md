# 数字人世界 V2：模型策略层

## 目标

在不破坏 V1 世界闭环的前提下，把“个体如何决策”从启发式规则切换成可插拔策略：

- 默认仍可使用启发式策略
- 配置完成后可切到 OpenAI 兼容模型
- 模型输出异常时自动回退到启发式策略

## 当前实现

### 配置

通过 `.env` 或环境变量读取：

- `DHW_POLICY_MODE=auto|heuristic|openai`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `DHW_TIMEOUT_SECONDS`
- `DHW_TEMPERATURE`
- `DHW_FALLBACK_TO_HEURISTIC`

默认行为：

- `auto` 模式下，如果 `OPENAI_API_KEY` 和 `OPENAI_MODEL` 都存在，则启用模型策略
- 否则回退为启发式策略

### 模型接口

当前使用 OpenAI 兼容的 `chat/completions` 接口，零额外依赖，直接用标准库 `urllib` 发送请求。

模型输入包含：

- 当前 observation
- trigger reasons
- working memory
- profile
- 当前地点、库存、可见工具、可见任务
- 可用 location id / task id

模型必须输出单个 JSON 对象：

```json
{
  "think": "I should get the broom first.",
  "reason": "get_required_tool",
  "action": {
    "action_type": "GO",
    "target": "warehouse",
    "payload": {}
  }
}
```

也允许：

```json
{
  "think": "Nothing changed that needs action.",
  "reason": "idle_no_action",
  "action": null
}
```

### 环境仍然掌握现实裁定

模型只负责给出动作意图。
动作持续时间、是否合法、是否成功，仍由环境决定。

例如：

- `GO` 的 duration 由地图距离决定
- `DO` 的 duration 由任务类型或 payload 决定
- `REST` 默认 3 tick

## 运行方式

### 启发式模式

`.env` 中不填 `OPENAI_MODEL`，或设置：

```env
DHW_POLICY_MODE=heuristic
```

### 模型模式

```env
DHW_POLICY_MODE=openai
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://your-compatible-endpoint/v1
OPENAI_MODEL=your-model-name
```

运行：

```powershell
python run_v1.py
```

输出会显示 `policy_mode`，用于确认当前实际使用的策略。
