# 数字人世界 V1 设计冻结

## 1. V1 目标

V1 不追求完整社会，也不追求长期记忆直接写入模型参数。

V1 只验证四件事：

1. 个体不是每个时间步都重算，而是由环境触发决策。
2. 行动具有持续时间，执行中的行动和完成后的行动会影响下一次决策。
3. working memory 只承载白天的短期连续性。
4. 夜间 consolidation 会把高价值经历整理到个人 profile。

## 2. 固定约束

### 时间

- 基础时间颗粒：`10s`
- 世界统一时钟推进
- 所有行动都要占用一个或多个 tick

### 决策触发

个体只在以下三类条件成立时进入决策：

1. 观察内容发生显著变化
2. 出现涉及该个体的事件
3. 上一个行动完成、失败或被打断

### 记忆结构

#### working memory

白天运行态短期记忆，和 observation 一起提交给模型。

包含：

- `active_goal`
- `current_intent`
- `recent_observation_changes`
- `recent_events`
- `recent_outcomes`
- `episodic_buffer`

#### profile

夜间整理后的长期结构化记忆。

包含：

- `learned_rules`
- `preferences`
- `skills`
- `habits`

V1 中 profile 是显式结构化数据。
后续如需要做参数化长期记忆，可把 profile 视为巩固阶段的桥接表示。

## 3. V1 架构

### WorldClock

- 每 tick 推进 `10s`
- 负责昼夜切换
- 触发夜间 consolidation

### WorldState

- 维护地图、地点类型、天气、任务、工具、人物位置
- 维护正在执行的动作
- 提供环境裁定接口

### Inspector

- 从世界状态生成个体局部 observation
- observation 同时保留结构化字段和文本摘要

### ObservationDiff

- 对比本轮与上一轮 observation
- 只把显著变化标记为决策触发

### Action Scheduler / Resolver

- 接收决策结果并创建动作实例
- 让动作跨多个 tick 执行
- 在完成、失败或中断时生成事件

### MemoryManager

- 白天把事件、观察变化、行动结果写入 working memory
- 夜间把高价值经验整理进 profile

### Policy Interface

- 统一接口：`decide(observation, working_memory, profile) -> THINK + ACTION`
- V1 使用规则策略模拟“微缩模型”
- 后续可以直接替换成真实模型

## 4. 动作状态机

每个动作都有：

- 类型
- 目标
- 开始时间
- 剩余 tick
- 是否可打断

动作生命周期：

1. `planned`
2. `executing`
3. `completed` / `failed` / `interrupted`

V1 默认动作：

- `GO`
- `DO`
- `USE`
- `SPEAK`
- `REST`
- `LEARN`

## 5. 打断规则

V1 固定如下规则：

- 普通观察变化不打断当前动作
- 高优先级事件可以打断当前动作

V1 唯一实现的高优先级打断：

- 下雨开始时，如果个体处于户外并且当前动作可打断，则打断当前动作并重新决策

## 6. 夜间巩固

夜间 consolidation 在 `21:00` 触发。

V1 只整理两类长期经验：

1. 工具规则
2. 天气偏好

具体规则：

- 如果白天发生“清洁失败且原因是没有扫帚”，则写入 `clean_square_requires_broom`
- 如果白天发生“在户外遭遇降雨并被迫回避”，则写入 `avoid_outdoor_in_rain`

## 7. 演示场景

V1 用一个两天场景演示完整闭环：

### Day 1

- 08:00 收到清洁广场任务
- 个体起初不知道清洁需要扫帚
- 在广场尝试清洁失败，学到“需要工具”
- 去仓库取扫帚
- 在户外清洁时遭遇降雨，被打断并回家
- 夜间 consolidation 更新 profile

### Day 2

- 08:00 再次收到清洁任务
- 早晨正在下雨
- 个体因为 profile 中已有避雨偏好，先在家等待
- 天气转晴后，因为 profile 中已有工具规则，直接去仓库取扫帚
- 完成清洁

## 8. V1 不做什么

- 不做在线训练
- 不做参数更新
- 不做多自主体社会传播
- 不做复杂经济系统
- 不做 UI

V1 的重点是把“环境触发决策 + 动作持续执行 + 双层记忆”闭环做稳定。
