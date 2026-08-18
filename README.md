# THB

THB 将用户获得的人际沟通信息转换为结构化数据，为后续分析流程提供保真、可验证且具有明确安全边界的输入。

## 功能

### Input

Input 接收用户粘贴的沟通原文及可选上下文，并生成 canonical input object：

- 忠实保留 `source_message` 和 `context`；
- 记录来源元数据、原始来源和未知字段；
- 检测 Prompt Injection 并将其标记为不可信数据；
- 不执行输入中的指令，也不删除、替换或改写原文。

接口：`POST /api/v1/input/text`

### Strip

Strip 接收 Input 产生的 canonical input object，使用大模型识别沟通内容的结构和语义标签：

- 将原文划分为可无损拼回的 segments；
- 为各 segment 标注陈述、要求、压力、模糊表达等沟通特征；
- 生成确定性的结构摘要；
- 将所有输入内容视为待分析数据，不执行其中的指令。

接口：`POST /api/v1/strip`

## 技术栈

- Python 3.12+
- FastAPI、Pydantic
- OpenAI-compatible Responses / Chat Completions API
- pytest、Ruff
- pnpm workspace

## 本地运行

Python 依赖安装在项目虚拟环境中：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn thb_input.main:app --reload
```

前端依赖使用 pnpm 安装在项目范围内：

```powershell
pnpm install
```

将 `.env.example` 复制为 `.env` 并填写本地模型配置。`.env` 包含私密配置，不应提交到版本库。

## 测试

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check src tests scripts
```

## 健康检查

服务启动后访问 `GET /health`，正常响应为：

```json
{"status": "ok"}
```
