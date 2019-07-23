#!/usr/local/bin/python

import socket
import re
import time
import os

os.environ['TZ'] = 'Asia/Shanghai'
time.tzset()

# irc-related constants
server = "**.**.**"
port = 6667
channels = ["#****", "#***", ]
name_list = [
    ]
botnick = "jbot"

namelist = {}
nameop = []
strdic = {}
namestrdic = {}
ndfile = 'ndfile.txt'
sdfile = 'sdfile.txt'
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


def connect_server():
    print("Establishing connection to [%s]" % (server))
    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # defines the socket

    # Connect
    irc.connect((server, port))

    # send info about yourself to the server
    irc.send("user " + botnick + " " + botnick + " " + botnick + " :testbot\r\n")
    irc.send("nick " + botnick + "\r\n")
    for channel in channels:
        irc.send("join " + channel + "\r\n")
    return irc


debugflg = 0


def connect_loop():
    irc = connect_server()

    dt = time.strftime("%Y-%m-%d", time.localtime())
    f = open('log/' + dt + '_log', 'a')
    text = ''
    while True:
        try:
            data = irc.recv(4096)
            if len(data) <= 0:
                irc = connect_server()
                tm = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                f.write(tm + '\n')
                f.write('Reconect!!!!!!!!')
                f.flush()
                continue

            while len(data) > 0:
                if data.find('\r\n') == -1:
                    text = data
                    break
                texttp, data = data.split('\r\n', 1)
                text += texttp + '\n'
                if re.match('PING :irc\.devel\.redhat\.com', text):
                    irc.send('PONG :irc.devel.redhat.com\r\n')
                    f.close()
                    f = open('log/' + dt + '_log', 'a')
                    text = ''
                    continue
                if dt != time.strftime("%Y-%m-%d", time.localtime()):
                    f.close()
                    dt = time.strftime("%Y-%m-%d", time.localtime())
                    f = open('log/' + dt + '_log', 'a')

                tm = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                f.write(tm + '\n')
                f.write(text)
                process_input(text, irc)  # actually process the input
                text = ''
                f.flush()

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
    m = re.findall(r'PRIVMSG (.+?) :.+', text)
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
    m = re.findall(key + ' .+? :(.+)', text)
    if len(m) > 0:
        return m[0]
    else:
        return ""


def sendmsg(goal, stext, irc):
    while len(stext) > 256:
        st1, stext = stext[0:256], stext[256:]
        if st1.find(' ', 1) > 0:
            st1, st2 = st1.rsplit(' ', 1)
            stext = st2 + stext
        irc.send('privmsg' + goal + st1 + '\r\n')
    irc.send('privmsg' + goal + stext + '\r\n')


