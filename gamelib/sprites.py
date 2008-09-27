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

class Simple(pygame.sprite.Sprite):
    def __init__(self, *groups):
        pygame.sprite.Sprite.__init__(self, groups)
        self.xoffset = 0
        self.yoffset = 0

    def draw(self, surf, rect):
        surf.blit(self.image, rect)

    def get_projection(self):
        return self.rect

class Particle(Simple):

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
                    spr.on_collision(side, self, group, 0, 0)

        return self.rect.left-oldr.left,self.rect.top-oldr.top

    def on_collision(self, side, sprite, group, dx, dy):
        pass


    def draw(self, surf, rect):
        surf.blit(self.image, rect)
        #surf.blit(self.image, (self.rect[0]+self.xoffset, self.rect[1]+self.yoffset))

    def hit(self):
        pass

    def get_projection(self):
        return self.rect

class Player(Collidable):
    def __init__(self, pos, facing=1):
        Collidable.__init__(self, self.groups)
        self.set_state("idle")
        self.image = self.right_images[0]
        self.rect = self.image.get_rect(topleft = pos)
        self.facing = facing
        self.shoot_timer = 0
        self.hit_timer = 0
        self.hp = 5
        self.ammo = 20
        self.score = 0
        self.frame = 0

        self.collide(self.game.static)
        self.collide(self.game.monsters)
        self.collide(self.game.triggers)

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
         # save copy of player's projection for calculating right shot projection
        self.player_proj = copy.copy(player.get_projection())
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

        self.collide(self.game.static)
        self.collide(self.game.monsters)

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


class DogAI():
    visibility_range = 450
    surrender_range = 600
    attack_range = 0
    player_path = []

    def update(self):
        if self.state == "idle":
            # checking player visibility
            if (abs(self.get_player_distance()) <= self.visibility_range and
                self.is_looking_on_player()):
                self.set_state("walk")
        elif self.state == "walk":
            # attack
            if abs(self.get_player_distance()) <= self.attack_range:
                pass
            # surrender
            elif abs(self.get_player_distance()) >= self.surrender_range:
                self.set_state("idle")
                self.player_path = []
                if self.xspeed > 0:
                    self.facing = 1
                else:
                    self.facing = -1
                self.xspeed = 0
                self.yspeed = 0
                return
            else:
                # get next point from player's path
                path_point = self.get_nearest_path_point()
                xdist = abs(self.rect.centerx - path_point[0])
                ydist = abs(self.rect.centery - path_point[1])

                # goto point
                if self.rect.centerx < path_point[0]:
                    self.xspeed = +self.speed
                elif self.rect.centerx > path_point[0]:
                    self.xspeed = -self.speed
                else:
                    xspeed = 0

                if self.rect.centery < path_point[1]:
                    self.yspeed = +self.speed
                elif self.rect.centery > path_point[1]:
                    self.yspeed = -self.speed
                else:
                    yspeed = 0

                # if we in place - remove this point from path
                if xdist >= 0 and xdist <= self.speed and ydist >= 0 and ydist <= self.speed:
                    self.player_path = self.player_path[1:]

                # checking if player trying run around mob
                if len(self.player_path) > 0:
                    if (self.rect.centerx < self.player_path[0][0] and self.player.rect.centerx < self.player_path[0][0] or
                        self.rect.centerx > self.player_path[0][0] and self.player.rect.centerx > self.player_path[0][0]):
                        self.player_path = []

        # adding new path points
        if self.state in ["walk"]:
            path_point = (self.player.rect.centerx - self.player.rect.centerx % self.speed, self.player.rect.centery - self.player.rect.centery % self.speed)
            if (len(self.player_path) > 0):
                if (self.player_path[-1] != path_point):
                    self.player_path.append(path_point)
            else:
                self.player_path.append(path_point)

    def get_player_distance(self):
        return self.rect.centerx - self.player.rect.centerx

    def get_nearest_path_point(self):
        return self.player_path[0]

    def is_looking_on_player(self):
        if (self.facing > 0 and self.get_player_distance() < 0 or
            self.facing < 0 and self.get_player_distance() > 0):
            return True
        else:
            return False


