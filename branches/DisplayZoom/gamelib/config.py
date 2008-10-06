import ConfigParser

#-default-values------------------------------#
fullscreen = 0
widescreen = 0
debug = 0
music = 1
zoom = 2
#---------------------------------------------#

def loadSettings(path):
    global zoom, fullscreen, widescreen, debug, music

    config = ConfigParser.ConfigParser()
    config.read(path)

    try: fullscreen = int(config.get("main", "fullscreen"))
    except: pass

    try: widescreen = int(config.get("main", "widescreen"))
    except: pass

    try: debug = int(config.get("main", "debug"))
    except: pass

    try: music = int(config.get("main", "music"))
    except: pass

    try: zoom = int(config.get("main", "zoom"))
    except: pass