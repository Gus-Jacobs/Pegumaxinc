"""A tiny, dependency-free Markdown -> HTML renderer.

Handles exactly the subset emitted by the course generator: ATX headings
(``#``/``##``/``###``), fenced code blocks (```lang), bold (**..**), inline
code (`..`), and paragraphs. Everything is HTML-escaped first, so course
content can never inject markup.
"""
import html
import re

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_CODE = re.compile(r"`([^`]+?)`")


def _inline(text: str) -> str:
    text = html.escape(text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _CODE.sub(r"<code>\1</code>", text)
    return text


def render_markdown(md: str) -> str:
    lines = (md or "").split("\n")
    out = []
    i = 0
    in_code = False
    code_lang = ""
    code_buf = []
    para = []

    def flush_para():
        if para:
            out.append("<p>" + "<br>".join(_inline(x) for x in para) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        fence = re.match(r"^```(\w*)\s*$", line.strip())
        if fence and not in_code:
            flush_para()
            in_code = True
            code_lang = fence.group(1) or ""
            code_buf = []
            i += 1
            continue
        if line.strip() == "```" and in_code:
            cls = f' class="language-{code_lang}"' if code_lang else ""
            out.append(f"<pre><code{cls}>" + html.escape("\n".join(code_buf)) + "</code></pre>")
            in_code = False
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_para()
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2).strip())}</h{level}>")
            i += 1
            continue

        if line.strip() == "":
            flush_para()
        else:
            para.append(line.strip())
        i += 1

    if in_code:  # unterminated fence — flush what we have
        out.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
    flush_para()
    return "\n".join(out)
