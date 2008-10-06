import sys, inspect, pygame
from pygame.rect import Rect

class EmergencyExit(SystemExit):
    '''SystemExit exception with message and traceback'''
    def __init__(self, msg):
        SystemExit.__init__(self)
        trace = ''
        for line in inspect.stack()[1:]:
            args = tuple(list(line[1:3]) + list((line[4][0].strip(),)))
            trace += '  [%s:%d -> %s]\n' % args
        sys.stderr.write('Emergency exit:\n  %s\n' % msg)
        sys.stderr.write('Traceback:\n')
        sys.stderr.write(trace)

class Callable:
    def __init__(self, callback):
        self.__call__ = callback

class Display:
    __instance = None
    def get_instance():
        if not(Display.__instance):
            Display.__instance = Display()
        return Display.__instance

    def __init__(self):
        self.resized = False
        self.__frontend = pygame.display.set_mode((320, 240))

    def flip(self):
        self.__frontend.blit(pygame.transform.scale(self.__frontend.subsurface(Rect(0,0,320,240)), (640,480)), [0,0])
        pygame.display.flip()
        if not(self.resized):
            self.resized = True
            pygame.display.set_mode((640, 480))

    def set_mode(self, resolution=(0,0), flags=pygame.HWSURFACE, depth=0):
        return pygame.display.set_mode(resolution, flags, depth)

    def get_surface(self):
        return self.__frontend

    def draw_rect(self, color, rect, width=0):
        pygame.draw.rect(self.__frontend, color,  rect, width)

    def blit(self, surface, coords):
        self.__frontend.blit(surface, coords)

    def get_rect(self):
        return self.__frontend.get_rect()

    get_instance = Callable(get_instance)