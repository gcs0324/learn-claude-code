#!/usr/bin/env python3
"""
SVG generator — monospace, exact CJK width calculation.
Rules:
  - Outer box: full viewBox width (1340px)
  - Inner boxes within same row: equal height (max among them)
  - ASCII width = font_size * 0.6, CJK width = font_size * 1.2
  - Padding: 20px horizontal, 12px vertical
"""

import re, math, subprocess

CJK = re.compile(r'[一-鿿　-〿＀-￯぀-ゟ゠-ヿ]')

def text_w(text: str, fs: float) -> float:
    """Rendered width of text in monospace."""
    cjk = sum(1 for c in text if CJK.match(c))
    return (len(text) - cjk) * fs * 0.6 + cjk * fs * 1.2

def max_w(texts: list[str], fs: float) -> float:
    return max(text_w(t, fs) for t in texts) if texts else 0

def box_w(texts: list[str], fs: float, pad: int = 40) -> int:
    return math.ceil(max_w(texts, fs) + pad)

def box_h(lines: int, fs: float, pad: int = 24) -> int:
    return lines * math.ceil(fs + 6) + pad

def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ─── layout helpers ───

FULL_W = 1340  # outer box width
LEFT_X = 30
INNER_PAD = 20  # left+right padding inside outer box
GAP = 15       # gap between inner boxes
PAD_X = 20     # text left padding inside inner box
PAD_Y = 12     # text top padding inside inner box
FS = 11        # default font size
LH = FS + 6    # line height
OUTER_PAD_Y = 10  # vertical padding for outer box (top + bottom)

class Block:
    """A text block that renders as a filled rect + text lines."""
    def __init__(self, lines: list[str], fill: str, text_color: str,
                 stroke: str = None, fs: float = FS):
        self.lines = lines
        self.fill = fill
        self.text_color = text_color
        self.stroke = stroke
        self.fs = fs
        self._w = box_w(lines, fs)
        self._h = box_h(len(lines), fs)

    @property
    def w(self): return self._w
    @property
    def h(self): return self._h
    def set_w(self, w: int): self._w = w
    def set_h(self, h: int): self._h = h

def layout_row(blocks: list[Block]) -> tuple[list[int], float]:
    """Equalize heights. Scale widths +20%, double gap, center."""
    maxh = max(b.h for b in blocks)
    for b in blocks:
        b.set_h(maxh)
        b.set_w(int(b.w * 1.2))  # +20% width
    dbl_gap = GAP * 2
    natural_total = sum(b.w for b in blocks) + dbl_gap * (len(blocks) - 1)
    available = FULL_W - 2 * INNER_PAD
    start_x = LEFT_X + INNER_PAD + (available - natural_total) / 2
    return [b.w for b in blocks], start_x

def outer_h(blocks: list[Block]) -> int:
    """Outer box height = max inner height + small vertical padding."""
    return max(b.h for b in blocks) + 2 * OUTER_PAD_Y

def render_blocks(x: float, y: float, blocks: list[Block]) -> list[str]:
    """Generate SVG elements for a row of centered, naturally-sized blocks."""
    ws, start_x = layout_row(blocks)
    out = []
    dbl_gap = GAP * 2
    cx = start_x
    for b, bw in zip(blocks, ws):
        extra = ""
        if b.stroke:
            extra = f' stroke="{b.stroke}" stroke-width="1.5"'
        out.append(f'  <rect x="{cx:.0f}" y="{y:.0f}" width="{bw}" height="{b.h}" fill="{b.fill}" rx="5"{extra}/>')
        ty = y + PAD_Y + b.fs
        for line in b.lines:
            out.append(f'  <text x="{cx+PAD_X:.0f}" y="{ty:.0f}" fill="{b.text_color}" font-size="{b.fs:.0f}" font-family="Menlo, Monaco, monospace">{esc(line)}</text>')
            ty += LH
        cx += bw + dbl_gap
    return out

