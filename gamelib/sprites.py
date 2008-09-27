#! /usr/bin/env python
import pygame, random, math
from pygame.locals import *

from data import *
import copy
TOP_SIDE    = 0
BOTTOM_SIDE = 2
LEFT_SIDE   = 3
RIGHT_SIDE  = 1

def speed_to_side(dx,dy):
    if abs(dx) > abs(dy):
        dy = 0
    else:
        dx = 0
    if dy < 0:
        return 0
    elif dx > 0:
        return 1
    elif dy > 0:
        return 2
    elif dx < 0:
        return 3
    else:
        return 0, 0

class Particle(pygame.sprite.Sprite):
    
    def __init__(self, pos, vx, vy, ax, ay, size, colorstructure, projected = False):
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.vx, self.vy, self.ax, self.ay = vx, vy, ax, ay
        self.images = []
        for x in colorstructure:
            start, end, duration = x
            startr, startg, startb = start
            endr, endg, endb = end
            def f(s, e, t):
                return s + int((e - s)*(t/float(duration)))
            for t in range(duration):
                image = pygame.Surface((size, size)).convert()
                image.fill((f(startr, endr, t), f(startg, endg, t), f(startb, endb, t)))
                self.images.append(image)
        self.image = self.images[0]
        self.rect = self.image.get_rect(center = pos)
        
    def update(self):
        self.rect.move_ip(self.vx, self.vy)
        self.vx = self.vx + self.ax
        self.vy = self.vy + self.ay
        if not self.images:
            self.kill()
        else:
            self.image = self.images.pop(0)
            
    def get_projection(self):
        return self.rect

class Collidable(pygame.sprite.Sprite):

    def __init__(self, *groups):
        pygame.sprite.Sprite.__init__(self, groups)
        self.collision_groups = []
        self.xoffset = 0
        self.yoffset = 0

    def collide(self, group):
        if group not in self.collision_groups:
            self.collision_groups.append(group)

    def move(self, dx, dy, collide=True):
        collide = True
        if collide:
            if dx!=0:
                dx, dummy = self.__move(dx,0)
            if dy!=0:
                dummy, dy = self.__move(0,dy)
        else:
            self.rect.move_ip(dx, dy)
        return dx, dy

    def __move(self,dx,dy):
        oldr = copy.copy(self.rect)
        self.rect.move_ip(dx, dy)
        proj = self.get_projection()
        proj.move_ip(dx, dy)
        side = speed_to_side(dx, dy)

        for group in self.collision_groups:
            for spr in group:
                if spr.rect.colliderect(self.rect) and spr.get_projection().colliderect(proj):
                    self.on_collision(side, spr, group, dx, dy)

        return self.rect.left-oldr.left,self.rect.top-oldr.top

    def on_collision(self, side, sprite, group, dx, dy):
        #self.rect.move_ip(-dx, -dy)
        pass

    def draw(self, surf):
        surf.blit(self.image, (self.rect[0]+self.xoffset, self.rect[1]+self.yoffset))

    def hit(self):
        pass

    def get_projection(self):
        return self.rect

class Simple(pygame.sprite.Sprite):
    def __init__(self, *groups):
        pygame.sprite.Sprite.__init__(self, groups)
        self.xoffset = 0
        self.yoffset = 0

    #def draw(self, surf):
        #surf.blit(self.image, (self.rect[0]+self.xoffset, self.rect[1]+self.yoffset))
    #    pass

    def get_projection(self):
        return self.rect

