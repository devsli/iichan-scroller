#! /usr/bin/env python

import pygame
from pygame.locals import *

from data import *
from sprites import *

class Level:

    def __init__(self, lvl=1):
        self.generate_lvl(lvl)

    def generate_lvl(self, lvl):
        PowerUp((250, 330), "ammo")
        PowerUp((350, 340), "heart")
        PowerUp((520, 360), "logo")
        Betard((700, 250))
        self.bg = load_image("back.png")

    def get_size(self):
        size = (4000, 200)
        return size