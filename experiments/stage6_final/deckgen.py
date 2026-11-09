"""Minimal OOXML .pptx writer (no third-party packages: python-pptx / pptxgenjs / Office are not installed and nothing
is downloaded) + an HTML twin of the same deck for PDF export (Edge headless) and visual QA.

Deck spec: list of dicts {kind: "title"|"section"|"content"|"figure"|"stats"|"table", title, subtitle, bullets,
image, image_alt, stats: [(value, label)], table: [[...]], notes}. 16:9, 13.333 x 7.5 in.
"""

import base64
import html
import zipfile
from pathlib import Path

from PIL import Image  # matplotlib dependency, available in the venv

EMU = 914400
W, H = 12192000, 6858000
DARK, INK, MUTED, ACCENT, ACCENT2, CARD, WHITE = "17262B", "1B1B1B", "5B6166", "0F7C82", "D9822B", "EEF4F4", "FFFFFF"
HEAD, BODY = "Cambria", "Calibri"
NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"


def e(v):
    return int(round(v * EMU))


def esc(s):
    return html.escape(str(s), quote=False)


GRP = ('<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/>'
       '<a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')


class Ids:
    def __init__(self):
        self.n = 1

    def __call__(self):
        self.n += 1
        return self.n


def run(text, sz, color, bold=False, font=BODY, italic=False):
    return (f'<a:r><a:rPr lang="en-US" sz="{int(sz * 100)}" b="{1 if bold else 0}" i="{1 if italic else 0}" dirty="0">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{font}"/><a:cs typeface="{font}"/></a:rPr>'
            f'<a:t>{esc(text)}</a:t></a:r>')


def para(text, sz, color, bold=False, font=BODY, bullet=False, align="l", space_after=6, italic=False):
    ppr = f'<a:pPr algn="{align}"'
    if bullet:
        ppr += ' marL="285750" indent="-285750"'
    ppr += f'><a:spcAft><a:spcPts val="{space_after * 100}"/></a:spcAft>'
    ppr += '<a:buFont typeface="Arial"/><a:buChar char="&#8226;"/>' if bullet else "<a:buNone/>"
    ppr += "</a:pPr>"
    return f"<a:p>{ppr}{run(text, sz, color, bold, font, italic)}</a:p>"


def textbox(ids, name, x, y, w, h, paras, anchor="t", fill=None):
    sid = ids()
    fl = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else "<a:noFill/>"
    ins = 'lIns="137160" tIns="91440" rIns="137160" bIns="91440"' if fill else 'lIns="0" tIns="0" rIns="0" bIns="0"'
    geom = "roundRect" if fill else "rect"
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{esc(name)}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>{fl}<a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" {ins} anchor="{anchor}"><a:normAutofit/></a:bodyPr><a:lstStyle/>'
            f'{"".join(paras)}</p:txBody></p:sp>')


def picture(ids, rid, x, y, w, h, alt):
    sid = ids()
    return (f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="Figure {sid}" descr="{html.escape(alt)}"/><p:cNvPicPr>'
            f'<a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="{rid}"/>'
            f'<a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/>'
            f'<a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')


def table_xml(ids, x, y, w, rows, sz=11):
    sid = ids()
    ncol = len(rows[0])
    cw = e(w / ncol)
    rh = e(0.36)
    grid = "".join(f'<a:gridCol w="{cw}"/>' for _ in range(ncol))
    trs = ""
    for i, r in enumerate(rows):
        tcs = ""
        for c in r:
            fill = DARK if i == 0 else (CARD if i % 2 == 0 else WHITE)
            col = WHITE if i == 0 else INK
            tcs += (f'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="l"/>{run(c, sz, col, i == 0)}</a:p></a:txBody>'
                    f'<a:tcPr marL="64008" marR="64008" marT="36576" marB="36576"><a:solidFill><a:srgbClr val="{fill}"/></a:solidFill></a:tcPr></a:tc>')
        trs += f'<a:tr h="{rh}">{tcs}</a:tr>'
    return (f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{sid}" name="Table {sid}"/><p:cNvGraphicFramePr>'
            f'<a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr>'
            f'<p:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{rh * len(rows)}"/></p:xfrm>'
            f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl>'
            f'<a:tblPr firstRow="1" bandRow="1"/><a:tblGrid>{grid}</a:tblGrid>{trs}</a:tbl></a:graphicData></a:graphic></p:graphicFrame>')