class Player(Collidable):
    def __init__(self, pos):
        Collidable.__init__(self, self.groups)
        self.set_state("idle")
        self.image = self.right_images[0]
        self.rect = self.image.get_rect(topleft = pos)
        self.facing = 1
        self.shoot_timer = 0
        self.hit_timer = 0
        self.hp = 5
        self.ammo = 20
        self.score = 0
        self.frame = 0

    def set_state(self, state = "idle"):
        self.state = state
        self.left_images = []
        self.right_images = self.gifs[state]
        for i in range(len(self.right_images)):
            self.left_images.append(pygame.transform.flip(self.right_images[i], 1, 0))

    def duck(self):
        self.set_state("duck")

    def shoot(self):
        if self.shoot_timer <= 0:
            self.shoot_timer = 20
            if self.state in ["idle", "walk"]:
                self.state = "stand_shoot"
            elif self.state in ["duck"]:
                self.state = "duck_shoot"
        self.ammo -= 1

    def update(self):
        dx = 0
        dy = 0
        key = pygame.key.get_pressed()

        # Move
        if self.hit_timer <= 0:
            if key[K_LEFT]:
                dx = -1
                self.facing = dx
                self.state = "walk"
            elif key[K_RIGHT]:
                dx = 1
                self.facing = dx
                self.state = "walk"
            if key[K_DOWN]:
                dy = 1
                self.state = "walk"
            elif key[K_UP]:
                dy = -1
                self.state = "walk"

        # Moving area
        if self.rect.left < 10:
            self.rect.left = 10
        if self.rect.bottom > 460:
            self.rect.bottom = 460
        if self.rect.top < 200:
            self.rect.top = 200

        if self.shoot_timer <= 0:
            if key[K_LCTRL]:
                pass
                self.state = "duck"
            elif (dx == 0) and (dy == 0):
                self.state = "idle"

        self.set_state(self.state)

        # Ammo control
        if self.ammo < 0: self.ammo = 0
        elif self.ammo > 100: self.ammo = 100

        # Looking left or right?
        if self.facing > 0:
            self.image = self.right_images[self.frame/5 % len(self.right_images)]
        if self.facing < 0:
            self.image = self.left_images[self.frame/5 % len(self.left_images)]

        # Switch between right and left animation
        if dx > 0:
            self.image = self.right_images[self.frame/4 % len(self.right_images)]
        if dx < 0:
            self.image = self.left_images[self.frame/4 % len(self.left_images)]

        self.move(4*dx, 4*dy)

        # Timers and frames
        self.frame -= 1
        self.hit_timer -= 1
        self.shoot_timer -= 1

    def on_collision(self, side, sprite, group, dx, dy):
        self.rect.move_ip(-dx, -dy)

    def kill(self):
        pygame.sprite.Sprite.kill(self)
        PlayerDie(self.rect.center, self.facing)

    def get_projection(self):
        if self.facing == 1:
            return Rect(self.rect[0] + 30, self.rect[1] + 140, self.rect[2] - 70, self.rect[3] - 130)
        else:
            return Rect(self.rect[0] + 40, self.rect[1] + 140, self.rect[2] - 70, self.rect[3] - 130)

class PlayerShot(Collidable):

    def __init__(self, pos, facing, img, player):
        Collidable.__init__(self, self.groups)
        self.facing = facing
        self.left_images = []
        self.right_images = img
        self.player_proj = copy.copy(player.get_projection()) # save copy of player for calculating right shot projection
        for i in range(len(self.right_images)):
            self.left_images.append(pygame.transform.flip(self.right_images[i], 1, 0))
        self.image = self.right_images[1]
        self.rect = self.image.get_rect(topleft = pos)
        self.rect[1] -= 12
        if self.facing > 0:
            self.speed = 10
            self.rect[0] += 60
        elif self.facing < 0:
            self.speed = -10
            self.rect[0] -= 140
        self.layer = self.get_projection().bottom
        self.timer = 0

    def update(self):
        if self.timer < 6:
            frame = 1
        else: frame = 0
        if self.facing > 0: self.image = self.right_images[frame]
        elif self.facing < 0: self.image = self.left_images[frame]
        if self.timer > 40:
            self.kill()
        self.timer += 1
        self.move(self.speed, 0)

    def kill(self):
        for i in range(10):
            if self.facing < 0:
                Particle(self.rect.midleft, random.randrange(-5, 6), random.randrange(-10, 0), 1, 1, 3,
                     [((58, 192, 253), (247, 254, 255), 5)])
            else: 
                Particle(self.rect.midright, random.randrange(-5, 6), random.randrange(-10, 0), -1, 1, 3,
                     [((58, 192, 253), (247, 254, 255), 5)])
        pygame.sprite.Sprite.kill(self)

    def on_collision(self, side, sprite, group, dx, dy):
        sprite.hit()
        self.kill()

    def get_projection(self):
        return Rect(self.rect[0], self.player_proj[1] + 10, self.rect[2], self.player_proj[3] - 10)

