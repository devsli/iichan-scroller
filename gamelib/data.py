'''Simple data loader module.

Loads data files from the "data" directory shipped with a game.

Enhancing this to handle caching etc. is left as an exercise for the reader.
'''

import os, pygame
from PIL import Image
from pygame.locals import *

data_py = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.normpath(os.path.join(data_py, '..', 'data'))

def filepath(filename):
    '''Determine the path to a file in the data directory.
    '''
    return os.path.join(data_dir, filename)

def load(filename, mode='rb'):
    '''Open a file in the data directory.

    "mode" is passed as the second arg to open().
    '''
    return open(os.path.join(data_dir, filename), mode)

def to_triplets(palette):
    return [palette[i:i+3] for i in range(0, len(palette), 3)]

def load_anim(file, mode="P"):
    img = Image.open(filepath(file))
    palette = to_triplets(img.getpalette())
    frames = []; i = 0
    while True:
        try:
            img.seek(i)
        except EOFError:
            break
        pg_surf = pygame.image.fromstring(img.tostring(), img.size, mode)
        pg_surf.set_palette(palette)
        pg_surf = pygame.transform.scale(pg_surf, (pg_surf.get_width()*2, pg_surf.get_height()*2))
        top_left_color = pg_surf.get_at((0, 0))
        if top_left_color == (255, 255, 255, 255):
            pg_surf.set_colorkey(img.info['transparency'])
        else:
            pg_surf.set_colorkey(top_left_color)
        frames.append(pg_surf.convert_alpha())
        i += 1
    print file, "loaded"
    frames.reverse()
    return frames

def load_image(filename):
	filename = filepath(filename)
	try:
		image = pygame.image.load(filename)
		image = pygame.transform.scale(image, (image.get_width()*2, image.get_height()*2))
	except pygame.error:
		raise SystemExit, "Unable to load: " + filename
	return image.convert_alpha()

def load_sound(filename, volume=0.5):
    filename = filepath(filename)
    try:
        sound = pygame.mixer.Sound(filename)
        sound.set_volume(volume)
    except:
        raise SystemExit, "Unable to load: " + filename
    return sound

def play_music(filename, volume=0.5, loop=-1):
    filename = filepath(filename)
    try:
        pygame.mixer.music.load(filename)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loop)
    except:
        raise SystemExit, "Unable to load: " + filename

def stop_music():
    pygame.mixer.music.stop()
