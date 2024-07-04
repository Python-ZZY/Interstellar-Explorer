import epg
import math
from functools import partial

class ActionManager:
    def __init__(self, sprite, actions, end_func=None, cover=True):
        self.sprite = sprite
        self.sprite.orig_image = sprite.image
        self.sprite.orig_rect = sprite.rect

        if actions and actions[0]:
            self.actions = AsyncActions(list=actions).copy()
            self.generator = self.actions.generate(sprite)
            self.generator.send(None)
        else:
            self.actions, self.generator = None, None
            
        self.end_func = end_func
        self.cover = cover
        self.covers = []
        self.update()

    def __bool__(self):
        return bool(self.generator)

    def add_cover(self, func):
        if func: self.covers.append(func)

    def clear_cover(self):
        self.covers.clear()
        self.sprite.image, self.sprite.rect = self.sprite.orig_image.copy(), self.sprite.orig_rect.copy()

    def update_cover(self):
        upd = self.sprite.orig_image, self.sprite.orig_rect
        for func in self.covers:
            upd = func(*upd)
        return upd

    def recover(self):
        self.covers.clear()
        for action in self.actions.all:
            if action.cover:
                self.covers.append(action.get_cover(self.sprite))

    def update(self):
        if self.generator:
            upd_c = self.update_cover()

            try:
                upd = self.generator.send(upd_c)
            except StopIteration:
                self.generator = None
                if not self.cover: self.clear_cover()
                self.sprite.orig_image, self.sprite.orig_rect = None, None
                if self.end_func:
                    self.end_func(self.sprite, self.actions)
                return
            else:
                if upd: self.sprite.image, self.sprite.rect = upd

class ActionObject: # TODO: action sprite bind
    def __init__(self, actions, end_func):
        self.end_func = end_func
        self.manager = None
        if actions:
            self.act(*actions, end_func=end_func)

    def add_cover(self, func):
        self.manager.add_cover(func)

    def clear_cover(self):
        self.manager.clear_cover()

    def act(self, *actions, end_func=None, cover=True):
        if self.manager and not self.manager.cover: self.manager.clear_cover()
        if end_func: self.end_func = end_func
        self.manager = ActionManager(self, actions, self.end_func, cover)

    def stop(self, call_end_func=False):
        if call_end_func:
            self.end_func(self, self.manager.actions)
        self.manager = None

    def update(self):
        if self.manager:
            self.manager.update()

class BaseAction:
    ATTR = {}
    COVER = False
    def __init__(self, duration=0, interval=0, total=1, interp=epg.math.mix, cover=None, **kw):
        epg.check_attr(kw, self.ATTR)

        if cover is None:
            cover = self.COVER

        self.duration, self.interval, self.total = duration, interval, total
        self.interp, self.cover = interp, cover
        self.initkw(kw)

    def __repr__(self):
        return "<" + ("+" if self.cover else "") + self.__class__.__name__ + \
        f" duration={self.duration}, interval={self.interval}, total={self.total}, {self.kw}>"
    
    def __bool__(self):
        return bool(self.total)

    def __delitem__(self, key):
        del self.kw[key]

    def __getitem__(self, key):
        return self.kw[key]

    def __setitem__(self, key, value):
        self.kw[key] = value

    def __eq__(self, value):
        return self.__class__ == value.__class__ and \
        self.kw == value.kw and \
        self.interval == value.interval and \
        self.duration == value.duration and \
        self.interp == value.interp
    
    def __neg__(self):
        value = self.copy()
        if rg := value.kw.get("range"):
            value["range"] = rg[::-1]
        return value

    __invert__ = __neg__

    def __add__(self, value):
        return self.combine(SyncActions, value)

    def __rshift__(self, value):
        return self.combine(AsyncActions, value)
    
    def __mul__(self, value):
        v = self.copy()
        v.total *= value
        return v

    __radd__ = __add__
    __rrshift__ = __rshift__
    __rmul__ = __mul__

    def combine(self, cls, value):
        if callable(value): value = Call(func=value)
        return (cls(list=[self], total=self.total)).combine(cls, value)

    def copy(self):
        return self.__class__(self.duration, self.interval, self.total, self.interp, 
            self.cover, **self.kw)

    def init(self, sprite):
        pass

    def initkw(self, kw):
        self.kw = self.ATTR.copy()
        self.kw.update(kw)
        self.orig_kw = self.kw.copy()

    def generate(self, sprite):
        i = 0
        self.init(sprite)
        upd = yield
        while i < self.total:
            g = self.single_generate(sprite)
            g.send(None)
            while True:
                try:
                    upd = yield g.send(upd)
                except StopIteration:
                    break
            i += 1
            
    def single_generate(self, s):
        pos = 0
        upd = yield
        upd = yield self.get(0, *upd)
        
        self.start_time = self.last_update = epg.get_time()
        while self.duration and pos < 1:
            now = epg.get_time()
            if now - self.last_update > self.interval:
                self.last_update = now
                pos = (now - self.start_time) / self.duration
                if pos > 1: pos = 1
            upd = yield self.get(pos, *upd)

        s.add_cover(self.get_cover(s))
        yield self.get(1, *upd)

    def get_cover(self, s):
        self.init(s)
        return partial(self.get, 1)

    def get_mixture(self, pos):
        return self.interp(*self["range"], pos)

    def get(self, pos, im, rect):
        return im, rect

