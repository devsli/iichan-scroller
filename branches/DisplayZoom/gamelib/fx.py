import data, pygame
from pygame.rect import Rect

class EffectCollection:
    def __init__(self):
        self.__effects = []

    def morph(self, surface):
        for effect in self.__effects:
            effect.morph(surface)

    def add(self, effect):
        effect.add_complete_callback(lambda effect: self.remove(effect))
        self.__effects.append(effect)

    def remove(self, effect):
        self.__effects.remove(effect)

class Effect:
    def __init__(self):
        self.dispose_after = 0
        self.__oncomplete = []

    def morph(self, surface):
        self.dispose_after -= 1
        if self.dispose_after <= 0:
            for method in self.__oncomplete:
                method(self)

    def add_complete_callback(self, callback):
        self.__oncomplete.append(callback)

class TireEffect(Effect):
    def __init__(self):
        Effect.__init__(self)
        self.dispose_after = 100

    def morph(self, surface):
        Effect.morph(self, surface)
        surface.blit(data.load_image("..\\data\\tire.png"), [160,120])

def quit(sender):
    exit()

class FadeoutEffect(Effect):
    def __init__(self, length):
        Effect.__init__(self)
        self.__length = length
        self.dispose_after = length
        self.__index = 0
        self.__step_size = 255.0/length
        self.__curtain = pygame.display.get_surface().copy()
        self.__curtain.fill((0,0,0))
        self.add_complete_callback(quit)

    def morph(self, surface):
        Effect.morph(self, surface)
        self.__curtain.set_alpha(self.__index)
        surface.blit(self.__curtain, [0,0])
        self.__index += self.__step_size