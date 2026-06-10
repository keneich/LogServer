#!/usr/bin/env python3
"""Markdown → Standalone HTML 변환 스크립트"""

import sys
import os
import markdown
from datetime import datetime

MD_FILE   = sys.argv[1] if len(sys.argv) > 1 else "README02-n.md"
HTML_FILE = os.path.splitext(MD_FILE)[0] + ".html"
TITLE     = os.path.splitext(os.path.basename(MD_FILE))[0]
NOW       = datetime.now().strftime("%Y-%m-%d %H:%M")

with open(MD_FILE, encoding="utf-8") as f:
    md_text = f.read()

# 첫 번째 h1을 문서 제목으로 추출
doc_title = TITLE
for line in md_text.splitlines():
    if line.startswith("# "):
        doc_title = line[2:].strip()
        break

body_html = markdown.markdown(
    md_text,
    extensions=["tables", "toc", "fenced_code", "nl2br"],
)

HTML_OUTPUT = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="generator" content="md_to_html.py" />
  <meta name="created" content="{NOW}" />
  <title>{doc_title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Sans+Mono:wght@400;600&display=swap" rel="stylesheet" />
  <style>
    /* ── Reset & Base ─────────────────────────────────────────── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --color-primary:    #0f3460;
      --color-secondary:  #16213e;
      --color-accent:     #e94560;
      --color-bg:         #f7f9fc;
      --color-surface:    #ffffff;
      --color-border:     #d0dce8;
      --color-text:       #1a1a2e;
      --color-muted:      #6b7a99;
      --color-code-bg:    #1e2a3a;
      --color-code-text:  #cdd9e5;
      --color-tag-bg:     #e8f0fe;
      --color-tag-text:   #1a56db;
      --radius:           8px;
      --shadow:           0 2px 12px rgba(15,52,96,.08);
    }}

    html {{ scroll-behavior: smooth; }}

    body {{
      font-family: 'Noto Sans KR', 'DejaVu Sans', system-ui, sans-serif;
      font-size: 15px;
      line-height: 1.8;
      color: var(--color-text);
      background: var(--color-bg);
      -webkit-font-smoothing: antialiased;
    }}

    /* ── Layout ───────────────────────────────────────────────── */
    .page-wrapper {{
      display: flex;
      min-height: 100vh;
    }}

    /* 사이드바 TOC */
    .sidebar {{
      width: 260px;
      min-width: 260px;
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      background: var(--color-secondary);
      color: #c8d6e5;
      padding: 32px 20px 40px;
      font-size: 13px;
      line-height: 1.6;
      flex-shrink: 0;
    }}
    .sidebar-logo {{
      font-size: 13px;
      font-weight: 700;
      letter-spacing: .06em;
      text-transform: uppercase;
      color: #ffffff;
      margin-bottom: 24px;
      padding-bottom: 14px;
      border-bottom: 1px solid rgba(255,255,255,.12);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .sidebar-logo::before {{
      content: "📋";
      font-size: 16px;
    }}
    .sidebar nav ul {{
      list-style: none;
    }}
    .sidebar nav > ul > li {{
      margin-bottom: 4px;
    }}
    .sidebar nav a {{
      display: block;
      padding: 5px 10px;
      border-radius: 5px;
      color: #a8bbd0;
      text-decoration: none;
      transition: background .15s, color .15s;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .sidebar nav a:hover {{
      background: rgba(255,255,255,.08);
      color: #ffffff;
    }}
    .sidebar nav ul ul {{
      padding-left: 14px;
      margin-top: 2px;
    }}
    .sidebar nav ul ul a {{
      font-size: 12px;
      color: #7a95b0;
      padding: 3px 8px;
    }}
    .sidebar nav ul ul a:hover {{
      color: #c8d6e5;
    }}

    /* 메인 콘텐츠 */
    main {{
      flex: 1;
      min-width: 0;
      padding: 48px 56px 80px;
      max-width: 900px;
    }}

    /* ── 헤더 메타 ────────────────────────────────────────────── */
    .doc-meta {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 36px;
      padding-bottom: 20px;
      border-bottom: 2px solid var(--color-border);
    }}
    .doc-meta .badge {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 11.5px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 20px;
      background: var(--color-tag-bg);
      color: var(--color-tag-text);
      letter-spacing: .03em;
    }}
    .doc-meta .badge.date {{
      background: #fef3c7;
      color: #92400e;
    }}

    /* ── 제목 ─────────────────────────────────────────────────── */
    h1, h2, h3, h4, h5, h6 {{
      font-weight: 700;
      line-height: 1.35;
      word-break: keep-all;
    }}
    h1 {{
      font-size: 30px;
      color: var(--color-primary);
      margin-bottom: 24px;
      padding-bottom: 14px;
      border-bottom: 3px solid var(--color-primary);
    }}
    h2 {{
      font-size: 21px;
      color: var(--color-secondary);
      margin-top: 48px;
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 1.5px solid var(--color-border);
    }}
    h3 {{
      font-size: 17px;
      color: var(--color-text);
      margin-top: 32px;
      margin-bottom: 10px;
    }}
    h4 {{
      font-size: 15px;
      color: var(--color-text);
      margin-top: 24px;
      margin-bottom: 8px;
    }}

    /* 앵커 링크 */
    h2::before, h3::before {{
      content: '';
      display: block;
      height: 72px;
      margin-top: -72px;
      pointer-events: none;
    }}

    /* ── 단락·텍스트 ──────────────────────────────────────────── */
    p {{
      margin-bottom: 14px;
      word-break: keep-all;
    }}
    a {{
      color: var(--color-primary);
      text-decoration: none;
      border-bottom: 1px dashed var(--color-border);
      transition: color .15s, border-color .15s;
    }}
    a:hover {{
      color: var(--color-accent);
      border-color: var(--color-accent);
    }}
    strong {{ font-weight: 700; color: var(--color-primary); }}
    em     {{ color: #555; font-style: italic; }}

    /* ── 테이블 ───────────────────────────────────────────────── */
    .table-wrap {{
      overflow-x: auto;
      margin: 18px 0 24px;
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13.5px;
      background: var(--color-surface);
    }}
    thead {{
      background: var(--color-primary);
      color: #ffffff;
    }}
    th {{
      padding: 11px 14px;
      text-align: left;
      font-weight: 600;
      font-size: 12.5px;
      letter-spacing: .04em;
      white-space: nowrap;
    }}
    td {{
      padding: 10px 14px;
      border-bottom: 1px solid #e8eef5;
      vertical-align: top;
      word-break: keep-all;
    }}
    tbody tr:nth-child(even) {{ background: #f8fafd; }}
    tbody tr:hover           {{ background: #eef5ff; transition: background .12s; }}

    /* ── 코드 ─────────────────────────────────────────────────── */
    code {{
      font-family: 'Noto Sans Mono', 'Ubuntu Mono', 'Courier New', monospace;
      font-size: 13px;
      background: #eef2f7;
      color: #c0392b;
      padding: 2px 6px;
      border-radius: 4px;
    }}
    pre {{
      background: var(--color-code-bg);
      color: var(--color-code-text);
      padding: 18px 20px;
      border-radius: var(--radius);
      overflow-x: auto;
      margin: 16px 0 20px;
      font-size: 13px;
      line-height: 1.6;
      box-shadow: var(--shadow);
    }}
    pre code {{
      background: none;
      padding: 0;
      color: inherit;
      font-size: inherit;
    }}

    /* ── 목록 ─────────────────────────────────────────────────── */
    ul, ol {{
      padding-left: 24px;
      margin-bottom: 14px;
    }}
    li {{ margin-bottom: 5px; }}
    li > ul, li > ol {{ margin-top: 5px; margin-bottom: 5px; }}

    /* ── 인용 ─────────────────────────────────────────────────── */
    blockquote {{
      border-left: 4px solid var(--color-primary);
      background: #f0f5ff;
      margin: 16px 0;
      padding: 10px 18px;
      border-radius: 0 var(--radius) var(--radius) 0;
      color: #444;
      font-size: 14px;
    }}
    blockquote p {{ margin: 0; }}

    /* ── 구분선 ───────────────────────────────────────────────── */
    hr {{
      border: none;
      border-top: 1.5px solid var(--color-border);
      margin: 36px 0;
    }}

    /* ── 푸터 ─────────────────────────────────────────────────── */
    .doc-footer {{
      margin-top: 72px;
      padding-top: 20px;
      border-top: 1px solid var(--color-border);
      font-size: 12px;
      color: var(--color-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    /* ── 상단 이동 버튼 ───────────────────────────────────────── */
    .back-to-top {{
      position: fixed;
      bottom: 32px;
      right: 32px;
      width: 42px;
      height: 42px;
      background: var(--color-primary);
      color: #fff;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      text-decoration: none;
      border: none;
      box-shadow: 0 4px 14px rgba(15,52,96,.3);
      opacity: 0;
      transition: opacity .2s;
    }}
    .back-to-top.visible {{ opacity: 1; }}

    /* ── 반응형 ───────────────────────────────────────────────── */
    @media (max-width: 860px) {{
      .sidebar   {{ display: none; }}
      main       {{ padding: 28px 20px 60px; }}
    }}
    @media print {{
      .sidebar, .back-to-top {{ display: none; }}
      main {{ padding: 0; max-width: 100%; }}
      a    {{ border: none; }}
    }}
  </style>
</head>
<body>
<div class="page-wrapper">

  <!-- 사이드바 TOC -->
  <aside class="sidebar">
    <div class="sidebar-logo">LogServer Docs</div>
    <nav>
      <ul>
        <li><a href="#1-배경">1. 배경</a></li>
        <li><a href="#2-목표">2. 목표</a></li>
        <li><a href="#ilm-저장-정책">ILM 저장 정책</a></li>
        <li>
          <a href="#3-기술-스택">3. 기술 스택</a>
          <ul>
            <li><a href="#서버-컴포넌트">서버 컴포넌트</a></li>
            <li><a href="#에이전트">에이전트</a></li>
          </ul>
        </li>
        <li>
          <a href="#4-서버-스펙">4. 서버 스펙</a>
          <ul>
            <li><a href="#로그-발생량-추정">로그 발생량 추정</a></li>
            <li><a href="#서버별-스펙">서버별 스펙</a></li>
          </ul>
        </li>
        <li><a href="#5-구축-일정-8주">5. 구축 일정</a></li>
      </ul>
    </nav>
  </aside>

  <!-- 메인 콘텐츠 -->
  <main id="top">
    <div class="doc-meta">
      <span class="badge">📄 LogServer</span>
      <span class="badge">ELK Stack 8.17.4</span>
      <span class="badge date">🗓 {NOW}</span>
    </div>

    <div class="content">
{body_html}
    </div>

    <footer class="doc-footer">
      <span>LogServer — ELK 스택 기반 중앙화 로그 수집·모니터링 시스템</span>
      <span>생성: {NOW}</span>
    </footer>
  </main>

</div>

<!-- 상단 이동 버튼 -->
<a href="#top" class="back-to-top" id="backToTop">↑</a>

<!-- 테이블 wrap 처리 -->
<script>
  document.querySelectorAll('table').forEach(function(t) {{
    var wrap = document.createElement('div');
    wrap.className = 'table-wrap';
    t.parentNode.insertBefore(wrap, t);
    wrap.appendChild(t);
  }});

  // 상단 이동 버튼 표시 제어
  var btn = document.getElementById('backToTop');
  window.addEventListener('scroll', function() {{
    btn.classList.toggle('visible', window.scrollY > 300);
  }});
</script>
</body>
</html>"""

with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(HTML_OUTPUT)

size = os.path.getsize(HTML_FILE)
print(f"[변환 중] {MD_FILE} → {HTML_FILE}")
print(f"[완료]   {HTML_FILE} 생성됨")
print(f"[크기]   {size:,} bytes  ({size // 1024} KB)")
