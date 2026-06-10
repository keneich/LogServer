#!/usr/bin/env python3
"""Markdown → PDF 변환 스크립트 (weasyprint 사용)"""

import sys
import os
import markdown
from weasyprint import HTML, CSS

MD_FILE  = sys.argv[1] if len(sys.argv) > 1 else "README02-n.md"
PDF_FILE = os.path.splitext(MD_FILE)[0] + ".pdf"

with open(MD_FILE, encoding="utf-8") as f:
    md_text = f.read()

body_html = markdown.markdown(
    md_text,
    extensions=["tables", "toc", "fenced_code", "nl2br"],
)

HTML_TEMPLATE = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Sans+Mono&display=swap');

  @page {{
    size: A4;
    margin: 18mm 20mm 18mm 20mm;
    @bottom-right {{
      content: counter(page) " / " counter(pages);
      font-family: 'Noto Sans KR', sans-serif;
      font-size: 9pt;
      color: #888;
    }}
  }}

  * {{
    box-sizing: border-box;
  }}

  body {{
    font-family: 'Noto Sans KR', 'DejaVu Sans', sans-serif;
    font-size: 10.5pt;
    line-height: 1.75;
    color: #1a1a2e;
    word-break: keep-all;
  }}

  /* ── 제목 ─────────────────────────────── */
  h1 {{
    font-size: 22pt;
    font-weight: 700;
    color: #0f3460;
    border-bottom: 3px solid #0f3460;
    padding-bottom: 8px;
    margin-top: 0;
    margin-bottom: 18px;
  }}
  h2 {{
    font-size: 15pt;
    font-weight: 700;
    color: #16213e;
    border-bottom: 1.5px solid #c8d6e5;
    padding-bottom: 5px;
    margin-top: 28px;
    margin-bottom: 12px;
  }}
  h3 {{
    font-size: 12pt;
    font-weight: 700;
    color: #1a1a2e;
    margin-top: 20px;
    margin-bottom: 8px;
  }}
  h4 {{
    font-size: 11pt;
    font-weight: 700;
    color: #333;
    margin-top: 16px;
    margin-bottom: 6px;
  }}

  /* ── 단락 ─────────────────────────────── */
  p {{
    margin: 0 0 10px 0;
  }}

  /* ── 테이블 ───────────────────────────── */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0 18px 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
  }}
  thead tr {{
    background-color: #0f3460;
    color: #ffffff;
  }}
  th {{
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
    letter-spacing: 0.02em;
  }}
  td {{
    padding: 7px 10px;
    border-bottom: 1px solid #e0e7f0;
    vertical-align: top;
  }}
  tbody tr:nth-child(even) {{
    background-color: #f4f8fc;
  }}
  tbody tr:hover {{
    background-color: #eaf2fb;
  }}
  th:first-child, td:first-child {{
    border-left: none;
  }}

  /* ── 코드 ─────────────────────────────── */
  code {{
    font-family: 'Noto Sans Mono', 'Ubuntu Mono', monospace;
    font-size: 8.5pt;
    background-color: #f0f4f8;
    padding: 1px 5px;
    border-radius: 3px;
    color: #c0392b;
  }}
  pre {{
    background-color: #1e2a3a;
    color: #cdd9e5;
    padding: 12px 16px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 12px 0;
    font-size: 8.5pt;
    line-height: 1.5;
    page-break-inside: avoid;
  }}
  pre code {{
    background: none;
    padding: 0;
    color: inherit;
  }}

  /* ── 목록 ─────────────────────────────── */
  ul, ol {{
    margin: 8px 0 12px 0;
    padding-left: 22px;
  }}
  li {{
    margin-bottom: 4px;
  }}

  /* ── 강조 ─────────────────────────────── */
  strong {{
    font-weight: 700;
    color: #0f3460;
  }}
  em {{
    color: #555;
  }}

  /* ── 구분선 ───────────────────────────── */
  hr {{
    border: none;
    border-top: 1.5px solid #c8d6e5;
    margin: 20px 0;
  }}

  /* ── 인용 ─────────────────────────────── */
  blockquote {{
    border-left: 4px solid #0f3460;
    background: #f4f8fc;
    margin: 12px 0;
    padding: 8px 14px;
    color: #555;
    font-size: 9.5pt;
  }}
</style>
</head>
<body>
{body_html}
</body>
</html>"""

print(f"[변환 중] {MD_FILE} → {PDF_FILE}")
HTML(string=HTML_TEMPLATE).write_pdf(PDF_FILE)
print(f"[완료]   {PDF_FILE} 생성됨")
print(f"[크기]   {os.path.getsize(PDF_FILE):,} bytes")
