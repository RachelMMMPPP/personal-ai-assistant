# 个人AI助手 — 用我自己的口吻自动回复

## 项目简介

这个项目的目标是训练一个"懂我"的AI助手，能够用**我自己的语气和风格**自动生成邮件回复草稿。

项目最初希望同时实现Gmail和WhatsApp的自动回复。我收集了两个平台的个人数据进行模型训练，但WhatsApp遇到了限制——个人账户无法直接使用自动回复，必须申请**WhatsApp Business API**并完成企业认证，对个人项目门槛较高。因此目前以Gmail为主要演示。

---

## 两种实现方案

### 方案一：调用现有大模型（当前项目）
直接接入 **Claude API**，通过 Prompt Engineering 让模型模仿我的语气生成回复草稿，配合 Gmail API 实现邮件读取和草稿保存。


### 方案二：训练自己的模型（探索版）
收集个人数据，对比微调多个开源模型，部署后提供个性化回复服务。

---

## 方案二详细过程

### 第一步：数据收集

**Gmail数据**
- 使用 Gmail API 导出个人历史邮件
- 提取发件人、收件人、主题、正文，整理成训练格式

**WhatsApp数据**
- 手动从手机导出聊天记录（.txt 格式）
- 用 Python 脚本解析，提取对话对（输入→我的回复）
- 数据增强后从约5000条扩展到约7700条

**为什么要收集WhatsApp数据？**

WhatsApp 的日常对话更能反映我真实的语气和表达习惯，比正式邮件更口语化，两者结合能让模型更全面地学习我的风格。

---

### 第二步：模型训练与对比

对以下4个开源模型进行 LoRA 微调，在 Google Colab 上训练，每次训练数小时：

| 模型 | 参数量 |
|---|---|
| Gemma-2B | 2B |
| Phi-4 | 14B |
| Llama 3.1 | 8B |
| Qwen-2.5 | 7B |

进行了两轮实验：
- **Demo1**：使用约5000条原始数据
- **Demo2**：数据增强后使用约7700条数据，整体效果有所提升

---

### 第三步：模型评估

#### 评估指标对比（与GPT Baseline相比）

**Demo1（约5000条数据）**

| 指标 | GPT Baseline | Llama3.1-8B | Phi4 | Gemma-2B | Qwen-2.5 |
|---|---|---|---|---|---|
| Toxicity | 0.0005 | 0.0058 | 0.0024 | 0.0021 | 0.0014 |
| Cosine Similarity | 0.8049 | 0.8199 | 0.8562 | 0.8191 | 0.7995 |
| Context Relevance | 0.713 | 0.796 | 0.7633 | 0.86 | 0.6595 |
| Style Similarity | 0.666 | 0.738 | 0.7769 | 0.812 | 0.6595 |

**Demo2（约7700条数据，数据增强后）**

| 指标 | GPT Baseline | Llama3.1-8B | Phi4 | Gemma-2B | Qwen-2.5 |
|---|---|---|---|---|---|
| Toxicity | 0.0013 | 0.0015 | 0.0022 | 0.0013 | 0.0023 |
| Cosine Similarity | 0.8376 | 0.8229 | 0.7959 | 0.8455 | 0.8047 |
| Context Relevance | 0.735 | 0.819 | 0.8168 | 0.854 | 0.6705 |
| Style Similarity | 0.6926 | 0.7107 | 0.7939 | 0.804 | 0.6137 |

**主要发现：**
- 数据增强后整体效果有所提升
- **Gemma-2B 综合表现最好**，在风格相似度和上下文相关性上超过了 GPT Baseline
- Qwen-2.5 表现最差

---

#### MMLU 通用能力测试

微调后模型在 MMLU（覆盖57个领域的综合语言理解基准）上的表现：

| 模型 | 原始分数 | 微调后分数 |
|---|---|---|
| Phi4 | 84.8 | 73.4 |
| Llama3.1-8B | 66.7 | 57.6 |
| Qwen-2.5 | 65.6 | 58.0 |
| Gemma-2B | 51.3 | 32.6 |

**观察：** 所有模型微调后通用能力均有所下降，这是个性化微调的典型权衡——模型在学习特定风格的同时，会损失一部分通用知识。这也说明**高度个性化和通用能力之间存在 trade-off**。

---

### 第四步：模型部署

**GCP Compute Engine**
- 启动 GPU 虚拟机，上传微调后的模型权重
- 优点：稳定，可自定义
- 缺点：需手动管理服务器，成本较高

**RunPod（也尝试过）**
- 按需租用 GPU，部署更简单快速
- 优点：便宜灵活，适合测试阶段
- 缺点：稳定性相对较低

---

## 为什么没有实现WhatsApp自动回复？

使用 WhatsApp API 需要：
- 注册通过审核的 **WhatsApp Business账户**
- 一个专用手机号码
- Meta Business Manager 资质认证

对个人项目门槛太高，因此当前版本仅展示 Gmail 部分。

---

## 技术栈

| 层级 | 技术 |
|---|---|
| 前端 | React + TypeScript + Tailwind CSS |
| 后端 | Python + FastAPI |
| 邮件接入 | Gmail API |
| AI模型（方案一） | Claude API |
| AI模型（方案二） | Gemma-2B / Phi4 / Llama3.1 / Qwen-2.5 |
| 微调方式 | LoRA |
| 训练平台 | Google Colab |
| 模型部署 | GCP Compute Engine / RunPod |
| 向量数据库 | ChromaDB |

---

## 系统架构

前端 (React) → 后端 (FastAPI) → Gmail API / Claude API / 自己部署的模型 → 保存草稿到Gmail草稿箱

# 方案一Gmail × Claude 邮件回复助手

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
## demo:
<img width="1401" height="664" alt="Screenshot 2026-05-08 at 6 45 52 PM" src="https://github.com/user-attachments/assets/9c7d0a95-9df7-436f-a0a1-9c44a4531865" />
