# THB v0.1 — Meaning Only

THB 将一段沟通文本压缩为可核验的事件含义。正式链路只有：

```text
Input → Strip → Extract → MeaningResult
```

它不选择策略、不生成回复，也不接收 `user_goal`。Extract 在现有模型调用中生成丰富
事件结构和内部 `meaning_selection`，MeaningService 再确定性选择、去重并合成
`MeaningResult`；不会新增模型调用，也不再把 `event_summary` 直接作为 Public Meaning。

## Python

```python
from thb import THB

result = THB("会议改到周三上午十点，地点不变。")
print(result.meaning)
```

## HTTP API

```bash
uvicorn thb_input.main:app --reload
```

`POST /api/v1/thb`：

```json
{
  "source_message": "会议改到周三上午十点，地点不变。",
  "context": null
}
```

成功响应只包含：

```json
{
  "meaning": "会议时间改为周三上午十点，地点保持不变。"
}
```

Swagger UI：`http://127.0.0.1:8000/docs`。
