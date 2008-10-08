#! /usr/bin/env python
import pygame, random, math, glob, os, copy
from pygame.locals import *
from utils import Display
import ConfigParser

from data import *
import utils

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

class SpriteHelper():
    def __init__(self):
        self.rect_cache = {}
        self.sprites_file = ConfigParser.ConfigParser()
        self.sprites_file.read([filepath(os.path.join(filepath('sprites'), file)) for file in glob.glob1(filepath('sprites'), '*.spr')])

    def load_rect(self, sprite_name, rect_name):
        '''Loading rect from file'''
        try:
            if not(self.rect_cache.has_key(sprite_name + rect_name)):
                x, y, w, h = self.sprites_file.get(sprite_name, rect_name).split(',')
                self.rect_cache[sprite_name + rect_name] = [int(x), int(y), int(w), int(h)]
            vals = self.rect_cache[sprite_name + rect_name]
            return Rect(vals[0], vals[1], vals[2], vals[3])
        except:
            raise SystemExit, "ERROR: Can't load rect '%s:%s'" % (sprite_name, rect_name)

    def get_fixed_rect(self, sprite_name, rect_name, base_rect, height = 0):
        '''Getting rect aligned with base rect center and added height'''
        rect = self.load_rect(sprite_name, rect_name)
        rect.centerx = base_rect.centerx + rect.x
        rect.centery = base_rect.centery + rect.y
        rect.move_ip(0, -height)
        return rect

    def get_fixed_sprite_rect(self, sprite_name, base_rect, image, fix_name='sprite'):
        '''Getting sprite rect aligned with base rect center'''
        x, y = self.sprites_file.get(sprite_name, fix_name).split(',')
        image_rect = image.get_rect(center = base_rect.center)
        image_rect.move_ip(int(x), int(y))
        return image_rect

    def load_anim(self, sprite_name, anim_name):
        file = self.sprites_file.get(sprite_name, anim_name)
        return load_anim(filepath(file))

    def load_image(self, sprite_name, image_name):
        file = self.sprites_file.get(sprite_name, image_name)
        return load_image(filepath(file))

class Simple(pygame.sprite.Sprite, SpriteHelper):
    draw_always = False
    def __init__(self, *groups):
        pygame.sprite.Sprite.__init__(self, groups)
        SpriteHelper.__init__(self)
        self.xoffset = 0
        self.yoffset = 0

    def draw(self, surf, rect):
        surf.blit(self.image, rect)

    def get_projection(self):
        return self.projection

    def kill(self):
        pygame.sprite.Sprite.kill(self)

    def get_height_rect(self):
        return self.get_projection()

    def get_sprite_rect(self):
        return self.get_height_rect()

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
        self.projection = self.image.get_rect(center = pos)

    def update(self):
        self.projection.move_ip(self.vx, self.vy)
        self.vx = self.vx + self.ax
        self.vy = self.vy + self.ay
        if not self.images:
            self.kill()
        else:
            self.image = self.images.pop(0)

class Collidable(pygame.sprite.Sprite, SpriteHelper):
    draw_always = False
    height = 0

    def __init__(self, *groups):
        pygame.sprite.Sprite.__init__(self, groups)
        SpriteHelper.__init__(self)
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
        oldr = copy.copy(self.get_projection())

        proj = self.get_projection()
        proj.move_ip(dx, dy)
        side = speed_to_side(dx, dy)

        for group in self.collision_groups:
            for spr in group:
                if spr.get_height_rect().colliderect(self.get_height_rect()) and spr.get_projection().colliderect(proj) and spr != self:
                    self.on_collision(side, spr, group, dx, dy)
                    spr.on_collision(side, self, group, dx, dy)

        return self.get_projection().left - oldr.left, self.get_projection().top - oldr.top

    def fall(self, dh):
        oldr = copy.copy(self.get_height_rect())

        height = self.get_height_rect()
        height.move_ip(0, dh)
        side = speed_to_side(0, dh)
        self.height -= dh

        for group in self.collision_groups:
            for spr in group:
                if spr.get_height_rect().colliderect(self.get_height_rect()) and spr.get_projection().colliderect(self.get_projection()) and spr != self:
                    self.on_fall_collision(side, spr, group, dh)
                    spr.on_fall_collision(side, self, group, dh)

        return self.get_height_rect().top - oldr.top

    def on_collision(self, side, sprite, group, dx, dy):
        pass

    def on_fall_collision(self, side, sprite, group, dy):
        pass

    def draw(self, surf, rect):
        surf.blit(self.image, rect)

    def hit(self):
        pass

    def get_projection(self):
        return self.projection

    def get_height_rect(self):
        return self.get_projection()

    def get_sprite_rect(self):
        return self.get_height_rect()

