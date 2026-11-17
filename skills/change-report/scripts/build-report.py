#!/usr/bin/env python3
"""Build .fullsend/report/index.html from report.json and the shots/ folder.

Usage: build-report.py <report dir>

The page is self-contained (images inlined as base64) and local only.
"""
import base64
import html
import json
import sys
from pathlib import Path


def esc(s):
    return html.escape(str(s or ""))


def img_data(path: Path):
    if not path or not path.exists():
        return None
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def shot(root, rel, boxes, side):
    src = img_data(root / rel) if rel else None
    if not src:
        return '<div class="missing">no before capture</div>' if side == "before" else '<div class="missing">missing</div>'
    out = [f'<div class="shot"><img src="{src}" alt="{esc(side)}">']
    for b in boxes:
        if b.get("on", "after") != side:
            continue
        out.append(
            '<div class="box" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">'
            '<span>{label}</span></div>'.format(
                x=b["x"], y=b["y"], w=b["w"], h=b["h"], label=esc(b.get("label", ""))
            )
        )
    out.append("</div>")
    return "".join(out)


def main():
    root = Path(sys.argv[1]).resolve()
    data = json.loads((root / "report.json").read_text())
    parts = []
    parts.append(f"<h1>{esc(data.get('title'))}</h1>")
    meta = " · ".join(
        x for x in [
            esc(data.get("date")),
            f"<code>{esc(data['branch'])}</code>" if data.get("branch") else "",
            f'<a href="{esc(data["pr"])}">{esc(data["pr"])}</a>' if data.get("pr") else "",
        ] if x
    )
    parts.append(f'<p class="meta">{meta}</p>')
    parts.append("<h2>Summary</h2><ul>" + "".join(f"<li>{esc(s)}</li>" for s in data.get("summary", [])) + "</ul>")
    rb = data.get("rules_bent") or []
    if rb:
        parts.append("<h2>Where it bends the normal flow</h2><table><tr><th>Rule</th><th>What happens instead</th><th>How you see it</th></tr>")
        for r in rb:
            parts.append(f"<tr><td>{esc(r.get('rule'))}</td><td>{esc(r.get('what_instead'))}</td><td>{esc(r.get('how_you_see_it'))}</td></tr>")
        parts.append("</table>")
    parts.append("<h2>Screens</h2>")
    for i, s in enumerate(data.get("screens", []), 1):
        boxes = s.get("boxes", [])
        parts.append(
            f'<section class="screen"><h3>{i}. {esc(s.get("name"))}'
            + (f' <small>{esc(s.get("record"))}</small>' if s.get("record") else "")
            + (f' <small>{esc(s.get("theme"))}</small>' if s.get("theme") else "")
            + "</h3>"
        )
        if s.get("note"):
            parts.append(f'<p class="note">{esc(s["note"])}</p>')
        parts.append('<div class="pair"><div><h4>Before</h4>' + shot(root, s.get("before"), boxes, "before") + "</div>")
        parts.append('<div><h4>After</h4>' + shot(root, s.get("after"), boxes, "after") + "</div></div></section>")
    ns = data.get("not_shown") or []
    if ns:
        parts.append("<h2>Not shown</h2><ul>" + "".join(f"<li>{esc(x)}</li>" for x in ns) + "</ul>")

    css = """
    :root{--bg:#fafafa;--fg:#15171c;--mut:#5c6473;--bd:#dfe2e8;--card:#fff;--red:#e11d2e}
    @media(prefers-color-scheme:dark){:root{--bg:#0f1115;--fg:#e6e8ee;--mut:#9aa3b2;--bd:#2a2f3a;--card:#161920;--red:#ff5c6c}}
    body{margin:0;padding:32px 24px;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif;max-width:1600px}
    h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:32px 0 8px;border-bottom:1px solid var(--bd);padding-bottom:6px}
    h3{font-size:15px;margin:24px 0 6px}h3 small{color:var(--mut);font-weight:400;margin-left:8px}h4{margin:0 0 6px;color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
    .meta,.note{color:var(--mut)}code{font-family:ui-monospace,Menlo,monospace;font-size:13px}
    table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--bd)}th{color:var(--mut);font-size:12px;text-transform:uppercase}
    .pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:1100px){.pair{grid-template-columns:1fr}}
    .shot{position:relative;display:inline-block;border:1px solid var(--bd);background:var(--card);max-width:100%;overflow:hidden}
    .shot img{display:block;max-width:100%;height:auto}
    .shot .box{position:absolute;border:3px solid var(--red);border-radius:4px;box-shadow:0 0 0 2px rgba(255,255,255,.6);pointer-events:none}
    .shot .box span{position:absolute;left:-3px;top:-24px;background:var(--red);color:#fff;font-size:12px;font-weight:600;padding:2px 6px;border-radius:4px;white-space:nowrap}
    .missing{border:1px dashed var(--bd);color:var(--mut);padding:40px;text-align:center}
    section.screen{page-break-inside:avoid}
    """
    # Boxes are in image pixels; scale them with the image when it is narrower than its natural width.
    js = """
    function fit(){document.querySelectorAll('.shot').forEach(function(s){var img=s.querySelector('img');if(!img||!img.naturalWidth)return;var k=img.clientWidth/img.naturalWidth;s.querySelectorAll('.box').forEach(function(b){if(!b.dataset.x){b.dataset.x=parseFloat(b.style.left);b.dataset.y=parseFloat(b.style.top);b.dataset.w=parseFloat(b.style.width);b.dataset.h=parseFloat(b.style.height);}b.style.left=b.dataset.x*k+'px';b.style.top=b.dataset.y*k+'px';b.style.width=b.dataset.w*k+'px';b.style.height=b.dataset.h*k+'px';});});}
    window.addEventListener('load',fit);window.addEventListener('resize',fit);
    """
    doc = (
        "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{esc(data.get('title'))}</title><style>{css}</style></head><body>"
        + "".join(parts)
        + f"<script>{js}</script></body></html>"
    )
    out = root / "index.html"
    out.write_text(doc)
    print(out)


if __name__ == "__main__":
    main()
