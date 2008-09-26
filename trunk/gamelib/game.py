#! /usr/bin/env python

import sys, os
import random

import pygame
from pygame.locals import *

from data import *
from sprites import *
from level import *

def RelRect(actor, camera):
    return Rect(actor.rect.x-camera.rect.x, actor.rect.y-camera.rect.y, actor.rect.w, actor.rect.h)

class Camera(object):
    def __init__(self, player, width):
        self.player = player
        self.rect = pygame.display.get_surface().get_rect()
        self.world = Rect(0, 0, width, 480)
        self.rect.center = self.player.rect.center
    def update(self):
        if self.player.rect.centerx > self.rect.centerx+32:
            self.rect.centerx = self.player.rect.centerx-32
        if self.player.rect.centerx < self.rect.centerx-32:
            self.rect.centerx = self.player.rect.centerx+32
        if self.player.rect.centery > self.rect.centery+32:
            self.rect.centery = self.player.rect.centery-32
        if self.player.rect.centery < self.rect.centery-32:
            self.rect.centery = self.player.rect.centery+32
        self.rect.clamp_ip(self.world)
    def draw_sprites(self, surf, sprites):
        for s in sprites:
            if s.rect.colliderect(self.rect):
                surf.blit(s.image, RelRect(s, self))

class Game(object):

    def __init__(self, screen, continuing=False):
        
        self.screen = screen
        self.sprites = pygame.sprite.OrderedUpdates()
        self.shots = pygame.sprite.OrderedUpdates()
        self.monsters = pygame.sprite.OrderedUpdates()
        self.powerups = pygame.sprite.OrderedUpdates()
        self.players = pygame.sprite.OrderedUpdates()
        
        PowerUp.groups = self.sprites, self.powerups
        Player.groups = self.sprites, self.players
        PlayerShot.groups = self.sprites, self.shots
        Betard.groups = self.sprites, self.monsters

        # Load animation once
        self.heart = load_image("heart_bar.gif")
        self.cells = load_image("cell_bar.gif")
        
        Player.gifs = {
            "idle": load_anim("loli_idle.gif"),
            "jump": load_anim("loli_jump.gif"),
            "walk": load_anim("loli_walk.gif"),
            "duck": load_anim("loli_duck.gif"),
            "duck_shoot": load_anim("loli_duck_shoot.gif"),
            "stand_shoot": load_anim("loli_stand_shoot.gif"),
            "blast": load_anim("blast.gif"),
        }
        PowerUp.gifs = {
            "heart": load_anim("heart.gif"),
            "ammo": load_anim("ammo.gif"),
            "logo": load_anim("logo.gif"),
        }
        Betard.gifs = {
            "idle": load_anim("betard_idle.gif"),
            "walk": load_anim("betard_walk.gif"),
        }
        
        self.score = 0
        self.lives = 3
        self.lvl   = 1
        
        self.clock = pygame.time.Clock()
        self.level = Level(self.lvl)
        self.bg = self.level.bg
        self.player = Player((100, 250))
        self.camera = Camera(self.player, self.level.get_size()[0])
        self.font = pygame.font.Font(filepath("font.ttf"), 16)
        
        self.running = 1
        self.music = "because_she_said_no.ogg"
        play_music(self.music, 0.5)
        
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
                        if (self.player.ammo > 0) and (self.player.shoot_timer <= 0):
                            if self.player.state in ["duck", "walk"]:
                                PlayerShot(
                                    self.player.rect.center,
                                    self.player.facing, 
                                    self.player.gifs["blast"]
                                )
                            else:
                                PlayerShot(
                                    (self.player.rect.center[0], self.player.rect.center[1]-25),
                                    self.player.facing, 
                                    self.player.gifs["blast"]
                                )
                            self.player.shoot()
                    if event.key == K_LCTRL:
                        self.player.state = "duck"
            
            for powerup in self.powerups:
                if self.player.rect.colliderect(powerup.rect):
                    # Pickup animation
                    #PowerUpDie(c.rect.center)
                    if powerup.type == "ammo":
                        self.player.ammo += 25
                        powerup.kill()
                    elif powerup.type == "heart" and self.player.hp < 5:
                        self.player.hp += 1
                        powerup.kill()
                    elif powerup.type == "logo":
                        self.player.score += 25
                        powerup.kill()
            
            # Updating all sprites
            for s in self.sprites:
                s.update()
                
            # Scrolling background
            self.screen.blit(self.bg, ((-self.camera.rect.x)%800, 0))
            self.screen.blit(self.bg, ((-self.camera.rect.x)%800 + 800, 0))
            self.screen.blit(self.bg, ((-self.camera.rect.x)%800 - 800, 0))
            self.camera.draw_sprites(self.screen, self.sprites)
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
        ren = self.font.render("FPS: %d" % self.clock.get_fps(), 1, (255, 255, 255))
        self.screen.blit(ren, (22, 80))