class Annihilable(Collidable):
    def __init__(self, hp):
        self.__max_hp = hp
        self.__hp = hp
        self.__on_die = []
        self.__on_hit = []

    def get_hp(self):
        return self.__hp

    def harm(self, amount):
        self.__hp -= amount
        for callback in self.__on_hit:
            callback()
        if self.__hp <= 0:
            self.die()

    def is_healable(self):
        return self.__hp < self.__max_hp

    def heal(self, amount):
        self.__hp += amount
        if self.__hp > self.__max_hp:
            self.__hp = self.__max_hp

    def die(self):
        for callback in self.__on_die:
            callback()

    def set_on_die(self, callback):
        self.__on_die.append(callback)
    def set_on_hit(self, callback):
        self.__on_hit.append(callback)

class Player(Annihilable):
    dfall = 0
    can_jump = 1
    speed = 3
    ammo_max = 100
    standing_on = None
    def __init__(self, pos, facing=1, height = 0):
        Collidable.__init__(self, self.groups)
        Annihilable.__init__(self, 5)

        self.group = 'player'
        self.type = 'loli'
        self.group_type = '%s.%s' % (self.group, self.type)

        self.gifs = {
            "idle": self.load_anim(self.group_type, 'texture_idle'),
            "jump": self.load_anim(self.group_type, 'texture_jump'),
            "fall": self.load_anim(self.group_type, 'texture_fall'),
            "walk": self.load_anim(self.group_type, 'texture_walk'),
            "duck": self.load_anim(self.group_type, 'texture_duck'),
            "duck_shoot": self.load_anim(self.group_type, 'texture_duck_shoot'),
            "stand_shoot":  self.load_anim(self.group_type, 'texture_stand_shoot'),
            "blast": self.load_anim(self.group_type, 'texture_blast'),
            "pain": self.load_anim(self.group_type, 'texture_hit'),
        }

        self.projection = self.load_rect(self.group_type, 'projection')
        self.projection.center = pos
        self.set_state("idle")
        self.image = self.right_images[0]
        self.facing = facing
        self.shoot_timer = 0
        self.hit_timer = 0
        self.__ammo = 20
        self.score = 0
        self.frame = 0
        self.state = "idle"
        self.height = height

        self.collide(self.game.static)
        self.collide(self.game.monsters)
        self.collide(self.game.triggers)
        self.collide(self.game.powerups)
        self.set_on_die(self.kill)
        self.set_on_hit(self.hit)

    def set_state(self, state = "idle"):
        self.state = state

        self.left_images = []
        self.right_images = self.gifs[state]
        for i in range(len(self.right_images)):
            self.left_images.append(pygame.transform.flip(self.right_images[i], 1, 0))

    def duck(self):
        self.set_state("duck")

    def has_ammo(self):
        return self.__ammo > 0
    def dec_ammo(self, amount=1):
        self.__ammo -= amount
        if self.__ammo < 0: self.__ammo = 0
    def inc_ammo(self, amount=1):
        self.__ammo += amount
        if self.__ammo > Player.ammo_max: self.__ammo = Player.ammo_max
    def get_ammo(self):
        return self.__ammo

    def fire(self, spritesArray):
        """
        Fire, push bullet sprite into spritesArray
        """
        if self.has_ammo() and (self.shoot_timer <= 0):
            if self.state in ["duck", "duck_shoot", "walk"]:
                height = self.height + 30
            else:
                height = self.height + 42
            pos = [self.get_projection().centerx, self.get_projection().centery]

            if self.facing > 0:
                pos[0] = self.get_height_rect().right
            else:
                pos[0] = self.get_height_rect().left

            shot = PlayerShot(pos, self.facing,
                self.gifs['blast'],
                self, height)
            spritesArray.change_layer(shot, shot.layer)
            self.__shoot()

    def __shoot(self):
        """
        Release the trigger of a gun
        """
        if self.shoot_timer <= 0:
            self.shoot_timer = 15
            if self.state in ["idle", "walk"]:
                self.state = "stand_shoot"
            elif self.state in ["duck"]:
                self.state = "duck_shoot"
        self.dec_ammo()

    def update(self):
        dx = 0
        dy = 0
        key = pygame.key.get_pressed()

        if self.state != "pain":

            # jumping and falling
            # must be before moving, for setting self.standing_on by collidable object
            dh = 0
            if self.dfall < 0:
                # trying to increase height
                dh = self.fall(self.dfall)
                self.dfall += 1
            # falling
            elif self.height > 0:
                # trying to decrease height
                dh = self.fall(self.dfall)
                self.dfall += 1
                # landing on ground
                if self.height <= 0:
                    self.height = 0
                    self.dfall = 0
                    self.can_jump = 1
                    dh = 0
                    #self.state = "idle"

            # Move
            if self.hit_timer <= 0:
                if self.state not in ['duck', 'duck_shoot']:
                    if key[K_LEFT]:
                        dx = -Player.speed
                        self.facing = dx
                        self.state = "walk"
                    elif key[K_RIGHT]:
                        dx = Player.speed
                        self.facing = dx
                        self.state = "walk"
                    if key[K_DOWN]:
                        # don't allow moving in air
                        if self.height == 0:
                            dy = Player.speed
                            self.state = "walk"
                        # but allow jump off from barrier
                        elif self.standing_on != None and self.can_jump:
                            self.can_jump = 0
                            self.projection.top = self.standing_on.get_projection().bottom
                            self.dfall = -7
                            self.standing_on = None
                    elif key[K_UP]:
                        # don't allow moving in air
                        if self.height == 0:
                            dy = -Player.speed
                            self.state = "walk"
                        # but allow jump off from barrier
                        elif self.standing_on != None and self.can_jump:
                            self.can_jump = 0
                            self.projection.bottom = self.standing_on.get_projection().top
                            self.dfall = -10
                            self.standing_on = None
                    elif key[K_LALT]:
                        if self.can_jump:
                            self.can_jump = 0
                            self.dfall = -10

            # Moving area
            if self.get_projection().left < 5:
                self.projection.left = 5
            if self.get_projection().bottom > 230:
                self.projection.bottom = 230
            if self.get_projection().top < 155:
                self.projection.top = 155

            if self.shoot_timer <= 0:
                if key[K_LCTRL]:
                    self.state = "duck"
                elif (dx == 0) and (dy == 0):
                    self.state = "idle"

            if dh < 0 and self.dfall <= 0:
                self.state = "jump"
            elif dh >= 0 and self.dfall > 0 and self.standing_on == None:
                self.state = "fall"

        else:
            if self.pain_timer > 0:
                self.pain_timer -= 1
            else:
                self.state = "idle"

        self.set_state(self.state)

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

        self.move(dx, dy)

        # Timers and frames
        self.frame -= 1
        self.hit_timer -= 1
        self.shoot_timer -= 1

        self.standing_on = None

    def on_collision(self, side, sprite, group, dx, dy):
        #self.projection.move_ip(-dx, -dy)
        pass

    def kill(self):
        pygame.sprite.Sprite.kill(self)
