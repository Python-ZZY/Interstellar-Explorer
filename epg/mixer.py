import pygame as pg
from pygame.mixer import *
import epg
import random

music_on = True
sound_on = True

class MusicManager:
    def __init__(self, paths, stop=True, rand=True, gpath=epg.get_asset):
        if gpath:
            self.paths = [gpath(p) for p in paths]
        else:
            self.paths = paths
            
        self.id = 0
        
        if stop:
            pg.mixer.music.stop()
            self.update()
        if rand:
            random.shuffle(self.paths)

    def update(self):
        if music_on and not pg.mixer.music.get_busy():
            pg.mixer.music.load(self.paths[self.id])
            pg.mixer.music.play()
            
            self.id += 1
            if self.id == len(self.paths):
                self.id = 0

    def stop(self, fadeout=200):
        pg.mixer.music.fadeout(fadeout)

def play_music(name, *args, gpath=epg.get_asset, **kw):
    if music_on:
        if gpath: name = gpath(name)
        music.load(name)
        music.play(*args, **kw)
        
def play_sound(name, *args, gpath=epg.get_asset, **kw):
    if sound_on:
        if gpath: name = gpath(name)
        Sound(name).play(*args, **kw)
