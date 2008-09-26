import ConfigParser

#-default-values------------------------------#
fullscreen = 0
widescreen = 0
show_bboxes = 0
#---------------------------------------------#

def loadSettings(path):
    global fullscreen, widescreen, show_bboxes

    config = ConfigParser.ConfigParser()
    config.read(path)

    try: fullscreen = int(config.get("main", "fullscreen"))
    except: pass

    try: widescreen = int(config.get("main", "widescreen"))
    except: pass

    try: show_bboxes = int(config.get("main", "show_bboxes"))
    except: pass
