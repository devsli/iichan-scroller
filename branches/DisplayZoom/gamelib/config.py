import ConfigParser

#-default-values------------------------------#
fullscreen = 0
widescreen = 0
debug = 0
music = 1
#---------------------------------------------#

def loadSettings(path):
    global fullscreen, widescreen, debug, music

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