def fit_image(path, bx, by, bw, bh):
    with Image.open(path) as im:
        iw, ih = im.size
    s = min(bw / iw, bh / ih)
    w, h = iw * s, ih * s
    return bx + (bw - w) / 2, by + (bh - h) / 2, w, h


def slide_shapes(sl, ids, rid_img, num, total):
    k = sl["kind"]
    dark = k in ("title", "section")
    sh = []
    if k == "title":
        sh.append(textbox(ids, "Title", 0.8, 2.0, 11.7, 1.8, [para(sl["title"], 40, WHITE, True, HEAD)], anchor="b"))
        sh.append(textbox(ids, "Subtitle", 0.8, 4.0, 11.7, 1.6, [para(t, 18, "BFD3D6") for t in sl.get("subtitle", [])]))
    elif k == "section":
        sh.append(textbox(ids, "Title", 0.8, 2.6, 11.7, 1.4, [para(sl["title"], 36, WHITE, True, HEAD)], anchor="b"))
        if sl.get("subtitle"):
            sh.append(textbox(ids, "Subtitle", 0.8, 4.1, 11.7, 1.2, [para(t, 18, "BFD3D6") for t in sl["subtitle"]]))
    else:
        sh.append(textbox(ids, "Title", 0.6, 0.35, 12.1, 0.9, [para(sl["title"], 28, INK, True, HEAD)], anchor="b"))
        if k == "figure":
            bw = 8.4 if sl.get("bullets") else 12.1
            x, y, w, h = fit_image(sl["image"], 0.6, 1.45, bw, 5.35)
            sh.append(picture(ids, rid_img, x, y, w, h, sl.get("image_alt", sl["title"])))
            if sl.get("bullets"):
                sh.append(textbox(ids, "Takeaways", 9.25, 1.5, 3.5, 5.2,
                                  [para(b, 14, INK, bullet=True, space_after=10) for b in sl["bullets"]], fill=CARD))
        elif k == "stats":
            st = sl["stats"]
            cw = (12.1 - 0.3 * (len(st) - 1)) / len(st)
            for i, (v, lab) in enumerate(st):
                sh.append(textbox(ids, f"Stat {i + 1}", 0.6 + i * (cw + 0.3), 1.6, cw, 2.1,
                                  [para(v, 34, ACCENT, True, HEAD), para(lab, 13, MUTED)], fill=CARD))
            if sl.get("bullets"):
                sh.append(textbox(ids, "Body", 0.6, 4.05, 12.1, 2.9, [para(b, 16, INK, bullet=True, space_after=8) for b in sl["bullets"]]))
        elif k == "table":
            sh.append(table_xml(ids, 0.6, 1.5, 12.1, sl["table"], sl.get("table_sz", 11)))
            if sl.get("bullets"):
                y0 = 1.6 + 0.36 * len(sl["table"])
                sh.append(textbox(ids, "Body", 0.6, y0, 12.1, 7.0 - y0, [para(b, 14, INK, bullet=True) for b in sl["bullets"]]))
        else:
            sh.append(textbox(ids, "Body", 0.6, 1.5, 12.1, 5.4, [para(b, 18, INK, bullet=True, space_after=12) for b in sl["bullets"]]))
    sh.append(textbox(ids, "Footer", 0.6, 7.05, 10.5, 0.3,
                      [para("SignSparK RL study · released-checkpoint results, not a paper reproduction", 9, "8FA3A6" if dark else MUTED)]))
    sh.append(textbox(ids, "Slide number", 11.9, 7.05, 0.8, 0.3, [para(f"{num}/{total}", 9, "8FA3A6" if dark else MUTED, align="r")]))
    bg = f'<p:bg><p:bgPr><a:solidFill><a:srgbClr val="{DARK if dark else WHITE}"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>'
    return bg, "".join(sh)