# Function for reacting to input
def process_input(text, irc):
    def _del_key(mkey):
        if mkey in namestrdic.keys():
            del namestrdic[mkey]
            with open(ndfile, 'w') as ndf:
                ndf.write(str(namestrdic))
        elif mkey in strdic.keys():
            del strdic[mkey]
            with open(sdfile, 'w') as sdf:
                sdf.write(str(strdic))
        else:
            return False
        return True

    message = getmsg(text, PRIVMSG).lower()
    gotg = getgoal(text)
    gotn = getname(text)
    if gotg == botnick or re.match(botnick, message):
        if re.match(botnick, message):
            message = message.split(botnick, 1)[1]
        message = message.strip().strip(',').strip()
        if re.match('ping', message, re.IGNORECASE) or \
                re.match('\x01ping', message, re.IGNORECASE):
            rtime = re.findall(r'([0-9]+)', message)
            if len(rtime) > 0:
                irc.send('notice' + sendgoal(text) + '\x01PING ' + rtime[0] + '\x01\r\n')
                return
            sendmsg(sendgoal(text), 'pong', irc)

        elif re.match('no[ ,]', message, re.IGNORECASE):
            message = message.split('no', 1)[1].strip().strip(',').strip()
            if re.search(' is ', message, re.IGNORECASE):
                mkey, mvalue = message.split(' is ', 1)
                _del_key(mkey=mkey)
                sendmsg(sendgoal(text), 'ok', irc)
                if mkey in name_list:
                    namestrdic[mkey] = mvalue
                    with open(ndfile, 'w') as ndf:
                        ndf.write(str(namestrdic))
                else:
                    strdic[mkey] = mvalue
                    with open(sdfile, 'w') as sdf:
                        sdf.write(str(strdic))
            else:
                stext = "Sorry, I've no idea "
                sendmsg(sendgoal(text), stext, irc)

        elif re.match('forget', message, re.IGNORECASE):
            mkey = message.split('forget')[1].strip()
            if _del_key(mkey=mkey):
                stext = "I've forgotten what I knew about " + mkey
                sendmsg(sendgoal(text), stext, irc)
            else:
                stext = "I never knew anything about " + mkey
                sendmsg(sendgoal(text), stext, irc)

        elif message in strdic.keys():
            stext = message + ' is ' + strdic[message]
            sendmsg(sendgoal(text), stext, irc)
        elif message in namestrdic.keys():
            if gotg == botnick:
                stext = message + ' is ' + namestrdic[message]
                sendmsg(sendgoal(text), stext, irc)
            else:
                if gotg in namelist.keys():
                    del namelist[gotg]
                irc.send('names ' + gotg + '\r\n')
                nameop.append((1, gotg, gotn, message))

        elif re.search(' is ', message, re.IGNORECASE):
            mkey, mvalue = message.split(' is ', 1)
            if mkey in strdic.keys():
                if strdic[mkey] == mvalue:
                    stext = 'yes I know it'
                else:
                    stext = 'but ' + mkey + ' is ' + strdic[mkey]
                sendmsg(sendgoal(text), stext, irc)
            elif mkey in namestrdic.keys():
                if namestrdic[mkey] == mvalue:
                    stext = 'yes I know it'
                else:
                    stext = 'but ' + mkey + ' is ' + namestrdic[mkey]
                sendmsg(sendgoal(text), stext, irc)
            else:
                sendmsg(sendgoal(text), 'ok', irc)
                if mkey in name_list:
                    namestrdic[mkey] = mvalue
                    with open(ndfile, 'w') as ndf:
                        ndf.write(str(namestrdic))
                else:
                    strdic[mkey] = mvalue
                    with open(sdfile, 'w') as sdf:
                        sdf.write(str(strdic))
        elif re.search(' add ', message, re.IGNORECASE):
            mkey, mvalue = message.split(' add ', 1)
            if mkey in strdic.keys():
                strdic[mkey] = strdic[mkey].strip() + ' ' + mvalue
                with open(sdfile, 'w') as sdf:
                    sdf.write(str(strdic))
                stext = mkey + ' is ' + strdic[mkey]
                sendmsg(sendgoal(text), stext, irc)
            elif mkey in namestrdic.keys():
                namestrdic[mkey] = namestrdic[mkey].strip() + ' ' + mvalue
                with open(ndfile, 'w') as ndf:
                    ndf.write(str(namestrdic))
                stext = mkey + ' is ' + namestrdic[mkey]
                sendmsg(sendgoal(text), stext, irc)
            else:
                stext = mkey + ' is not defined'
                sendmsg(sendgoal(text), stext, irc)
        elif re.search(' del ', message, re.IGNORECASE):
            mkey, mvalue = message.split(' del ', 1)
            if mkey in strdic.keys():
                value_list = strdic[mkey].strip().split()
                if mvalue in value_list:
                    value_list.remove(mvalue)
                    strdic[mkey] = ' '.join(value_list)
                    with open(sdfile, 'w') as sdf:
                        sdf.write(str(strdic))
                    stext = mkey + ' is ' + strdic[mkey]
                    sendmsg(sendgoal(text), stext, irc)
                else:
                    stext = mvalue + ' is not in ' + mkey
                    sendmsg(sendgoal(text), stext, irc)

            elif mkey in namestrdic.keys():
                value_list = namestrdic[mkey].strip().split()
                if mvalue in value_list:
                    value_list.remove(mvalue)
                    namestrdic[mkey] = ' '.join(value_list)
                    with open(ndfile, 'w') as ndf:
                        ndf.write(str(namestrdic))
                    stext = mkey + ' is ' + namestrdic[mkey]
                    sendmsg(sendgoal(text), stext, irc)
                else:
                    stext = mvalue + ' is not in ' + mkey
                    sendmsg(sendgoal(text), stext, irc)
            else:
                stext = mkey + ' is not defined'
                sendmsg(sendgoal(text), stext, irc)

        # channel
        elif re.match('join ', message, re.IGNORECASE):
            chan = message.split('join')[1].strip()
            irc.send('join ' + chan + '\r\n')
            stext = "Try to join %s" % chan
            sendmsg(sendgoal(text), stext, irc)
        elif re.match('leave ', message, re.IGNORECASE):
            chan = message.split('leave')[1].strip()
            irc.send('part ' + chan + '\r\n')
            stext = "Try to leave %s" % chan
            sendmsg(sendgoal(text), stext, irc)

        else:
            stext = "Sorry, I've no idea "
            sendmsg(sendgoal(text), stext, irc)

    elif re.search(NAMEINFO + '.+?= .+? :.+', text):
        nameinfo = re.findall(NAMEINFO + ' .+ = (.+) :(.+)\n', text)
        nif = nameinfo[0][1].replace('@', '')
        if nameinfo[0] in namelist.keys():
            namelist[nameinfo[0][0]] += ' ' + nif
        else:
            namelist[nameinfo[0][0]] = nif

    elif re.search(NAMEEND + '.+ :End of /NAMES list', text):
        if len(nameop) == 0:
            return
        nop, ngoal, nsender, namekey = nameop.pop(0)
        if nop == 0:
            return
        elif nop == 1:
            nameinfo = namestrdic[namekey].split()
            nownameinfo = namelist[ngoal].split()
            stext = namekey + ' is'
            offline_list = ''
            for nif in nameinfo:
                nflag = True
                for nnif in nownameinfo:
                    if re.match(nif, nnif):
                        nflag = False
                        stext += ' ' + nnif
                if nflag:
                    stext += ' ' + nif
                    offline_list += ' ' + nif
            sendmsg(' ' + ngoal + ' :', stext, irc)
            if offline_list:
                offline_list += ' is/are offline'
                sendmsg(' ' + ngoal + ' :', offline_list, irc)

    else:
        return


'''
Start
'''
connect_loop()
