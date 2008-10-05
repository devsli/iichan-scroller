#! /usr/bin/env python

import sys, os
import random

import pygame
from pygame.locals import *

from data import *
from sprites import *
from level import *


def RelRect(rect, camera):
    return Rect(rect.x - camera.rect.x, rect.y - camera.rect.y, rect.w, rect.h)

class Camera(object):
    def __init__(self, player, width):
        self.player = player
        self.rect = pygame.display.get_surface().get_rect()
        self.world = Rect(0, 0, width, 480)
        self.rect.center = self.player.get_height_rect().center
    def update(self):
        if self.player.get_height_rect().centerx > self.rect.centerx+32:
            self.rect.centerx = self.player.get_height_rect().centerx-32
        if self.player.get_height_rect().centerx < self.rect.centerx-32:
            self.rect.centerx = self.player.get_height_rect().centerx+32
        if self.player.get_height_rect().centery > self.rect.centery+32:
            self.rect.centery = self.player.get_height_rect().centery-32
        if self.player.get_height_rect().centery < self.rect.centery-32:
            self.rect.centery = self.player.get_height_rect().centery+32
        self.rect.clamp_ip(self.world)

    def draw_sprites(self, surf, sprites):
        for s in sprites:
            if s.get_sprite_rect().colliderect(self.rect) or s.draw_always:
                s.draw(surf, RelRect(s.get_sprite_rect(), self))

class Game(object):
    dialog_mode = False

    def __init__(self, screen, config, continuing=False):
        self.screen = screen
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
        self.font = pygame.font.Font(filepath("font.ttf"), 16)
        self.debug_font = pygame.font.Font(filepath("font.ttf"), 10)

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
        self.screen.blit(ren, (180-ren.get_width()/2, 135))
        pygame.display.flip()
        pygame.time.wait(2500)

    def gameover_screen(self):
        self.end()

    def winrar(self):
        self.draw_stats()
        ren = self.font.render("You are WINRAR!", 1, (255, 255, 255), (0, 0, 0))
        self.screen.blit(ren, (320-ren.get_width()/2, 235))
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
                        # FIXME: move into Player class
                        if not self.dialog_mode:
                            if (self.player.ammo > 0) and (self.player.shoot_timer <= 0):
                                if self.player.state in ["duck", "duck_shoot", "walk"]:
                                    height = self.player.height + 60
                                else:
                                    height = self.player.height + 85
                                pos = [self.player.get_projection().centerx, self.player.get_projection().centery]

                                if self.player.facing > 0:
                                    pos[0] = self.player.get_height_rect().right
                                else:
                                    pos[0] = self.player.get_height_rect().left

                                shot = PlayerShot(pos, self.player.facing,
                                                  self.player.gifs['blast'],
                                                  self.player, height)
                                self.sprites.change_layer(shot, shot.layer)
                                self.player.shoot()
                        else:
                            self.dialog.continue_dialog()
                    # FIXME: move into Player class
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
            pygame.draw.rect(self.screen, (0, 0, 0),  Rect(0, 0, self.config.width, 480), 0)
            # draw 3 bg layers
            bglayer_speed = [1, 0.9, 0.2]
            for bglayer_num in range(2, -1, -1):
                for bg in self.level.backgrounds_layers[bglayer_num]:
                    rect = RelRect(bg.texture.get_rect(), self.camera)
                    rect.x = bg.x - self.camera.rect.x * bglayer_speed[bglayer_num]
                    if rect.colliderect(Rect(0, 0, self.config.width, 480)):
                        self.screen.blit(bg.texture, (bg.x - self.camera.rect.x * bglayer_speed[bglayer_num], bg.y))

            self.camera.draw_sprites(self.screen, self.sprites)

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
                    pygame.draw.rect(self.screen, (0, 255, 0),  RelRect(sprite.get_projection(), self.camera), 1)
                    pygame.draw.rect(self.screen, (255, 0, 0),  RelRect(sprite.get_height_rect(), self.camera), 1)
                    ren = self.debug_font.render("%d" % self.sprites.get_layer_of_sprite(sprite), 1, (255, 255, 255))
                    self.screen.blit(ren, RelRect(sprite.get_height_rect(), self.camera))

                for trigger in self.triggers:
                    pygame.draw.rect(self.screen, (0, 255, 0),  RelRect(trigger.get_projection(), self.camera), 1)
                    pygame.draw.rect(self.screen, (0, 0, 255),  RelRect(trigger.get_height_rect(), self.camera), 1)

                for betard in self.monsters:
                    ren = self.debug_font.render("Speed: %d %d" % (betard.xspeed, betard.yspeed), 1, (255, 255, 255))
                    self.screen.blit(ren, (RelRect(betard.get_height_rect(), self.camera)[0], RelRect(betard.get_height_rect(), self.camera)[1]+16))

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

            pygame.display.flip()
            #pygame.time.wait(2)

    def draw_stats(self):
        # HP
        for i in range(self.player.hp):
            self.screen.blit(self.heart, (self.screen.get_rect().width - 60 - i*30, 16))
        # Ammo
        self.screen.blit(self.cells, (22, 16))
        ren = self.font.render("%d" % self.player.ammo, 1, (255, 255, 255))
        self.screen.blit(ren, (90-ren.get_width(), 26))
        # Score
        ren = self.font.render("%09d" % self.player.score, 1, (255, 255, 255))
        self.screen.blit(ren, (self.screen.get_rect().centerx-ren.get_width()/2, 26))
        # Out of ammo?
        if self.player.ammo == 0:
            ren = self.font.render("Out of ammo!", 1, (255, 255, 255))
            self.screen.blit(ren, (self.screen.get_rect().centerx-ren.get_width()/2, 80))
        # FPS
        if self.config.debug:
            ren = self.font.render("FPS: %d" % self.clock.get_fps(), 1, (255, 255, 255))
            self.screen.blit(ren, (22, 80))

    def start_dialog(self, dialog):
        self.dialog = dialog
        self.dialog_mode = True

    def end_dialog(self):
        self.dialog_mode = False
        self.dialog = None