THEME = f"""<a:theme {NS.split(' xmlns:r')[0]} name="SignSparK RL"><a:themeElements><a:clrScheme name="SignSparK RL">
<a:dk1><a:srgbClr val="{INK}"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="{DARK}"/></a:dk2>
<a:lt2><a:srgbClr val="{CARD}"/></a:lt2><a:accent1><a:srgbClr val="{ACCENT}"/></a:accent1><a:accent2><a:srgbClr val="{ACCENT2}"/></a:accent2>
<a:accent3><a:srgbClr val="2A78D6"/></a:accent3><a:accent4><a:srgbClr val="1BAF7A"/></a:accent4><a:accent5><a:srgbClr val="6250D6"/></a:accent5>
<a:accent6><a:srgbClr val="52514E"/></a:accent6><a:hlink><a:srgbClr val="0F7C82"/></a:hlink><a:folHlink><a:srgbClr val="6250D6"/></a:folHlink></a:clrScheme>
<a:fontScheme name="SignSparK RL"><a:majorFont><a:latin typeface="{HEAD}"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
<a:minorFont><a:latin typeface="{BODY}"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>
<a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>"""
CLRMAP = ('bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" '
          'accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"')


def rels(items):
    return XML + f'<Relationships xmlns="{PKG}">' + "".join(
        f'<Relationship Id="{i}" Type="{REL}/{t}" Target="{tg}"/>' for i, t, tg in items) + "</Relationships>"


def notes_xml(text):
    ps = "".join(f'<a:p><a:r><a:rPr lang="en-US" sz="1200" dirty="0"/><a:t>{esc(t)}</a:t></a:r></a:p>' for t in text.split("\n"))
    return (XML + f'<p:notes {NS}><p:cSld><p:spTree>{GRP}'
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Slide Image Placeholder 1"/><p:cNvSpPr><a:spLocks noGrp="1" noRot="1" noChangeAspect="1"/></p:cNvSpPr>'
            '<p:nvPr><p:ph type="sldImg"/></p:nvPr></p:nvSpPr><p:spPr/></p:sp>'
            '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>{ps}</p:txBody></p:sp>'
            '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>')


NOTES_MASTER = (XML + f'<p:notesMaster {NS}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg><p:spTree>{GRP}'
                '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Slide Image Placeholder 1"/><p:cNvSpPr><a:spLocks noGrp="1" noRot="1" noChangeAspect="1"/></p:cNvSpPr>'
                '<p:nvPr><p:ph type="sldImg" idx="2"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="685800" y="1143000"/><a:ext cx="5486400" cy="3086100"/></a:xfrm>'
                '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln w="12700"><a:solidFill><a:prstClr val="black"/></a:solidFill></a:ln></p:spPr></p:sp>'
                '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" sz="quarter" idx="3"/></p:nvPr></p:nvSpPr>'
                '<p:spPr><a:xfrm><a:off x="685800" y="4400550"/><a:ext cx="5486400" cy="3600450"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
                '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>'
                f'</p:spTree></p:cSld><p:clrMap {CLRMAP}/><p:notesStyle><a:lvl1pPr marL="0" algn="l"><a:defRPr sz="1200"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
                '<a:latin typeface="+mn-lt"/></a:defRPr></a:lvl1pPr></p:notesStyle></p:notesMaster>')
MASTER = (XML + f'<p:sldMaster {NS}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg><p:spTree>{GRP}</p:spTree></p:cSld>'
          f'<p:clrMap {CLRMAP}/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
          '<p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz="4000"><a:latin typeface="+mj-lt"/></a:defRPr></a:lvl1pPr></p:titleStyle>'
          '<p:bodyStyle><a:lvl1pPr><a:defRPr sz="1800"><a:latin typeface="+mn-lt"/></a:defRPr></a:lvl1pPr></p:bodyStyle>'
          '<p:otherStyle><a:lvl1pPr><a:defRPr sz="1800"><a:latin typeface="+mn-lt"/></a:defRPr></a:lvl1pPr></p:otherStyle></p:txStyles></p:sldMaster>')
