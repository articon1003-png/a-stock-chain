# MemOS API 文档

> 来源: https://memos-docs.openmem.net/cn/api_docs/start/overview/

## 概述

MemOS 提供完整的记忆管理 API，可将记忆相关功能集成到 AI 应用中，实现用户与 AI 智能体的记忆生产、调度、召回与生命周期管理。

## 基础信息

- **Base URL**: `https://memos.memtensor.cn/api/openmem/v1`
- **API 控制台**: https://memos-dashboard.openmem.net/apikeys/
- **认证方式**: Header `Authorization: Token <API_KEY>`
- **版本**: 3.1.0

> 警告: 勿在客户端或公共仓库暴露 API Key，应通过环境变量或服务端调用。

---

## 核心 API

### 1. 添加消息 (Add Message)

`POST /add/message`

存储用户对话中的原始消息内容，MemOS 自动解析并生成记忆。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户唯一标识符 |
| conversation_id | string | 否 | 会话唯一标识符，传入可明确当前会话 |
| messages | array | 是 | 消息列表，每条包含 role 和 content |

**示例:**

```json
{
  "user_id": "memos_user_123",
  "conversation_id": "0610",
  "messages": [
    {"role": "user", "content": "我想暑假出去玩，你能帮我推荐下吗？"},
    {"role": "assistant", "content": "好的！是自己出行还是和家人朋友一起呢？"},
    {"role": "user", "content": "肯定要带孩子啊，我们家出门都是全家一起。"}
  ]
}
```

---

### 2. 检索记忆 (Search Memory)

`POST /search/memory`

检索用户相关记忆片段，供 Agent 使用。召回类型包括：事实记忆、偏好记忆、工具记忆、技能 Skill。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户唯一标识符 |
| conversation_id | string | 否 | 会话 ID，不传则跨会话检索 |
| query | string | 是 | 用户输入的查询内容 |
| filter | object | 否 | 记忆过滤条件，支持 and/or 和时间比较 |
| knowledgebase_ids | array | 否 | 限定知识库范围，传 `all` 检索所有 |
| memory_limit | integer | 否 | 返回记忆数量限制 |

**过滤器示例:**

```json
{
  "and": [{"create_time": {"gte": "2025-01-01"}}]
}
```

**请求示例:**

```json
{
  "user_id": "memos_user_123",
  "query": "帮我总结今年和阅读相关的记忆",
  "knowledgebase_ids": ["kb_xxx"],
  "filter": {
    "and": [
      {"create_time": {"gte": "2025-01-01"}},
      {"create_time": {"lte": "2025-12-31"}}
    ]
  }
}
```

---

### 3. 获取记忆 (Get Memory)

`POST /get/memory`

获取某个用户的记忆，包含事实记忆、偏好记忆与工具记忆。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户唯一标识符 |

---

### 4. 删除记忆 (Delete Memory)

`POST /delete/memory`

删除指定用户的记忆，支持批量删除。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户唯一标识符 |
| memory_ids | array | 是 | 要删除的记忆 ID 列表 |

---

### 5. 获取消息 (Get Message)

`POST /get/message`

获取指定会话的用户与助手历史对话记录，可按数量限制返回。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户唯一标识符 |
| conversation_id | string | 是 | 会话唯一标识符 |

---

### 6. 获取任务状态 (Get Status)

`POST /get/status`

获取异步处理任务的状态。

---

## 消息 API

### 7. 添加反馈 (Add Feedback)

`POST /add/feedback`

添加对当前会话消息的反馈，MemOS 可基于反馈更正记忆。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户唯一标识符 |
| conversation_id | string | 是 | 会话唯一标识符 |
| message_id | string | 是 | 消息 ID |
| rating | string | 是 | 反馈评价 (positive/negative) |

---

## 自研模型 API

### 8. 抽取记忆 (Extract Memory)

`POST /extract/memory`

基于 MemOS 自研抽取模型，从对话消息中直接抽取并返回事实与偏好记忆。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| messages | array | 是 | 对话消息列表 |

**请求示例:**

```json
{
  "messages": [
    {"role": "user", "content": "我暑假定好去广州旅游，住宿的话有哪些连锁酒店可选？"},
    {"role": "assistant", "content": "您可以考虑【七天、全季、希尔顿】等等"},
    {"role": "user", "content": "我选七天"}
  ]
}
```

**响应:**

```json
{
  "memory": [...],
  "preference": [...]
}
```

---

### 9. 记忆重排 (Rerank)

`POST /rerank`

基于 memos-reranker 小模型，对候选记忆进行相关性重排。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model | string | 否 | 模型名，默认 `memos-reranker-0.6b` |
| query | string | 是 | 用户查询 |
| memories | array | 是 | 候选记忆列表 |

**请求示例:**

