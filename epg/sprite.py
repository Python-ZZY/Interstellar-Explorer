import pygame as pg
import epg
from pygame.sprite import *

class Sprite(Sprite):
    def draw(self, screen, offset=None):
        if offset:
            screen.blit(self.image, self.rect.topleft + epg.Vector2(offset))
        else:
            screen.blit(self.image, self.rect)

class Static(Sprite):
    def __init__(self, surf, groups=(), anchor="center", use_float=False, **rectkw):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(**rectkw) if use_float else self.image.get_rect(**rectkw)
        self.anchor = anchor

class AStatic(Static, epg.action.ActionObject):
    def __init__(self, surf, *actions, end_func=None, **statickw):
        Static.__init__(self, surf, **statickw)
        self.orig_image, self.orig_rect = None, None
        
        epg.action.ActionObject.__init__(self, actions, end_func)
        AStatic.update(self)
    
    def update(self):
        Static.update(self)
        epg.action.ActionObject.update(self)

class BaseDynamic(Sprite):
    def __init__(self, types, groups=(), state=None, total=None,
                 anchor="center", call_after_kill=None, use_float=False, **rectkw):
        super().__init__(*groups)
        
        self.types, self.state, self.total, self.anchor = types, state, total, anchor
        self.call_after_kill = call_after_kill
        self.now_total = 1
            
        if not state:
            self.state = tuple(self.types.keys())[0]
        self.state_changed = False

        self.image = self.animation.get_surface()
        self.rect = self.image.get_frect(**rectkw) if use_float else self.image.get_rect(**rectkw)

    @property
    def animation(self):
        return self.types[self.state]

    def update(self):
        '''Update the animation. Return True if the image has changed'''
        if i := self.animation.update(self.state_changed):
            if self.total != None and self.now_total > self.total:
                self.kill()
                if self.call_after_kill: self.call_after_kill()

            self.state_changed = False
            self.image = i

            if self.animation.id == 0 and self.total != None:
                self.now_total += 1
            
            if getattr(self, "manager", None):
                self.orig_image = self.image
                arg = getattr(self.orig_rect, self.anchor)
                self.rect.size = self.image.get_size()
                setattr(self.rect, self.anchor, arg)

            return True
        
    def update_state(self, state):
        if state != self.state:
            self.types[state].id = 0
            self.state = state

            self.state_changed = True
            BaseDynamic.update(self)

class Dynamic(BaseDynamic):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        Dynamic.update(self)
        
class ADynamic(BaseDynamic, epg.action.ActionObject):
    def __init__(self, types, *actions, end_func=None, **dynamickw):
        BaseDynamic.__init__(self, types, **dynamickw)
        epg.action.ActionObject.__init__(self, actions, end_func)
    
    def update(self):
        BaseDynamic.update(self)
        epg.action.ActionObject.update(self)
        
def OsDynamic(animation, *args, **kw):
    return Dynamic({"":animation}, *args, **kw)

def OsADynamic(animation, *args, **kw):
    return ADynamic({"":animation}, *args, **kw)

def get(obj, cls=OsDynamic, *clsargs, **clskw):
    if isinstance(obj, epg.Surface):
        obj = epg.image.StaticAnimation(obj)
    if isinstance(obj, epg.image.Animation):
        obj = cls(obj, *clsargs, **clskw)
    elif not isinstance(obj, Sprite):
        epg.throw("invalid type", repr(type(obj)))
        
    return obj

def get_static(actions, *args, **kwargs):
    if actions is None: actions = ()
    return AStatic(*args, *actions, **kwargs) if actions or actions == () else Static(*args, **kwargs)

def get_dynamic(actions, *args, **kwargs):
    if actions is None: actions = ()
    return ADynamic(*args, *actions, **kwargs) if actions or actions == () else Dynamic(*args, **kwargs)

def get_surface(sprite, *args, **kw):
    if isinstance(sprite, str):
        return epg.image.load_transformed(sprite, *args, **kw)
    elif isinstance(sprite, epg.Surface):
        return sprite
    else:
        return sprite.image