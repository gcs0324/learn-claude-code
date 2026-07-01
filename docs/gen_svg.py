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

FULL_W = 1400  # outer box width
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


# ═══════════════════════════════════════════════════
def gen_s10():
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 1150" font-family="Menlo, Monaco, monospace">')
    out.append('  <defs><marker id="ab" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#2563eb"/></marker></defs>')
    out.append('  <rect width="1400" height="1150" fill="#f8fafc" rx="8"/>')
    out.append('  <rect x="0" y="0" width="1400" height="44" fill="#1e293b" rx="8"/>')
    out.append('  <rect x="0" y="32" width="1400" height="12" fill="#1e293b"/>')
    out.append('  <text x="700" y="28" fill="#e2e8f0" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">s10 System Prompt · 运行时组装, 不硬编码</text>')

    cy = 60.0

    # ── 1. Problem ──
    lbl, cy = phase_label(cy, "1. 问题: s09 硬编码 SYSTEM prompt", "#64748b")
    out.extend(lbl)

    b0a = Block(["s09 的 SYSTEM:", "", "SYSTEM = (", '  f"You are a coding agent at {WORKDIR}."', '  "Use tools. Act, do not explain."', '  "Before multi-step tasks, use todo_write."', '  "Skills available via list_skills..."', '  "Relevant memories are injected..."', ")"], "#0f172a", "#94a3b8")
    b0b = Block(["三个痛点:", "", "1. 换项目要重写整个 prompt", "   不知道哪些该改哪些该留", "2. 修改一处可能影响全局", "   加工具描述可能与现有指令冲突", "3. 每次都带全部内容", "   不用的 section 也浪费 token"], "#fef2f2", "#991b1b", "#fca5a5")
    b0c = Block(["解决思路:", "把一大段字符串拆成", "独立 section 字典", "运行时按需拼接", "缓存结果避免重复组装"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b0a, b0b, b0c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 2. PROMPT_SECTIONS ──
    lbl, cy = phase_label(cy, "2. PROMPT_SECTIONS: 分段定义", "#2563eb")
    out.extend(lbl)

    b1a = Block(["PROMPT_SECTIONS = {", '  "identity": "You are a coding agent.",', '  "tools": "Available tools:",', '          "bash, read, write",', '  "workspace": f"Working dir: {WORKDIR}",', '  "memory": "Relevant memories",', '           "are injected below.",', "}"], "#0f172a", "#94a3b8")
    b1b = Block(["每个 section 独立维护:", "", "修改 tools 不影响 identity", "新增 memory 不动 workspace", "换项目改 workspace 即可", "", "对比: 硬编码是一整块", "  section 是乐高积木"], "#dbeafe", "#1e40af", "#60a5fa")
    b1c = Block(["始终加载 (3个):", "· identity 身份", "· tools 工具列表", "· workspace 工作目录", "", "按需加载 (1个):", "· memory 记忆内容", "  判断: MEMORY.md 是否存在"], "#f0fdf4", "#166534", "#16a34a")
    lines, oh, _ = render_phase(cy, [b1a, b1b, b1c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 3. assemble_system_prompt ──
    lbl, cy = phase_label(cy, "3. assemble_system_prompt(): 按需拼接", "#7c3aed")
    out.extend(lbl)

    b2a = Block(["def assemble_system_prompt(", "    context: dict) -> str:", "  sections = []", "  # 始终加载", '  sections.append(PROMPT["identity"])', '  sections.append(PROMPT["tools"])', '  sections.append(PROMPT["workspace"])', "  # 按需加载", "  if context.get(\"memories\"):", '    sections.append("Relevant memories:")', "  return \"\\n\\n\".join(sections)"], "#0f172a", "#94a3b8")
    b2b = Block(["拼接逻辑:", "", "identity  tools  workspace", "         ↓", "    memory 存在?", "    ├─ 是 → 追加", "    └─ 否 → 跳过", "", "结果: 3-4 段 prompt 字符串"], "#faf5ff", "#6b21a8", "#a855f7")
    b2c = Block(["为什么不全加载?", "", "· token 有成本", "  system prompt 每轮计费", "· 信息越少大模型越专注", "  无关指令是噪音", "· 按状态决定更准确", "  有记忆才说记忆"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b2a, b2b, b2c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 4. get_system_prompt ──
    lbl, cy = phase_label(cy, "4. get_system_prompt(): 确定性缓存", "#dc2626")
    out.extend(lbl)

    b3a = Block(["def get_system_prompt(", "    context: dict) -> str:", "  global _last_key, _last_prompt", "  key = json.dumps(context,", "    sort_keys=True,", "    ensure_ascii=False,", "    default=str)", "  if key == _last_key:", "    return _last_prompt  # 命中", "  _last_key = key", "  _last_prompt = assemble(context)", "  return _last_prompt"], "#0f172a", "#94a3b8")
    b3b = Block(["缓存机制:", "", "1. json.dumps 序列化 context", "2. 与上次 key 比较", "3. 相同 → 直接返回 (打印 cache hit)", "4. 不同 → 重新组装 (打印 assembled)", "", "同一轮多次 LLM 调用,", "context 不变, 只组装一次"], "#fef2f2", "#991b1b", "#fca5a5")
    b3c = Block(["为什么不用 hash()?", "", "· Python hash() 有进程随机化", "  不适合做稳定 cache key", "· 遇到 list/dict 报错", "  unhashable type", "· json.dumps 确定性输出", "  sort_keys 保证字段顺序"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b3a, b3b, b3c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 5. update_context ──
    lbl, cy = phase_label(cy, "5. update_context(): 真实状态推导", "#16a34a")
    out.extend(lbl)

    b4a = Block(["def update_context(", "    context, messages):", "  memories = \"\"", "  if MEMORY_INDEX.exists():", "    content = MEMORY_INDEX", "      .read_text().strip()", "    if content:", "      memories = content", "  return {", '    "enabled_tools":', '      list(TOOL_HANDLERS.keys()),', '    "workspace": str(WORKDIR),', '    "memories": memories,', "  }"], "#0f172a", "#94a3b8")
    b4b = Block(["真实状态, 不是关键词:", "", "enabled_tools:", "  列出实际注册的工具", "", "workspace:", "  当前工作目录路径", "", "memories:", "  检查 MEMORY.md 是否存在", "  存在则读取其内容"], "#f0fdf4", "#166534", "#16a34a")
    b4c = Block(["vs 关键词匹配:", "", "用户说 memory", "≠ 有记忆文件", "", "用户没提 memory", "≠ 不需要记忆", "", "基于文件系统判断", "更可靠"], "#dbeafe", "#1e40af", "#60a5fa")
    lines, oh, _ = render_phase(cy, [b4a, b4b, b4c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 6. agent_loop ──
    lbl, cy = phase_label(cy, "6. agent_loop: 运行时组装 prompt", "#0ea5e9")
    out.extend(lbl)

    steps = ["update_context()", "get_system_prompt()", "API 调用 + 工具执行", "update_context()", "get_system_prompt()"]
    step_blocks = [Block([s], "#f0f9ff", "#0c4a6e", "#0ea5e9") for s in steps]
    box_h5 = max(b.h for b in step_blocks)
    for b in step_blocks: b.set_h(box_h5)
    out.append(outer_box(cy, box_h5))
    out.extend(render_blocks(LEFT_X + PAD_X, cy, step_blocks))

    cy += box_h5 + 15

    # ── Summary ──
    summary_h = 260
    out.append(f'  <rect x="{LEFT_X}" y="{cy:.0f}" width="{FULL_W}" height="{summary_h}" fill="#1e293b" rx="8"/>')

    sy = cy + 35
    out.append(f'  <text x="{LEFT_X + FULL_W//2:.0f}" y="{sy:.0f}" fill="#fbbf24" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">分段定义 · 按需拼接 · 确定性缓存</text>')
    sy += 35

    # Left: s09 → s10
    l_lines = ["从 s09 到 s10 的变化:", "", "s09: SYSTEM = 硬编码字符串", "s10: PROMPT_SECTIONS + assemble", "s09: 无缓存", "s10: json.dumps 确定性缓存", "s09: 无状态感知", "s10: update_context 真实状态"]
    lw = box_w(l_lines, 12, pad=40)
    lh = box_h(len(l_lines), 12)
    out.append(f'  <rect x="80" y="{sy:.0f}" width="{lw}" height="{lh}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(l_lines):
        c = "#93c5fd" if i == 0 else "#94a3b8"
        fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="100" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    # Right: key design
    r_lines = ["三个关键设计:", "", "1. 分段独立: 修改一个不动其他", "2. 状态驱动: 文件存在才加载", "3. 确定性缓存: json.dumps 做 key", "", "类比: s09 memory 两级加载", "s10 prompt 也是两级:", "  静态 section 始终在线", "  动态 section 按需注入"]
    rw = box_w(r_lines, 12, pad=40)
    rh = box_h(len(r_lines), 12)
    rx = 80 + lw + 40
    out.append(f'  <rect x="{rx:.0f}" y="{sy:.0f}" width="{rw}" height="{rh}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(r_lines):
        c = "#86efac" if i == 0 else "#94a3b8"
        fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="{rx+20:.0f}" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    # Arrow
    ax = 80 + lw + 10
    out.append(f'  <line x1="{ax:.0f}" y1="{sy + lh//2:.0f}" x2="{ax+25:.0f}" y2="{sy + lh//2:.0f}" stroke="#64748b" stroke-width="2" marker-end="url(#ab)"/>')

    sy += max(lh, rh) + 20

    # vs CC
    vs_texts = [
        "s10 模拟 vs 真实 Claude Code",
        "",
        "s10 (模拟): 4 个 section + json.dumps 缓存, 避免重复拼接字符串",
        "真实 CC: 动态 section 数量, 三层缓存 (lodash memoize + section 注册 + API prompt cache boundary)",
        "真实 CC: 静态 section 命中 global cache, 动态 section (如 mcp_instructions) 每次重建",
    ]
    vsw = max(box_w(vs_texts, 12, pad=40), 1100)
    vsh = box_h(len(vs_texts), 12)
    out.append(f'  <rect x="80" y="{sy:.0f}" width="{vsw}" height="{vsh}" fill="#1e293b" stroke="#475569" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(vs_texts):
        if i == 0:
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#fbbf24" font-size="13" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        elif t.startswith("s10"):
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#f87171" font-size="11" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        elif t.startswith("真实"):
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#4ade80" font-size="11" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        else:
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#94a3b8" font-size="11" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    out.append('</svg>')
    return "\n".join(out)


# ═══════════════════════════════════════════════════
def gen_s12():
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 1250" font-family="Menlo, Monaco, monospace">')
    out.append('  <defs><marker id="ab" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#2563eb"/></marker></defs>')
    out.append('  <rect width="1400" height="1250" fill="#f8fafc" rx="8"/>')
    out.append('  <rect x="0" y="0" width="1400" height="44" fill="#1e293b" rx="8"/>')
    out.append('  <rect x="0" y="32" width="1400" height="12" fill="#1e293b"/>')
    out.append('  <text x="700" y="28" fill="#e2e8f0" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">s12 Task System · 文件持久化的任务依赖图</text>')

    cy = 60.0

    # ── 1. TodoWrite vs Task System ──
    lbl, cy = phase_label(cy, "1. 问题: TodoWrite 不够用", "#64748b")
    out.extend(lbl)

    b0a = Block(["TodoWrite (s05):", "", "· 会话内存中的清单", "· 无依赖关系", "· 无 owner 认领", "· 会话结束即丢失", "· 不能跨 Agent 协作"], "#0f172a", "#94a3b8")
    b0b = Block(["Task System (s12):", "", "· .tasks/{id}.json 持久化", "· blockedBy 依赖图", "· owner 字段 + claim", "· 跨会话保留进度", "· 多 Agent 可协作"], "#f0fdf4", "#166534", "#16a34a")
    b0c = Block(["核心区别:", "", "TodoWrite = 执行清单", "  当前任务, 会话内", "", "Task = 任务系统", "  可恢复, 跨会话", "  大目标拆小任务"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b0a, b0b, b0c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 2. Task dataclass ──
    lbl, cy = phase_label(cy, "2. Task 数据结构 + 存储", "#2563eb")
    out.extend(lbl)

    b1a = Block(["@dataclass", "class Task:", "  id: str", "  subject: str", "  description: str", "  status: str", "    # pending|in_progress|completed", "  owner: str | None", "  blockedBy: list[str]", "", "TASKS_DIR = .tasks/", "# .tasks/{id}.json"], "#0f172a", "#94a3b8")
    b1b = Block([".tasks/ 目录结构:", "", "task_001.json →", '  {"id":"task_001",', '   "subject":"setup schema",', '   "status":"completed",', '   "owner":"agent",', '   "blockedBy":[]}', "", "task_002.json →", '  {"subject":"create API",', '   "blockedBy":["task_001"]}'], "#1e293b", "#94a3b8")
    b1c = Block(["文件持久化:", "", "· 每个任务一个 JSON 文件", "· create/claim/complete 实时写盘", "· 跨会话: list_tasks 扫描目录", "  即可恢复全部进度", "· ID: timestamp + random hex", "  简单但够用"], "#dbeafe", "#1e40af", "#60a5fa")
    lines, oh, _ = render_phase(cy, [b1a, b1b, b1c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 3. can_start + claim + complete ──
    lbl, cy = phase_label(cy, "3. 核心操作: can_start + claim + complete", "#7c3aed")
    out.extend(lbl)

    b2a = Block(["def can_start(task_id):", "  task = load_task(task_id)", "  for dep_id in task.blockedBy:", "    if not _task_path(dep_id).exists():", "      return False  # 缺失=blocked", "    if load_task(dep_id).status", "       != \"completed\":", "      return False", "  return True"], "#0f172a", "#94a3b8")
    b2b = Block(["def claim_task(task_id, owner):", "  task = load_task(task_id)", "  if task.status != \"pending\":", "    return \"cannot claim\"", "  if not can_start(task_id):", "    return \"Blocked by: ...\"", "  task.owner = owner", "  task.status = \"in_progress\"", "  save_task(task)"], "#faf5ff", "#6b21a8", "#a855f7")
    b2c = Block(["def complete_task(task_id):", "  task = load_task(task_id)", "  task.status = \"completed\"", "  save_task(task)", "  # 扫描被解锁的下游", "  unblocked = [t.subject", "    for t in list_tasks()", "    if t.status == \"pending\"", "    and t.blockedBy", "    and can_start(t.id)]", "  return msg + unblocked"], "#f0fdf4", "#166534", "#16a34a")
    lines, oh, _ = render_phase(cy, [b2a, b2b, b2c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 4. 状态机 ──
    lbl, cy = phase_label(cy, "4. 状态机: pending → in_progress → completed", "#dc2626")
    out.extend(lbl)

    b3a = Block(["pending", "", "create_task 创建", "blockedBy 未全部完成时", "can_start = false", "claim 被拒绝"], "#fef2f2", "#991b1b", "#fca5a5")
    b3b = Block(["in_progress", "", "claim_task 认领后", "owner 已设置", "can_start 已通过", "其他 Agent 不能重复认领"], "#fef3c7", "#92400e", "#f59e0b")
    b3c = Block(["completed", "", "complete_task 完成后", "自动扫描所有 pending 任务", "报告被解锁的下游任务", "下游的 can_start → true"], "#f0fdf4", "#166534", "#16a34a")
    lines, oh, _ = render_phase(cy, [b3a, b3b, b3c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 5. DAG example ──
    lbl, cy = phase_label(cy, "5. DAG 示例: 搭数据库 → 写 API → 加测试", "#16a34a")
    out.extend(lbl)

    b4a = Block(["schema = create_task(", '  "setup database schema")', "endpoints = create_task(", '  "create API endpoints",', "  blockedBy=[schema.id])", "tests = create_task(", '  "write tests",', "  blockedBy=[endpoints.id])", "docs = create_task(", '  "write docs",', "  blockedBy=[schema.id])"], "#0f172a", "#94a3b8")
    b4b = Block(["执行顺序:", "", "1. claim + complete schema", "   → 解锁 endpoints, docs", "2. claim + complete endpoints", "   → 解锁 tests", "3. claim + complete docs", "   (无下游依赖)", "4. claim + complete tests", "   (最后完成)"], "#f0fdf4", "#166534", "#16a34a")
    b4c = Block(["DAG 结构:", "", "     schema", "    /      \\", "   v        v", "endpoints   docs", "   |", "   v", " tests", "", "schema 阻塞 endpoints+docs", "endpoints 阻塞 tests"], "#dbeafe", "#1e40af", "#60a5fa")
    lines, oh, _ = render_phase(cy, [b4a, b4b, b4c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 6. agent_loop with tasks ──
    lbl, cy = phase_label(cy, "6. agent_loop: 8 个工具 (3 基础 + 5 任务)", "#0ea5e9")
    out.extend(lbl)

    steps = ["bash", "read_file", "write_file", "create_task", "list_tasks", "get_task", "claim_task", "complete_task"]
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
    out.append(f'  <text x="{LEFT_X + FULL_W//2:.0f}" y="{sy:.0f}" fill="#fbbf24" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">文件持久化 · blockedBy 依赖图 · 跨会话可恢复</text>')
    sy += 35

    # Left: vs TodoWrite
    l_lines = ["vs TodoWrite (s05):", "", "TodoWrite: 会话内存清单", "Task: .tasks/ 文件持久化", "TodoWrite: 无依赖", "Task: blockedBy 依赖图", "TodoWrite: 无 owner", "Task: owner + claim 认领", "TodoWrite: 会话结束丢失", "Task: 跨会话恢复进度"]
    lw = box_w(l_lines, 12, pad=40)
    lh = box_h(len(l_lines), 12)
    out.append(f'  <rect x="80" y="{sy:.0f}" width="{lw}" height="{lh}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(l_lines):
        c = "#93c5fd" if i == 0 else "#94a3b8"
        fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="100" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    # Right: key design
    r_lines = ["三个关键设计:", "", "1. 文件持久化", "   每个任务一个 JSON 文件", "   跨会话恢复只需扫描目录", "2. blockedBy 依赖检查", "   can_start 全部完成才允许", "   缺失依赖 = blocked", "3. complete 自动解锁下游", "   无需手动追踪依赖关系"]
    rw = box_w(r_lines, 12, pad=40)
    rh = box_h(len(r_lines), 12)
    rx = 80 + lw + 40
    out.append(f'  <rect x="{rx:.0f}" y="{sy:.0f}" width="{rw}" height="{rh}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(r_lines):
        c = "#86efac" if i == 0 else "#94a3b8"
        fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="{rx+20:.0f}" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    # Arrow
    ax = 80 + lw + 10
    out.append(f'  <line x1="{ax:.0f}" y1="{sy + lh//2:.0f}" x2="{ax+25:.0f}" y2="{sy + lh//2:.0f}" stroke="#64748b" stroke-width="2" marker-end="url(#ab)"/>')

    sy += max(lh, rh) + 20

    # vs CC
    vs_texts = [
        "s12 模拟 vs 真实 Claude Code",
        "",
        "s12 (模拟): 6 个字段 + 5 个工具 + .tasks/ JSON 文件 + blockedBy 依赖",
        "真实 CC: 9 个字段 (含 activeForm blocks metadata) + 4 个独立工具 (TaskCreate TaskGet TaskUpdate TaskList)",
        "真实 CC: 双重锁防竞争 (任务文件锁 + 列表级锁) + 高水位标防 ID 重用 + fs.watch 响应式监听",
    ]
    vsw = max(box_w(vs_texts, 12, pad=40), 1100)
    vsh = box_h(len(vs_texts), 12)
    out.append(f'  <rect x="80" y="{sy:.0f}" width="{vsw}" height="{vsh}" fill="#1e293b" stroke="#475569" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(vs_texts):
        if i == 0:
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#fbbf24" font-size="13" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        elif t.startswith("s12"):
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#f87171" font-size="11" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        elif t.startswith("真实"):
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#4ade80" font-size="11" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        else:
            out.append(f'  <text x="100" y="{ly:.0f}" fill="#94a3b8" font-size="11" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    out.append('</svg>')
    return "\n".join(out)


# ═══════════════════════════════════════════════════
def gen_s13():
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 1050" font-family="Menlo, Monaco, monospace">')
    out.append('  <defs><marker id="ab" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#2563eb"/></marker></defs>')
    out.append('  <rect width="1400" height="1050" fill="#f8fafc" rx="8"/>')
    out.append('  <rect x="0" y="0" width="1400" height="44" fill="#1e293b" rx="8"/>')
    out.append('  <rect x="0" y="32" width="1400" height="12" fill="#1e293b"/>')
    out.append('  <text x="700" y="28" fill="#e2e8f0" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">s13 Background Tasks · daemon 线程异步执行, Agent 不阻塞</text>')

    cy = 60.0

    # ── 1. Problem ──
    lbl, cy = phase_label(cy, "1. 问题: 同步 bash 阻塞 Agent", "#64748b")
    out.extend(lbl)

    b0a = Block(["s12 同步执行:", "", "pip install torch", "  → Agent 等 10 分钟", "npm run build", "  → Agent 等 3 分钟", "", "LLM 按 token 计费", "空转 = 浪费"], "#0f172a", "#94a3b8")
    b0b = Block(["类比: 洗衣机", "", "衣服扔进去 → 按下启动", "然后去干别的", "做饭 回消息 看论文", "30 分钟后洗衣机提醒", "", "不会站在前面干等"], "#fef2f2", "#991b1b", "#fca5a5")
    b0c = Block(["解决思路:", "", "慢操作 → daemon 线程", "Agent 继续处理其他任务", "后台完成后 → 注入通知", "", "判断: 模型显式请求优先", "      关键词启发式兜底"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b0a, b0b, b0c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 2. should_run_background ──
    lbl, cy = phase_label(cy, "2. should_run_background(): 双重判断", "#2563eb")
    out.extend(lbl)

    b1a = Block(["def should_run_background(", "    tool_name, tool_input):", "  # 模型显式请求 (优先)", "  if tool_input.get(", '      "run_in_background"):', "    return True", "  # 启发式兜底", "  return is_slow_operation(", "    tool_name, tool_input)"], "#0f172a", "#94a3b8")
    b1b = Block(["is_slow_operation():", "", "关键词列表:", "install build test deploy", "compile docker pip npm", "cargo pytest make", "", "命令包含任一关键词", "→ 判定为慢操作"], "#dbeafe", "#1e40af", "#60a5fa")
    b1c = Block(["CC 的真实做法:", "", "bash 工具 schema 有", "run_in_background:", "  type: boolean", "", "模型自己决定哪些命令", "丢后台, 不靠关键词猜", "", "教学版保留启发式兜底"], "#f0fdf4", "#166534", "#16a34a")
    lines, oh, _ = render_phase(cy, [b1a, b1b, b1c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 3. start_background_task ──
    lbl, cy = phase_label(cy, "3. start_background_task(): daemon 线程", "#7c3aed")
    out.extend(lbl)

    b2a = Block(["def start_background_task(", "    block) -> str:", "  global _bg_counter", "  bg_id = f\"bg_{counter:04d}\"", "  def worker():", "    result = execute_tool(block)", "    with background_lock:", '      tasks[bg_id]["status"]=', '        "completed"', "      results[bg_id] = result", "  t = Thread(target=worker,", "           daemon=True)", "  t.start()", "  return bg_id"], "#0f172a", "#94a3b8")
    b2b = Block(["数据结构:", "", "background_tasks:", "  bg_id → {tool_use_id,", "           command, status}", "", "background_results:", "  bg_id → output", "", "background_lock:", "  threading.Lock()", "  保护并发读写"], "#faf5ff", "#6b21a8", "#a855f7")
    b2c = Block(["daemon 线程:", "", "· Thread(daemon=True)", "  主线程退出时自动清理", "· 线程内执行命令", "  不阻塞 agent_loop", "· Lock 保护写操作", "  线程安全"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b2a, b2b, b2c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 4. collect + agent_loop ──
    lbl, cy = phase_label(cy, "4. collect_background_results + agent_loop", "#dc2626")
    out.extend(lbl)

    b3a = Block(["def collect_background_results():", "  with background_lock:", "    ready = [bid for bid, t", "      in tasks.items()", '      if t["status"]=="completed"]', "  notifications = []", "  for bg_id in ready:", "    with background_lock:", "      task = tasks.pop(bg_id)", "      output = results.pop(bg_id)", "    notifications.append(", '      "<task_notification>\\n"', '      f"{output}\\n"', '      "</task_notification>")', "  return notifications"], "#0f172a", "#94a3b8")
    b3b = Block(["agent_loop 变化:", "", "每个 tool_use block:", "  if should_run_background:", "    bg_id = start_bg_task(block)", '    注入 placeholder 通知', "  else:", "    同步执行", "", "每轮工具执行后:", "  bg_notifications =", "    collect_bg_results()", "  注入到 messages"], "#fef2f2", "#991b1b", "#fca5a5")
    b3c = Block(["通知格式:", "", "后台开始时:", '"Background task bg_0001",', '"started: pip install torch"', "", "后台完成时:", "<task_notification>", "  ... 命令输出 ...", "</task_notification>", "", "下轮 LLM 调用时可见"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b3a, b3b, b3c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 5. Flow ──
    lbl, cy = phase_label(cy, "5. agent_loop: 同步 + 后台混合", "#16a34a")
    out.extend(lbl)

    steps = ["tool_use", "should_run_background?", "同步: handler", "后台: daemon线程", "collect_results", "注入通知", "下一轮LLM"]
    step_blocks = [Block([s], "#f0f9ff", "#0c4a6e", "#0ea5e9") for s in steps]
    box_h5 = max(b.h for b in step_blocks)
    for b in step_blocks: b.set_h(box_h5)
    out.append(outer_box(cy, box_h5))
    out.extend(render_blocks(LEFT_X + PAD_X, cy, step_blocks))

    cy += box_h5 + 15

    # ── Summary ──
    summary_h = 230
    out.append(f'  <rect x="{LEFT_X}" y="{cy:.0f}" width="{FULL_W}" height="{summary_h}" fill="#1e293b" rx="8"/>')

    sy = cy + 35
    out.append(f'  <text x="{LEFT_X + FULL_W//2:.0f}" y="{sy:.0f}" fill="#fbbf24" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">daemon 线程 · 双重判断 · 通知注入</text>')
    sy += 35

    # Left: key concepts
    l_lines = ["核心概念:", "", "daemon 线程:", "  Thread(daemon=True)", "  不阻塞主循环", "", "双重判断:", "  模型显式 run_in_background", "  + 关键词启发式兜底", "", "线程安全:", "  threading.Lock 保护"]
    lw = box_w(l_lines, 12, pad=40)
    lh = box_h(len(l_lines), 12)
    out.append(f'  <rect x="80" y="{sy:.0f}" width="{lw}" height="{lh}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(l_lines):
        c = "#93c5fd" if i == 0 else "#94a3b8"
        fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="100" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    # Right: vs CC
    r_lines = ["s13 模拟 vs 真实 CC:", "", "s13 (模拟): 4 方法 + 3 数据结构", "  关键词启发式 + daemon 线程", "  通知注入到 messages", "", "真实 CC:", "  模型显式 run_in_background", "  Monitor 工具流式输出", "  task_notification 格式通知"]
    rw = box_w(r_lines, 12, pad=40)
    rh = box_h(len(r_lines), 12)
    rx = 80 + lw + 40
    out.append(f'  <rect x="{rx:.0f}" y="{sy:.0f}" width="{rw}" height="{rh}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(r_lines):
        c = "#86efac" if i == 0 else "#94a3b8"
        fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="{rx+20:.0f}" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    # Arrow
    ax = 80 + lw + 10
    out.append(f'  <line x1="{ax:.0f}" y1="{sy + lh//2:.0f}" x2="{ax+25:.0f}" y2="{sy + lh//2:.0f}" stroke="#64748b" stroke-width="2" marker-end="url(#ab)"/>')

    out.append('</svg>')
    return "\n".join(out)


# ═══════════════════════════════════════════════════
def gen_s15():
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 1050" font-family="Menlo, Monaco, monospace">')
    out.append('  <defs><marker id="ab" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#2563eb"/></marker></defs>')
    out.append('  <rect width="1400" height="1050" fill="#f8fafc" rx="8"/>')
    out.append('  <rect x="0" y="0" width="1400" height="44" fill="#1e293b" rx="8"/>')
    out.append('  <rect x="0" y="32" width="1400" height="12" fill="#1e293b"/>')
    out.append('  <text x="700" y="28" fill="#e2e8f0" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">s15 Agent Teams · MessageBus 文件收件箱 + 队友线程</text>')

    cy = 60.0

    # ── 1. SubAgent vs Teammate ──
    lbl, cy = phase_label(cy, "1. 子 Agent vs 队友", "#64748b")
    out.extend(lbl)

    b0a = Block(["s06 子 Agent:", "", "· 一次性, 用完销毁", "· 只回传结论", "· 上下文完全隔离", "· 临时工模式", "", "spawn_subagent(desc)", "  → 跑完 → 返回字符串"], "#0f172a", "#94a3b8")
    b0b = Block(["s15 队友:", "", "· 多轮 (最多 10 轮)", "· 异步收件箱通信", "· 通过消息共享信息", "· 长期同事模式", "", "spawn_teammate_thread(", "  name, role, prompt)", "  → daemon 线程 →", "    BUS.send 汇报"], "#f0fdf4", "#166534", "#16a34a")
    b0c = Block(["核心区别:", "", "子Agent = 临时工", "  叫来干一件事就走", "", "队友 = 长期同事", "  能通信 能协作", "  跑在自己的线程里"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b0a, b0b, b0c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 2. MessageBus ──
    lbl, cy = phase_label(cy, "2. MessageBus: 文件收件箱", "#2563eb")
    out.extend(lbl)

    b1a = Block(["class MessageBus:", "", "  def send(from, to,", "          content, type):", "    msg = {from,to,content,", "           type, ts}", "    inbox = .mailboxes/", "            {to}.jsonl", "    append 一行 JSON", "", "  def read_inbox(agent):", "    读 {agent}.jsonl", "    逐行解析 JSON", "    删除文件 (消费式)", "    返回消息列表"], "#0f172a", "#94a3b8")
    b1b = Block([".mailboxes/ 目录:", "", "lead.jsonl", "  ← 队友发来的消息", "alice.jsonl", "  ← Lead 发给 Alice 的消息", "bob.jsonl", "  ← Lead 发给 Bob 的消息", "", "每个 Agent 一个文件", "跨线程可观察"], "#1e293b", "#94a3b8")
    b1c = Block(["为什么用文件?", "", "· 跨线程可观察", "  cat .mailboxes/alice.jsonl", "· 真实 CC 也是文件收件箱", "  ~/.claude/teams/{team}/", "  inboxes/{agent}.json", "· 消费式读取", "  读完删除, 避免重复"], "#dbeafe", "#1e40af", "#60a5fa")
    lines, oh, _ = render_phase(cy, [b1a, b1b, b1c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 3. spawn_teammate_thread ──
    lbl, cy = phase_label(cy, "3. spawn_teammate_thread(): 启动队友", "#7c3aed")
    out.extend(lbl)

    b2a = Block(["def spawn_teammate_thread(", "    name, role, prompt):", "  system = f\"You are {name},", '            a {role}.\"', "  def run():", "    messages = [user: prompt]", "    sub_tools = [bash, read,", "                write, send]", "    for _ in range(10):", "      inbox = BUS.read(name)", "      if inbox: inject", "      response = LLM call", "      ... execute tools ...", "    BUS.send(name, lead,", "             summary, result)", "  Thread(daemon=True).start()"], "#0f172a", "#94a3b8")
    b2b = Block(["队友工具集 (4 个):", "", "· bash", "· read_file", "· write_file", "· send_message", "", "没有任务管理、cron 等", "聚焦通信机制", "", "Lead 工具集 (14 个):", "+ spawn_teammate", "+ send_message", "+ check_inbox"], "#faf5ff", "#6b21a8", "#a855f7")
    b2c = Block(["关键设计:", "", "· daemon 线程", "  主线程退出时自动清理", "· 最多 10 轮", "  防止无限循环", "· 完成后自动汇报", "  BUS.send(name, lead,", "           summary)", "· active_teammates 追踪", "  运行中的队友"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b2a, b2b, b2c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 4. Lead inbox ──
    lbl, cy = phase_label(cy, "4. Lead inbox 注入 + 权限冒泡 (教学版省略)", "#dc2626")
    out.extend(lbl)

    b3a = Block(["Lead 主循环结束后:", "", "inbox = BUS.read_inbox(", '            "lead")', "if inbox:", "  inbox_text =", '    f"From {m[\"from\"]}:', '     {m[\"content\"]}"', "  history.append(", '    user: "[Inbox]\\n', '            {inbox_text}")', "", "下一轮 LLM 调用时可见"], "#0f172a", "#94a3b8")
    b3b = Block(["权限冒泡 (CC 真实实现):", "", "1. 队友遇审批 →", "   permission_request →", "   Lead 收件箱", "2. Lead inbox poller →", "   路由到审批队列", "3. 用户审批 →", "   permission_response →", "   队友收件箱", "4. 队友 poller (500ms) →", "   收到回复 → 继续/拒绝", "", "教学版省略此流程"], "#fef2f2", "#991b1b", "#fca5a5")
    b3c = Block(["CC 的 15 种消息类型:", "", "plain text / idle /", "permission_request /", "permission_response /", "plan_approval /", "shutdown_request /", "shutdown_approved /", "task_assignment /", "teammate_terminated / ...", "", "文本包装在", "<teammate-message>", "XML 标签中"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b3a, b3b, b3c])
    out.extend(lines)

    cy += oh + 10
    out.append(arrow(cy))
    cy += 22

    # ── 5. Flow ──
    lbl, cy = phase_label(cy, "5. 并行执行: Lead + Alice + Bob", "#16a34a")
    out.extend(lbl)

    steps = ["Lead: spawn alice bob", "Alice: 创建 schema", "Bob: 写 API 客户端", "Alice: BUS.send 汇报", "Bob: BUS.send 汇报", "Lead: inbox 注入", "Lead: 汇总结果"]
    step_blocks = [Block([s], "#f0f9ff", "#0c4a6e", "#0ea5e9") for s in steps]
    box_h5 = max(b.h for b in step_blocks)
    for b in step_blocks: b.set_h(box_h5)
    out.append(outer_box(cy, box_h5))
    out.extend(render_blocks(LEFT_X + PAD_X, cy, step_blocks))

    cy += box_h5 + 15

    # ── Summary ──
    summary_h = 230
    out.append(f'  <rect x="{LEFT_X}" y="{cy:.0f}" width="{FULL_W}" height="{summary_h}" fill="#1e293b" rx="8"/>')

    sy = cy + 35
    out.append(f'  <text x="{LEFT_X + FULL_W//2:.0f}" y="{sy:.0f}" fill="#fbbf24" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">文件收件箱 · 队友线程 · inbox 注入</text>')
    sy += 35

    # Left
    l_lines = ["核心概念:", "", "MessageBus:", "  文件收件箱, send + read", "  .mailboxes/*.jsonl", "", "spawn_teammate_thread:", "  daemon 线程, 最多 10 轮", "  简化工具集 (4 个)", "  完成后自动 BUS.send 汇报"]
    lw = box_w(l_lines, 12, pad=40)
    lh = box_h(len(l_lines), 12)
    out.append(f'  <rect x="80" y="{sy:.0f}" width="{lw}" height="{lh}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(l_lines):
        c = "#93c5fd" if i == 0 else "#94a3b8"
        fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="100" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    # Right
    r_lines = ["s15 模拟 vs 真实 CC:", "", "s15 (模拟): 1 MessageBus +", "  spawn_teammate_thread", "  文件 JSONL 收件箱", "  队友 4 工具, 最多 10 轮", "", "真实 CC:", "  15 种消息类型", "  proper-lockfile 防并发", "  idle loop 替代 10 轮限制", "  双向权限冒泡机制"]
    rw = box_w(r_lines, 12, pad=40)
    rh = box_h(len(r_lines), 12)
    rx = 80 + lw + 40
    out.append(f'  <rect x="{rx:.0f}" y="{sy:.0f}" width="{rw}" height="{rh}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(r_lines):
        c = "#86efac" if i == 0 else "#94a3b8"
        fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="{rx+20:.0f}" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22

    # Arrow
    ax = 80 + lw + 10
    out.append(f'  <line x1="{ax:.0f}" y1="{sy + lh//2:.0f}" x2="{ax+25:.0f}" y2="{sy + lh//2:.0f}" stroke="#64748b" stroke-width="2" marker-end="url(#ab)"/>')

    out.append('</svg>')
    return "\n".join(out)


# ═══════════════════════════════════════════════════
def gen_s16():
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 950" font-family="Menlo, Monaco, monospace">')
    out.append('  <defs><marker id="ab" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#2563eb"/></marker></defs>')
    out.append('  <rect width="1400" height="950" fill="#f8fafc" rx="8"/>')
    out.append('  <rect x="0" y="0" width="1400" height="44" fill="#1e293b" rx="8"/>')
    out.append('  <rect x="0" y="32" width="1400" height="12" fill="#1e293b"/>')
    out.append('  <text x="700" y="28" fill="#e2e8f0" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">s16 Team Protocols · 结构化握手 + request-response 模式</text>')
    cy = 60.0

    lbl, cy = phase_label(cy, "1. 两种协议: shutdown + plan_approval", "#64748b")
    out.extend(lbl)
    b0a = Block(["shutdown:", "  Lead → 队友", "  体面关机握手", "  Lead 发请求 →", "  队友收尾 → 确认", "  pending → approved"], "#fef2f2", "#991b1b", "#fca5a5")
    b0b = Block(["plan_approval:", "  队友 → Lead", "  计划审批协议", "  队友提交计划 →", "  Lead 审批 → 动手", "  pending → approved/rejected"], "#dbeafe", "#1e40af", "#60a5fa")
    b0c = Block(["共同机制:", "", "· request_id 贯穿全链路", "· ProtocolState 追踪状态", "· dispatch_message 路由", "· match_response 校验", "· pending_requests 字典"], "#fef3c7", "#92400e", "#f59e0b")
    lines, oh, _ = render_phase(cy, [b0a, b0b, b0c])
    out.extend(lines); cy += oh + 10; out.append(arrow(cy)); cy += 22

    lbl, cy = phase_label(cy, "2. ProtocolState + dispatch + match", "#2563eb")
    out.extend(lbl)
    b1a = Block(["ProtocolState:", "  request_id: str", "  type: shutdown|plan", "  sender / target", "  status: pending|", "    approved|rejected", "  payload / created_at", "", "pending_requests:", "  dict[request_id]"], "#0f172a", "#94a3b8")
    b1b = Block(["dispatch_message:", "", "handle_inbox_message", "  按 msg_type 分发:", "", "shutdown_request:", "  → 回复 + 停止循环", "", "plan_approval_response:", "  → 注入 [Approved]", "  或 [Rejected]", "", "普通消息:", "  → 注入 messages"], "#faf5ff", "#6b21a8", "#a855f7")
    b1c = Block(["match_response:", "", "1. 按 request_id 查找", "2. 校验 response_type", "   匹配 request_type", "3. 校验 status==pending", "   防止重复处理", "4. 更新 status:", "   approved / rejected"], "#f0fdf4", "#166534", "#16a34a")
    lines, oh, _ = render_phase(cy, [b1a, b1b, b1c])
    out.extend(lines); cy += oh + 10; out.append(arrow(cy)); cy += 22

    lbl, cy = phase_label(cy, "3. 四步协议流程 + 统一 inbox 消费", "#7c3aed")
    out.extend(lbl)
    steps = ["1.Lead 发请求+创建状态", "2.队友 inbox dispatch", "3.队友 回复+request_id", "4.Lead match_response", "consume_lead_inbox"]
    step_blocks = [Block([s], "#f0f9ff", "#0c4a6e", "#0ea5e9") for s in steps]
    box_h5 = max(b.h for b in step_blocks)
    for b in step_blocks: b.set_h(box_h5)
    out.append(outer_box(cy, box_h5))
    out.extend(render_blocks(LEFT_X + PAD_X, cy, step_blocks))
    cy += box_h5 + 15

    summary_h = 180
    out.append(f'  <rect x="{LEFT_X}" y="{cy:.0f}" width="{FULL_W}" height="{summary_h}" fill="#1e293b" rx="8"/>')
    sy = cy + 35
    out.append(f'  <text x="{LEFT_X + FULL_W//2:.0f}" y="{sy:.0f}" fill="#fbbf24" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">request_id 贯穿全链路 · 三重校验 · 统一 inbox 消费</text>')
    sy += 30
    l_lines = ["核心概念:", "", "request_id: 请求带着出去, 回复带着回来", "ProtocolState: 追踪每个请求的完整生命周期", "match_response: 类型校验 + 防重复处理", "consume_lead_inbox: 先协议后消息, 避免状态遗漏"]
    lw = box_w(l_lines, 12, pad=40); lh = box_h(len(l_lines), 12)
    out.append(f'  <rect x="80" y="{sy:.0f}" width="{lw}" height="{lh}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(l_lines):
        c = "#93c5fd" if i == 0 else "#94a3b8"; fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="100" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22
    out.append('</svg>')
    return "\n".join(out)


# ═══════════════════════════════════════════════════
def gen_s17():
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 950" font-family="Menlo, Monaco, monospace">')
    out.append('  <defs><marker id="ab" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#2563eb"/></marker></defs>')
    out.append('  <rect width="1400" height="950" fill="#f8fafc" rx="8"/>')
    out.append('  <rect x="0" y="0" width="1400" height="44" fill="#1e293b" rx="8"/>')
    out.append('  <rect x="0" y="32" width="1400" height="12" fill="#1e293b"/>')
    out.append('  <text x="700" y="28" fill="#e2e8f0" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">s17 Autonomous Agents · 自己看板, 自己认领</text>')
    cy = 60.0

    lbl, cy = phase_label(cy, "1. 三阶段生命周期: WORK → IDLE → SHUTDOWN", "#64748b")
    out.extend(lbl)
    b0a = Block(["WORK:", "  inbox → LLM → 工具循环", "  bash/read/write/send", "  + claim_task/complete_task", "  退出: stop_reason", "         != tool_use"], "#0f172a", "#94a3b8")
    b0b = Block(["IDLE:", "  idle_poll 每 5s 轮询", "  1. 检查 inbox (优先)", "  2. scan_unclaimed_tasks", "  3. 有活 → 回到 WORK", "  退出: 60s 超时", "       或 shutdown_request"], "#fef3c7", "#92400e", "#f59e0b")
    b0c = Block(["SHUTDOWN:", "  BUS.send summary", "  退出 daemon 线程", "", "IDLE_POLL_INTERVAL = 5s", "IDLE_TIMEOUT = 60s"], "#f0fdf4", "#166534", "#16a34a")
    lines, oh, _ = render_phase(cy, [b0a, b0b, b0c])
    out.extend(lines); cy += oh + 10; out.append(arrow(cy)); cy += 22

    lbl, cy = phase_label(cy, "2. idle_poll + scan_unclaimed_tasks", "#2563eb")
    out.extend(lbl)
    b1a = Block(["def idle_poll(name, messages):", "  for _ in range(12):", "    sleep(5)", "    inbox = BUS.read(name)", "    if inbox:", "      if shutdown_request:", "        return shutdown", "      inject → return work", "    tasks = scan_unclaimed()", "    if tasks:", "      claim + inject prompt", "      return work", "  return timeout"], "#0f172a", "#94a3b8")
    b1b = Block(["def scan_unclaimed_tasks():", "  all = list_tasks()", "  unclaimed = [t for t in all", "    if t.status == pending", "    and t.owner is None", "    and can_start(t.id)]", "  return unclaimed", "", "过滤条件:", "  · pending 状态", "  · 无 owner (未被认领)", "  · blockedBy 全部完成"], "#dbeafe", "#1e40af", "#60a5fa")
    b1c = Block(["关键设计:", "", "· inbox 优先于任务板", "  Lead 消息优先级最高", "· 自动认领无需 Lead", "  claim_task → 注入 prompt", "  → 回到 WORK 循环", "· 超时保护", "  60s 无活自动退出", "· 真实 CC 无固定超时", "  用 idle loop 持续轮询"], "#f0fdf4", "#166534", "#16a34a")
    lines, oh, _ = render_phase(cy, [b1a, b1b, b1c])
    out.extend(lines); cy += oh + 10; out.append(arrow(cy)); cy += 22

    lbl, cy = phase_label(cy, "3. 队友自治循环: 不再依赖 Lead 分配", "#7c3aed")
    out.extend(lbl)
    steps = ["WORK: LLM+工具", "IDLE: idle_poll 5s", "scan_unclaimed", "auto claim", "回到 WORK", "60s超时→SHUTDOWN"]
    step_blocks = [Block([s], "#f0f9ff", "#0c4a6e", "#0ea5e9") for s in steps]
    box_h5 = max(b.h for b in step_blocks)
    for b in step_blocks: b.set_h(box_h5)
    out.append(outer_box(cy, box_h5))
    out.extend(render_blocks(LEFT_X + PAD_X, cy, step_blocks))
    cy += box_h5 + 15

    summary_h = 160
    out.append(f'  <rect x="{LEFT_X}" y="{cy:.0f}" width="{FULL_W}" height="{summary_h}" fill="#1e293b" rx="8"/>')
    sy = cy + 35
    out.append(f'  <text x="{LEFT_X + FULL_W//2:.0f}" y="{sy:.0f}" fill="#fbbf24" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">空闲轮询 · 自动认领 · 三阶段生命周期</text>')
    sy += 30
    l_lines = ["核心变化:", "", "s16: 队友完成 → 退出线程, 等 Lead 下次 spawn", "s17: 队友完成 → IDLE 轮询 → 自己找活 → 自动 claim → 回到 WORK", "Lead 只需 create_task, 队友自己 scan + claim + complete"]
    lw = box_w(l_lines, 12, pad=40); lh = box_h(len(l_lines), 12)
    out.append(f'  <rect x="80" y="{sy:.0f}" width="{lw}" height="{lh}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(l_lines):
        c = "#93c5fd" if i == 0 else "#94a3b8"; fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="100" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22
    out.append('</svg>')
    return "\n".join(out)


# ═══════════════════════════════════════════════════
def gen_s18():
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 950" font-family="Menlo, Monaco, monospace">')
    out.append('  <defs><marker id="ab" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#2563eb"/></marker></defs>')
    out.append('  <rect width="1400" height="950" fill="#f8fafc" rx="8"/>')
    out.append('  <rect x="0" y="0" width="1400" height="44" fill="#1e293b" rx="8"/>')
    out.append('  <rect x="0" y="32" width="1400" height="12" fill="#1e293b"/>')
    out.append('  <text x="700" y="28" fill="#e2e8f0" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">s18 Worktree Isolation · 各干各的目录, 互不干扰</text>')
    cy = 60.0

    lbl, cy = phase_label(cy, "1. 问题: 共享目录互相覆盖 → Git Worktree 隔离", "#64748b")
    out.extend(lbl)
    b0a = Block(["s17 问题:", "", "Alice write config.py", "Bob   write config.py", "→ 互相覆盖!", "", "分不清谁的改动", "无法干净回滚"], "#fef2f2", "#991b1b", "#fca5a5")
    b0b = Block(["Git Worktree 方案:", "", "同一仓库, 多个独立", "工作目录 + 独立分支", "", ".worktrees/", "  auth-refactor/", "    (分支 wt/auth-refactor)", "  ui-login/", "    (分支 wt/ui-login)"], "#1e293b", "#94a3b8")
    b0c = Block(["解决:", "", "Alice → auth-refactor/", "Bob   → ui-login/", "", "各干各的目录", "各改各的分支", "互不干扰", "独立回滚"], "#f0fdf4", "#166534", "#16a34a")
    lines, oh, _ = render_phase(cy, [b0a, b0b, b0c])
    out.extend(lines); cy += oh + 10; out.append(arrow(cy)); cy += 22

    lbl, cy = phase_label(cy, "2. create_worktree + 安全校验 + 绑定", "#2563eb")
    out.extend(lbl)
    b1a = Block(["def create_worktree(", "    name, task_id):", "  validate_name(name)", "  # 拒绝 ../ 和非法字符", "  # [A-Za-z0-9._-]{1,64}", "  git worktree add", "    path -b wt/name HEAD", "  if task_id:", "    bind_task_to_worktree(", "      task_id, name)", "  log_event(create,...)"], "#0f172a", "#94a3b8")
    b1b = Block(["bind_task_to_worktree:", "", "  task = load_task(id)", "  task.worktree = name", "  save_task(task)", "", "  # 只写 worktree 字段", "  # 不改 status", "  # 保持 pending", "  # 等队友自己 claim"], "#dbeafe", "#1e40af", "#60a5fa")
    b1c = Block(["清理:", "", "remove_worktree:", "  git worktree remove", "  git branch -D wt/name", "", "keep_worktree:", "  保留目录和分支", "", "log_event:", "  记录操作到 events.jsonl"], "#f0fdf4", "#166534", "#16a34a")
    lines, oh, _ = render_phase(cy, [b1a, b1b, b1c])
    out.extend(lines); cy += oh + 10; out.append(arrow(cy)); cy += 22

    lbl, cy = phase_label(cy, "3. 完整流程: 任务 → Worktree → 队友 → 清理", "#7c3aed")
    out.extend(lbl)
    steps = ["Lead: create_task", "Lead: create_worktree", "bind: task.worktree=name", "队友: claim + cd", "队友: 独立目录工作", "remove/keep_worktree"]
    step_blocks = [Block([s], "#f0f9ff", "#0c4a6e", "#0ea5e9") for s in steps]
    box_h5 = max(b.h for b in step_blocks)
    for b in step_blocks: b.set_h(box_h5)
    out.append(outer_box(cy, box_h5))
    out.extend(render_blocks(LEFT_X + PAD_X, cy, step_blocks))
    cy += box_h5 + 15

    summary_h = 160
    out.append(f'  <rect x="{LEFT_X}" y="{cy:.0f}" width="{FULL_W}" height="{summary_h}" fill="#1e293b" rx="8"/>')
    sy = cy + 35
    out.append(f'  <text x="{LEFT_X + FULL_W//2:.0f}" y="{sy:.0f}" fill="#fbbf24" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">安全校验 · 任务绑定 · Git 原生隔离</text>')
    sy += 30
    l_lines = ["三层叠加:", "", "s15-s17: 谁干什么 (任务+自治) + 怎么通信 (MessageBus+协议)", "s18: 在哪干 (Git worktree 目录隔离)", "validate_worktree_name 防路径穿越, bind_task_to_worktree 不改状态, git 原生分支隔离"]
    lw = box_w(l_lines, 12, pad=40); lh = box_h(len(l_lines), 12)
    out.append(f'  <rect x="80" y="{sy:.0f}" width="{lw}" height="{lh}" fill="#334155" rx="6"/>')
    ly = sy + 12 + 12 + 4
    for i, t in enumerate(l_lines):
        c = "#93c5fd" if i == 0 else "#94a3b8"; fs2 = 13 if i == 0 else 11
        out.append(f'  <text x="100" y="{ly:.0f}" fill="{c}" font-size="{fs2:.0f}" font-weight="bold" font-family="Menlo, Monaco, monospace">{esc(t)}</text>')
        ly += 22
    out.append('</svg>')
    return "\n".join(out)


if __name__ == "__main__":
    base = "/Users/cs_beike/IdeaProjects/learn-claude-code/docs"
    tasks = [
        ("s07", gen_s07, "s07_skill_mechanism.svg"),
        ("s09", gen_s09, "s09_memory_mechanism.svg"),
        ("s10", gen_s10, "s10_system_prompt.svg"),
        ("s12", gen_s12, "s12_task_system.svg"),
        ("s13", gen_s13, "s13_background_tasks.svg"),
        ("s15", gen_s15, "s15_agent_teams.svg"),
        ("s16", gen_s16, "s16_team_protocols.svg"),
        ("s17", gen_s17, "s17_autonomous_agents.svg"),
        ("s18", gen_s18, "s18_worktree_isolation.svg"),
    ]
    for name, gen, filename in tasks:
        path = f"{base}/{name}/{filename}"
        svg = gen()
        with open(path, "w") as f:
            f.write(svg)
        r = subprocess.run(["xmllint", "--noout", path], capture_output=True)
        status = "✓" if r.returncode == 0 else f"✗ {r.stderr.decode()}"
        print(f"{path} ({len(svg)} bytes) XML: {status}")