```json
{
  "model": "memos-reranker-0.6b",
  "query": "用户有什么兴趣爱好",
  "memories": [
    "用户喜欢打羽毛球",
    "用户在杭州做后端开发",
    "用户偏好简洁的回复风格"
  ]
}
```

---

## 对话 API

### 10. 对话 (Chat)

`POST /chat`

完成带有记忆召回与知识库增强的对话生成。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户唯一标识符 |
| query | string | 是 | 用户输入 |
| model | string | 否 | 模型名称 |
| conversation_id | string | 否 | 会话 ID |
| date | string | 否 | 日期 |
| topic | string | 否 | 话题 |
| agent_id | string | 否 | Agent ID |
| app_id | string | 否 | App ID |

**请求示例:**

```json
{
  "user_id": "memos_user_123",
  "query": "上海有哪些好玩的",
  "model": "deepseek-r1",
  "conversation_id": "23006762-a064-456e-a33b-d2452bdfa09f",
  "date": "2025-09-19",
  "topic": "推荐公园",
  "agent_id": "agent_id_2025-12-15-01",
  "app_id": "app_id_2025-12-15-01"
}
```

---

## 知识库 API

### 11. 创建知识库

`POST /create/knowledgebase`

创建与项目关联的知识库。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 知识库名称 |
| description | string | 否 | 知识库描述 |

---

### 12. 移除知识库

`POST /delete/knowledgebase`

从当前项目中移除知识库。彻底删除需从控制台操作。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| knowledgebase_id | string | 是 | 知识库 ID |

---

### 13. 添加知识库文件

`POST /add/knowledgebase-file`

向指定知识库上传文件。默认上传普通文档；当 `file[].type` 为 `skill` 时，上传 Markdown Skill 文件或 ZIP 技能包。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| knowledgebase_id | string | 是 | 知识库 ID |
| file | array | 是 | 文件列表，包含 name、type、content |

---

### 14. 获取知识库文件

`POST /get/knowledgebase-file`

两种方式获取文件信息：
- 传 `file_ids` 获取指定文件详情
- 传 `knowledgebase_id` 获取知识库下所有文件

> 两种方式只能选一种，同时传会报错。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| knowledgebase_id | string | 否 | 知识库 ID |
| file_ids | array | 否 | 文件 ID 列表 |

---

### 15. 删除知识库文件

`POST /delete/knowledgebase-file`

从指定知识库中删除文件。删除 Skill 文件时，关联的 Skill 会同步删除。

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| knowledgebase_id | string | 是 | 知识库 ID |
| file_ids | array | 是 | 文件 ID 列表 |

---

## 错误码

详见: https://memos-docs.openmem.net/cn/api_docs/help/error_codes/

---

## 快速开始

1. 从 [MemOS 控制台](https://memos-dashboard.openmem.net/apikeys/) 获取 API Key
2. 调用 `POST /add/message` 存储对话，生成记忆
3. 调用 `POST /search/memory` 检索记忆，为模型提供参考

## Python 示例

```python
import requests

API_BASE = "https://memos.memtensor.cn/api/openmem/v1"
API_KEY = "your_api_key_here"

headers = {
    "Authorization": f"Token {API_KEY}",
    "Content-Type": "application/json"
}

# 添加消息
def add_message(user_id, conversation_id, messages):
    resp = requests.post(f"{API_BASE}/add/message", headers=headers, json={
        "user_id": user_id,
        "conversation_id": conversation_id,
        "messages": messages
    })
    return resp.json()

# 检索记忆
def search_memory(user_id, query, conversation_id=None):
    payload = {"user_id": user_id, "query": query}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    resp = requests.post(f"{API_BASE}/search/memory", headers=headers, json=payload)
    return resp.json()

# 对话 (带记忆召回)
def chat(user_id, query, model=None):
    payload = {"user_id": user_id, "query": query}
    if model:
        payload["model"] = model
    resp = requests.post(f"{API_BASE}/chat", headers=headers, json=payload)
    return resp.json()
```

## 知识库示例

```python
# 创建知识库
def create_kb(name, description=""):
    resp = requests.post(f"{API_BASE}/create/knowledgebase", headers=headers, json={
        "name": name,
        "description": description
    })
    return resp.json()

# 上传文件到知识库
def upload_kb_file(kb_id, filename, content, file_type="document"):
    resp = requests.post(f"{API_BASE}/add/knowledgebase-file", headers=headers, json={
        "knowledgebase_id": kb_id,
        "file": [{"name": filename, "type": file_type, "content": content}]
    })
    return resp.json()

# 检索知识库记忆
def search_with_kb(user_id, query, kb_ids):
    resp = requests.post(f"{API_BASE}/search/memory", headers=headers, json={
        "user_id": user_id,
        "query": query,
        "knowledgebase_ids": kb_ids
    })
    return resp.json()
```
