#!/usr/bin/env python3
"""index.src.html → index.html

허브 스펙 표 자리({{SPEC_*}})를 아래 SPEC 데이터로 채웁니다.
  python3 build.py            index.html, en/index.html, ja/index.html 생성
  python3 build.py --preview  preview*.html 생성 (이미지를 원본 CDN 주소로 연결)
번역: i18n/en.json, i18n/ja.json 의 strings는 "한국어 원문": "번역" 쌍입니다.
한국어 원문을 고치면 같은 키를 두 파일에서도 함께 고쳐야 합니다. 빌드 때 번역이 빠진 한국어가 있으면 목록을 출력합니다.
수치 출처: gokiso.jp 각 제품 페이지 스펙 표 (단위 mm, g)
"""
import re, sys, html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# (행 이름, [프론트, 리어])
SPEC = {
    "SC_RIM": {
        "cols": [("FRONT", "QR 100"), ("REAR", "QR 130")],
        "rows": [
            ("무게", ["230g", "445g"]),
            ("OLD", ["100mm", "130mm"]),
            ("스포크 홀", ["20H ~ 36H", "24H ~ 36H"]),
            ("센터-플랜지", ["26.8 / 26.8", "27.4 / 16.8"]),
            ("PCD", ["45 / 45", "49 / 54"]),
            ("베어링", ["4개", "7개"]),
            ("래칫", ["-", "4폴 / 92노치"]),
            ("프리허브", ["-", "시마노 11단 / 캄파놀로 10·11단"]),
            ("바디 · 액슬", ["Ti-6Al-4V", "Ti-6Al-4V"]),
        ],
    },
    "SC_TA": {
        "cols": [("FRONT", "12 x 100"), ("REAR", "12 x 142")],
        "rows": [
            ("무게", ["312g", "500g"]),
            ("OLD", ["100mm", "142mm"]),
            ("스포크 홀", ["24H ~ 36H", "24H ~ 36H"]),
            ("센터-플랜지", ["21.9 / 28.4", "33.3 / 17.8"]),
            ("PCD", ["58 / 52", "58 / 58"]),
            ("베어링", ["4개", "10개"]),
            ("래칫", ["-", "4폴 / 92노치"]),
            ("프리허브", ["-", "시마노 11·12단 / 캄파놀로 11·12단 / SRAM XDR"]),
            ("바디 · 액슬", ["Ti-6Al-4V", "Ti-6Al-4V"]),
        ],
    },
    "CL_RIM": {
        "cols": [("FRONT", "QR 100"), ("REAR", "QR 130")],
        "rows": [
            ("무게", ["202g", "401g"]),
            ("OLD", ["100mm", "130mm"]),
            ("스포크 홀", ["20H ~ 36H", "24H ~ 36H"]),
            ("베어링", ["4개", "7개"]),
            ("래칫", ["-", "4폴 / 92노치"]),
            ("프리허브", ["-", "시마노 11단 / 캄파놀로 10·11단"]),
            ("바디 · 액슬", ["A7075-T73 · Ti-6Al-4V", "A7075-T73 · Ti-6Al-4V"]),
            ("컬러", ["매트 레드 / 매트 블랙", "매트 레드 / 매트 블랙"]),
        ],
    },
    "CL_TA": {
        "cols": [("FRONT", "12 x 100"), ("REAR", "12 x 142")],
        "rows": [
            ("무게", ["260g", "460g"]),
            ("OLD", ["100mm", "142mm"]),
            ("스포크 홀", ["24H ~ 36H", "24H ~ 36H"]),
            ("센터-플랜지", ["22.1 / 28.6", "33.6 / 18.1"]),
            ("PCD", ["60 / 55", "60 / 60"]),
            ("베어링", ["4개", "8개"]),
            ("래칫", ["-", "4폴 / 92노치"]),
            ("프리허브", ["-", "시마노 11·12단 / 캄파놀로 11·12단 / SRAM XDR"]),
            ("바디 · 액슬", ["A7075-T73 · Ti-6Al-4V", "A7075-T73 · Ti-6Al-4V"]),
            ("컬러", ["매트 레드 / 매트 블랙", "매트 레드 / 매트 블랙"]),
        ],
    },
}


def table(g):
    head = "".join(f"<th>{s}<small>{c}</small></th>" for s, c in g["cols"])
    body = "".join(
        f"<tr><th>{html.escape(name)}</th>" + "".join(f"<td>{html.escape(v)}</td>" for v in vals) + "</tr>"
        for name, vals in g["rows"]
    )
    for name, vals in g["rows"]:
        assert len(vals) == len(g["cols"]), name
    return f'<table class="geo"><thead><tr><th></th>{head}</tr></thead><tbody>{body}</tbody></table>'


# 표 안의 한국어 (행 이름과 셀 값) 번역
SPEC_LABELS = {
    "en": {"무게": "Weight", "스포크 홀": "Spoke holes", "센터-플랜지": "Center to flange", "베어링": "Bearings", "래칫": "Ratchet",
           "프리허브": "Freehub", "바디 · 액슬": "Body · Axle", "컬러": "Color",
           "4개": "4 pcs", "7개": "7 pcs", "8개": "8 pcs", "10개": "10 pcs", "4폴 / 92노치": "4 pawls / 92 notches",
           "시마노 11단 / 캄파놀로 10·11단": "Shimano 11s / Campagnolo 10·11s",
           "시마노 11·12단 / 캄파놀로 11·12단 / SRAM XDR": "Shimano 11·12s / Campagnolo 11·12s / SRAM XDR",
           "매트 레드 / 매트 블랙": "Matte Red / Matte Black"},
    "ja": {"무게": "重量", "스포크 홀": "スポーク穴", "센터-플랜지": "センター-フランジ", "베어링": "ベアリング", "래칫": "ラチェット",
           "프리허브": "フリーボディ", "바디 · 액슬": "ボディ · シャフト", "컬러": "カラー",
           "4개": "4個", "7개": "7個", "8개": "8個", "10개": "10個", "4폴 / 92노치": "4爪 / 92ノッチ",
           "시마노 11단 / 캄파놀로 10·11단": "シマノ 11s / カンパニョーロ 10·11s",
           "시마노 11·12단 / 캄파놀로 11·12단 / SRAM XDR": "シマノ 11·12s / カンパニョーロ 11·12s / SRAM XDR",
           "매트 레드 / 매트 블랙": "マットレッド / マットブラック"},
}

