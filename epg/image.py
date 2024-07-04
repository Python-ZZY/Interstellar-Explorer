import pygame as pg
import epg
from functools import lru_cache, partial
from pygame.image import *

def load_transformed(name, scale_by=None, flip=None, rotate=None, gpath=epg.get_asset):
    if gpath: name = gpath(name)
    surf = pg.image.load(name)
    
    if scale_by:
        surf = pg.transform.scale_by(surf, scale_by)
    if flip:
        surf = pg.transform.flip(surf, *flip)
    if rotate:
        surf = pg.transform.rotate(surf, rotate)

    return surf

def load(name, gpath=epg.get_asset):
    if gpath: name = gpath(name)
    return pg.image.load(name)

def loads(name, start=0, stop=None, step=1, load=load, **loadkw):
    if "{}" not in name:
        yield load(name, **loadkw)
        return
    
    isload = False
    for i in epg.math.counter(start, stop, step):
        try:
            yield load(name.format(i), **loadkw)
        except FileNotFoundError as e:
            if not isload: raise e
            break
        else:
            isload = True

get = lru_cache(256)(load_transformed)
gets = partial(loads, load=get)

def load_sheet(name, x=None, y=None, tile=None, id=0, load=load, **loadkw):
    return SpriteSheet(load(name, **loadkw), x, y, tile, id)

def load_static_animation(name, load=load, **loadkw):
    if isinstance(name, str):
        return StaticAnimation(load(name, **loadkw))
    elif isinstance(name, epg.Surface):
        return StaticAnimation(name)
    return name

class SpriteSheet:
    def __init__(self, surf, x=None, y=None, tile=None, id=0, cached=True):
        if x and y and (not tile):
            tile = (surf.get_width() // x, surf.get_height() // y)
        elif tile:
            if x == None: x = surf.get_width() // tile[0]
            if y == None: y = surf.get_height() // tile[1]
        else:
            epg.throw("miss required argument(s)")
        self.x, self.y = x, y

        self.orginal_image = surf
        self.tile = tile
        self.id = id
        self.cached = None # Important!
        self.cached = [self.update() for i in range(len(self))] if cached else None

    def __iter__(self):
        for y in range(self.y):
            for x in range(self.x):
                yield self.get_surface(x, y)

    def __next__(self):
        return self.update()
    
    def __len__(self):
        return self.x * self.y

    def get_surface(self, *pos):
        if self.cached:
            return self.cached[self.id]
        else:
            if not pos:
                pos = self.get_pos_by_id(self.id)
            return self.orginal_image.subsurface(
                (pos[0]*self.tile[0], pos[1]*self.tile[1],
                 self.tile[0], self.tile[1])
                ).convert_alpha()

    def get_pos_by_id(self, id):
        return id % self.x, id // self.x

    def next_image(self):
        surf = self.get_surface()

        self.id += 1
        if self.id == len(self):
            self.id = 0

        return surf

    update = next_image

class FileSheet(SpriteSheet):
    def __init__(self, surfs, id=0):
        self.cached = tuple(surfs)
        self.id = id
        try:
            self.tile = self.cached[0].get_size()
        except IndexError:
            epg.throw("no images in this sheet")

    def __len__(self):
        return len(self.cached)

    def get_pos_by_id(self, id):
        return id
        
class Animation:
    def __init__(self, sheet=None, delay=None, interval=0, 
                 cls=SpriteSheet, **sheetkw):
        self.sheet = sheet if isinstance(sheet, SpriteSheet) else cls(sheet, **sheetkw)
        self.interval = interval

        self.last_update = -epg.get_time()
        if delay != None:
            self.last_update += delay

    @property
    def id(self):
        return self.sheet.id
    @id.setter
    def id(self, value):
        self.sheet.id = value
    
    def get_surface(self):
        return self.sheet.get_surface()

    def next_image(self):
        return self.sheet.next_image()

    def update(self, reset=False):
        now = epg.get_time()
        if reset or (now - self.last_update > self.interval):
            self.last_update = now
            return self.next_image()

class StaticAnimation(Animation):
    def __init__(self, surf):
        self.image = surf

    @property
    def id(self):
        return 0
    @id.setter
    def id(self, value):
        pass

    def get_surface(self):
        return self.image

    def next_image(self):
        return self.image

    def update(self, reset=False):
        if reset:
            return self.image
