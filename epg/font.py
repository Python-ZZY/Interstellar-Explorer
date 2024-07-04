import pygame as pg
import epg
from functools import lru_cache
from pygame.font import *

default_font = NotImplemented
def set_default(font, gpath=epg.get_asset):
    global default_font
    default_font = gpath(font) if gpath else font

@lru_cache(10)
def load(font=None, size=None, gpath=epg.get_asset):
    if not font:
        font = default_font
    elif isinstance(font, str) and gpath:
        font = gpath(font)

    if size is None:
        if isinstance(font, pg.Font):
            return font
        size = 20
    
    return Font(font, size)

def normal_render(text, size=20, color=(255, 255, 255), antialias=True, font=None, 
                style=(), gpath=epg.get_asset, **kw):
    if not font: 
        font = default_font
    if isinstance(font, str):
        if gpath: font = gpath(font)
        font = load(font, size)

    if style == False:
        font.underline = font.bold = font.italic = font.strikethrough = False
    else:
        for s in style:
            setattr(font, s, True)

    return font.render(text, antialias, color, **kw)

def text_render(text, *args, padx=0, pady=0, bgcolor=None, **kw):
    if padx or pady:
        r = normal_render(text, *args, **kw)
        surf = epg.Surface((r.get_width() + padx * 2, r.get_height() + pady * 2)).convert_alpha()
        surf.fill(bgcolor or (0, 0, 0, 0))
        surf.blit(r, (padx, pady))
        return surf

    return normal_render(text, *args, bgcolor=bgcolor, **kw)