def phase_label(y: float, text: str, color: str, fs: float = 12) -> tuple[list[str], float]:
    """Render a phase label bar."""
    w = box_w([text], fs, pad=40)
    out = [
        f'  <rect x="{LEFT_X}" y="{y:.0f}" width="{w}" height="26" fill="{color}" rx="6"/>',
        f'  <rect x="{LEFT_X}" y="{y+13:.0f}" width="{w}" height="13" fill="{color}"/>',
        f'  <text x="{LEFT_X + w//2:.0f}" y="{y+18:.0f}" fill="#fff" font-size="{fs:.0f}" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">{esc(text)}</text>',
    ]
    return out, y + 32

def outer_box(y: float, h: float) -> str:
    return f'  <rect x="{LEFT_X}" y="{y:.0f}" width="{FULL_W}" height="{h:.0f}" fill="#fff" stroke="#cbd5e1" stroke-width="1.5" rx="6"/>'

def arrow(y: float) -> str:
    return f'  <line x1="{LEFT_X + FULL_W//2}" y1="{y:.0f}" x2="{LEFT_X + FULL_W//2}" y2="{y+16:.0f}" stroke="#2563eb" stroke-width="2" marker-end="url(#ab)"/>'

def render_phase(y: float, blocks: list[Block]) -> tuple[list[str], float, float]:
    """Render outer box + inner blocks. Returns (svg_lines, box_height, new_y)."""
    # layout_row equalizes heights and distributes width
    out = []
    oh = outer_h(blocks)
    out.append(outer_box(y, oh))
    out.extend(render_blocks(LEFT_X + INNER_PAD, y + OUTER_PAD_Y, blocks))
    return out, oh, y + oh