LAYOUT = (XML + f'<p:sldLayout {NS} type="blank" preserve="1"><p:cSld name="Blank"><p:spTree>{GRP}</p:spTree></p:cSld>'
          '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')


def write_pptx(slides, path, title="SignSparK RL study"):
    path = Path(path)
    n = len(slides)
    z = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)
    ct = ['<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
          '<Default Extension="xml" ContentType="application/xml"/>', '<Default Extension="png" ContentType="image/png"/>',
          '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
          '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
          '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
          '<Override PartName="/ppt/notesMasters/notesMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"/>',
          '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
          '<Override PartName="/ppt/theme/theme2.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
          '<Override PartName="/ppt/presProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"/>',
          '<Override PartName="/ppt/viewProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml"/>',
          '<Override PartName="/ppt/tableStyles.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"/>',
          '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
          '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>']
    img_no = 0
    for i, sl in enumerate(slides, 1):
        ids = Ids()
        items = [("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"), ("rId2", "notesSlide", f"../notesSlides/notesSlide{i}.xml")]
        rid_img = None
        if sl.get("image"):
            img_no += 1
            z.write(sl["image"], f"ppt/media/image{img_no}.png")
            rid_img = "rId3"
            items.append(("rId3", "image", f"../media/image{img_no}.png"))
        bg, shapes = slide_shapes(sl, ids, rid_img, i, n)
        z.writestr(f"ppt/slides/slide{i}.xml", XML + f'<p:sld {NS}><p:cSld>{bg}<p:spTree>{GRP}{shapes}</p:spTree></p:cSld>'
                   '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')
        z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", rels(items))
        z.writestr(f"ppt/notesSlides/notesSlide{i}.xml", notes_xml(sl.get("notes", "")))
        z.writestr(f"ppt/notesSlides/_rels/notesSlide{i}.xml.rels",
                   rels([("rId1", "notesMaster", "../notesMasters/notesMaster1.xml"), ("rId2", "slide", f"../slides/slide{i}.xml")]))
        ct.append(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
        ct.append(f'<Override PartName="/ppt/notesSlides/notesSlide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>')
    z.writestr("[Content_Types].xml", XML + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' + "".join(ct) + "</Types>")
    z.writestr("_rels/.rels", XML + f'<Relationships xmlns="{PKG}">'
               f'<Relationship Id="rId1" Type="{REL}/officeDocument" Target="ppt/presentation.xml"/>'
               '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
               f'<Relationship Id="rId3" Type="{REL}/extended-properties" Target="docProps/app.xml"/></Relationships>')
    z.writestr("docProps/core.xml", XML + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
               'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
               'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
               f'<dc:title>{esc(title)}</dc:title><dc:creator>SignSparK RL project</dc:creator></cp:coreProperties>')
    z.writestr("docProps/app.xml", XML + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
               f'<Application>deckgen.py</Application><Slides>{n}</Slides><Notes>{n}</Notes></Properties>')
    pr = [("rId1", "slideMaster", "slideMasters/slideMaster1.xml"), ("rId2", "notesMaster", "notesMasters/notesMaster1.xml"),
          ("rId3", "theme", "theme/theme1.xml"), ("rId4", "presProps", "presProps.xml"), ("rId5", "viewProps", "viewProps.xml"),
          ("rId6", "tableStyles", "tableStyles.xml")] + [(f"rId{10 + i}", "slide", f"slides/slide{i}.xml") for i in range(1, n + 1)]
    z.writestr("ppt/_rels/presentation.xml.rels", rels(pr))
    sld = "".join(f'<p:sldId id="{255 + i}" r:id="rId{10 + i}"/>' for i in range(1, n + 1))
    z.writestr("ppt/presentation.xml", XML + f'<p:presentation {NS} saveSubsetFonts="1"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/>'
               f'</p:sldMasterIdLst><p:notesMasterIdLst><p:notesMasterId r:id="rId2"/></p:notesMasterIdLst><p:sldIdLst>{sld}</p:sldIdLst>'
               f'<p:sldSz cx="{W}" cy="{H}"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>')
    z.writestr("ppt/presProps.xml", XML + f"<p:presentationPr {NS}/>")
    z.writestr("ppt/viewProps.xml", XML + f'<p:viewPr {NS}><p:normalViewPr><p:restoredLeft sz="15620"/><p:restoredTop sz="80000"/></p:normalViewPr></p:viewPr>')
    z.writestr("ppt/tableStyles.xml", XML + '<a:tblStyleLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>')
    z.writestr("ppt/slideMasters/slideMaster1.xml", MASTER)
    z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", rels([("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"), ("rId2", "theme", "../theme/theme1.xml")]))
    z.writestr("ppt/slideLayouts/slideLayout1.xml", LAYOUT)
    z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels([("rId1", "slideMaster", "../slideMasters/slideMaster1.xml")]))
    z.writestr("ppt/notesMasters/notesMaster1.xml", NOTES_MASTER)
    z.writestr("ppt/notesMasters/_rels/notesMaster1.xml.rels", rels([("rId1", "theme", "../theme/theme2.xml")]))
    z.writestr("ppt/theme/theme1.xml", XML + THEME)
    z.writestr("ppt/theme/theme2.xml", XML + THEME)
    z.close()
    return path


def check_pptx(path):
    """Well-formedness of every XML part + every relationship target exists + every slide has notes."""
    import xml.dom.minidom as md
    z = zipfile.ZipFile(path)
    names = set(z.namelist())
    errs = []
    for nm in names:
        if nm.endswith((".xml", ".rels")):
            try:
                md.parseString(z.read(nm))
            except Exception as ex:  # noqa: BLE001
                errs.append(f"{nm}: {ex}")
        if nm.endswith(".rels"):
            base = nm.replace("_rels/", "").rsplit(".rels", 1)[0]
            folder = base.rsplit("/", 1)[0] if "/" in base else ""
            dom = md.parseString(z.read(nm))
            for r in dom.getElementsByTagName("Relationship"):
                t = r.getAttribute("Target")
                parts = (folder + "/" + t).split("/") if folder else t.split("/")
                out = []
                for p in parts:
                    if p == "..":
                        out.pop()
                    elif p and p != ".":
                        out.append(p)
                if "/".join(out) not in names:
                    errs.append(f"{nm}: missing target {t}")
    n_sl = len([x for x in names if x.startswith("ppt/slides/slide")])
    n_no = len([x for x in names if x.startswith("ppt/notesSlides/notesSlide")])
    if n_sl != n_no:
        errs.append(f"slides {n_sl} != notes {n_no}")
    return {"parts": len(names), "slides": n_sl, "errors": errs}


def write_html(slides, path, title):
    css = f"""@page {{ size: 13.333in 7.5in; margin: 0 }} body {{ margin: 0; font-family: {BODY}, Arial, sans-serif; }}
.s {{ width: 13.333in; height: 7.5in; position: relative; overflow: hidden; page-break-after: always; background: #fff; box-sizing: border-box; }}
.d {{ background: #{DARK}; }} .t {{ position: absolute; left: .6in; top: .35in; width: 12.1in; height: .9in; display: flex; align-items: flex-end;
font: bold 28pt {HEAD}, Georgia, serif; color: #{INK}; }} .big {{ position: absolute; left: .8in; top: 2in; width: 11.7in; font: bold 40pt {HEAD}, serif; color: #fff; }}
.sub {{ position: absolute; left: .8in; top: 4.05in; width: 11.7in; color: #BFD3D6; font-size: 18pt; }} .sub p {{ margin: 0 0 6pt }}
.img {{ position: absolute; left: .6in; top: 1.45in; height: 5.35in; display: flex; align-items: center; justify-content: center; }}
.img img {{ max-width: 100%; max-height: 100%; }} .card {{ background: #{CARD}; border-radius: 10px; padding: .1in .15in; box-sizing: border-box; position: absolute; }}
ul {{ margin: 0; padding-left: .3in; }} li {{ margin-bottom: 9pt; color: #{INK}; }} .ft {{ position: absolute; left: .6in; top: 7.05in; font-size: 9pt; color: #{MUTED}; }}
.d .ft {{ color: #8FA3A6; }} .num {{ position: absolute; right: .6in; top: 7.05in; font-size: 9pt; color: #{MUTED}; }}
.v {{ font: bold 34pt {HEAD}, serif; color: #{ACCENT}; }} .l {{ font-size: 13pt; color: #{MUTED}; }}
table {{ border-collapse: collapse; width: 12.1in; position: absolute; left: .6in; top: 1.5in; }} td, th {{ padding: 3px 5px; text-align: left; height: .3in; }}
th {{ background: #{DARK}; color: #fff; }} tr:nth-child(odd) td {{ background: #{CARD}; }}"""
    out = [f"<!doctype html><html><head><meta charset='utf-8'><title>{esc(title)}</title><style>{css}</style></head><body>"]
    n = len(slides)
    for i, sl in enumerate(slides, 1):
        k = sl["kind"]
        dark = k in ("title", "section")
        h = [f"<div class='s{' d' if dark else ''}'>"]
        if dark:
            top = "2in" if k == "title" else "2.6in"
            h.append(f"<div class='big' style='top:{top}'>{esc(sl['title'])}</div>")
            if sl.get("subtitle"):
                h.append("<div class='sub'>" + "".join(f"<p>{esc(t)}</p>" for t in sl["subtitle"]) + "</div>")
        else:
            h.append(f"<div class='t'>{esc(sl['title'])}</div>")
            if k == "figure":
                bw = 8.4 if sl.get("bullets") else 12.1
                b64 = base64.b64encode(Path(sl["image"]).read_bytes()).decode()
                h.append(f"<div class='img' style='width:{bw}in'><img alt='{html.escape(sl.get('image_alt', ''))}' src='data:image/png;base64,{b64}'></div>")
                if sl.get("bullets"):
                    h.append("<div class='card' style='left:9.25in;top:1.5in;width:3.5in;height:5.2in;font-size:14pt'><ul>" +
                             "".join(f"<li>{esc(b)}</li>" for b in sl["bullets"]) + "</ul></div>")
            elif k == "stats":
                st = sl["stats"]
                cw = (12.1 - 0.3 * (len(st) - 1)) / len(st)
                for j, (v, lab) in enumerate(st):
                    h.append(f"<div class='card' style='left:{0.6 + j * (cw + 0.3)}in;top:1.6in;width:{cw}in;height:2.1in'>"
                             f"<div class='v'>{esc(v)}</div><div class='l'>{esc(lab)}</div></div>")
                if sl.get("bullets"):
                    h.append("<div style='position:absolute;left:.6in;top:4.05in;width:12.1in;font-size:16pt'><ul>" +
                             "".join(f"<li>{esc(b)}</li>" for b in sl["bullets"]) + "</ul></div>")
            elif k == "table":
                rows = sl["table"]
                sz = sl.get("table_sz", 11)
                h.append(f"<table style='font-size:{sz}pt'>" + "<tr>" + "".join(f"<th>{esc(c)}</th>" for c in rows[0]) + "</tr>" +
                         "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in rows[1:]) + "</table>")
                if sl.get("bullets"):
                    y0 = 1.6 + 0.36 * len(rows)
                    h.append(f"<div style='position:absolute;left:.6in;top:{y0}in;width:12.1in;font-size:14pt'><ul>" +
                             "".join(f"<li>{esc(b)}</li>" for b in sl["bullets"]) + "</ul></div>")
            else:
                h.append("<div style='position:absolute;left:.6in;top:1.5in;width:12.1in;font-size:18pt'><ul>" +
                         "".join(f"<li>{esc(b)}</li>" for b in sl["bullets"]) + "</ul></div>")
        h.append("<div class='ft'>SignSparK RL study · released-checkpoint results, not a paper reproduction</div>")
        h.append(f"<div class='num'>{i}/{n}</div></div>")
        out.append("".join(h))
    out.append("</body></html>")
    Path(path).write_text("".join(out), encoding="utf-8")
