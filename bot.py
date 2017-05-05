#!/usr/local/bin/python

import socket
import re
import time

# irc-related constants
server = "****"  
port = 6667
channels = ["#****", ]
botnick = "****"
ownernick = '****'

# make stuff that lets you talk to IRC
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # defines the socket


namelist = {}
nameop = []
strdic = {}
namestrdic = {}
ndfile = 'ndfile.txt'
sdfile = 'sdfile.txt'
ownerfile = 'ownerfile.txt'
try:
    sdf = open(sdfile, 'r')
    strdic = eval(sdf.read())
    sdf.close()
except:
    pass

try:
    ndf = open(ndfile, 'r')
    namestrdic = eval(ndf.read())
    ndf.close()
except:
    pass
PRIVMSG = 'PRIVMSG'
NAMEINFO = '353'
NAMEEND = '366'


def connect_loop():
    print "Establishing connection to [%s]" % (server)
    # Connect
    irc.connect((server, port))

    # send info about yourself to the server
    irc.send("user " + botnick + " " + botnick + " " + botnick + " :testbot\r\n")
    irc.send("nick " + botnick + "\r\n")
    for channel in channels:
        irc.send("join " + channel + "\r\n")

    dt = time.strftime("%Y-%m-%d", time.localtime())
    f = open('log/' + dt + '_log', 'a')
    while True:
        try:
            text = irc.recv(2040)
            if re.match('PING :irc.devel.redhat.com', text):
                irc.send('PONG :irc.devel.redhat.com\r\n')
                f.close()
                f = open('log/' + dt + '_log', 'a')
                continue
            if dt != time.strftime("%Y-%m-%d", time.localtime()):
                f.close()
                dt = time.strftime("%Y-%m-%d", time.localtime())
                f = open('log/' + dt + '_log', 'a')

            tm = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            f.write(tm + '\n')
            f.write(text)
            process_input(text)  # actually process the input

        except Exception as e:

            print(str(e))
            continue  # don't crash on exception; keep going
    f.close()


def getname(text):
    if text.split(' ')[0].find('@'):
        return text[1:text.find('!')]
    else:
        return text.split(' ')[0][1:text.find('!')]


def getgoal(text):
    m = re.findall(r'PRIVMSG (.+) :.+', text)
    if len(m) > 0:
        return m[0]
    else:
        pass


def sendgoal(text):
    sg = getgoal(text)
    if sg == botnick:
        return ' ' + getname(text) + ' :'
    else:
        return ' ' + sg + ' :' + getname(text) + ', '


def getmsg(text, key):
    m = re.findall(key + ' .+ :(.+)', text)
    if len(m) > 0:
        return m[0]
    else:
        return ""


