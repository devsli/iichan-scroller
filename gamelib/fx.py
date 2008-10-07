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
        """
        Countdown effect lifetime
        """
        self.dispose_after -= 1
        if self.dispose_after <= 0:
            self.complete()

    def complete(self):
            for method in self.__oncomplete:
                method(self)

    def add_complete_callback(self, callback):
        self.__oncomplete.append(callback)

def quit(sender):
    exit()

class FadeoutEffect(Effect):
    def __init__(self, to_color, length):
        Effect.__init__(self)
        self.__length = length
        self.dispose_after = length
        self.__index = 0
        self.__step_size = 255.0/length
        self.__curtain = pygame.display.get_surface().copy()
        self.__curtain.fill(to_color)

    def morph(self, surface):
        Effect.morph(self, surface)
        self.__curtain.set_alpha(self.__index)
        surface.blit(self.__curtain, [0,0])
        self.__index += self.__step_size


class FadeinEffect(Effect):
    def __init__(self, from_color, length):
        Effect.__init__(self)
        self.__length = length
        self.dispose_after = length
        self.__index = 0
        self.__step_size = 255.0/length
        self.__curtain = pygame.display.get_surface().copy()
        self.__curtain.fill(from_color)

    def morph(self, surface):
        Effect.morph(self, surface)
        self.__curtain.set_alpha(255 - self.__index)
        surface.blit(self.__curtain, [0,0])
        self.__index += self.__step_size

class SequenceEffect(Effect):
    def __init__(self):
        Effect.__init__(self)
        self.__effects = []

    def morph(self, surface):
        if (self.__effects.count >= 0):
            try:
                self.__effects[0].morph(surface)
            except:
                self.complete()
        else:
            self.complete()

    def add(self, effect):
        effect.add_complete_callback(lambda effect: self.remove(effect))
        self.__effects.append(effect)

    def remove(self, effect):
        self.__effects.remove(effect)

class FlashEffect(SequenceEffect):
    def __init__(self):
        SequenceEffect.__init__(self)
        self.add(FadeoutEffect((255,255,255), 3))
        self.add(FadeinEffect((255,255,255), 50))

class QuitEffect(FadeoutEffect):
    """
    Fade display out
    """
    def __init__(self, length, action=quit):
        FadeoutEffect.__init__(self, (0,0,0), length)
        self.add_complete_callback(action)