#        PlayerDie(self.rect.center, self.facing)

    def get_height_rect(self):
        if self.state in ['walk', 'idle', 'pain', 'stand_shoot', 'jump', 'fall']:
            rect = self.get_fixed_rect(self.group_type, 'height', self.projection, self.height)
        elif self.state in ['duck', 'duck_shoot']:
            rect = self.get_fixed_rect(self.group_type, 'height_duck', self.projection, self.height)
        return rect

    def hit(self):
        if self.state not in ('jump', 'fall'):
            self.set_state("pain")
            self.pain_timer = 15

    def get_sprite_rect(self):
        if self.state in ['walk', 'idle', 'pain', 'stand_shoot', 'jump', 'fall']:
            return self.get_fixed_sprite_rect(self.group_type, self.get_height_rect(), self.image)
        elif self.state in ['duck', 'duck_shoot']:
            return self.get_fixed_sprite_rect(self.group_type, self.get_height_rect(), self.image, 'sprite_duck')

    def draw(self, surf, rect):
        surf.blit(self.image, rect)

    def say(self, text):
        Balloon(self, text)

class PlayerShot(Collidable):
    def __init__(self, pos, facing, img, player, height):
        Collidable.__init__(self, self.groups)
        self.facing = facing
        self.left_images = []
        self.right_images = img
         # save copy of player's projection for calculating right shot projection
        self.player_proj = copy.copy(player.get_projection())
        for i in range(len(self.right_images)):
            self.left_images.append(pygame.transform.flip(self.right_images[i], 1, 0))
        self.image = self.right_images[0]
        #self.rect = self.image.get_rect(topleft = pos)
        self.projection = self.load_rect('blast', 'projection')
        self.void_image = load_image(filepath('sprites/void.png'))
        self.projection.center = pos
        self.height = height
        if self.facing > 0:
            self.speed = 5
        elif self.facing < 0:
            self.speed = -5
        self.layer = self.get_projection().bottom
        self.timer = 0

        self.collide(self.game.static)
        self.collide(self.game.monsters)

    def update(self):
        frame = self.timer % len(self.right_images)
        if self.timer > 10:
            if self.facing > 0:
                self.image = self.right_images[frame]
            elif self.facing < 0:
                self.image = self.left_images[frame]
        else:
            self.image = self.void_image
        if self.timer > 50:
            self.kill()
        self.timer += 1
        self.move(self.speed, 0)

    def kill(self):
        for i in range(15):
            if self.facing < 0:
                Particle(self.get_height_rect().midleft, random.randrange(-5, 6), random.randrange(-10, 0), 1, 1, 3,
                     [((58, 192, 253), (247, 254, 255), 7)])
            else:
                Particle(self.get_height_rect().midright, random.randrange(-5, 6), random.randrange(-10, 0), -1, 1, 3,
                     [((58, 192, 253), (247, 254, 255), 7)])
        pygame.sprite.Sprite.kill(self)

    def on_collision(self, side, sprite, group, dx, dy):
        try:
            sprite.harm(1)
        except:
            pass
        self.kill()

    def get_sprite_rect(self):
        if self.facing > 0:
            return self.get_fixed_sprite_rect('blast', self.get_height_rect(), self.image, 'sprite_right')
        else:
            return self.get_fixed_sprite_rect('blast', self.get_height_rect(), self.image, 'sprite_left')

    def get_height_rect(self):
        rect = copy.copy(self.projection)
        rect.move_ip(0, -self.height)
        return rect