# ═══════════════════════════════════════════════════
def gen_s07():
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 1300" font-family="Menlo, Monaco, monospace">')
    out.append('  <defs><marker id="ab" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#2563eb"/></marker></defs>')
    out.append('  <rect width="1400" height="1300" fill="#f8fafc" rx="8"/>')
    out.append('  <rect x="0" y="0" width="1400" height="44" fill="#1e293b" rx="8"/>')
    out.append('  <rect x="0" y="32" width="1400" height="12" fill="#1e293b"/>')
    out.append('  <text x="700" y="28" fill="#e2e8f0" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">s07 Skill 加载机制 · 两级按需知识注入</text>')

    cy = 60.0

    # ── Phase 0 ──
    lbl, cy = phase_label(cy, "0. 安装 (开发者操作)", "#64748b")
    out.extend(lbl)

    b0a = Block(["skills/", "├── code-review/", "│   └── SKILL.md"], "#1e293b", "#94a3b8")
    b0b = Block(["SKILL.md 内容:", "---", "name: code-review", "description: 代码审查,安全检查,性能", "---", "# Code Review Skill ..."], "#0f172a", "#94a3b8")
    b0c = Block(["安装 = 创建文件", "放在 skills/<name>/ 下即可", "程序启动时自动发现", "无需注册, 无需配置"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b0a, b0b, b0c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── Phase 1 ──
    lbl, cy = phase_label(cy, "1. 启动扫描 _scan_skills()", "#2563eb")
    out.extend(lbl)

    b1a = Block(["def _scan_skills():", "  for d in SKILLS_DIR.iterdir():", "    manifest = d / \"SKILL.md\"", "    meta,body=_parse_frontmatter(raw)", "    SKILL_REGISTRY[name] = {", '      "name":name,"description":desc,', '      "content":raw }'], "#0f172a", "#94a3b8")
    b1b = Block(["SKILL_REGISTRY (内存字典)", "─────────────────", '"code-review" → {', '  name: "code-review",', '  description: "代码审查...",', '  content: "---\\nname: ..."', "}"], "#f0fdf4", "#166534", "#16a34a")
    b1c = Block(["启动时执行一次", "所有 skill 常驻内存", "后续查找 O(1)", "成本: 0 tokens (纯文件IO)"], "#dbeafe", "#1e40af", "#60a5fa")
    lines, oh, _ = render_phase(cy, [b1a, b1b, b1c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── Phase 2 ──
    lbl, cy = phase_label(cy, "2. 注入 SYSTEM prompt", "#7c3aed")
    out.extend(lbl)

    b2a = Block(["def build_system():", "  catalog = list_skills()", '  return f"Skills available:"', '         f"{catalog}\\n"', '         "Use load_skill ..."'], "#0f172a", "#94a3b8")
    b2b = Block(["SYSTEM prompt (每次API请求都携带):", "Skills available:", "- code-review: 代码审查,安全检查,", "  性能分析,可维护性评估", "成本: ~100 tokens/skill"], "#faf5ff", "#6b21a8", "#a855f7")
    lines, oh, _ = render_phase(cy, [b2a, b2b])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── Phase 3 ──
    lbl, cy = phase_label(cy, "3. 大模型判断并调用 load_skill", "#dc2626")
    out.extend(lbl)

    b3a = Block(["大模型推理过程:", '(1) 用户: "帮我review代码"', "(2) SYSTEM: code-review可用", "(3) 判断: 加载此skill"], "#fef2f2", "#991b1b", "#fca5a5")
    b3b = Block(["大模型发起的tool_use:", "{", '  "type":"tool_use",', '  "name":"load_skill",', '  "input":{', '    "name":"code-review"', "  }", "}"], "#0f172a", "#93c5fd")
    b3c = Block(["大模型如何知道该调用?", "1. SYSTEM有skill目录", "2. TOOLS有load_skill", "3. 匹配任务与描述", "4. 发起tool_use"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b3a, b3b, b3c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── Phase 4 ──
    lbl, cy = phase_label(cy, "4. load_skill() 返回完整内容", "#16a34a")
    out.extend(lbl)

    b4a = Block(["def load_skill(name):", "  skill = SKILL_REGISTRY.get(name)", '  return skill["content"]', "  # 返回完整SKILL.md原文"], "#0f172a", "#94a3b8")
    b4b = Block(["tool_result (注入上下文):", '"---', "name: code-review", "---", "# Code Review Skill", '## 1. Security ..."', "成本: ~2000 tokens"], "#f0fdf4", "#166534", "#16a34a")
    lines, oh, _ = render_phase(cy, [b4a, b4b])
    out.extend(lines)

    cy += oh + 4

    # Result bar (full width)
    result_t = "大模型获得完整skill指令 → 按SKILL.md检查清单执行: 安全检查→正确性→性能→可维护性"
    rw = box_w([result_t], 11, pad=40)
    out.append(f'  <rect x="{LEFT_X}" y="{cy:.0f}" width="{FULL_W}" height="20" fill="#ecfdf5" stroke="#6ee7b7" rx="3"/>')
    out.append(f'  <text x="{LEFT_X + FULL_W//2:.0f}" y="{cy+14:.0f}" fill="#065f46" font-size="11" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">{esc(result_t)}</text>')

    cy += 26
    out.append(arrow(cy))
    cy += 22

    # ── Phase 5 ──
    lbl, cy = phase_label(cy, "5. TOOLS 注册 (大模型为何能调用)", "#0ea5e9")
    out.extend(lbl)

    b5a = Block(["TOOLS = [ ...,", '  { "name":"load_skill",', '    "description":"Load full content', '                  of a skill by name.",', '    "input_schema":{', '      "properties":{', '        "name":{"type":"string"} } } } ]'], "#0f172a", "#94a3b8")
    b5b = Block(["TOOL_HANDLERS = {", '  "load_skill": load_skill,', "}", "", "agent_loop 流程:", "  tool_use → TOOL_HANDLERS[name]", "  → handler(**input)", "  → tool_result 返回给大模型"], "#f0f9ff", "#0c4a6e", "#0ea5e9")
    lines, oh, _ = render_phase(cy, [b5a, b5b])
    out.extend(lines)

    cy += oh + 15

    # ── Summary section ──
    summary_h = 280
    out.append(f'  <rect x="{LEFT_X}" y="{cy:.0f}" width="{FULL_W}" height="{summary_h}" fill="#1e293b" rx="8"/>')

    sy = cy + 35
    out.append(f'  <text x="{LEFT_X + FULL_W//2:.0f}" y="{sy:.0f}" fill="#fbbf24" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">两级加载架构 · 总结</text>')
    sy += 35

    # L1
    l1_lines = ["Layer 1: 目录注入 (便宜, 始终在线)", "", "· SYSTEM prompt含所有skill的名称+一行描述", "· 成本: ~100 tokens/skill, 始终随请求发送", "· 作用: 让大模型知道有哪些能力可用"]
    l1w = box_w(l1_lines, 12, pad=40)
    l1h = box_h(len(l1_lines), 12)
    out.append(f'  <rect x="80" y="{sy:.0f}" width="{l1w}" height="{l1h}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(l1_lines):
        c = "#93c5fd" if i == 0 else "#94a3b8"
        fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="100" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    # L2
    l2_lines = ["Layer 2: 完整加载 (按需, 精准注入)", "", "· 大模型调用 load_skill(name) 工具", "· 返回完整 SKILL.md, ~2000 tokens/skill", "· 仅实际使用时才消耗 token"]
    l2w = box_w(l2_lines, 12, pad=40)
    l2h = box_h(len(l2_lines), 12)
    l2x = 80 + l1w + 40
    out.append(f'  <rect x="{l2x:.0f}" y="{sy:.0f}" width="{l2w}" height="{l2h}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(l2_lines):
        c = "#86efac" if i == 0 else "#94a3b8"
        fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="{l2x+20:.0f}" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    # Arrow between L1-L2
    ax = 80 + l1w + 10
    out.append(f'  <line x1="{ax:.0f}" y1="{sy + l1h//2:.0f}" x2="{ax+25:.0f}" y2="{sy + l1h//2:.0f}" stroke="#64748b" stroke-width="2" marker-end="url(#ab)"/>')

    sy += max(l1h, l2h) + 20

    # vs real
    vs_texts = [
        "s07 模拟 vs 真实 Claude Code",
        "",
        "s07 (模拟): SYSTEM有目录 → 大模型调用load_skill → 返回tool_result → 下一轮才读到 → 2个API回合",
        "真实: system-reminder有目录 → 大模型调用Skill工具 → harness直接注入SKILL.md → 1个API回合",
        "核心差异: s07的load_skill是普通工具(tool_result下一轮); 真实Skill是harness级工具(同轮注入,对大模型透明)",
    ]
    vsw = max(box_w(vs_texts, 12, pad=40), 1100)
    vsh = box_h(len(vs_texts), 12)
    out.append(f'  <rect x="80" y="{sy:.0f}" width="{vsw}" height="{vsh}" fill="#1e293b" stroke="#475569" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(vs_texts):
        if i == 0:
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#fbbf24" font-size="13" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        elif t.startswith("s07"):
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#f87171" font-size="11" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        elif t.startswith("真实"):
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#4ade80" font-size="11" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        else:
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#94a3b8" font-size="11" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    out.append('</svg>')
    return "\n".join(out)


# ═══════════════════════════════════════════════════
def gen_s09():
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 1250" font-family="Menlo, Monaco, monospace">')
    out.append('  <defs><marker id="ab" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#2563eb"/></marker></defs>')
    out.append('  <rect width="1400" height="1250" fill="#f8fafc" rx="8"/>')
    out.append('  <rect x="0" y="0" width="1400" height="44" fill="#1e293b" rx="8"/>')
    out.append('  <rect x="0" y="32" width="1400" height="12" fill="#1e293b"/>')
    out.append('  <text x="700" y="28" fill="#e2e8f0" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">s09 Memory 记忆系统 · 持久化跨会话知识</text>')

    cy = 60.0

    # ── 1. Storage ──
    lbl, cy = phase_label(cy, "1. 存储层 (.memory/)", "#64748b")
    out.extend(lbl)

    b0a = Block([".memory/", "├── MEMORY.md", "├── user-pref-tabs.md", "├── project-facts.md", "└── feedback-x.md"], "#1e293b", "#94a3b8")
    b0b = Block(["MEMORY.md (索引, 始终加载):", "", "- [User Pref Tabs](user-pref-tabs.md)", "  — 用户喜欢 tab 缩进", "- [Project Facts](project-facts.md)", "  — 使用 PostgreSQL"], "#0f172a", "#94a3b8")
    b0c = Block(["单个记忆文件格式:", "---", "name: user-pref-tabs", "description: 用户喜欢 tab 缩进", "type: user", "---", "用户偏好使用 tab 缩进..."], "#0f172a", "#93c5fd")
    b0d = Block(["4种类型:", "user    用户偏好", "feedback  用户反馈", "project  项目事实", "reference 外部参考"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b0a, b0b, b0c, b0d])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 2. Startup ──
    lbl, cy = phase_label(cy, "2. 启动阶段: build_system()", "#2563eb")
    out.extend(lbl)

    b1a = Block(["def build_system():", "  index = read_memory_index()", "  # 读取 MEMORY.md", "  return f\"Memories available:", "          {index}\\n", '          Respect user preferences."'], "#0f172a", "#94a3b8")
    b1b = Block(["SYSTEM prompt 包含记忆索引:", "", "Memories available:", "- [User Pref Tabs](...)", "- [Project Facts](...)", "", "成本: ~50 tokens/记忆"], "#faf5ff", "#6b21a8", "#a855f7")
    b1c = Block(["每次 API 请求都携带索引", "成本极低", "让大模型知道", "有哪些记忆可用"], "#dbeafe", "#1e40af", "#60a5fa")
    lines, oh, _ = render_phase(cy, [b1a, b1b, b1c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 3. load_memories ──
    lbl, cy = phase_label(cy, "3. 每轮对话: load_memories()", "#7c3aed")
    out.extend(lbl)

    b2a = Block(["def load_memories(messages):", "  selected = select_relevant(messages)", "  # 收集最近3条用户消息", "  # → LLM选择相关记忆", "  # → 失败则关键词匹配降级", "  for filename in selected:", "    content = read_memory_file(filename)", '  return "<relevant_memories>\\n..."'], "#0f172a", "#94a3b8")
    b2b = Block(["select_relevant_memories():", "", "1. 收集最近3条用户消息", "2. LLM: \"哪些记忆相关?\"", "   返回 [0, 3]", "3. LLM失败 → 关键词降级", "4. 最多选5个记忆文件"], "#f0fdf4", "#166534", "#16a34a")
    b2c = Block(["注入位置:", "agent_loop 开始时", "注入到当前用户消息前面", "", "<relevant_memories>", "  完整记忆内容...", "</relevant_memories>"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b2a, b2b, b2c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 4. extract_memories ──
    lbl, cy = phase_label(cy, "4. 每轮后: extract_memories()", "#dc2626")
    out.extend(lbl)

    b3a = Block(["def extract_memories(messages):", "  dialogue = 收集最近10条对话", "  existing = list_memory_files()", '  LLM: "提取用户偏好/项目事实"', "       \"返回JSON\"", "  for mem in items:", "    write_memory_file(name,type,", "                       desc,body)", "  _rebuild_index()  # 更新索引"], "#0f172a", "#94a3b8")
    b3b = Block(["LLM 提取 prompt:", "", '"Extract user preferences,', ' constraints, or project facts.', ' Return JSON: name, type,', ' description, body."', '', "如果无新内容或已存在, 返回 []"], "#fef2f2", "#991b1b", "#fca5a5")
    b3c = Block(["触发时机:", "每轮对话结束后", "(stop_reason ≠ tool_use)", "", "使用原始对话 (压缩前)", "保证完整度"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b3a, b3b, b3c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 5. consolidate ──
    lbl, cy = phase_label(cy, "5. consolidate_memories() ≥10 触发", "#16a34a")
    out.extend(lbl)

    b4a = Block(["def consolidate_memories():", "  if len(list_memory_files()) < 10:", "    return  # 不到10个不触发", '  LLM: "合并重复, 删除过时"', '       "保持<30个"', "  # 删除所有旧文件", "  for f in glob(*.md): f.unlink()", "  # 写入合并后的记忆", "  for mem in items: write(...)"], "#0f172a", "#94a3b8")
    b4b = Block(["合并规则:", "", "1. 合并重复记忆为一条", "2. 删除过时/被推翻的记忆", "3. 总数控制在30以内", "4. 优先保留用户偏好", "", "类比: Dream / 梦境整理"], "#f0fdf4", "#166534", "#16a34a")
    b4c = Block(["触发条件:", "记忆文件数 ≥ 10", "", "执行后:", "旧文件全部删除", "写入合并后的新文件", "打印: consolidated", "  N → M memories"], "#dbeafe", "#1e40af", "#60a5fa")
    lines, oh, _ = render_phase(cy, [b4a, b4b, b4c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 6. agent_loop ──
    lbl, cy = phase_label(cy, "6. agent_loop 完整流程", "#0ea5e9")
    out.extend(lbl)

    steps = ["① load_memories()", "② build_system()", "③ 压缩管线(s08)", "④ API调用+工具执行", "⑤ extract+consolidate"]
    step_blocks = [Block([s], "#f0f9ff", "#0c4a6e", "#0ea5e9") for s in steps]
    box_h5 = max(b.h for b in step_blocks)
    for b in step_blocks: b.set_h(box_h5)
    out.append(outer_box(cy, box_h5))
    out.extend(render_blocks(LEFT_X + PAD_X, cy, step_blocks))

    cy += box_h5 + 15

    # ── Summary ──
    summary_h = 280
    out.append(f'  <rect x="{LEFT_X}" y="{cy:.0f}" width="{FULL_W}" height="{summary_h}" fill="#1e293b" rx="8"/>')

    sy = cy + 35
    out.append(f'  <text x="{LEFT_X + FULL_W//2:.0f}" y="{sy:.0f}" fill="#fbbf24" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">两级加载 · 双向记忆</text>')
    sy += 35

    # Read
    r_lines = ["读: 两级加载 (同s07 skill)", "", "Layer 1: MEMORY.md索引 → SYSTEM (~50 tokens/记忆)", "Layer 2: select → 完整文件 → <relevant_memories>", "LLM选择 + 关键词降级, 最多5个"]
    rw = box_w(r_lines, 12, pad=40)
    rh = box_h(len(r_lines), 12)
    out.append(f'  <rect x="80" y="{sy:.0f}" width="{rw}" height="{rh}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(r_lines):
        c = "#93c5fd" if i == 0 else "#94a3b8"
        fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="100" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    # Write
    w_lines = ["写: 自动提取 (s09独有)", "", "每轮后: extract_memories() → LLM提取", "→ write + rebuild_index", "≥10时: consolidate_memories() → LLM合并", "→ 删旧写新 → 跨会话保留"]
    ww = box_w(w_lines, 12, pad=40)
    wh = box_h(len(w_lines), 12)
    wx = 80 + rw + 40
    out.append(f'  <rect x="{wx:.0f}" y="{sy:.0f}" width="{ww}" height="{wh}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(w_lines):
        c = "#86efac" if i == 0 else "#94a3b8"
        fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="{wx+20:.0f}" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    # Arrow
    ax = 80 + rw + 10
    out.append(f'  <line x1="{ax:.0f}" y1="{sy + rh//2:.0f}" x2="{ax+25:.0f}" y2="{sy + rh//2:.0f}" stroke="#64748b" stroke-width="2" marker-end="url(#ab)"/>')

    sy += max(rh, wh) + 20

    # vs skill
    vs_texts = [
        "vs s07 skill: 同与不同",
        "",
        "相同: 都是两级加载 (索引在线+内容按需), 都用LLM做选择/匹配, 都注入到上下文",
        "不同: memory是读+写双向 (自动提取+合并), skill是只读 (开发者写, 大模型用)",
        "memory持久化到.memory/目录, 跨会话保留; skill安装在skills/目录, 由开发者维护",
    ]
    vsw = max(box_w(vs_texts, 12, pad=40), 1100)
    vsh = box_h(len(vs_texts), 12)
    out.append(f'  <rect x="80" y="{sy:.0f}" width="{vsw}" height="{vsh}" fill="#1e293b" stroke="#475569" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(vs_texts):
        if i == 0:
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#fbbf24" font-size="13" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        elif t.startswith("相同"):
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#93c5fd" font-size="11" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        elif t.startswith("不同"):
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#f87171" font-size="11" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        else:
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#94a3b8" font-size="11" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    out.append('</svg>')
    return "\n".join(out)


if __name__ == "__main__":
    for name, gen in [("s07", gen_s07), ("s09", gen_s09)]:
        path = f"/Users/cs_beike/IdeaProjects/learn-claude-code/docs/{name}_skill_mechanism.svg" if name == "s07" else f"/Users/cs_beike/IdeaProjects/learn-claude-code/docs/{name}_memory_mechanism.svg"
        svg = gen()
        with open(path, "w") as f:
            f.write(svg)
        r = subprocess.run(["xmllint", "--noout", path], capture_output=True)
        status = "✓" if r.returncode == 0 else f"✗ {r.stderr.decode()}"
        print(f"{path} ({len(svg)} bytes) XML: {status}")
