"""IEEE-style report builder: one content source (report_content.py: title, authors, abstract, keywords, sections of
blocks) -> (1) IEEEtran LaTeX source (compile on any TeX installation; none is installed here), (2) an IEEE-styled
two-column HTML rendering, printed to PDF with Edge headless.

Blocks: ("p", text) | ("ul", [items]) | ("fig", path, caption, wide) | ("table", caption, rows, wide) | ("eq", text)
Inline markup in text: **bold**, *italic*, `code`. Numbers are filled in report_content.py from measured JSON only.

  python -E -s experiments/stage6_final/report_build.py
"""

import base64
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "research" / "final"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


def inline_html(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)


TEX_MAP = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "−": "--", "–": "--", "—": "---", "≥": r"$\geq$", "≤": r"$\leq$",
           "×": r"$\times$", "≈": r"$\approx$", "±": r"$\pm$", "→": r"$\rightarrow$", "≪": r"$\ll$", "∈": r"$\in$", "≡": r"$\equiv$",
           "κ": r"$\kappa$", "σ": r"$\sigma$", "τ": r"$\tau$", "μ": r"$\mu$", "ξ": r"$\xi$", "ε": r"$\varepsilon$", "β": r"$\beta$",
           "λ": r"$\lambda$", "φ": r"$\phi$", "Δ": r"$\Delta$", "ŝ": r"$\hat{s}$", "²": r"$^2$", "√": r"$\surd$", "Σ": r"$\Sigma$",
           "∗": r"$\ast$", "·": r"$\cdot$", "…": r"\ldots{}", "’": "'", "“": "``", "”": "''", "°": r"$^\circ$", "∞": r"$\infty$",
           "≠": r"$\neq$", "‖": r"$\|$", "⁻": "-", "¹": r"$^1$", "₀": r"$_0$", "ᵢ": r"$_i$", "∑": r"$\sum$", "π": r"$\pi$", "η": r"$\eta$",
           "ρ": r"$\rho$", "α": r"$\alpha$", "θ": r"$\theta$", "∼": r"$\sim$", "⊂": r"$\subset$", "✓": "yes", "✗": "no", "ℝ": r"$\mathbb{R}$"}


def tex(t):
    out = []
    for ch in t:
        out.append(TEX_MAP.get(ch, ch))
    s = "".join(out)
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\\emph{\1}", s)
    return re.sub(r"`(.+?)`", r"\\texttt{\1}", s)


def build_tex(C, figdir):
    L = [r"\documentclass[conference]{IEEEtran}", r"\usepackage{graphicx,booktabs,amssymb,amsfonts,url}", r"\begin{document}",
         r"\title{" + tex(C["title"]) + "}", r"\author{" + r" \and ".join(r"\IEEEauthorblockN{" + tex(a) + "}" for a in C["authors"]) + "}",
         r"\maketitle", r"\begin{abstract}" + tex(C["abstract"]) + r"\end{abstract}",
         r"\begin{IEEEkeywords}" + tex(", ".join(C["keywords"])) + r"\end{IEEEkeywords}"]
    nt = 0
    for sec in C["sections"]:
        L.append((r"\section*{" if sec.get("unnumbered") else r"\section{") + tex(sec["title"]) + "}")
        for b in sec["blocks"]:
            k = b[0]
            if k == "sub":
                L.append(r"\subsection{" + tex(b[1]) + "}")
            elif k == "p":
                L.append(tex(b[1]) + "\n")
            elif k == "ul":
                L.append(r"\begin{itemize}" + "".join(r"\item " + tex(i) for i in b[1]) + r"\end{itemize}")
            elif k == "eq":
                L.append(r"\begin{center}" + tex(b[1]) + r"\end{center}")
            elif k == "fig":
                env = "figure*" if b[3] else "figure"
                w = r"\textwidth" if b[3] else r"\columnwidth"
                L.append(rf"\begin{{{env}}}[t]\centering\includegraphics[width={w}]{{figures/{Path(b[1]).name}}}\caption{{{tex(b[2])}}}\end{{{env}}}")
            elif k == "table":
                nt += 1
                env = "table*" if b[3] else "table"
                rows = b[2]
                cols = "l" * len(rows[0])
                body = r" \\ ".join(" & ".join(tex(str(c)) for c in r) for r in rows[1:])
                L.append(rf"\begin{{{env}}}[t]\centering\caption{{{tex(b[1])}}}\footnotesize\begin{{tabular}}{{{cols}}}\toprule "
                         + " & ".join(r"\textbf{" + tex(str(c)) + "}" for c in rows[0]) + r" \\ \midrule " + body + r" \\ \bottomrule\end{tabular}"
                         + rf"\end{{{env}}}")
    L.append(r"\begin{thebibliography}{9}")
    for i, r in enumerate(C["references"], 1):
        L.append(rf"\bibitem{{r{i}}} " + tex(r))
    L.append(r"\end{thebibliography}\end{document}")
    return "\n".join(L)