class SpecialAction(BaseAction):
    def generate(self, sprite):
        yield
        yield from self.single_generate(sprite)

    def single_generate(self, sprite):
        pass

    def get_mixture(self, *a):
        pass

class BaseActions(BaseAction):
    ATTR = {"list":None}
    def init(self, s):
        self.cover = False

    def initkw(self, kw):
        super().initkw(kw)
        if not self["list"]:
            self["list"] = self.orig_kw["list"] = list()

    def __bool__(self):
        return all((self.total, self["list"]))

    def __invert__(self):
        value = self.copy()
        value["list"] = value["list"][::-1]
        return value

    def __neg__(self):
        value = self.copy()
        value["list"] = [-a for a in value["list"][::-1]]
        return value

    def __add__(self, value):
        return self.combine(SyncActions, value)

    def __rshift__(self, value):
        return self.combine(AsyncActions, value)

    def __iter__(self):
        yield from self["list"]

    @property
    def all(self):
        actions = []
        for a in self:
            if isinstance(a, BaseActions):
                actions.extend(a.all)
            else:
                actions.append(a)

        return actions
    
    def copy(self):
        return self.__class__(self.duration, self.interval, self.total, self.interp, 
            self.cover, list=[a.copy() for a in self])

    def combine(self, cls, value):
        if callable(value): value = Call(func=value)
        if value.total == self.total and isinstance(self, cls):
            v = self.copy()
            if isinstance(value, BaseAction):
                v.append(value)
            else:
                v.extend(value["list"])
            return v
        else:
            return cls(list=[self, value])

    def insert(self, index, action):
        lst = self["list"]
        index = (len(lst) + index) if index < 0 else index
        try:
            lst.insert(index, action)
        except TypeError:
            lst = list(lst)
            lst.insert(index, action)
        if index > 0:
            last_action = lst[index - 1]
            if last_action == action:
                last_action.total += action.total
                lst.pop(index)
                
    def append(self, action):
        self.insert(len(self["list"]), action)

    def extend(self, actions):
        for a in self.actions:
            self.append(a)

class SyncActions(BaseActions):
    def generate(self, sprite):
        i = 0
        upd = yield
        while i < self.total:
            gens = [a.generate(sprite) for a in self["list"]]
            for g in gens: g.send(None)

            while True:
                for i, g in enumerate(gens):
                    try:
                        upd = g.send(upd)
                    except StopIteration:
                        gens.remove(g)
                if not gens:
                    break
                upd = yield upd
                
            i += 1

class AsyncActions(BaseActions):
    def generate(self, sprite):
        i = 0
        while i < self.total:
            for a in self["list"]:
                yield from a.generate(sprite)
            i += 1

class Call(SpecialAction):
    ATTR = {"func":None}
    def single_generate(self, s):
        self["func"](s)
        yield

class Clear(SpecialAction):
    def single_generate(self, s):
        s.clear_cover()
        yield

class Kill(SpecialAction):
    ATTR = {"call_end_func":True}
    def single_generate(self, s):
        if self["call_end_func"] and s.manager.end_func:
            s.manager.end_func(s, s.manager.actions)
        s.kill()
        yield

