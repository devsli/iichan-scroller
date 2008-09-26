#! /usr/bin/env python
import pygame, random, math
from pygame.locals import *

from data import *

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
        if collide:
            if dx!=0:
                dx, dummy = self.__move(dx,0)
            if dy!=0:
                dummy, dy = self.__move(0,dy)
        else:
            self.rect.move_ip(dx, dy)
        return dx, dy
    
    def clamp_off(self, sprite, side):
        if side == TOP_SIDE:
            self.rect.top = sprite.rect.bottom
        if side == RIGHT_SIDE:
            self.rect.right = sprite.rect.left
        if side == BOTTOM_SIDE:
            self.rect.bottom = sprite.rect.top
        if side == LEFT_SIDE:
            self.rect.left = sprite.rect.right
    
    def __move(self,dx,dy):
        oldr = self.rect
        self.rect.move_ip(dx, dy)
        side = speed_to_side(dx, dy)

        for group in self.collision_groups:
            for spr in group:
                if spr.rect.colliderect(self.rect):
                    self.on_collision(side, spr, group)

        return self.rect.left-oldr.left,self.rect.top-oldr.top
    
    def on_collision(self, side, sprite, group):
        self.clamp_off(sprite, side)
    
    def draw(self, surf):
        surf.blit(self.image, (self.rect[0]+self.xoffset, self.rect[1]+self.yoffset))

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
        
    def on_collision(self, side, sprite, group):
        self.clamp_off(sprite, side)
        if side == TOP_SIDE:
            pass
        if side == BOTTOM_SIDE:
            pass
    
    def kill(self):
        pygame.sprite.Sprite.kill(self)
        PlayerDie(self.rect.center, self.facing)
        
class PlayerShot(Collidable):
    
    def __init__(self, pos, facing, img):
        Collidable.__init__(self, self.groups)
        self.facing = facing
        self.left_images = []
        self.right_images = img
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
        pygame.sprite.Sprite.kill(self)

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

class PowerUpDie(Collidable):
    def __init__(self, pos):
        Collidable.__init__(self, self.groups) 
        self.image = self.images[0]
        self.rect = self.image.get_rect(center = pos)
        self.timer = 0

    def update(self):
        self.timer += 1
        if self.timer < 12:
            self.image = self.images[self.timer/5 % len(self.images)]
        else:
            self.kill()
            
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
            
    def hit(self):
        pass
    
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