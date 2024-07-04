import pygame as pg
from pygame import *
import os
import sys
import asyncio
import warnings

__version__ = "0.0a0.dev0"

def throw(*_msg):
    msg = ""
    for s in _msg:
        msg += str(s) + " "
    raise pg.error(msg)

def check_attr(kw, attr):
    bad = set(kw) - set(attr)
    if len(bad) > 0:
        throw("invalid argument(s):", bad)

def init(size=(0, 0), caption=None, icon=None, fps=60, appcls=None, ime=True, **kw):
    '''Initialize and set the pygame window'''
    global app, clock, game_fps

    if ime:
        os.environ["SDL_IME_SHOW_UI"] = str(ime)
    
    pg.init()
    screen = pg.display.set_mode(size, **kw)
    app = (appcls and appcls()) or App()

    clock = pg.time.Clock()
    game_fps = fps
    
    if caption:
        pg.display.set_caption(caption)
    if icon:
        pg.display.set_icon(icon)

    return app

def get_path(relative_path):
    '''Return the full path (sys._MEIPASS as the cwd if using pyinstaller)'''
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.normpath(os.path.join(base_path, relative_path))

def get_asset(path):
    return get_path(os.path.join(assets, path))    

time_offset = 0
def get_time():
    '''Return the game time minus the event.get() loss'''
    return pg.time.get_ticks() - time_offset

def test_fps():
    '''Set the caption to FPS in order to test the game'''
    display.set_caption(str(clock.get_fps()))

def update_display():
    clock.tick(game_fps)
    display.flip()

class App:
    def __init__(self, screen=None, scene=None):
        self.screen = screen if screen else display.get_surface()
        self.scene = scene
        self.attr = {}
        self.cached = {}
        self.app_running = False
        self.init()

    def __getitem__(self, key):
        return self.attr[key]

    def __setitem__(self, key, value):
        self.attr[key] = value

    def init(self):
        pass

    def update(self):
        pass
        
    def cache(self, scene, name):
        self.cached[name] = scene

    def run(self, scene=None):
        asyncio.run(self.async_run(scene))
        
    async def async_run(self, scene=None):
        if scene: self.switch(scene)

        self.app_running = True
        while self.app_running:
            scene = self.scene

            self.scene.scene_running = True
            while self.scene.scene_running:
                self.scene.single_run()

                await asyncio.sleep(0)
                
            if self.scene == scene: self.quit()

    def quit(self):
        self.app_running = False
        self.scene.quit()

    def switch(self, scene):
        if not isinstance(scene, Scene):
            try:
                scene = self.cached[scene]
            except KeyError:
                throw("no scene found")

        if self.scene and self.scene.scene_running:
            self.scene.quit()
            ##if sync_screen:
            ##    self.scene.screen = scene.screen ## TODO
        self.scene = scene
        
import epg.locals as locals
import epg.collision as collision
import epg.data as data
import epg.math as math
import epg.mixer as mixer
import epg.image as image
import epg.mask as mask
import epg.action as action
import epg.scene as scene
import epg.font as font
import epg.renderer as renderer
import epg.sprite as sprite
import epg.ui as ui

from .font import text_render
from .scene import Scene, AScene
from .sprite import Sprite, Static, AStatic, Dynamic, ADynamic, OsDynamic, OsADynamic
from .mixer import MusicManager, play_music, play_sound
from .image import Animation, SpriteSheet, FileSheet, load_sheet

load_font = font.load
get_image = image.get
load_image = image.load
get_mask = mask.get
get_sprite = sprite.get

assets = ""
attr = {}