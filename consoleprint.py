import builtins
import InGameConsole

inGameConsole = None

def setUpConsole(conn,height=200,width=800):
    global inGameConsole
    inGameConsole = InGameConsole.InGameConsole(conn,height,width)

def getConsole():
    global inGameConsole
    return inGameConsole

def removeConsole():
    global inGameConsole
    inGameConsole.remove()
    inGameConsole = None

def print(*args):
    global inGameConsole
    for arg in args:
        if (inGameConsole):
            inGameConsole.printToConsole(arg)
    builtins.print(*args)
#TODO: handle multi line prints

#Intercept print function to send output to InGameConsole
# def dprint(*args):
#     inGameConsole.printToConsole(*args)
#     __builtins__['oldprint'](*args)
# #if 'oldprint' not in __builtins__:
# __builtins__['oldprint'] = __builtins__['print']
# __builtins__['print'] = dprint
# def print(*args):
#     for arg in args:
#         inGameConsole.printToConsole(arg)
#     builtins.print(*args)
#consoleprint.print("test")