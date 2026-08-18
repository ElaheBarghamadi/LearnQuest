import hashlib

TINT_COUNT = 8


def _tint_of(slug) -> int:
    if not slug:
        return 0
    h = int(hashlib.md5(str(slug).encode('utf-8')).hexdigest(), 16)
    return h % TINT_COUNT


def tile_mode(product) -> str:
    if product.image:
        return 'img'
    payload = product.effect_payload or {}
    css_class = payload.get('css_class') or ''
    et = product.effect_type or ''
    if et in ('frame', 'frame_animated') and css_class:
        return 'frame'
    if et == 'username_color' and css_class:
        return 'ucolor'
    if et in ('profile_effect', 'profile_card_animated') and css_class:
        return 'effect'
    if et.startswith('theme'):
        return 'theme'
    if et in ('profile_background', 'wallpaper_pack') and css_class:
        return 'pbg'
    return 'emoji'


def annotate_tiles(products):
    items = list(products)
    for p in items:
        p.tile_mode = tile_mode(p)
        p.preview_css = (p.effect_payload or {}).get('css_class', '')
        p.tint = _tint_of(p.category.slug if p.category else '')
    return items
