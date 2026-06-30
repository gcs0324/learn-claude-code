#!/usr/bin/env python3
"""
SVG generator with correct text-width calculation for monospace fonts.
Strategy: CJK char = 2 × ASCII char width.
ASCII width = font_size × 0.6
CJK width = font_size × 1.2
"""

import re
import math

CJK_PATTERN = re.compile(r'[一-鿿　-〿＀-￯぀-ゟ゠-ヿ]')

def text_width(text: str, font_size: float) -> float:
    """Calculate rendered width of text in monospace font."""
    cjk = sum(1 for c in text if CJK_PATTERN.match(c))
    ascii_count = len(text) - cjk
    ascii_w = font_size * 0.6
    cjk_w = font_size * 1.2
    return ascii_count * ascii_w + cjk * cjk_w

def rect_for_text(text: str, font_size: float, padding: float = 20) -> float:
    """Return rect width for a single line of text, with padding."""
    return math.ceil(text_width(text, font_size) + padding * 2)

def max_text_width(texts: list[str], font_size: float) -> float:
    """Return the maximum width among multiple lines."""
    return max(text_width(t, font_size) for t in texts)

def rect_for_multiline(texts: list[str], font_size: float, padding: float = 20) -> tuple[float, float]:
    """Return (width, height) for a multi-line text block."""
    w = math.ceil(max_text_width(texts, font_size) + padding * 2)
    h = math.ceil(len(texts) * (font_size + 6) + padding * 2)
    return w, h

def text_elem(x: float, y: float, text: str, font_size: float, color: str = "#e2e8f0",
              bold: bool = False, anchor: str = "start", cls: str = "") -> str:
    """Generate a <text> element."""
    attrs = f'x="{x:.0f}" y="{y:.0f}" fill="{color}" font-size="{font_size:.0f}" font-family="Menlo, Monaco, monospace"'
    if bold:
        attrs += ' font-weight="bold"'
    if cls:
        attrs += f' class="{cls}"'
    # Escape XML special chars
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'  <text {attrs}>{safe}</text>'

def code_block(x: float, y: float, lines: list[str], font_size: float = 11) -> str:
    """Generate a dark code block with auto-sized rect."""
    w, h = rect_for_multiline(lines, font_size)
    result = [f'  <rect x="{x:.0f}" y="{y:.0f}" width="{w}" height="{h}" fill="#0f172a" rx="5"/>']
    ly = y + font_size + 6
    for line in lines:
        # Parse tspan markers: {c:COLOR}text{/c} or {b}text{/b} for bold
        result.append(f'  <text x="{x+12:.0f}" y="{ly:.0f}" fill="#94a3b8" font-size="{font_size:.0f}" font-family="Menlo, Monaco, monospace">{escape_xml(line)}</text>')
        ly += font_size + 6
    result.append(f'<!-- block w={w} h={h} -->')
    return "\n".join(result)

def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def colored_text(x: float, y: float, segments: list[tuple[str, str]], font_size: float) -> str:
    """Text with colored segments. segments = [(text, color), ...]"""
    safe_segs = [(escape_xml(t), c) for t, c in segments]
    combined = "".join(f'<tspan fill="{c}">{t}</tspan>' for t, c in safe_segs)
    return f'  <text x="{x:.0f}" y="{y:.0f}" font-size="{font_size:.0f}" font-family="Menlo, Monaco, monospace">{combined}</text>'

# ═══════════════════════════════════════════════════════
# s07 Skill Loading SVG
# ═══════════════════════════════════════════════════════

