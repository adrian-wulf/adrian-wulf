#!/usr/bin/env python3
"""Grafiki profilu GitHub w systemie „Tusz i sygnał”.

GitHub nie wczytuje fontów w SVG, więc tekst zamieniamy na ścieżki (HarfBuzz kształtuje, fontTools daje kontury).
Wynik: hero-{light,dark}.svg, work-{light,dark}.svg, sign-{light,dark}.svg w ../
"""
import re
from pathlib import Path
from io import BytesIO
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = Path(__file__).parent
OUT = HERE.parent

# kolory z redesign/paleta (role semantyczne)
THEMES = {
    'light': dict(bg='#FDFDFA', subtle='#F7F7F4', text='#181713', sec='#5E5C55', border='#D8D7D2', strong='#181713',
                  hl='#FBD500', on_hl='#181713', ok='#0E6936', bubble='#181713', bubble_text='#FDFDFA', bubble_acc='#FBD500'),
    'dark':  dict(bg='#0E0D0A', subtle='#17160F', text='#F1F0EC', sec='#B5B3AB', border='#3A3830', strong='#F1F0EC',
                  hl='#FAD622', on_hl='#181713', ok='#6FD39A', bubble='#262419', bubble_text='#F1F0EC', bubble_acc='#FAD622'),
}


class Face:
    def __init__(self, path, axes=None):
        tt = TTFont(path)
        if axes:
            tt = instantiateVariableFont(tt, axes)
        buf = BytesIO(); tt.save(buf); data = buf.getvalue()
        self.tt = TTFont(BytesIO(data))
        self.glyphs = self.tt.getGlyphSet()
        self.upm = self.tt['head'].unitsPerEm
        self.hbfont = hb.Font(hb.Face(data))

    def shape(self, text):
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
        hb.shape(self.hbfont, buf, {'kern': True, 'liga': True})
        return buf.glyph_infos, buf.glyph_positions

    def width(self, text, size, track=0.0):
        _, pos = self.shape(text)
        return sum(p.x_advance for p in pos) * size / self.upm + track * size * max(len(pos) - 1, 0)

    def path(self, text, x, y, size, track=0.0):
        infos, pos = self.shape(text)
        s = size / self.upm; order = self.tt.getGlyphOrder(); out = []; cx = 0
        for info, p in zip(infos, pos):
            pen = SVGPathPen(self.glyphs)
            tp = TransformPen(pen, (s, 0, 0, -s, x + (cx + p.x_offset) * s, y - p.y_offset * s))
            self.glyphs[order[info.codepoint]].draw(tp)
            d = re.sub(r'-?\d+\.\d+', lambda m: f'{float(m.group()):.1f}'.rstrip('0').rstrip('.'), pen.getCommands())
            if d: out.append(d)
            cx += p.x_advance + track * self.upm
        return ' '.join(out)


SRC = HERE
DISPLAY = Face(SRC / 'Archivo-VF.ttf', {'wdth': 75, 'wght': 900})
BOLD = Face(SRC / 'Archivo-VF.ttf', {'wdth': 100, 'wght': 700})
BODY = Face(SRC / 'Archivo-VF.ttf', {'wdth': 100, 'wght': 450})
MONO = Face(SRC / 'IBMPlexMono-Medium.ttf')


def t(face, text, x, y, size, fill, track=0.0):
    return f'<path fill="{fill}" d="{face.path(text, x, y, size, track)}"/>'


def svg(w, h, title, desc, body, c):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">'
            f'<title id="t">{title}</title><desc id="d">{desc}</desc>'
            f'{body}</svg>\n')