class Fireball(Collidable):
    power = 1
    def __init__(self, pos, facing, img, initiator, height):
        Collidable.__init__(self, self.groups)
        self.facing = facing
        self.left_images = []
        self.right_images = img
        self.initiator_proj = copy.copy(initiator.get_projection())
        for i in range(len(self.right_images)):
            self.left_images.append(pygame.transform.flip(self.right_images[i], 1, 0))
        self.image = self.right_images[1]
        self.projection = self.load_rect('fireball', 'projection')
        self.projection.center = pos
        self.height = height
        if self.facing > 0:
            self.speed = 5
        elif self.facing < 0:
            self.speed = -5
        self.layer = self.get_projection().bottom
        self.timer = 0

        self.collide(self.game.static)
        self.collide(self.game.players)

    def update(self):
        if self.timer > 6:
            frame = len(self.right_images) - 1
        else:
            frame = self.timer/3
        if self.facing > 0: self.image = self.right_images[frame]
        elif self.facing < 0: self.image = self.left_images[frame]
        if self.timer > 50:
            self.kill()
        self.timer += 1
        self.move(self.speed, 0)

    def kill(self):
        for i in range(15):
            if self.facing < 0:
                Particle(self.get_height_rect().midleft, random.randrange(-5, 6), random.randrange(-10, 0), 1, 1, 3,
                     [((255, 247, 155), (252, 122, 45), 5)])
            else:
                Particle(self.get_height_rect().midright, random.randrange(-5, 6), random.randrange(-10, 0), -1, 1, 3,
                     [((255, 247, 155), (252, 122, 45), 5)])
        pygame.sprite.Sprite.kill(self)

    def on_collision(self, side, sprite, group, dx, dy):
        try:
            sprite.harm(Fireball.power)
        except:
            pass
        self.kill()

    def get_height_rect(self):
        rect = copy.copy(self.projection)
        rect.move_ip(0, -self.height)
        return rect

    def get_sprite_rect(self):
        if self.facing > 0:
            return self.get_fixed_sprite_rect('fireball', self.get_height_rect(), self.image, 'sprite_right')
        else:
            return self.get_fixed_sprite_rect('fireball', self.get_height_rect(), self.image, 'sprite_left')