class PowerUp(Collidable):
    def __init__(self, pos, type):
        Collidable.__init__(self, self.groups)
        self.type = type
        self.images = self.gifs[type]
        self.image = self.images[0]
        self.rect = self.image.get_rect(topleft = pos)
        self.frame = 0
    def update(self):
        self.frame += 1
        self.image = self.images[self.frame/5 % len(self.images)]

    def get_projection(self):
        return self.rect
    
    def kill(self):
        for i in range(5):
            Particle(self.rect.center, random.randrange(-3, 4), random.randrange(-10, 0), 0, 1, 4,
                 [((255, 255, 255), (255, 255, 255), 10)])
        pygame.sprite.Sprite.kill(self)

class Betard(Collidable):
    def __init__(self, pos, type = 1):
        Collidable.__init__(self, self.groups)
        self.set_state("idle")
        self.timer = 0
        self.xspeed = 0
        self.yspeed = 0
        self.decision = 0
        self.type = type
        self.set_state()
        self.image = self.left_images[0]
        self.images = None
        self.rect = self.image.get_rect(topleft = pos)

    def set_state(self, state = "idle"):
        self.state = state
        self.right_images = []
        self.left_images = self.gifs[state]
        for i in range(len(self.left_images)):
            self.right_images.append(pygame.transform.flip(self.left_images[i], 1, 0))

    def kill(self):
        pass

    def update(self):

        if self.timer > 40:
            self.decision = random.randrange(3)
            self.timer = 0

        if self.decision == 0:
            if self.state != "idle": self.set_state("idle")
            if self.xspeed > 0: self.images = self.right_images
            else: self.images = self.left_images
            self.xspeed = 0
            self.yspeed = 0
        elif self.decision == 1:
            if self.state != "walk": self.set_state("walk")
            self.images = self.right_images
            self.xspeed = 3
            self.yspeed = 0
        elif self.decision == 2:
            if self.state != "walk": self.set_state("walk")
            self.images = self.left_images
            self.xspeed = -3
            self.yspeed = 0

        self.image = self.images[self.timer/9 % len(self.images)]
        self.timer += 1
        self.move(self.xspeed, self.yspeed)

    def on_collision(self, side, sprite, group, dx, dy):
        self.rect.move_ip(-dx*2, -dy*2)

    def hit(self):
        Balloon((self.rect.x, self.rect.y), )

    def get_projection(self):
        return Rect(self.rect[0] + 30, self.rect[1] + 140, self.rect[2] - 70, self.rect[3] - 130)

class Static(Collidable):
    def __init__(self, pos, type):
        Collidable.__init__(self, self.groups)
        self.type = type
        self.image = self.images[type]
        #self.image = self.images[0]
        self.rect = self.image.get_rect(topleft = pos)

    def get_projection(self):
        if self.type == 'box':
            return Rect(self.rect[0], self.rect[1] + 80, self.rect[2], self.rect[3] - 80)
        elif self.type == 'barrel':
            return Rect(self.rect[0], self.rect[1] + 100, self.rect[2], self.rect[3] - 100)
        elif self.type == 'box_group':
            return Rect(self.rect[0], self.rect[1] + 170, self.rect[2], self.rect[3] - 170)

class Balloon(Simple):
    def __init__(self, pos):
        Simple.__init__(self, self.groups)
        self.rect = self.image.get_rect(center = pos)
        self.timer = 0

    def update(self):
        self.timer += 1
        if self.timer < 30:
            return
        self.kill()

    def draw(self, surf):
        surf.blit(self.image, (self.rect[0]+self.xoffset, self.rect[1]+self.yoffset))
        ren = self.font.render("OUCH!11", 1, (0, 0, 0))
        self.screen.blit(ren, (1,1))