def gen_s07():
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 1300" font-family="Menlo, Monaco, monospace">')
    lines.append('  <defs>')
    lines.append('    <marker id="ab" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">')
    lines.append('      <path d="M0,0 L8,3 L0,6 Z" fill="#2563eb"/>')
    lines.append('    </marker>')
    lines.append('  </defs>')
    lines.append('  <rect width="1400" height="1300" fill="#f8fafc" rx="8"/>')

    # Title
    lines.append(f'  <rect x="0" y="0" width="1400" height="44" fill="#1e293b" rx="8"/>')
    lines.append(f'  <rect x="0" y="32" width="1400" height="12" fill="#1e293b"/>')
    lines.append(f'  <text x="700" y="28" fill="#e2e8f0" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">s07 Skill 加载机制 · 两级按需知识注入</text>')

    cy = 60  # current y

    # ── Phase 0: Install ──
    lines.append(f'<!-- Phase 0: Install -->')
    ph0_texts = [
        '0. 安装 (开发者操作)',
    ]
    ph0_w = rect_for_text(ph0_texts[0], 12) + 20
    lines.append(f'  <rect x="30" y="{cy}" width="140" height="26" fill="#64748b" rx="6"/>')
    lines.append(f'  <rect x="30" y="{cy+13}" width="140" height="13" fill="#64748b"/>')
    lines.append(f'  <text x="100" y="{cy+18}" fill="#fff" font-size="12" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">0. 安装 (开发者)</text>')

    box_y = cy + 32
    # Box content - 3 columns
    col1_lines = [
        'skills/',
        '├── code-review/',
        '│   └── SKILL.md',
    ]
    col2_lines = [
        'SKILL.md 内容:',
        '---',
        'name: code-review',
        'description: 代码审查,安全检查,性能',
        '---',
        '# Code Review Skill ...',
    ]
    col3_lines = [
        '安装 = 创建文件',
        '放在 skills/<name>/ 下即可',
        '程序启动时自动发现',
        '无需注册, 无需配置',
    ]

    cw1, ch1 = rect_for_multiline(col1_lines, 11)
    cw2, ch2 = rect_for_multiline(col2_lines, 11)
    cw3, ch3 = rect_for_multiline(col3_lines, 11)
    box_h = max(ch1, ch2, ch3)
    box_w = cw1 + cw2 + cw3 + 60

    lines.append(f'  <rect x="30" y="{box_y}" width="{box_w}" height="{box_h}" fill="#fff" stroke="#cbd5e1" rx="6"/>')

    xp = 45
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{cw1}" height="{ch1-24}" fill="#1e293b" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in col1_lines:
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#94a3b8" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    xp += cw1 + 15
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{cw2}" height="{ch2-24}" fill="#0f172a" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in col2_lines:
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#94a3b8" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    xp += cw2 + 15
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{cw3}" height="{ch3-24}" fill="#fef3c7" stroke="#f59e0b" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in col3_lines:
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#92400e" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    cy = box_y + box_h + 10

    # Arrow
    lines.append(f'  <line x1="700" y1="{cy}" x2="700" y2="{cy+16}" stroke="#2563eb" stroke-width="2" marker-end="url(#ab)"/>')
    cy += 22

    # ── Phase 1: Scan ──
    lines.append(f'<!-- Phase 1: Scan -->')
    p1_label_w = rect_for_text('1. 启动扫描 _scan_skills()', 12) + 20
    lines.append(f'  <rect x="30" y="{cy}" width="{p1_label_w}" height="26" fill="#2563eb" rx="6"/>')
    lines.append(f'  <rect x="30" y="{cy+13}" width="{p1_label_w}" height="13" fill="#2563eb"/>')
    lines.append(f'  <text x="{30+p1_label_w//2:.0f}" y="{cy+18}" fill="#fff" font-size="12" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">1. 启动扫描 _scan_skills()</text>')

    box_y = cy + 32
    p1_code = [
        'def _scan_skills():',
        '  for d in SKILLS_DIR.iterdir():',
        '    manifest = d / "SKILL.md"',
        '    meta,body = _parse_frontmatter(raw)',
        '    SKILL_REGISTRY[name] = {',
        '      "name":name, "description":desc,',
        '      "content":raw }',
    ]
    p1_code_w, p1_code_h = rect_for_multiline(p1_code, 11)

    p1_reg = [
        'SKILL_REGISTRY (内存字典)',
        '─────────────────',
        '"code-review" → {',
        '  name: "code-review",',
        '  description: "代码审查...",',
        '  content: "---\nname: ..."',
        '}',
    ]
    p1_reg_w, p1_reg_h = rect_for_multiline(p1_reg, 11)

    p1_note = [
        '启动时执行一次',
        '所有 skill 常驻内存',
        '后续查找 O(1)',
        '成本: 0 tokens (纯文件IO)',
    ]
    p1_note_w, p1_note_h = rect_for_multiline(p1_note, 11)

    box_w = p1_code_w + p1_reg_w + p1_note_w + 60
    box_h = max(p1_code_h, p1_reg_h, p1_note_h) + 24

    lines.append(f'  <rect x="30" y="{box_y}" width="{box_w}" height="{box_h}" fill="#fff" stroke="#cbd5e1" rx="6"/>')

    xp = 45
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{p1_code_w}" height="{p1_code_h-24}" fill="#0f172a" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in p1_code:
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#94a3b8" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    xp += p1_code_w + 15
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{p1_reg_w}" height="{p1_reg_h-24}" fill="#f0fdf4" stroke="#16a34a" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in p1_reg:
        color = "#166534" if "───" not in t else "#bbf7d0"
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#166534" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    xp += p1_reg_w + 15
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{p1_note_w}" height="{p1_note_h-24}" fill="#dbeafe" stroke="#60a5fa" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in p1_note:
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#1e40af" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    cy = box_y + box_h + 10
    lines.append(f'  <line x1="700" y1="{cy}" x2="700" y2="{cy+16}" stroke="#2563eb" stroke-width="2" marker-end="url(#ab)"/>')
    cy += 22

    # ── Phase 2: SYSTEM prompt ──
    p2_label_w = rect_for_text('2. 注入 SYSTEM prompt', 12) + 20
    lines.append(f'  <rect x="30" y="{cy}" width="{p2_label_w}" height="26" fill="#7c3aed" rx="6"/>')
    lines.append(f'  <rect x="30" y="{cy+13}" width="{p2_label_w}" height="13" fill="#7c3aed"/>')
    lines.append(f'  <text x="{30+p2_label_w//2:.0f}" y="{cy+18}" fill="#fff" font-size="12" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">2. 注入 SYSTEM prompt</text>')

    box_y = cy + 32
    p2_code = [
        'def build_system():',
        '  catalog = list_skills()',
        '  return f"Skills available:"',
        '         f"{catalog}\\n"',
        '         "Use load_skill ..."',
    ]
    p2_code_w, p2_code_h = rect_for_multiline(p2_code, 11)

    p2_result = [
        'SYSTEM prompt (每次API请求都携带):',
        'Skills available:',
        '- code-review: 代码审查,安全检查,',
        '  性能分析,可维护性评估',
        '成本: ~100 tokens/skill',
    ]
    p2_result_w, p2_result_h = rect_for_multiline(p2_result, 11)

    box_w = p2_code_w + p2_result_w + 45
    box_h = max(p2_code_h, p2_result_h) + 24

    lines.append(f'  <rect x="30" y="{box_y}" width="{box_w}" height="{box_h}" fill="#fff" stroke="#cbd5e1" rx="6"/>')

    xp = 45
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{p2_code_w}" height="{p2_code_h-24}" fill="#0f172a" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in p2_code:
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#94a3b8" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    xp += p2_code_w + 15
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{p2_result_w}" height="{p2_result_h-24}" fill="#faf5ff" stroke="#a855f7" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in p2_result:
        color = "#6b21a8"
        if t.startswith("成本"):
            color = "#1e40af"
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="{color}" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    cy = box_y + box_h + 10
    lines.append(f'  <line x1="700" y1="{cy}" x2="700" y2="{cy+16}" stroke="#2563eb" stroke-width="2" marker-end="url(#ab)"/>')
    cy += 22

    # ── Phase 3: LLM calls load_skill ──
    p3_label_w = rect_for_text('3. 大模型判断并调用 load_skill', 12) + 20
    lines.append(f'  <rect x="30" y="{cy}" width="{p3_label_w}" height="26" fill="#dc2626" rx="6"/>')
    lines.append(f'  <rect x="30" y="{cy+13}" width="{p3_label_w}" height="13" fill="#dc2626"/>')
    lines.append(f'  <text x="{30+p3_label_w//2:.0f}" y="{cy+18}" fill="#fff" font-size="12" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">3. 大模型判断并调用 load_skill</text>')

    box_y = cy + 32
    p3_reason = [
        '大模型推理过程:',
        '(1) 用户: "帮我review代码"',
        '(2) SYSTEM: code-review可用',
        '(3) 判断: 加载此skill',
    ]
    p3_reason_w, p3_reason_h = rect_for_multiline(p3_reason, 11)

    p3_tool = [
        '大模型发起的tool_use:',
        '{',
        '  "type":"tool_use",',
        '  "name":"load_skill",',
        '  "input":{',
        '    "name":"code-review"',
        '  }',
        '}',
    ]
    p3_tool_w, p3_tool_h = rect_for_multiline(p3_tool, 11)

    p3_how = [
        '大模型如何知道该调用?',
        '1. SYSTEM有skill目录',
        '2. TOOLS有load_skill',
        '3. 匹配任务与描述',
        '4. 发起tool_use',
    ]
    p3_how_w, p3_how_h = rect_for_multiline(p3_how, 11)

    box_w = p3_reason_w + p3_tool_w + p3_how_w + 60
    box_h = max(p3_reason_h, p3_tool_h, p3_how_h) + 24

    lines.append(f'  <rect x="30" y="{box_y}" width="{box_w}" height="{box_h}" fill="#fff" stroke="#cbd5e1" rx="6"/>')

    xp = 45
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{p3_reason_w}" height="{p3_reason_h-24}" fill="#fef2f2" stroke="#fca5a5" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in p3_reason:
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#991b1b" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    xp += p3_reason_w + 15
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{p3_tool_w}" height="{p3_tool_h-24}" fill="#0f172a" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in p3_tool:
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#93c5fd" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    xp += p3_tool_w + 15
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{p3_how_w}" height="{p3_how_h-24}" fill="#fef3c7" stroke="#f59e0b" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in p3_how:
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#92400e" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    cy = box_y + box_h + 10
    lines.append(f'  <line x1="700" y1="{cy}" x2="700" y2="{cy+16}" stroke="#2563eb" stroke-width="2" marker-end="url(#ab)"/>')
    cy += 22

    # ── Phase 4: Return content ──
    p4_label_w = rect_for_text('4. load_skill() 返回完整内容', 12) + 20
    lines.append(f'  <rect x="30" y="{cy}" width="{p4_label_w}" height="26" fill="#16a34a" rx="6"/>')
    lines.append(f'  <rect x="30" y="{cy+13}" width="{p4_label_w}" height="13" fill="#16a34a"/>')
    lines.append(f'  <text x="{30+p4_label_w//2:.0f}" y="{cy+18}" fill="#fff" font-size="12" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">4. load_skill() 返回完整内容</text>')

    box_y = cy + 32
    p4_code = [
        'def load_skill(name):',
        '  skill = SKILL_REGISTRY.get(name)',
        '  return skill["content"]',
        '  # 返回完整SKILL.md原文',
    ]
    p4_code_w, p4_code_h = rect_for_multiline(p4_code, 11)

    p4_result = [
        'tool_result (注入上下文):',
        '"---',
        'name: code-review',
        '---',
        '# Code Review Skill',
        '## 1. Security ..."',
        '成本: ~2000 tokens',
    ]
    p4_result_w, p4_result_h = rect_for_multiline(p4_result, 11)

    box_w = p4_code_w + p4_result_w + 45
    box_h = max(p4_code_h, p4_result_h) + 24

    lines.append(f'  <rect x="30" y="{box_y}" width="{box_w}" height="{box_h}" fill="#fff" stroke="#cbd5e1" rx="6"/>')

    xp = 45
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{p4_code_w}" height="{p4_code_h-24}" fill="#0f172a" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in p4_code:
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#94a3b8" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    xp += p4_code_w + 15
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{p4_result_w}" height="{p4_result_h-24}" fill="#f0fdf4" stroke="#16a34a" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in p4_result:
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#166534" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    cy = box_y + box_h + 10

    # Result bar
    result_text = '大模型获得完整skill指令 → 按SKILL.md检查清单执行: 安全检查→正确性→性能→可维护性'
    result_w = rect_for_text(result_text, 11) + 20
    lines.append(f'  <rect x="30" y="{cy}" width="{result_w}" height="20" fill="#ecfdf5" stroke="#6ee7b7" rx="3"/>')
    lines.append(f'  <text x="{30+result_w//2:.0f}" y="{cy+14}" fill="#065f46" font-size="11" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">{escape_xml(result_text)}</text>')

    cy += 26
    lines.append(f'  <line x1="700" y1="{cy}" x2="700" y2="{cy+16}" stroke="#2563eb" stroke-width="2" marker-end="url(#ab)"/>')
    cy += 22

    # ── Phase 5: Tool registration ──
    p5_label_w = rect_for_text('5. TOOLS 注册 (大模型为何能调用)', 12) + 20
    lines.append(f'  <rect x="30" y="{cy}" width="{p5_label_w}" height="26" fill="#0ea5e9" rx="6"/>')
    lines.append(f'  <rect x="30" y="{cy+13}" width="{p5_label_w}" height="13" fill="#0ea5e9"/>')
    lines.append(f'  <text x="{30+p5_label_w//2:.0f}" y="{cy+18}" fill="#fff" font-size="12" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">5. TOOLS 注册 (大模型为何能调用)</text>')

    box_y = cy + 32
    p5_tools = [
        'TOOLS = [ ...,',
        '  { "name":"load_skill",',
        '    "description":"Load full content of a skill by name.",',
        '    "input_schema":{',
        '      "properties":{',
        '        "name":{"type":"string"} } } } ]',
    ]
    p5_tools_w, p5_tools_h = rect_for_multiline(p5_tools, 11)

    p5_handler = [
        'TOOL_HANDLERS = {',
        '  "load_skill": load_skill,',
        '}',
        '',
        'agent_loop: tool_use',
        '  → TOOL_HANDLERS[name]',
        '  → handler(**input)',
        '  → tool_result',
    ]
    p5_handler_w, p5_handler_h = rect_for_multiline(p5_handler, 11)

    box_w = p5_tools_w + p5_handler_w + 45
    box_h = max(p5_tools_h, p5_handler_h) + 24

    lines.append(f'  <rect x="30" y="{box_y}" width="{box_w}" height="{box_h}" fill="#fff" stroke="#cbd5e1" rx="6"/>')

    xp = 45
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{p5_tools_w}" height="{p5_tools_h-24}" fill="#0f172a" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in p5_tools:
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#94a3b8" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    xp += p5_tools_w + 15
    lines.append(f'  <rect x="{xp}" y="{box_y+12}" width="{p5_handler_w}" height="{p5_handler_h-24}" fill="#f0f9ff" stroke="#0ea5e9" rx="5"/>')
    ly = box_y + 12 + 11 + 6
    for t in p5_handler:
        lines.append(f'  <text x="{xp+12}" y="{ly:.0f}" fill="#0c4a6e" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 17

    cy = box_y + box_h + 10

    # ── Bottom summary ──
    lines.append(f'  <rect x="30" y="{cy}" width="1340" height="340" fill="#1e293b" rx="8"/>')
    cy += 35

    lines.append(f'  <text x="700" y="{cy}" fill="#fbbf24" font-size="15" font-weight="bold" text-anchor="middle" font-family="Menlo, Monaco, monospace">两级加载架构 · 总结</text>')
    cy += 30

    # L1 box
    l1_texts = [
        'Layer 1: 目录注入 (便宜, 始终在线)',
        '',
        '· SYSTEM prompt含所有skill的名称+一行描述',
        '· 成本: ~100 tokens/skill, 始终随请求发送',
        '· 作用: 让大模型知道有哪些能力可用',
    ]
    l1_w, l1_h = rect_for_multiline(l1_texts, 12)
    lines.append(f'  <rect x="80" y="{cy}" width="{l1_w}" height="{l1_h}" fill="#334155" rx="6"/>')
    ly = cy + 12 + 12 + 4
    for i, t in enumerate(l1_texts):
        if i == 0:
            lines.append(f'  <text x="100" y="{ly:.0f}" fill="#93c5fd" font-size="13" font-weight="bold" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        else:
            lines.append(f'  <text x="100" y="{ly:.0f}" fill="#94a3b8" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 22

    # Arrow between L1 and L2
    arrow_x = 80 + l1_w + 15
    lines.append(f'  <line x1="{arrow_x}" y1="{cy+l1_h//2}" x2="{arrow_x+30}" y2="{cy+l1_h//2}" stroke="#64748b" stroke-width="2" marker-end="url(#ab)"/>')

    # L2 box
    l2_texts = [
        'Layer 2: 完整加载 (按需, 精准注入)',
        '',
        '· 大模型调用 load_skill(name) 工具',
        '· 返回完整 SKILL.md, ~2000 tokens/skill',
        '· 仅实际使用时才消耗 token',
    ]
    l2_w, l2_h = rect_for_multiline(l2_texts, 12)
    l2_x = arrow_x + 40
    lines.append(f'  <rect x="{l2_x}" y="{cy}" width="{l2_w}" height="{l2_h}" fill="#334155" rx="6"/>')
    ly = cy + 12 + 12 + 4
    for i, t in enumerate(l2_texts):
        if i == 0:
            lines.append(f'  <text x="{l2_x+20}" y="{ly:.0f}" fill="#86efac" font-size="13" font-weight="bold" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        else:
            lines.append(f'  <text x="{l2_x+20}" y="{ly:.0f}" fill="#94a3b8" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 22

    cy += max(l1_h, l2_h) + 20

    # vs real
    vs_texts = [
        's07 模拟 vs 真实 Claude Code',
        '',
        's07 (模拟): SYSTEM有目录 → 大模型调用load_skill → 返回tool_result → 下一轮才读到 → 2个API回合',
        '真实: system-reminder有目录 → 大模型调用Skill工具 → harness直接注入SKILL.md → 1个API回合',
        '核心差异: s07的load_skill是普通工具(tool_result下一轮); 真实Skill是harness级工具(同轮注入)',
    ]
    vs_w, vs_h = rect_for_multiline(vs_texts, 12)
    vs_w = max(vs_w, 1100)
    lines.append(f'  <rect x="80" y="{cy}" width="{vs_w}" height="{vs_h}" fill="#1e293b" stroke="#475569" rx="6"/>')
    ly = cy + 12 + 12 + 4
    for i, t in enumerate(vs_texts):
        if i == 0:
            lines.append(f'  <text x="100" y="{ly:.0f}" fill="#fbbf24" font-size="13" font-weight="bold" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        elif t.startswith('s07'):
            lines.append(f'  <text x="100" y="{ly:.0f}" fill="#f87171" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        elif t.startswith('真实'):
            lines.append(f'  <text x="100" y="{ly:.0f}" fill="#4ade80" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        else:
            lines.append(f'  <text x="100" y="{ly:.0f}" fill="#94a3b8" font-size="11" font-family="Menlo, Monaco, monospace">{escape_xml(t)}</text>')
        ly += 22

    lines.append('</svg>')
    return "\n".join(lines)


if __name__ == "__main__":
    svg = gen_s07()
    path = "/Users/cs_beike/IdeaProjects/learn-claude-code/docs/s07_skill_mechanism.svg"
    with open(path, "w") as f:
        f.write(svg)
    print(f"Generated {path} ({len(svg)} bytes)")
    # Validate
    import subprocess
    r = subprocess.run(["xmllint", "--noout", path], capture_output=True)
    if r.returncode == 0:
        print("XML valid ✓")
    else:
        print(f"XML error: {r.stderr.decode()}")