SITE = "https://gokiso.rubiworkshop.com/"
LANGS = [("ko", "KO", ""), ("en", "EN", "en/"), ("ja", "JA", "ja/")]
HANGUL = re.compile("[가-힣]")
JA_FONT = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
           '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400&display=swap" rel="stylesheet">'
           '<style>:root{--font:"RubiLatin","Noto Sans JP","Hiragino Sans","Yu Gothic",system-ui,sans-serif}</style>')


def lang_switch(cur):
    depth = "" if cur == "ko" else "../"
    return "".join(
        f'<a href="{depth}{path or "./"}" hreflang="{code}" lang="{code}"{" class=\"on\" aria-current=\"true\"" if code == cur else ""}>{label}</a>'
        for code, label, path in LANGS
    ).replace('href=".././"', 'href="../"')


HREFLANG = "\n".join(
    [f'<link rel="alternate" hreflang="{c}" href="{SITE}{p}">' for c, _, p in LANGS]
    + [f'<link rel="alternate" hreflang="x-default" href="{SITE}">']
)


def translate(html_text, tr):
    out = html_text
    for key in sorted(tr["strings"], key=len, reverse=True):
        val = tr["strings"][key]
        k = re.escape(key)
        out = re.sub(r"(>\s*)" + k + r"(\s*<)", lambda m: m.group(1) + val + m.group(2), out)
        out = out.replace(f'"{key}"', f'"{val}"')
    for pat, rep in tr["patterns"]:
        out = re.sub(pat, rep, out)
    return out


def render(code):
    src = (ROOT / "index.src.html").read_text(encoding="utf-8")
    out = re.sub(r"\{\{SPEC_(\w+)\}\}", lambda m: table(SPEC[m.group(1)]), src)
    out = out.replace("{{LANG}}", lang_switch(code)).replace("{{HREFLANG}}", HREFLANG)
    assert "{{" not in out, "채워지지 않은 자리표시자가 있습니다"
    if code == "ko":
        return out
    tr = json.loads((ROOT / f"i18n/{code}.json").read_text(encoding="utf-8"))
    for ko, t in sorted(SPEC_LABELS[code].items(), key=lambda x: -len(x[0])):
        out = out.replace(f"<th>{ko}</th>", f"<th>{t}</th>").replace(f"<td>{ko}</td>", f"<td>{t}</td>")
    out = translate(out, tr)
    m = tr["meta"]
    out = out.replace('<html lang="ko">', f'<html lang="{m["lang"]}">')
    out = out.replace(f'<link rel="canonical" href="{SITE}">', f'<link rel="canonical" href="{SITE}{m["path"]}">')
    out = out.replace(f'<meta property="og:url" content="{SITE}">', f'<meta property="og:url" content="{SITE}{m["path"]}">')
    out = out.replace('content="ko_KR"', f'content="{m["locale"]}"')
    out = out.replace('"inLanguage": "ko-KR"', f'"inLanguage": "{m["lang"]}"')
    if code == "ja":
        # 일본어는 한글 서체(에스코어 드림) 대신 Noto Sans JP (영문·숫자는 Pretendard 유지)
        out = out.replace("</style>\n</head>", "</style>\n" + JA_FONT + "\n</head>", 1)
    # 하위 폴더에서 이미지 경로
    out = re.sub(r'((?:src|href)=")images/', r"\1../images/", out)
    out = out.replace("url(images/", "url(../images/")
    left = sorted(set(re.findall(r"[^<>\"]*[가-힣][^<>\"]*", out)))
    left = [x.strip() for x in left if x.strip() and "/*" not in x]
    if left:
        print(f"[{code}] 번역되지 않은 한국어 {len(left)}건:", left[:30])
    return out


def main():
    manifest = (ROOT / ".github/image-manifest.txt").read_text().splitlines()
    cdn = dict(reversed(l.split()) for l in manifest if l.strip())
    for code, _, path in LANGS:
        out = render(code)
        used = set(re.findall(r"images/[\w/.-]+\.(?:jpg|png|svg|gif)", out))
        for u in sorted(used - set(cdn)):
            print("매니페스트에 없는 이미지:", u)
        if "--preview" in sys.argv:
            out = re.sub(r"(?:\.\./)?images/[\w/.-]+\.(?:jpg|png|svg|gif)", lambda m: cdn.get(m.group(0).replace("../", ""), m.group(0)), out)
            name = f"preview{'-' + code if code != 'ko' else ''}.html"
            (ROOT / name).write_text(out, encoding="utf-8")
            print(name)
        else:
            dest = ROOT / path / "index.html"
            dest.parent.mkdir(exist_ok=True)
            dest.write_text(out, encoding="utf-8")
            print(dest.relative_to(ROOT))


if __name__ == "__main__":
    main()
