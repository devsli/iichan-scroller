#! /usr/bin/env python

import pygame
from pygame.locals import *
import ConfigParser

from data import *
from sprites import *

class Background:
    def __init__(self, file, x, y, z):
        self.texture = load_image(filepath(file))
        self.x = x
        self.y = y
        self.z = z
        self.rect = self.texture.get_rect(topleft = (x, y))

    def __str__(self):
        return self.file

    def zcmp(bg1, bg2):
        if bg1.z > bg2.z:
            return -1
        elif bg1.z < bg2.z:
            return 1
        else:
            return 0

class Level:
    size = (4000, 200)

    def __init__(self, lvl=1):
        self.generate_lvl(lvl)

    def generate_lvl(self, lvl):
        level = ConfigParser.ConfigParser()
        level_file = filepath("level%d.lvl" % lvl)
        level.read((filepath("base.lvl"), level_file))

        try:
            x, y = level.get("general", "size").split(',')
            self.size = (int(x), int(y))
        except:
            pass

        resources = {}
        if 'resources' in level.sections():
            for res in level.items('resources'):
                resources['@' + res[0]] = res[1]

        self.backgrounds_layers = [[], [], []]
        if 'background' in level.sections():
            for background in level.items('background'):
                file, layer, x, y, z = background[1].split(',')
                try:
                    file = resources[file] if file[0] == '@' else file
                except:
                    raise SystemExit, "Unknown resource '%s' in file '%s'" % (file, level_file)
                self.backgrounds_layers[int(layer)].append(Background(file, int(x), int(y), int(z)))

        for backgrounds in self.backgrounds_layers:
            backgrounds.sort(cmp=Background.zcmp)

        if 'objects' in level.sections():
            for object in level.items('objects'):
                obj, x, y, z, dir = object[1].split(',')
                obj = obj.strip()
                x = int(x)
                y = int(y)
                z = int(z)
                if obj in ['ammo', 'heart', 'logo']:
                    PowerUp((x, y), obj)
                elif obj == 'betard':
                    Betard((x, y))
                elif obj == 'player':
                    self.player = Player((x, y))
                elif obj in ['box', 'barrel']:
                    Static((x, y), obj)

    def get_size(self):
        return self.size

if __name__ == '__main__':
    Level()