class Betard(Collidable, DogAI):
    speed = 3
    def __init__(self, pos, type = 1, facing = 1):
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
        self.life = 2
        self.facing = facing

        self.collide(self.game.static)
        self.collide(self.game.players)

    def set_state(self, state = "idle"):
        self.state = state
        self.right_images = []
        self.left_images = self.gifs[state]
        for i in range(len(self.left_images)):
            self.right_images.append(pygame.transform.flip(self.left_images[i], 1, 0))

    def kill(self):
        pygame.sprite.Sprite.kill(self)

    def update(self):
        if self.life <= 0:
            self.kill()
        DogAI.update(self)

        if self.facing > 0:
            self.image = self.right_images[self.timer/5 % len(self.right_images)]
        if self.facing < 0:
            self.image = self.left_images[self.timer/5 % len(self.left_images)]

        # Switch between right and left animation
        if self.xspeed > 0:
            self.image = self.right_images[self.timer/9 % len(self.right_images)]
        if self.xspeed < 0:
            self.image = self.left_images[self.timer/9 % len(self.left_images)]

        self.timer += 1
        self.move(self.xspeed, self.yspeed)

    def on_collision(self, side, sprite, group, dx, dy):
        self.rect.move_ip(-dx, -dy)

    def hit(self):
        self.life -= 1
        if self.life > 0:
            Balloon(self.rect, "OUCH!!!")

    def get_projection(self):
        return Rect(self.rect[0] + 30, self.rect[1] + 140, self.rect[2] - 70, self.rect[3] - 130)

class Static(Collidable):
    def __init__(self, pos, type):
        Collidable.__init__(self, self.groups)
        self.type = type
        self.image = self.images[type]
        self.rect = self.image.get_rect(topleft = pos)

    def get_projection(self):
        if self.type == 'box':
            return Rect(self.rect[0], self.rect[1] + 80, self.rect[2], self.rect[3] - 80)
        elif self.type == 'barrel':
            return Rect(self.rect[0], self.rect[1] + 100, self.rect[2], self.rect[3] - 100)
        elif self.type == 'box_group':
            return Rect(self.rect[0], self.rect[1] + 170, self.rect[2], self.rect[3] - 170)

    def on_collision(self, side, sprite, group, dx, dy):
        sprite.rect.move_ip(-dx, -dy)

class Balloon(Simple):
    def __init__(self, initiator_rect, text):
        Simple.__init__(self, self.groups)
        self.initiator_rect = initiator_rect # for tracking initiator moving
        self.text = text
        self.rect = self.image.get_rect(center = (self.initiator_rect.centerx, self.initiator_rect.y-10))
        self.timer = 0
        self.font = pygame.font.Font(filepath("font.ttf"), 14)

    def update(self):
        self.rect = self.image.get_rect(center = (self.initiator_rect.centerx, self.initiator_rect.y-10))
        self.timer += 1
        if self.timer < 30:
            return
        self.kill()

    def draw(self, surf, rect):
        surf.blit(self.image, rect)
        ren = self.font.render(self.text, 1, (0, 0, 0))
        surf.blit(ren, (rect.centerx-ren.get_width()/2, rect.centery-ren.get_height()/2 - 5))

class SpawnTrigger(Collidable):
    def __init__(self, rect, spawnobj, spawnx, spawny, spawndir):
        Collidable.__init__(self, self.groups)
        self.rect = rect
        self.spawnobj = spawnobj
        self.spawnx = spawnx
        self.spawny = spawny
        self.spawndir = spawndir

    def draw(self, surf, rect):
        pass

    def on_collision(self, side, sprite, group, dx, dy):
        if self.spawnobj == 'betard':
            Betard((self.spawnx, self.spawny), facing = self.spawndir)
        self.kill()



