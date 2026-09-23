"""Génère une fiche visuelle (image PNG) pour partager une découverte, façon Mapster."""
from __future__ import annotations

import io
import math
import textwrap

from PIL import Image, ImageDraw, ImageFont

from app.utils.categories import color_for

CARD_SIZE = (1080, 1350)
BANNER_HEIGHT = 260
MARGIN = 70

# Polices système courantes, essayées dans l'ordre ; en dernier recours Pillow
# fournit une police par défaut redimensionnable (>= Pillow 10.1).
_BOLD_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
_REGULAR_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def _load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _shorten_address(adresse: str, titre: str, max_parts: int = 3) -> str:
    """Réduit une adresse Nominatim (souvent très longue) aux quelques segments
    les plus utiles : rue, quartier/ville — en retirant le nom du lieu s'il est
    déjà répété en première position (il apparaît déjà dans le titre de la fiche).
    """
    parts = [p.strip() for p in adresse.split(",") if p.strip()]
    if parts and parts[0].lower() == titre.strip().lower():
        parts = parts[1:]
    return ", ".join(parts[:max_parts])


def _draw_star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r_outer: float, filled: bool, color: str):
    r_inner = r_outer * 0.42
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = r_outer if i % 2 == 0 else r_inner
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    if filled:
        draw.polygon(points, fill=color)
    else:
        draw.polygon(points, outline=color, width=3)


def _draw_stars(draw: ImageDraw.ImageDraw, x: int, y: int, note: int, total: int = 5,
                 radius: int = 22, gap: int = 18, color: str = "#F4A261"):
    cx = x + radius
    for i in range(total):
        _draw_star(draw, cx, y + radius, radius, filled=i < note, color=color)
        cx += 2 * radius + gap


def _wrap_and_draw(draw: ImageDraw.ImageDraw, text: str, font, x: int, y: int, max_width: int,
                    fill: str, line_spacing: int = 10, max_lines: int | None = None) -> int:
    """Dessine `text` en le repliant pour tenir dans `max_width`. Retourne le y final."""
    avg_char_width = draw.textlength("Ma", font=font) / 2 or 1
    wrap_chars = max(1, int(max_width / avg_char_width))
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        wrapped = textwrap.wrap(paragraph, width=wrap_chars) or [""]
        lines.extend(wrapped)

    truncated = False
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True

    for i, line in enumerate(lines):
        if truncated and i == len(lines) - 1:
            while line and draw.textlength(line + "…", font=font) > max_width:
                line = line[:-1]
            line = line + "…"
        draw.text((x, y), line, font=font, fill=fill)
        bbox = font.getbbox(line) if line else (0, 0, 0, font.size)
        y += (bbox[3] - bbox[1]) + line_spacing
    return y


def generate_share_card(entry: dict) -> bytes:
    """Construit une fiche PNG à partir d'une découverte (dict issu du DataFrame).

    Champs attendus : titre, categorie, adresse, note, commentaire, statut.
    Retourne les octets PNG, prêts pour st.image / st.download_button.
    """
    categorie = entry.get("categorie") or "Autre lieu"
    accent = color_for(categorie)

    img = Image.new("RGB", CARD_SIZE, "#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Bannière colorée avec la catégorie
    draw.rectangle([0, 0, CARD_SIZE[0], BANNER_HEIGHT], fill=accent)
    category_font = _load_font(_BOLD_CANDIDATES, 40)
    draw.text((MARGIN, BANNER_HEIGHT / 2 - 24), categorie.upper(), font=category_font, fill="#FFFFFF")

    y = BANNER_HEIGHT + 60

    title_font = _load_font(_BOLD_CANDIDATES, 64)
    titre = str(entry.get("titre") or "Sans titre")
    y = _wrap_and_draw(draw, titre, title_font, MARGIN, y, CARD_SIZE[0] - 2 * MARGIN,
                        fill="#1A1A1A", line_spacing=14, max_lines=3)
    y += 20

    adresse = entry.get("adresse")
    if isinstance(adresse, str) and adresse.strip():
        addr_font = _load_font(_REGULAR_CANDIDATES, 32)
        short_adresse = _shorten_address(adresse.strip(), titre)
        if short_adresse:
            y = _wrap_and_draw(draw, short_adresse, addr_font, MARGIN, y,
                                CARD_SIZE[0] - 2 * MARGIN, fill="#555555", max_lines=2)
            y += 20

    note = entry.get("note")
    is_nan = isinstance(note, float) and note != note  # NaN != NaN
    try:
        note_val = 0 if note in (None, "") or is_nan else int(note)
    except (TypeError, ValueError):
        note_val = 0
    if note_val > 0:
        _draw_stars(draw, MARGIN, y, note_val)
        y += 70

    statut = entry.get("statut")
    if isinstance(statut, str) and statut.strip():
        statut_font = _load_font(_REGULAR_CANDIDATES, 30)
        draw.text((MARGIN, y), f"Statut : {statut}", font=statut_font, fill="#777777")
        y += 60

    commentaire = entry.get("commentaire")
    if isinstance(commentaire, str) and commentaire.strip():
        y += 20
        draw.line([MARGIN, y, CARD_SIZE[0] - MARGIN, y], fill="#EEEEEE", width=2)
        y += 40
        comment_font = _load_font(_REGULAR_CANDIDATES, 34)
        y = _wrap_and_draw(draw, commentaire.strip(), comment_font, MARGIN, y,
                            CARD_SIZE[0] - 2 * MARGIN, fill="#333333", max_lines=8)

    # Recadre la fiche à la hauteur réellement utilisée plutôt que de garder un
    # format fixe qui laisse un grand vide pour les entrées avec peu de texte.
    final_height = min(CARD_SIZE[1], y + 140)
    img = img.crop((0, 0, CARD_SIZE[0], final_height))
    draw = ImageDraw.Draw(img)

    footer_font = _load_font(_REGULAR_CANDIDATES, 26)
    footer_text = "Mon carnet de découvertes"
    fw = draw.textlength(footer_text, font=footer_font)
    draw.text((CARD_SIZE[0] - MARGIN - fw, final_height - 60), footer_text, font=footer_font, fill="#AAAAAA")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
