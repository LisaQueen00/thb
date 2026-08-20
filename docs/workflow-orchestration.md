# Meaning-only workflow

THB v0.1 的唯一产品链路是 `Input → Strip → Extract → MeaningResult`。

- Input 保存原始消息和可选背景。
- Strip 标记沟通表达，不改变原文。
- Extract 建立有证据边界的事件模型、`event_summary` 调试摘要和内部
  `meaning_selection`。
- Meaning 从 `meaning_selection` 选择高置信度、高产品重要度信息，进行确定性去重与
  简洁合成，不调用模型，也不读取 `event_summary` 作为结果来源。

`event_summary` 不只是显性句面的改写。对于纠正、改善、否定提醒、责问或责任预设，
它会恢复原句有充分依据的必要隐含前提，并以“对方认为/描述为”等方式保留来源边界。
普通请求和通知不会被强行加入负面评价；向上汇报也不会在没有证据时被解释为投诉、
施压或升级处理。

Extract 在同一次结构化输出中维护内部 `pragmatic_interpretation`：

- `explicit_content`：显性断言、要求、询问和通知；
- `implied_stances`：原句强烈支持的预设或立场，使用 high/medium/low 离散置信度；
- `contextual_implications`：依赖更多语境的效果、目的或心理动机。

最终 Meaning 默认组合显性内容与有独立认知价值的高置信度 implied stance，并保留
unknown/unconfirmed 边界。低置信度立场和 contextual implication 默认不进入输出。
这个内部结构不会出现在 Public API 中。

`meaning_selection` 将候选信息标记为 core speech act、material stance、fact boundary、
responsibility、commitment、consequence 或 conflict，并分别记录 confidence 与
materiality。普通执行细节缺失默认是低产品重要度，不进入最终 Meaning。

Python 调用和 `POST /api/v1/thb` 使用同一个 `THBWorkflow.run()`。HTTP 请求只接受
`source_message` 与可选 `context`，成功响应只返回 `meaning`。阶段失败继续以
`<STAGE>_FAILED`、阶段名和错误消息传播。

本版本没有策略选择、回复生成、用户目标、暂停或恢复接口。