class PowerUp(Collidable):
    types = ["ammo", "heart", "logo"]
    def __init__(self, pos, type, height=0):
        Collidable.__init__(self, self.groups)
        if type in self.types:
            self.group = 'powerup'
            self.type = type
            self.group_type = '%s.%s' % (self.group, self.type)
            self.images = self.load_anim(self.group_type, 'texture')
        else: raise SystemExit, "ERROR: Can't load powerup type: '%s'" % type
        self.image = self.images[0]
        self.projection = self.load_rect(self.group_type, 'projection')
        self.projection.center = pos
        self.frame = 0
        self.height = height

    def update(self):
        self.frame += 1
        self.image = self.images[self.frame/5 % len(self.images)]

    def kill(self):
        for i in range(10):
            Particle(self.get_height_rect().center, random.randrange(-3, 4), random.randrange(-10, 0), 0, 1, 3,
                 [((255, 255, 255), (255, 255, 255), 10)])
        pygame.sprite.Sprite.kill(self)

    def get_height_rect(self):
        return self.get_fixed_rect(self.group_type, 'height', self.projection, self.height)

    def collect(self):
        if self.type == "ammo":
            self.game.player.inc_ammo(25)
            self.kill()
        elif self.type == "heart" and self.game.player.is_healable():
            self.game.player.heal(1)
            self.kill()
        elif self.type == "logo":
            self.game.player.score += 25
            self.kill()

    def on_collision(self, side, sprite, group, dx, dy):
        self.collect()

    def on_fall_collision(self, side, sprite, group, dh):
        self.collect()