class Switch(SpecialAction):
    ATTR = {"scene":None, "cache":None}
    def single_generate(self, s):
        s.switch(self["scene"], cache=self["cache"])
        yield

class Remain(SpecialAction):
    def single_generate(self, s):
        while True: yield

class Act(BaseAction):
    ATTR = {"func":None}
    def get(self, pos, *args):
        if f := self["func"]: f(pos, *args)

class Delay(BaseAction):
    pass

class Fade(BaseAction):
    ATTR = {"range":(0, 255)}
    COVER = True
    def get(self, pos, im, rect):
        surf = im.copy()
        surf.set_alpha(self.get_mixture(pos))
        return surf, rect
    
class FadeIn(Fade):
    pass

class FadeOut(Fade):
    ATTR = {"range":(255, 0)}

class Transform(BaseAction):
    ATTR = {"range":(1, 2), "anchor":"center", "func":epg.transform.scale_by}
    COVER = True
    def get(self, pos, im, rect):
        surf = self["func"](im, self.get_mixture(pos))
        new_rect = surf.get_rect()
        setattr(new_rect, self["anchor"], getattr(rect, self["anchor"]))
        return surf, new_rect

class ScaleBy(Transform):
    pass

class ScaleTo(Transform):
    ATTR = {"range":(0, 0), "anchor":"center", "func":epg.transform.scale}
    def init(self, s):
        d = self.orig_kw
        x = d.copy()
        if isinstance(d["range"][0], int):
            x["range"] = [None, d["range"]]

        for i in (0, 1):
            if not x["range"][i]:
                self["range"] = list(x["range"])
                self["range"][i] = s.orig_rect.size

class Rotate(Transform):
    ATTR = {"range":(0, 360), "anchor":"center", "func":epg.transform.rotate}

class Flip(BaseAction):
    ATTR = {"x":True, "y":False}
    COVER = True
    def get(self, pos, im, rect):
        return epg.transform.flip(im, self["x"], self["y"]), rect

class MoveBy(BaseAction):
    ATTR = {"range":(0, 0)}
    COVER = True
    def init(self, s):
        d = self.orig_kw
        if isinstance(d["range"][0], int):
            self["range"] = ((0, 0), d["range"])

    def get(self, pos, im, rect):
        return im, rect.move(*self.get_mixture(pos))

class MoveTo(BaseAction):
    ATTR = {"range":(0, 0), "anchor":"topleft"}
    COVER = True
    def init(self, s):
        d = self.orig_kw
        x = d.copy()
        if isinstance(d["range"][0], int):
            x["range"] = [None, d["range"]]
        for i in (0, 1):
            if not x["range"][i]:
                self["range"] = list(x["range"])
                self["range"][i] = getattr(s.orig_rect, self["anchor"])

    def get(self, pos, im, rect):
        rect = rect.copy()
        setattr(rect, self["anchor"], self.get_mixture(pos))
        return im, rect

class Erase(BaseAction):
    ATTR = {"range":((0, 0), (1, 0)), "anchor":"topleft", "size":(1, 1), 
    "eraser":None, "fill":True}
    def init(self, s):
        x, sz = self.orig_kw["size"], s.orig_rect.size
        self.eraser_rect = epg.Rect(0, 0, x[0]*sz[0], x[1]*sz[1])
        self["range"] = list(self["range"])
        for i in (0, 1):
            y = self.orig_kw["range"][i]
            self["range"][i] = y[0]*sz[0], y[1]*sz[1]

    def get(self, pos, im, rect):
        eraser_rect = self.eraser_rect.copy()
        setattr(eraser_rect, self["anchor"], self.get_mixture(pos))
        im = im.copy()
        if self["fill"]: im.fill((0, 0, 0, 0), eraser_rect)
        if self["eraser"]: im.blit(self["eraser"], eraser_rect)
        return im, rect

class Shake(BaseAction):
    ATTR = {"dist":(10, 0), "func":(math.sin, math.sin)}
    def get(self, pos, im, rect):
        p = pos * math.tau
        rect = rect.move(self["func"][0](p) * self["dist"][0],
                         self["func"][1](p) * self["dist"][1])
        return im, rect
