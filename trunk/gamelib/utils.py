import sys, inspect

class EmergencyExit(SystemExit):
    '''SystemExit exception with message and traceback'''
    def __init__(self, msg):
        SystemExit.__init__(self)
        trace = ''
        for line in inspect.stack()[1:]:
            args = tuple(list(line[1:3]) + list((line[4][0].strip(),)))
            trace += '  [%s:%d -> %s]\n' % args
        sys.stderr.write('Emergency exit:\n  %s\n' % msg)
        sys.stderr.write('Traceback:\n')
        sys.stderr.write(trace)
