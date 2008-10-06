#! /usr/bin/env python

import pygame, sys
from pygame.locals import *
import ConfigParser
import config

from data import *
from sprites import *
from utils import *

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
    size = (2000, 100)
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
                try:
                    file, layer, x, y, z = background[1].split(',')
                    file = resources[file] if file[0] == '@' else file
                except:
                    raise EmergencyExit, "Error when parsing line '%s'" % background[1]
                self.backgrounds_layers[int(layer)].append(Background(file, int(x), int(y), int(z)))

        for backgrounds in self.backgrounds_layers:
            backgrounds.sort(cmp=Background.zcmp)

        if 'objects' in level.sections():
            for object in level.items('objects'):
                try:
                    group_obj, x, y, h, dir = object[1].split(',')
                    dir = -1 if dir.strip() == "left" else 1
                    group_obj = group_obj.strip()
                    group, obj = group_obj.split('.')

                    x = int(x)
                    y = int(y)
                    h = int(h)

                    if group == 'powerup':
                        PowerUp((x, y), obj, h)
                    elif group == 'enemy':
                        Betard((x, y), facing = dir)
                    elif group == 'player':
                        self.player = Player((x, y), dir, h)
                    elif group == 'static':
                        Static((x, y), obj, h)
                except EmergencyExit:
                    raise EmergencyExit, "Can't load object '%s' during loading '%s'" % (group_obj, level_file)

        if 'triggers' in level.sections():
            for trigger in level.items('triggers'):
                all = trigger[1].split(',')
                obj = all[0].strip()
                if obj == 'spawn_trigger':
                    obj, x, y, w, h, spawnobj, spawnx, spawny, spawnheight, spawndir = trigger[1].split(',')
                    x = int(x)
                    y = int(y)
                    w = int(w)
                    h = int(h)
                    spawnobj = spawnobj.strip()
                    spawnx   = int(spawnx)
                    spawny   = int(spawny)
                    spawnheight   = int(spawnheight)
                    spawndir = dir = -1 if spawndir.strip() == "left" else 1
                    SpawnTrigger(Rect(x, y, w, h), spawnobj, spawnx, spawny, spawndir)
                elif obj == 'dialog_trigger':
                    obj, x, y, w, h, dialog = trigger[1].split(',')
                    x = int(x)
                    y = int(y)
                    w = int(w)
                    h = int(h)
                    dialog = dialog.strip()
                    DialogTrigger(Rect(x, y, w, h), dialog)


    def get_size(self):
        return self.size

if __name__ == '__main__':
    Level()
