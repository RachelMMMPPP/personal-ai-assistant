# Gmail × Claude 邮件回复助手

用 Claude AI 生成 Gmail 邮件回复草稿，支持 RAG（基于历史邮件的检索增强生成）。

提供两种使用方式：
- **Web UI**：FastAPI 后端 + React 前端
- **CLI**：命令行交互模式

## 项目结构

```
gmail-claude-reply/
├── api.py             # FastAPI 后端入口
├── main.py            # CLI 入口（保留）
├── gmail_client.py    # Gmail API 封装（OAuth2 + MIME 解析）
├── claude_client.py   # Claude API 封装（流式 + 自适应思考）
├── vector_store.py    # RAG 层（ChromaDB + OpenAI Embeddings）
├── requirements.txt
├── .env.example
├── frontend/          # React + Vite + TypeScript 前端
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── components/
│   │       ├── EmailList.tsx
│   │       ├── EmailDetail.tsx
│   │       └── DraftPanel.tsx
│   └── package.json
└── credentials/       # OAuth2 凭证（不提交 git）
```

## 快速开始

### 1. Python 依赖

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

| 变量 | 说明 |
|---|---|
| `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com) 获取 |
| `OPENAI_API_KEY` | 可选，用于 RAG embedding；不填则跳过 RAG |
| `GMAIL_CREDENTIALS_PATH` | OAuth2 凭证路径（默认 `credentials/client_secret.json`） |
| `GMAIL_TOKEN_PATH` | Token 缓存路径（默认 `credentials/token.json`） |
| `CHROMA_DB_PATH` | 向量数据库路径（默认 `.chroma_db`） |

### 3. Gmail OAuth2

1. [Google Cloud Console](https://console.cloud.google.com) → 创建项目 → 启用 Gmail API
2. 创建 OAuth 2.0 客户端（桌面应用），下载 JSON
3. 保存为 `credentials/client_secret.json`
4. 首次启动后端时浏览器会自动打开授权页面，授权后 token 自动缓存

### 4. 前端依赖

```bash
cd frontend
npm install
```

## 运行

### Web UI 模式

终端 1 — 启动后端：
```bash
uvicorn api:app --reload --port 8000
```

终端 2 — 启动前端：
```bash
cd frontend
npm run dev
```

浏览器访问 `http://localhost:5173`

### CLI 模式

```bash
# 交互式生成回复草稿
python main.py

# 索引最近 100 封邮件到向量数据库（启用 RAG）
python main.py index
```

## API 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/emails` | 获取最新 10 封邮件 |
| POST | `/api/index` | 索引最近 100 封邮件 |
| POST | `/api/draft` | 生成回复草稿（SSE 流式） |

## RAG 架构

```
用户选择邮件
     │
     ▼
search_similar(query, n=5)          ← ChromaDB cosine 检索
     │
     ▼
build_rag_prompt(email, similar)    ← 组装 prompt（相似邮件 + 待回复邮件）
     │
     ▼
Claude claude-opus-4-7              ← SSE 流式输出（自适应思考）
     │
     ▼
前端实时显示草稿
```

- **向量数据库**：ChromaDB（本地持久化，cosine 相似度）
- **Embedding 模型**：OpenAI `text-embedding-3-small`
- **RAG 降级**：未设置 `OPENAI_API_KEY` 时自动跳过，正常生成草稿

## 注意事项

- Gmail OAuth2 scope 仅为只读（`gmail.readonly`），不会修改或发送邮件
- `.chroma_db/` 目录为本地向量库，不提交 git