class DogAI():
    visibility_range = 225
    surrender_range = 500
    attack_range = 50
    player_path = []
    ai_timer = 0
    in_attack_point = False

    def update(self):
        if self.state == "idle":
            # checking player visibility and hear shot
            if abs(self.get_player_distance()) <= self.visibility_range:
                if self.is_looking_on_player() or self.player.shoot_timer > 0:
                    self.set_state("walk")
        elif self.state == "walk":
            if abs(self.get_player_distance()) >= self.surrender_range:
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
                if len(self.player_path) > 0:
                    # keep only last 30 path points
                    if len(self.player_path) > 30:
                        self.player_path = self.player_path[-30:]
                    path_point = self.player_path[0]

                    if abs(self.get_player_distance()) <= 50:
                        if self.xspeed > 0:
                            path_point[0] = self.player.get_projection().centerx - 50
                        elif self.xspeed < 0:
                            path_point[0] = self.player.get_projection().centerx + 50
                        path_point[1] = self.player.get_projection().centery

                    xdist = self.get_projection().centerx - path_point[0]
                    ydist = self.get_projection().centery - path_point[1]

                    if ydist in range(-10, 10) and abs(xdist) < self.attack_range:
                        self.in_attack_point = True
                    else:
                        self.in_attack_point = False

                    angle = math.atan2(ydist, xdist)
                    self.angle = int(270 - (angle * 180) / math.pi)

                    self.xspeed = abs(math.sin(math.radians(self.angle))*self.speed)
                    self.yspeed = abs(math.cos(math.radians(self.angle))*self.speed)

                    # if we in place - remove this point from path
                    if xdist >= 0 and xdist in range(-5, 5) and ydist >= 0 and ydist in range(-5, 5):
                        self.player_path = self.player_path[1:]

                    # manually check directions
                    if self.get_projection().centerx < path_point[0]:
                        self.xspeed = +self.xspeed
                    elif self.get_projection().centerx > path_point[0]:
                        self.xspeed = -self.xspeed
                    else:
                        xspeed = 0

                    if self.get_projection().centery < path_point[1]:
                        self.yspeed = +self.yspeed
                    elif self.get_projection().centery > path_point[1]:
                        self.yspeed = -self.yspeed
                    else:
                        yspeed = 0

                    # checking if player trying run around mob
                    if len(self.player_path) > 0:
                        if (self.get_projection().centerx < self.player_path[0][0] and self.player.get_projection().centerx < self.player_path[0][0] or
                            self.get_projection().centerx > self.player_path[0][0] and self.player.get_projection().centerx > self.player_path[0][0]):
                            self.player_path = []

        # adding new path points
        if self.state in ["walk"] and self.ai_timer % 5 == 0:
            path_point = [self.player.get_projection().centerx - self.player.get_projection().centerx % self.speed, self.player.get_projection().centery - self.player.get_projection().centery % self.speed]
            if (len(self.player_path) > 0):
                if (self.player_path[-1] != path_point):
                    self.player_path.append(path_point)
            else:
                self.player_path.append(path_point)
        self.ai_timer += 1

    def get_player_distance(self):
        return self.get_projection().centerx - self.player.get_projection().centerx

    def get_nearest_path_point(self):
        return self.player_path[0]

    def is_looking_on_player(self):
        if (self.facing > 0 and self.get_player_distance() < 0 or
            self.facing < 0 and self.get_player_distance() > 0):
            return True
        else:
            return False