# Function for reacting to input
def process_input(text):

    message = getmsg(text, PRIVMSG).lower()
    gotg = getgoal(text)
    gotn = getname(text)
    if gotg == botnick or re.match(botnick, message):
        if re.match(botnick, message):
            message = message.split(botnick)[1]
        message = message.strip().strip(',').strip()
        if re.match('ping', message, re.IGNORECASE) or \
                re.match('\x01ping', message, re.IGNORECASE):
            rtime = re.findall(r'([0-9]+)', message)
            if len(rtime) > 0:
                irc.send('notice' + sendgoal(text) + '\x01PING ' + rtime[
                    0] + '\x01\r\n')
                return
            irc.send('privmsg' + sendgoal(text) + 'pong ' + '\r\n')
        elif re.match('forget', message, re.IGNORECASE):
            message =message.split('forget')[1].strip()
            if message in namestrdic.keys():
                del namestrdic[message]
                stext = "I've forgotten what I knew about " + message
                irc.send('privmsg' + sendgoal(text) + stext + '\r\n')
                ndf = open(ndfile, 'w')
                ndf.write(str(namestrdic))
                ndf.close()
            elif message in strdic:
                del strdic[message]
                stext = "I've forgotten what I knew about " + message
                irc.send('privmsg' + sendgoal(text) + stext + '\r\n')
                sdf = open(sdfile, 'w')
                sdf.write(str(strdic))
                sdf.close()
            else:
                stext = "I never knew anything about " + message
                irc.send('privmsg' + sendgoal(text) + stext + '\r\n')

        elif message in strdic.keys():
            stext = message + ' is ' +strdic[message]
            irc.send('privmsg' + sendgoal(text) + stext + '\r\n')
        elif message in namestrdic.keys():
            if gotg == botnick:
                stext = message + ' is ' + namestrdic[message]
                irc.send('privmsg' + sendgoal(text) + stext + '\r\n')
            else:
                if gotg in namelist.keys():
                    del namelist[gotg]
                irc.send('names ' + gotg + '\r\n')
                nameop.append((1, gotg, gotn, message))

        elif re.search(' is ', message, re.IGNORECASE):
            mkey, mvalue = message.split(' is ')
            if mkey in strdic.keys() or mkey in namestrdic.keys():
                if strdic[mkey] == mvalue:
                    stext = 'yes I know it'
                else:
                    stext = 'but ' + mkey + ' is ' + strdic[mkey]
                irc.send('privmsg' + sendgoal(text) + stext + '\r\n')
            else:
                irc.send('privmsg' + sendgoal(text) + 'ok' + '\r\n')
                strdic[mkey] = mvalue
                sdf = open(sdfile, 'w')
                sdf.write(str(strdic))
                sdf.close()
        elif re.search(' nlis ', message, re.IGNORECASE):
            mkey, mvalue = message.split(' nlis ')
            if mkey in strdic.keys() or mkey in namestrdic.keys():
                if namestrdic[mkey] == mvalue:
                    stext = 'yes I know it'
                else:
                    stext = 'but ' + mkey + ' is ' + namestrdic[mkey]
                irc.send('privmsg' + sendgoal(text) + stext + '\r\n')
            else:
                irc.send('privmsg' + sendgoal(text) + 'ok' + '\r\n')
                namestrdic[mkey] = mvalue
                ndf = open(ndfile, 'w')
                ndf.write(str(namestrdic))
                ndf.close()
        else:
            irc.send(
                'privmsg' + sendgoal(text) + "Sorry, I've no idea " + '\r\n')

    elif re.search(ownernick, message, re.IGNORECASE):
        tm = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        onf = open(ownerfile, 'a')
        onf.write(tm + '\n')
        onf.write(gotn + ' to ' + gotg + ':' + message + '\n')
        onf.close()
        if gotg in namelist.keys():
            del namelist[gotg]
        irc.send('names ' + gotg + '\r\n')
        nameop.append((0, gotg, gotn, None))

    elif re.search(NAMEINFO + '.+= .+ :.+', text):
        nameinfo = re.findall(NAMEINFO + ' .+ = (.+) :(.+)\r', text)
        nif = nameinfo[0][1].replace('@', '')
        if nameinfo[0] in namelist.keys():
            namelist[nameinfo[0][0]] += ' ' + nif
        else:
            namelist[nameinfo[0][0]] = nif

    elif re.search(NAMEEND + '.+ :End of /NAMES list', text):
        if len(nameop) == 0:
            return
        nop = nameop[0][0]
        ngoal = nameop[0][1]
        nsender = nameop[0][2]
        namekey = nameop[0][3]
        nameop.pop(0)
        if nop == 0:
            if re.search(ownernick, namelist[ngoal]):
                return
            else:
                stext = nsender + ', sorry ' + ownernick + ' is away'
                irc.send('privmsg' + ngoal + ' :' + stext + '\r\n')
        elif nop == 1:
            nameinfo = namestrdic[namekey].split()
            nownameinfo = namelist[ngoal].split()
            stext = namekey + ' is'
            for nif in nameinfo:
                nflag = True
                for nnif in nownameinfo:
                    if re.match(nif, nnif):
                        nflag = False
                        stext += ' ' + nnif
                if nflag:
                    stext += ' ' + nif
            irc.send('privmsg ' + ngoal + ' :' + stext + '\r\n')

    else:
        return

'''
Start
'''
connect_loop()