CSS = """@page { size: Letter; margin: 0.75in 0.62in 1in 0.62in; }
body { font-family: 'Times New Roman', Times, serif; font-size: 10pt; line-height: 1.18; color: #000; margin: 0; }
h1 { font-size: 22pt; font-weight: normal; text-align: center; margin: 0 0 8pt; line-height: 1.15; }
.auth { text-align: center; font-size: 11pt; margin-bottom: 14pt; } .auth .note { font-size: 9pt; font-style: italic; }
.cols { column-count: 2; column-gap: 0.25in; text-align: justify; hyphens: auto; }
.abs { font-weight: bold; font-size: 9pt; } .abs i { font-weight: bold; } .kw { font-size: 9pt; font-weight: bold; margin-bottom: 8pt; }
h2 { font-size: 10pt; font-weight: normal; font-variant: small-caps; text-align: center; margin: 10pt 0 4pt; letter-spacing: .3pt; }
h3 { font-size: 10pt; font-weight: normal; font-style: italic; margin: 6pt 0 3pt; }
p { margin: 0 0 4pt; text-indent: 1em; } ul { margin: 2pt 0 5pt 1.1em; padding: 0; } li { margin-bottom: 2pt; }
figure { margin: 6pt 0 8pt; break-inside: avoid; text-align: center; } figure img { width: 100%; }
figure.wide { column-span: all; } figcaption { font-size: 8pt; text-align: justify; margin-top: 3pt; }
.tbl { break-inside: avoid; margin: 6pt 0 8pt; } .tbl.wide { column-span: all; }
.tcap { font-size: 8pt; text-align: center; font-variant: small-caps; margin-bottom: 3pt; }
table { border-collapse: collapse; width: 100%; font-size: 7.6pt; } th, td { padding: 1.5pt 3pt; text-align: left; vertical-align: top; }
thead th { border-top: 1px solid #000; border-bottom: .6px solid #000; } tbody tr:last-child td { border-bottom: 1px solid #000; }
.eq { text-align: center; margin: 4pt 0; font-style: italic; } code { font-family: 'Courier New', monospace; font-size: 8.5pt; }
.refs { font-size: 8pt; } .refs p { text-indent: 0; padding-left: 1.6em; text-indent: -1.6em; }"""


def build_html(C):
    h = [f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(C['title'])}</title><style>{CSS}</style></head><body>",
         f"<h1>{inline_html(C['title'])}</h1><div class='auth'>{'<br>'.join(inline_html(a) for a in C['authors'])}"
         f"<br><span class='note'>{inline_html(C.get('date', ''))}</span></div><div class='cols'>",
         f"<p class='abs' style='text-indent:0'><i>Abstract</i>—{inline_html(C['abstract'])}</p>",
         f"<p class='kw' style='text-indent:0'><i>Index Terms</i>—{inline_html(', '.join(C['keywords']))}</p>"]
    n, nf, nt = 0, 0, 0
    for sec in C["sections"]:
        if sec.get("unnumbered"):
            h.append(f"<h2>{inline_html(sec['title'])}</h2>")
        else:
            h.append(f"<h2>{ROMAN[n]}. {inline_html(sec['title'])}</h2>")
            n += 1
        sub = 0
        for b in sec["blocks"]:
            k = b[0]
            if k == "sub":
                h.append(f"<h3>{chr(65 + sub)}. {inline_html(b[1])}</h3>")
                sub += 1
            elif k == "p":
                h.append(f"<p>{inline_html(b[1])}</p>")
            elif k == "ul":
                h.append("<ul>" + "".join(f"<li>{inline_html(i)}</li>" for i in b[1]) + "</ul>")
            elif k == "eq":
                h.append(f"<div class='eq'>{inline_html(b[1])}</div>")
            elif k == "fig":
                nf += 1
                b64 = base64.b64encode(Path(b[1]).read_bytes()).decode()
                h.append(f"<figure class='{'wide' if b[3] else ''}'><img alt='Figure {nf}' src='data:image/png;base64,{b64}'>"
                         f"<figcaption>Fig. {nf}. {inline_html(b[2])}</figcaption></figure>")
            elif k == "table":
                nt += 1
                rows = b[2]
                h.append(f"<div class='tbl{' wide' if b[3] else ''}'><div class='tcap'>Table {ROMAN[nt - 1]}<br>{inline_html(b[1])}</div><table><thead><tr>"
                         + "".join(f"<th>{inline_html(str(c))}</th>" for c in rows[0]) + "</tr></thead><tbody>"
                         + "".join("<tr>" + "".join(f"<td>{inline_html(str(c))}</td>" for c in r) + "</tr>" for r in rows[1:]) + "</tbody></table></div>")
    h.append("<h2>References</h2><div class='refs'>" + "".join(f"<p>[{i}] {inline_html(r)}</p>" for i, r in enumerate(C["references"], 1)) + "</div>")
    h.append("</div></body></html>")
    return "".join(h)


def main():
    sys.path.insert(0, str(HERE))
    import report_content as RC
    C = RC.content()
    OUT.mkdir(parents=True, exist_ok=True)
    tdir = OUT / "latex"
    (tdir / "figures").mkdir(parents=True, exist_ok=True)
    for sec in C["sections"]:
        for b in sec["blocks"]:
            if b[0] == "fig":
                shutil.copy(b[1], tdir / "figures" / Path(b[1]).name)
    (tdir / "SignSparK_RL_report.tex").write_text(build_tex(C, tdir / "figures"), encoding="utf-8")
    hp = OUT / "SignSparK_RL_report.html"
    hp.write_text(build_html(C), encoding="utf-8")
    pdf = OUT / "SignSparK_RL_report.pdf"
    subprocess.run([str(EDGE), "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", hp.as_uri()],
                   capture_output=True, timeout=180)
    print("wrote", hp, pdf, pdf.exists() and pdf.stat().st_size)


if __name__ == "__main__":
    main()