class Betard(Annihilable, DogAI):
    speed = 1.5
    attack_pause = 0

    def __init__(self, pos, type = 1, facing = 1):
        Collidable.__init__(self, self.groups)
        Annihilable.__init__(self, 2)
        self.speed = self.speed
        self.group = 'enemy'
        self.type = 'betard'
        self.group_type = '%s.%s' % (self.group, self.type)

        self.gifs = {
            "idle": self.load_anim(self.group_type, 'texture_idle'),
            "walk": self.load_anim(self.group_type, 'texture_walk'),
            "pain": self.load_anim(self.group_type, 'texture_pain'),
            "attack": self.load_anim(self.group_type, 'texture_attack'),
            "fireball": self.load_anim(self.group_type, 'texture_fireball'),
        }

        self.set_state("idle")
        self.timer = random.randrange(30)
        self.xspeed = 0
        self.yspeed = 0
        self.decision = 0
        self.type = type
        self.set_state()
        self.image = self.left_images[0]
        self.images = None
        self.projection = self.load_rect(self.group_type, 'projection')
        self.projection.center = pos

        self.facing = facing
        self.set_image()

        self.collide(self.game.static)
        self.collide(self.game.players)
        self.collide(self.game.monsters)
        self.set_on_die(self.kill)
        self.set_on_hit(self.hit)

    def set_state(self, state = "idle"):
        self.state = state
        self.right_images = []
        self.left_images = self.gifs[state]
        for i in range(len(self.left_images)):
            self.right_images.append(pygame.transform.flip(self.left_images[i], 1, 0))

    def kill(self):
        if random.randrange(5) % 2 == 0:
            type = random.randrange(len(PowerUp.types))
            PowerUp(self.get_projection().center, PowerUp.types[type], 0)
        pygame.sprite.Sprite.kill(self)

    def update(self):
        DogAI.update(self)

        if self.xspeed > 0:
            self.facing = 1
        elif self.xspeed < 0:
            self.facing = -1

        self.set_image()
        if self.state == "attack":
            if self.attack_timer == 0:
                self.set_state("walk")
                self.timer = random.randrange(30)
                self.attack_pause = 60
            self.attack_timer -= 1
            if self.attack_timer == 20:
                height = self.height + 50
                pos = [self.get_projection().centerx, self.get_projection().centery]
                if self.facing > 0:
                    pos[0] = self.get_height_rect().right
                if self.facing < 0:
                    pos[0] =self.get_height_rect().left
                Fireball(pos, self.facing, self.gifs["fireball"], self, height)

        else:
            if self.in_attack_point:
                if self.attack_pause == 0:
                    self.xspeed = 0
                    self.yspeed = 0
                    self.set_state("attack")
                    self.attack_timer = 80
                    self.timer = 0
                else:
                    self.attack_pause -= 1
        if self.state == "pain":
            if self.pain_timer == 0:
                self.set_state("walk")
            self.pain_timer -= 1

        self.timer += 1
        self.move(self.xspeed, self.yspeed)

    def on_collision(self, side, sprite, group, dx, dy):
        self.get_projection().move_ip(-dx, -dy)
        # start walking if player touching
        if sprite in self.game.players:
            if self.state != "attack":
                self.set_state("walk")

    def hit(self):
        if self.state != "attack":
            if random.randrange(10) in range(4):
                Balloon(self, "OUCH!!!")
            self.set_state("pain")
            self.xspeed = 0
            self.yspeed = 0
            self.pain_timer = 10

    def set_image(self):
        if self.facing > 0:
            self.image = self.right_images[self.timer/9 % len(self.right_images)]
        elif self.facing < 0:
            self.image = self.left_images[self.timer/9 % len(self.left_images)]

    def get_height_rect(self):
        return self.get_fixed_rect(self.group_type, 'height', self.projection, self.height)

    def get_sprite_rect(self):
        return self.get_fixed_sprite_rect(self.group_type, self.get_height_rect(), self.image)

class Static(Collidable):
    def __init__(self, pos, type, height=0):
        Collidable.__init__(self, self.groups)
        self.group = 'static'
        self.type = type
        self.group_type = '%s.%s' % (self.group, self.type)
        self.image = self.load_image(self.group_type, 'texture')
        self.projection = self.load_rect(self.group_type, 'projection')
        self.projection.center = pos
        self.height = height

    def on_collision(self, side, sprite, group, dx, dy):
        sprite.projection.move_ip(-dx, -dy)

    def get_height_rect(self):
        return self.get_fixed_rect(self.group_type, 'height', self.projection, self.height)

    def get_sprite_rect(self):
        return self.get_fixed_sprite_rect(self.group_type, self.get_height_rect(), self.image)

    def on_fall_collision(self, side, sprite, group, dh):
        # something landed to surface so bump it back
        sprite.height -= self.get_height_rect().top - sprite.get_height_rect().bottom
        sprite.can_jump = 1
        sprite.dfall = 0
        if side == 2:
            sprite.standing_on = self
            # fix sprite projection
            d = sprite.projection.bottom - self.projection.bottom
            sprite.projection.bottom = self.projection.bottom
            sprite.height -= d

