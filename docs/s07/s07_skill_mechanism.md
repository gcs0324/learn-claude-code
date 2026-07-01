# s07 Skill 加载机制

## 1. 整体流程：Skill 如何安装、生效、被调用

```mermaid
flowchart TB
    subgraph A["① 安装阶段（开发者操作）"]
        A1["在 skills/ 目录下创建子文件夹<br/>如 skills/code-review/"]
        A2["编写 SKILL.md 文件<br/>含 YAML frontmatter + Markdown 正文"]
        A1 --> A2
    end

    subgraph B["② 启动阶段（程序自动）"]
        B1["_scan_skills() 扫描 skills/ 目录"]
        B2["_parse_frontmatter() 解析每个 SKILL.md"]
        B3["构建 SKILL_REGISTRY 字典<br/>{name, description, content}"]
        B4["build_system() 生成 SYSTEM prompt<br/>注入 skill 目录（仅名称+描述）"]
        B5["启动时调用一次，常驻内存"]

        B1 --> B2 --> B3 --> B4 --> B5
    end

    subgraph C["③ 上下文阶段（大模型看到）"]
        C1["每次请求 API 时携带 SYSTEM prompt<br/>内容类似：<br/>'Skills available:<br/>- code-review: 代码审查...<br/>- pdf: PDF处理...<br/>Use load_skill to get full details.'"]
        C2["大模型看到 skill 名称和一行描述<br/>约 100 tokens/skill，极低成本"]
    end

    subgraph D["④ 调用阶段（大模型触发）"]
        D1["大模型判断当前任务需要某个 skill"]
        D2["大模型发起 tool_use：<br/>load_skill(name='code-review')"]
        D3["load_skill() 从 SKILL_REGISTRY<br/>取出完整 SKILL.md 内容"]
        D4["完整内容以 tool_result 形式<br/>注入到对话上下文"]
        D5["大模型读取完整指令后<br/>按 skill 规范执行任务"]
        
        D1 --> D2 --> D3 --> D4 --> D5
    end

    A --> B --> C --> D
```

## 2. 两层加载架构

```mermaid
flowchart LR
    subgraph L1["Layer 1: 轻量目录（始终存在）"]
        L1A["SYSTEM prompt 中包含<br/>所有 skill 的名称 + 一行描述"]
        L1B["成本：~100 tokens/skill<br/>始终随请求发送"]
        L1C["作用：让大模型知道<br/>有哪些能力可用"]
    end

    subgraph L2["Layer 2: 完整加载（按需）"]
        L2A["大模型调用 load_skill(name)"]
        L2B["返回完整 SKILL.md<br/>~2000 tokens/skill"]
        L2C["成本：仅当实际使用时才消耗<br/>随 tool_result 注入上下文"]
    end

    L1 --> L2
```

## 3. 数据流详解

```mermaid
sequenceDiagram
    participant Dev as 👨‍💻 开发者
    participant FS as 📁 skills/ 目录
    participant Scan as 🔍 _scan_skills()
    participant Reg as 📋 SKILL_REGISTRY
    participant Sys as 📝 SYSTEM prompt
    participant LLM as 🤖 大模型
    participant Tool as ⚙️ load_skill()
    
    Note over Dev,FS: === 安装阶段 ===
    Dev->>FS: 创建 skills/code-review/SKILL.md
    Note over FS: YAML frontmatter + 正文内容
    
    Note over Scan,Reg: === 启动阶段 ===
    Scan->>FS: 遍历 skills/ 下所有子目录
    FS-->>Scan: 返回每个 SKILL.md 文件路径
    Scan->>Scan: _parse_frontmatter() 解析
    Scan->>Reg: 写入 {name, description, content}
    Reg->>Sys: build_system() 生成目录摘要
    Note over Sys: "Skills available:<br/>- code-review: 代码审查...<br/>- pdf: PDF处理..."
    
    Note over LLM: === 对话阶段 ===
    Sys->>LLM: 每次请求携带 SYSTEM（含 skill 目录）
    Note over LLM: 大模型看到有 code-review skill<br/>判断当前适合做代码审查
    
    Note over LLM,Tool: === 调用阶段 ===
    LLM->>Tool: tool_use: load_skill(name="code-review")
    Tool->>Reg: 查找 SKILL_REGISTRY["code-review"]
    Reg-->>Tool: 返回完整 SKILL.md 内容
    Tool-->>LLM: tool_result: 完整 skill 指令
    Note over LLM: 现在大模型有了完整的<br/>代码审查指南，按要求执行
```

## 4. 关键代码对应

```mermaid
flowchart TD
    subgraph code["code.py 关键函数"]
        C1["line 71: _scan_skills()<br/>扫描 skills/ 目录"]
        C2["line 88: list_skills()<br/>生成目录摘要文本"]
        C3["line 95: build_system()<br/>构造含目录的 SYSTEM prompt"]
        C4["line 273: load_skill(name)<br/>按名返回完整内容"]
        C5["line 301: TOOLS 注册<br/>load_skill 作为工具暴露"]
        C6["line 308: TOOL_HANDLERS<br/>load_skill → load_skill 函数"]
    end

    C1 --> C3
    C2 --> C3
    C3 --> C5
    C4 --> C6
    C5 --> C6
```

## 5. 总结

| 阶段 | 谁操作 | 做什么 | 成本 |
|------|--------|--------|------|
| 安装 | 开发者 | 在 `skills/<name>/SKILL.md` 写文件 | 0 tokens |
| 启动 | `_scan_skills()` | 扫描目录，解析 frontmatter，构建注册表 | 0 tokens |
| 注入 | `build_system()` | 把 skill 名称+描述写入 SYSTEM prompt | ~100 tokens/skill |
| 触发 | 大模型 | 判断任务需要 skill，调用 `load_skill(name)` | 0 额外 tokens |
| 加载 | `load_skill()` | 从注册表取完整 SKILL.md 返回 | ~2000 tokens/skill |

**核心设计**：两级加载 —— 目录始终在线（便宜），完整内容按需注入（贵但精准）。大模型通过 SYSTEM prompt 知道有哪些 skill，通过 tool_use 按名请求完整内容。
