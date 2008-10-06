#! /usr/bin/env python

import sys, os
import random
import config

import pygame
from pygame.locals import *

from data import *
from sprites import *
from level import *
from utils import Display


def RelRect(rect, camera):
    return Rect(rect.x - camera.rect.x, rect.y - camera.rect.y, rect.w, rect.h)

class Camera(object):
    def __init__(self, player, width):
        self.player = player
        self.rect = Display().get_instance().get_surface().get_rect()
        self.world = Rect(0, 0, width, 240)
        self.rect.center = self.player.get_height_rect().center
    def update(self):
        if self.player.get_height_rect().centerx > self.rect.centerx+16:
            self.rect.centerx = self.player.get_height_rect().centerx-16
        if self.player.get_height_rect().centerx < self.rect.centerx-16:
            self.rect.centerx = self.player.get_height_rect().centerx+16
        if self.player.get_height_rect().centery > self.rect.centery+16:
            self.rect.centery = self.player.get_height_rect().centery-16
        if self.player.get_height_rect().centery < self.rect.centery-16:
            self.rect.centery = self.player.get_height_rect().centery+16
        self.rect.clamp_ip(self.world)

    def draw_sprites(self, sprites):
        for s in sprites:
            if s.get_sprite_rect().colliderect(self.rect) or s.draw_always:
                s.draw(Display.get_instance().get_surface(), RelRect(s.get_sprite_rect(), self))