class Balloon(Simple):
    def __init__(self, initiator, text):
        Simple.__init__(self, self.groups)
        self.initiator = initiator
        self.text = text
        self.projection = Rect(0, 0, 0, 0)
        self.timer = 0
        self.font = pygame.font.Font(filepath("font.ttf"), 7)
        self.update()

    def update(self):
        self.projection.center = self.initiator.get_projection().center
        self.height = self.initiator.height + self.initiator.get_height_rect().height
        self.timer += 1
        if self.timer < 30:
            return
        self.kill()

    def draw(self, surf, rect):
        surf.blit(self.image, rect)
        ren = self.font.render(self.text, 1, (0, 0, 0))
        surf.blit(ren, (rect.centerx - ren.get_width() / 2,
                        rect.centery-ren.get_height() / 2 - 2))

    def get_sprite_rect(self):
        r = self.image.get_rect(center=self.get_projection().center)
        r.move_ip(0, -self.height)
        return r

class SpawnTrigger(Collidable):
    def __init__(self, projection, spawnobj, spawnx, spawny, spawndir):
        Collidable.__init__(self, self.groups)
        self.projection = projection
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

    def get_height_rect(self):
        rect = copy.copy(self.get_projection())
        rect.move_ip(0, -self.height)
        return rect

class DialogTrigger(Collidable):
    def __init__(self, projection, dialog):
        Collidable.__init__(self, self.groups)
        self.projection = projection
        self.dialog = dialog

    def draw(self, surf, rect):
        pass

    def hit(self):
        self.set_state("pain")
        self.pain_timer = 15

    def activate(self):
        self.game.start_dialog(DialogBar(self.dialog))
        self.kill()

    def on_collision(self, side, sprite, group, dx, dy):
        self.activate()

    def on_fall_collision(self, side, sprite, group, dy):
        self.activate()

    def get_height_rect(self):
        rect = copy.copy(self.get_projection())
        rect.move_ip(0, -self.height)
        return rect

class DialogBar(Simple):
    draw_always = True

    def __init__(self, dialog):
        Simple.__init__(self, self.groups)
        self.dialog = dialog

        dialog_file = ConfigParser.ConfigParser()
        dialog_file.read(filepath("dialogs"))
        self.text = []
        if dialog in dialog_file.sections():
            try:
                self.face1 = load_image(dialog_file.get(dialog, "face1").strip())
                self.face2 = load_image(dialog_file.get(dialog, "face2").strip())
            except:
                raise SystemExit, "ERROR: Can't load faces for dialog '%s'" % dialog

            try:
                string_n = 1
                option = "string%s" % string_n
                while dialog_file.has_option(dialog, option):
                    self.text.append(dialog_file.get(dialog, option).strip())
                    string_n += 1
                    option = "string%s" % string_n
                if string_n == 1:
                    self.text.append("")
            except:
                raise SystemExit, "ERROR: Can't load strings for dialog '%s'" % dialog

        self.projection = self.image.get_rect(topleft = (0, 0))
        self.projection.centerx = Display.get_instance().get_rect().centerx
        self.font = pygame.font.Font(filepath("font.ttf"), 7)
        self.part = 0

    def continue_dialog(self):
        if self.part + 1 >= len(self.text):
            self.kill()
            self.game.end_dialog()
        else:
            self.part += 1

    def update(self):
        pass

    def draw(self, surf, rect):
        surf.blit(self.image, self.get_sprite_rect())
        surf.blit(self.face1, (self.get_sprite_rect().x + 5, self.get_sprite_rect().y + 5))
        surf.blit(self.face2, (self.get_sprite_rect().x + 283, self.get_sprite_rect().y + 5))
        ren = self.font.render(self.text[self.part], 1, (255, 255, 255))
        surf.blit(ren, (self.get_sprite_rect().centerx-ren.get_width()/2, self.get_sprite_rect().centery-ren.get_height()/2))