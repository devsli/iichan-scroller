'''Game main module.

Contains the entry point used by the run_game.py script.

Feel free to put all your game code here, or in other modules in this "gamelib"
package.
'''

import pygame, os, data, config
from pygame.locals import *
from game import *

def main():
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    config.loadSettings("config.cfg")
    pygame.init()
    pygame.display.set_icon(pygame.image.load(data.filepath("loli_still.gif")))
    pygame.display.set_caption('Codename: because she said no')

    if config.widescreen:
      config.width = 768
    else:
      config.width = 640

    if config.fullscreen:
        screen = pygame.display.set_mode((config.width, 480), pygame.FULLSCREEN, 32)
        pygame.mouse.set_visible(0)
    else:
        screen = pygame.display.set_mode((config.width, 480))

    Game(screen, config)