def hero(c, theme):
    W, H = 1200, 490; b = []
    # logo
    b.append(f'<rect x="68" y="48" width="16" height="16" fill="{c["hl"]}"/><rect x="64" y="44" width="16" height="16" fill="{c["text"]}"/>')
    b.append(t(BOLD, 'wulf code it', 94, 62, 24, c['text']))
    b.append(t(MONO, 'ADRIAN WĘCŁAWSKI “WULF”', 64, 128, 18, c['sec'], 0.06))
    # tytuł: trzy linie, druga i trzecia zakreślona
    size, lh, y0 = 74, 78, 214
    lines = [('ENTER IT ONCE.', False), ('THE SYSTEM', True), ('DOES THE REST.', True)]
    for i, (line, mark) in enumerate(lines):
        y = y0 + i * lh
        if mark:
            w = DISPLAY.width(line, size)
            b.append(f'<rect x="60" y="{y - size * 0.80:.1f}" width="{w + 10:.1f}" height="{size * 0.95:.1f}" fill="{c["hl"]}"/>')
        b.append(t(DISPLAY, line, 64 if not mark else 65, y, size, c['on_hl'] if mark else c['text']))
    b.append(t(BODY, 'Apps, automations and websites for businesses', 64, 422, 22, c['sec']))
    b.append(t(BODY, 'in Germany and Poland. Polish, German, English.', 64, 452, 22, c['sec']))

    # panel: prawdziwy przebieg z realizacji (gastronomia)
    X, Y, PW, PH = 676, 40, 460, 424
    b.append(f'<rect x="{X}" y="{Y}" width="{PW}" height="{PH}" fill="{c["subtle"]}" stroke="{c["strong"]}" stroke-width="2"/>')
    b.append(t(MONO, 'FROM A REAL PROJECT', X + 22, Y + 38, 16, c['sec'], 0.05))
    w = MONO.width('BURGER BAR', 16, 0.05); b.append(t(MONO, 'BURGER BAR', X + PW - 22 - w, Y + 38, 16, c['sec'], 0.05))
    # dymek
    bx, by = X + 22, Y + 60
    b.append(f'<rect x="{bx}" y="{by}" width="416" height="112" fill="{c["bubble"]}"/>')
    b.append(t(MONO, 'STAFF · TELEGRAM · 11:42', bx + 18, by + 30, 16, c['bubble_text'], 0.04))
    b.append(t(BODY, '2 photos + voice note:', bx + 18, by + 62, 20, c['bubble_text']))
    b.append(t(BOLD, '“smash burger, 20% off today”', bx + 18, by + 90, 20, c['bubble_acc']))
    b.append(f'<path d="M{bx + 30} {by + 112} v22" stroke="{c["sec"]}" stroke-width="2" stroke-dasharray="4 4"/>')
    sy = by + 134
    b.append(f'<rect x="{bx}" y="{sy}" width="416" height="44" fill="{c["bg"]}" stroke="{c["border"]}" stroke-width="2"/>')
    b.append(t(BODY, 'Bot wrote the caption and built the reel', bx + 16, sy + 29, 19, c['text']))
    b.append(f'<path d="M{bx + 30} {sy + 44} v22" stroke="{c["sec"]}" stroke-width="2" stroke-dasharray="4 4"/>')
    # cele 2×2
    ty = sy + 66; cw, ch = 205, 68
    targets = [('Facebook · Instagram', 'reel posted'), ('TikTok', 'reel posted'), ('Website menu', 'price updated'), ('Glovo', 'price updated')]
    for i, (name, state) in enumerate(targets):
        cx = bx + (i % 2) * (cw + 6); cy = ty + (i // 2) * (ch + 6)
        b.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" fill="{c["bg"]}" stroke="{c["ok"]}" stroke-width="2"/>')
        b.append(t(BOLD, name, cx + 14, cy + 28, 18, c['text']))
        b.append(t(MONO, state, cx + 14, cy + 52, 16, c['ok']))
    return svg(W, H, 'Adrian Węcławski “Wulf” · Wulf Code it: Enter it once. The system does the rest.',
               'Apps, automations and websites for businesses in Germany and Poland. Example from a real project: staff send two photos and a voice note on Telegram; the bot writes the caption, builds a reel, posts it to Facebook, Instagram and TikTok and updates the price on the website menu and on Glovo.',
               ''.join(b), c)


WORK = [
    ('RESTAURANT · BOT + WEBSITE', 'A photo and a voice note', 'become a finished reel',
     ['Reels from 56 templates go to Facebook, Instagram', 'and TikTok. A price changed in the bot updates', 'the website menu and Glovo.'], 'no editing software, one price everywhere'),
    ('CLEANING COMPANY · APP + WEBSITE', 'A crew app: QR login,', 'rota and hours',
     ['Staff sign in with one scan and check in at the', 'client. Breaks and monthly hours reports per', 'employee and client add up by themselves.'], 'reports without a spreadsheet'),
    ('ONLINE TRADING · BOT', 'Shared once,', 'posted in five places',
     ['A reseller forwards a listing to a Telegram bot.', 'It tidies the text, adds tags and links, then posts', 'to Telegram, Discord, Facebook, WhatsApp, LINE.'], 'one share instead of five platforms'),
    ('LEAD DEVELOPER · DEFINIUM', 'A compliance platform', 'for NIS2, DORA and GDPR',
     ['Six modules instead of spreadsheets and email:', 'compliance, risks, vulnerabilities, vendors,', 'incidents and policies. Built from the first commit.'], 'live with a public demo at definium.eu'),
]


def work(c, theme):
    W, H = 1200, 760; b = []
    b.append(t(DISPLAY, "WHAT I'VE BUILT", 64, 96, 52, c['text']))
    b.append(t(BODY, 'Client projects are described without names.', 64, 136, 20, c['sec']))
    cw, ch, gx, gy, x0, y0 = 530, 262, 12, 12, 64, 170
    for i, (meta, h1, h2, body, res) in enumerate(WORK):
        x = x0 + (i % 2) * (cw + gx + 16); y = y0 + (i // 2) * (ch + gy + 12)
        b.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" fill="{c["bg"]}" stroke="{c["border"]}" stroke-width="2"/>')
        b.append(t(MONO, meta, x + 24, y + 38, 16, c['sec'], 0.04))
        b.append(t(BOLD, h1, x + 24, y + 74, 24, c['text']))
        b.append(t(BOLD, h2, x + 24, y + 104, 24, c['text']))
        for k, line in enumerate(body):
            b.append(t(BODY, line, x + 24, y + 140 + k * 26, 18, c['sec']))
        b.append(f'<path d="M{x + 24} {y + ch - 46} H{x + cw - 24}" stroke="{c["border"]}" stroke-width="1.5" stroke-dasharray="3 4"/>')
        b.append(t(MONO, res, x + 24, y + ch - 18, 16, c['ok']))
    return svg(W, H, "What I've built",
               'Four projects. Restaurant: a Telegram bot turns staff photos and a voice note into reels for Facebook, Instagram and TikTok and updates prices on the website and Glovo. Cleaning company: a crew app with QR sign-in, rota, check-ins and monthly hours reports. Online trading: a bot that posts one forwarded listing to five platforms. Definium: lead developer of a compliance platform for NIS2, DORA and GDPR with six modules and a public demo.',
               ''.join(b), c)


def sign(c, theme):
    W, H = 1200, 120; b = []
    b.append(f'<path d="M64 24 H1136" stroke="{c["strong"]}" stroke-width="2"/>')
    b.append(f'<rect x="68" y="60" width="16" height="16" fill="{c["hl"]}"/><rect x="64" y="56" width="16" height="16" fill="{c["text"]}"/>')
    b.append(t(MONO, 'WULF, CODE IT.', 96, 75, 18, c['text'], 0.08))
    label = 'wulf-code.eu  ·  kontakt@wulf-code.it'
    w = MONO.width(label, 18); b.append(t(MONO, label, 1136 - w, 75, 18, c['sec']))
    return svg(W, H, 'Wulf, code it.', 'Signature: wulf-code.eu, kontakt@wulf-code.it', ''.join(b), c)


for theme, c in THEMES.items():
    (OUT / f'hero-{theme}.svg').write_text(hero(c, theme), encoding='utf-8')
    (OUT / f'work-{theme}.svg').write_text(work(c, theme), encoding='utf-8')
    (OUT / f'sign-{theme}.svg').write_text(sign(c, theme), encoding='utf-8')
print('ok', sorted(p.name for p in OUT.glob('*.svg')))
