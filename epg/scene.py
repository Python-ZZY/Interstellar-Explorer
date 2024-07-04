import epg

class Scene(epg.Rect):
    def __init__(self, screen=None, init=True):
        self.screen = screen if screen else epg.app.screen
        super().__init__(self.screen.get_rect())

        self.scene_running = False
        self.music_manager = None
        self.funcs = {}
        self.groups = {}

        if init:
            self.init()

    def __eq__(self, value):
        return self is value

    def run(self):
        self.scene_running = True
        while self.scene_running:
            self.single_run()
            
    def single_run(self):
        for sendarg, func in self.funcs.values():
            if sendarg:
                func(self)
            else:
                func()
        
        self.update()
        if not self.scene_running:
            return

        self._draw()
        
        now = epg.time.get_ticks()
        events = epg.event.get()
        epg.time_offset += epg.time.get_ticks() - now

        for event in events:
            if event.type == epg.QUIT:
                self.onexit()
            else:
                self.events(event)

        epg.app.update()
        epg.update_display()

    def add_func(self, func, name=None, sendarg=False):
        if not name: name = func
        self.funcs[name] = (sendarg, func)

    def get_func(self, name):
        return self.funcs[name][1]
    
    def del_func(self, name):
        del self.funcs[name]
        
    def add_group(self, *names, pref="group_", asattr=True):
        keys = tuple(self.groups)
        for name in names:
            if name in keys:
                epg.throw("group %s already exists"%name)
            self.groups[name] = g = epg.sprite.Group()
            if asattr: setattr(self, pref + str(name), g)
        return g

    def get_group(self, name):
        return self.groups[name]
    
    def del_group(self, *names, pref="group_", asattr=True):
        for name in names:
            try:
                del self.groups[name]
            except KeyError:
                epg.throw("group %s does not exist"%name)
            if asattr: delattr(self, pref + str(name), g)

    def do_group(self, func):
        for group in self.groups.values():
            func(self, group)
    
    def draw_group(self, offset=None):
        for group in self.groups.values():
            for sprite in group:
                sprite.draw(self.screen, offset)
                
    def update_group(self):
        for group in self.groups.values():
            group.update()

    def set_music(self, *paths, **kw):
        self.music_manager = epg.MusicManager(paths, **kw)
        self.add_func(self.music_manager.update, "music_manager")

    def unset_music(self):
        self.del_func("music_manager")

    def switch(self, scene, cache=None):
        if cache:
            epg.app.cache(self, cache)
        epg.app.switch(scene)

    def init(self):
        pass

    def onexit(self):
        self.quit()
        
    def quit(self):
        self.scene_running = False

    def _draw(self):
        self.draw()

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.draw_group()
    
    def update(self):
        self.update_group()

    def events(self, event):
        pass

class AScene(Scene, epg.action.ActionObject):
    def __init__(self, screen=None, bgcolor=(0, 0, 0), end_func=None, init=True):
        Scene.__init__(self, screen, init=False)
        epg.action.ActionObject.__init__(self, None, end_func)
        self.real_screen = self.screen
        self.screen = self.screen.copy()
        self.bgcolor = bgcolor
        self.orig_image, self.orig_rect = None, None
        self.image, self.rect = self.screen, self.screen.get_rect()
        if init:
            self.init()

    def act(self, *actions, end_func=None, cover=False):
        epg.action.ActionObject.act(self, *actions, end_func=end_func, cover=cover)

    def kill(self):
        self.quit()

    def single_run(self):
        epg.action.ActionObject.update(self)
        self.screen = self.image
        Scene.single_run(self)

    def _draw(self):
        self.real_screen.fill(self.bgcolor)
        self.draw()
        self.real_screen.blit(self.screen, self.rect)

    def update(self):
        epg.action.ActionObject.update(self)
        Scene.update(self)