class Game(object):
    dialog_mode = False

    def __init__(self, config, continuing=False):
        self.config = config
        self.sprites = pygame.sprite.LayeredUpdates()
        self.shots = pygame.sprite.LayeredUpdates()
        self.monsters = pygame.sprite.LayeredUpdates()
        self.powerups = pygame.sprite.LayeredUpdates()
        self.players = pygame.sprite.LayeredUpdates()
        self.static = pygame.sprite.LayeredUpdates()
        self.notstatic = pygame.sprite.LayeredUpdates()
        self.particles = pygame.sprite.LayeredUpdates()
        self.triggers = pygame.sprite.LayeredUpdates()
        self.topmost = pygame.sprite.LayeredUpdates()

        PowerUp.groups = self.sprites, self.powerups, self.notstatic
        Player.groups = self.sprites, self.players, self.notstatic
        PlayerShot.groups = self.sprites, self.shots, self.notstatic
        Betard.groups = self.sprites, self.monsters, self.notstatic
        Static.groups = self.sprites, self.static
        Balloon.groups = self.sprites, self.topmost
        Particle.groups = self.sprites, self.particles, self.topmost
        SpawnTrigger.groups = self.triggers
        DialogTrigger.groups = self.triggers
        DialogBar.groups = self.sprites
        Fireball.groups = self.sprites, self.shots, self.notstatic

        Collidable.game = self
        Simple.game = self

        # Load animation once
        self.heart = load_image("heart_bar.gif")
        self.cells = load_image("cell_bar.gif")

        Balloon.image = load_image("balloon.png")
        DialogBar.image = load_image("dialog_bar.png")

        self.score = 0
        self.lives = 3
        self.lvl   = 1

        self.clock = pygame.time.Clock()
        self.level = Level(self.lvl)
        self.player = self.level.player
        self.camera = Camera(self.player, self.level.get_size()[0])
        self.font = pygame.font.Font(filepath("font.ttf"), 8)
        self.debug_font = pygame.font.Font(filepath("font.ttf"), 5)

        DogAI.player = self.player

        self.running = 1
        if self.config.music == 1:
            self.music = "because_she_said_no.ogg"
            play_music(self.music, 0.5)

        # set layers for static sprites
        for sprite in self.sprites:
            self.sprites.change_layer(sprite, sprite.get_projection().centery)

        self.main_loop()

    def end(self):
        self.running = 0

    def redo_level(self):
        if self.running:
            self.clear_sprites()
            self.level = Level(self.lvl)
            self.player = Player((0, 0))
            self.camera = Camera(self.player, self.level.get_size()[0])

    def show_death(self):
        ren = self.font.render("Why so slow?", 1, (255, 255, 255))
        self.screen.blit(ren, (90-ren.get_width()/2, 67))
        pygame.display.flip()
        pygame.time.wait(2500)

    def gameover_screen(self):
        self.end()

    def winrar(self):
        self.draw_stats()
        ren = self.font.render("You are WINRAR!", 1, (255, 255, 255), (0, 0, 0))
        self.screen.blit(ren, ((160)-ren.get_width()/2, 117))
        pygame.display.flip()
        pygame.time.wait(2500)

    def clear_sprites(self):
        for sprite in self.sprites:
            pygame.sprite.Sprite.kill(sprite)

    def main_loop(self):

        while self.running:
            self.clock.tick(60)
            self.camera.update()

            # Reacting on keystrokes
            for event in pygame.event.get():
                if event.type == QUIT:
                    sys.exit()
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        sys.exit()
                    elif event.key == K_SPACE:
                        if not self.dialog_mode:
                            self.player.fire(self.sprites)
                        else:
                            self.dialog.continue_dialog()
                    if event.key == K_LCTRL:
                        self.player.state = "duck"
                    if event.key == K_d:
                        self.config.debug = not self.config.debug

            # Updating all sprites
            if not self.dialog_mode:
                for s in self.sprites:
                    s.update()
            else:
                self.dialog.update()

            # FIXME: may be move cleaning into debug (useful during design/development,
            # not necessary in release)
            Display.get_instance().draw_rect((0, 0, 0),  Rect(0, 0, config.width, 240), 0)
            # draw 3 bg layers
            bglayer_speed = [1, 0.9, 0.2]
            for bglayer_num in range(2, -1, -1):
                for bg in self.level.backgrounds_layers[bglayer_num]:
                    rect = RelRect(bg.texture.get_rect(), self.camera)
                    rect.x = bg.x - self.camera.rect.x * bglayer_speed[bglayer_num]
                    if rect.colliderect(Rect(0, 0, config.width, 240)):
                        Display.get_instance().blit(bg.texture, (bg.x - self.camera.rect.x * bglayer_speed[bglayer_num], bg.y))

            self.camera.draw_sprites(self.sprites)

            # changing layer for moving objects
            for sprite in self.notstatic:
                new_layer = RelRect(sprite.get_projection(), self.camera).bottom
                if new_layer != self.sprites.get_layer_of_sprite(sprite):
                    self.sprites.change_layer(sprite, new_layer)

            # move some sprites to front layer
            for sprite in self.topmost:
                self.sprites.move_to_front(sprite)

            # show bboxes for debugging and easy objects creating
            if self.config.debug:
                for sprite in self.sprites:
                    Display.get_instance().draw_rect((0, 255, 0),  RelRect(sprite.get_projection(), self.camera), 1)
                    Display.get_instance().draw_rect((255, 0, 0),  RelRect(sprite.get_height_rect(), self.camera), 1)
                    ren = self.debug_font.render("%d" % self.sprites.get_layer_of_sprite(sprite), 1, (255, 255, 255))
                    
                    Display.get_instance().blit(ren, RelRect(sprite.get_height_rect(), self.camera))

                for trigger in self.triggers:
                    Display.get_instance().draw_rect((0, 255, 0),  RelRect(trigger.get_projection(), self.camera), 1)
                    Display.get_instance().draw_rect((0, 0, 255),  RelRect(trigger.get_height_rect(), self.camera), 1)

                for betard in self.monsters:
                    ren = self.debug_font.render("Speed: %d %d" % (betard.xspeed, betard.yspeed), 1, (255, 255, 255))
                    Display.get_instance().blit(ren, (RelRect(betard.get_height_rect(), self.camera)[0], RelRect(betard.get_height_rect(), self.camera)[1]+8))

            if not self.dialog_mode:
                self.draw_stats()

            # To be or not to be?
            if not self.player.alive() and not self.playerdying:
                if self.lives <= 0:
                    self.gameover_screen()
                else:
                    self.show_death()
                    self.lives -= 1
                    self.redo_level()

            Display.get_instance().flip()
            #pygame.display.flip()
            #pygame.time.wait(2)

    def draw_stats(self):
        # HP
        for i in range(self.player.hp):
            Display.get_instance().blit(self.heart, (Display.get_instance().get_rect().width - 30 - i*15, 8))
        # Ammo
        Display.get_instance().blit(self.cells, (22, 16))
        ren = self.font.render("%d" % self.player.ammo, 1, (255, 255, 255))
        Display.get_instance().blit(ren, (90-ren.get_width(), 13))
        # Score
        ren = self.font.render("%09d" % self.player.score, 1, (255, 255, 255))
        Display.get_instance().blit(ren, (Display.get_instance().get_rect().centerx-ren.get_width()/2, 13))
        # Out of ammo?
        if self.player.ammo == 0:
            ren = self.font.render("Out of ammo!", 1, (255, 255, 255))
            Display.get_instance().blit(ren, (Display.get_instance().get_rect().centerx-ren.get_width()/2, 40))
        # FPS
        if self.config.debug:
            ren = self.font.render("FPS: %d" % self.clock.get_fps(), 1, (255, 255, 255))
            Display.get_instance().blit(ren, (11, 40))

    def start_dialog(self, dialog):
        self.dialog = dialog
        self.dialog_mode = True

    def end_dialog(self):
        self.dialog_mode = False
        self.dialog = None
