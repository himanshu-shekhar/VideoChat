#-------------------------------------------------------------------------------
# Name:         VideoChat
# Purpose:      VideoChat for lan
#
# Author:       Rogue
#
# Created:      17-07-2013
# Copyright:    (c) Rogue 2013
# Licence:      GPL
#-------------------------------------------------------------------------------

import socket
import threading
import Tkinter as tk
from time import sleep
import tkMessageBox
import sys #not req

#For video Capturing Image, ImageTk, Device in VideoCapture
from PIL import Image,ImageTk
from VideoCapture import Device

#For Audio Capturing pyaudio
import pyaudio

DEBUG=True

def debug(s):
    if DEBUG:
        print s

class gui():

    PORT=9801
    dataSize=65535

    #Change values for Image
    width=640
    height=480

    #Change values for audio quality
    chunk = 4096
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100


    #------------------Used by program while running. DO NOT edit.
    sndPicDataAvail=False
    sndAudDataAvail=False
    recvPicDataAvail=False
    recvAudDataAvail=False
    prog=False
    stop=False
    exitProg=False
    #------------------------------------------------------------

    def __init__(self, root):
        self.root=root
        self.root.wm_title("Video Chatting: Coded by Rogue")
        self.root.protocol('WM_DELETE_WINDOW', self.safeExit)

        self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.cam=Device()
        self.photo=ImageTk.PhotoImage(self.cam.getImage())

        p = pyaudio.PyAudio()
        self.audStream = p.open(format = self.FORMAT,
                        channels = self.CHANNELS,
                        rate = self.RATE,
                        input = True,
                        output = True,
                        frames_per_buffer = self.chunk)
        self.design()
        t1=threading.Thread(target=self.sndData)
        t2=threading.Thread(target=self.recvData)
        t3=threading.Thread(target=self.showMe)
        t4=threading.Thread(target=self.callrecv)
        t1.daemon=True
        t2.daemon=True
        t3.daemon=True
        t4.daemon=True
        t1.start()
        t2.start()
        t3.start()
        t4.start()

    def design(self):
        self.frame=tk.Frame(self.root)
        self.label=tk.Label(self.frame, text="Enter the ip address")
        self.label.pack()
        self.input=tk.Entry(self.frame)
        self.input.pack()
        self.start=tk.Button(self.frame, text="Call", command=self.call)
        self.start.pack()
        self.frame.pack(fill=tk.X)
        self.mainCanvas=tk.Canvas(self.root, height=self.height, width=self.width, relief=tk.RAISED, bd=5, bg="white")
        self.mainCanvas.pack(fill=tk.BOTH)

    def startThreads(self):
        threading.Thread(target=self.videosnd).start()
        threading.Thread(target=self.videorecv).start()
        threading.Thread(target=self.audiosnd).start()
        threading.Thread(target=self.audiorecv).start()

    def call(self):
        if self.prog:
            self.start.configure(text="Call")
            self.prog=False
        else:
            ip=self.input.get()
            try:
                tmp=socket.getaddrinfo(ip,80)
                print tmp
            except socket.gaierror:
                tkMessageBox.showerror('Error','Error in connecting to {}!!!'.format(ip))
                return

            try:
                self.sock.sendto("this is to stop the callrecv",self.selfaddr)
                self.sock.sendto("Can i connect???",(ip,self.PORT))
                data,addr=self.sock.recvfrom(self.dataSize)
                print data
                if data=="OK":
                    self.addr=(ip, self.PORT)
                    self.start.configure(text="End Call")
                    self.prog=True
                    self.startThreads()
                elif data=="NO":
                    tkMessageBox.showerror('Error','Connection refused!!!'.format(ip))
                else:
                    tkMessageBox.showerror('Error','Error in connecting!!!'.format(ip))
            except:
                tkMessageBox.showerror('Error','Error in Connecting!!!'.format(ip))
            self.stop=False

    def askques(self,addr):
        return tkMessageBox.askyesno('Calling...','trying to connect. Accept')

    def callrecv(self):
        self.selfaddr=(socket.gethostbyname(socket.gethostname()), self.PORT)
        self.sock.bind(self.selfaddr)
        debug("callrecv started at {}".format(socket.gethostbyname(socket.gethostname())))
##        debug('{}'.format(tkMessageBox.askyesno('Calling...','{} is trying to connect. Accept ?')))
        while not self.exitProg:
            if not self.prog and not self.stop:
                data, addr=self.sock.recvfrom(self.dataSize)
##                connect=self.askques('123')
##                print data, addr, addr[0]
##                debug('data recv {}'.format(data))
                if addr==self.selfaddr:
                    self.stop=True
                else:
##                    connect=tkMessageBox.askyesno('Calling...','{} is trying to connect. Accept ?'.format(addr[0]))
                    connect=True
                    if connect:
                        debug('sending ok')
                        self.sock.sendto("OK",addr)
                        self.start.configure(text="End Call")
                        self.addr=addr
                        self.prog=True
                        self.startThreads()
                    else:
                        self.sock.sendto("NO",addr)
            sleep(2)

    def sndData(self):
        #This is gonna run till the end. If you want to encrypt it do it here. Am not gonna do it
        while not self.exitProg:
            while self.prog:
                try:
                    if self.sndAudDataAvail:
                        self.sock.sendto(self.sndAudData, self.addr)
                        self.sndAudDataAvail=False
                except:
                    debug('error in sndData audio. current val: {},{},{}'.format(self.prog, self.sndAudDataAvail, self.sndPicDataAvail))

                try:
                    if self.sndPicDataAvail:
                        self.sock.sendto(self.sndPicData, self.addr)
                        self.sndPicDataAvail=False
                except:
                    debug('error in sndData pic. current val: {},{},{}'.format(self.prog, self.sndAudDataAvail, self.sndPicDataAvail))
            sleep(1)

    def recvData(self):
        #This is gonna run till the end. If you want to decrypt it do it here. Am not gonna do it
        while not self.exitProg:
            while self.prog:
                try:
                    data,addr=self.sock.recvfrom(self.dataSize)
                    if addr==self.addr:
                        typ=data[0]
                        if typ=='p':
                            self.recvPicData=data[1:]
                            self.recvPicDataAvail=True
                        if typ=='a':
                            self.recvAudData=data[1:]
                            self.recvAudDataAvail=True
                except:
                    debug('error in recvData. current val: {},{},{}'.format(self.prog, self.sndAudDataAvail, self.sndPicDataAvail))
            sleep(1)

    #w1 , h1 is the current size and w2, h2 is the resize output.
    def getPILImage(self, buf, w1, h1, w2, h2, recv=False):
        if not recv:
            img = Image.fromstring('RGB', (w1,h1), buf, 'raw', 'BGR', 0, -1)
            img=img.resize((w2,h2))
            img=img.transpose(Image.FLIP_LEFT_RIGHT)
        else:
            img= Image.fromstring('RGB',(w1,h1), buf, 'raw')
            img=img.resize((w2,h2))
        return img

    def getData(self, typ):
        if typ=="pic" and self.recvPicDataAvail:
            val=self.recvPicData
            self.recvPicDataAvail=False
            return val
        if typ=="aud" and self.recvAudDataAvail:
            val=self.recvAudData
            self.recvAudDataAvail=False
            return val

    def setSendData(self, data, typ):
        if typ=="pic":
            #Write data only if previous data has been sent i.e sndPicDataAvail is false
            if not self.sndPicDataAvail:
                self.sndPicData='p'+data
                self.sndPicDataAvail=True
        if typ=="aud":
            if not self.sndAudDataAvail:
                self.sndAudData='a'+data
                self.sndAudDataAvail=True


    def videosnd(self):
        while self.prog:
            try:
                pic,w,h=self.cam.getBuffer()
                pic=self.getPILImage(pic,w,h,160,120)
                self.setSendData(pic.tostring(), "pic")
                sleep(.1)
            except:
                debug("Error in videosnd")

    def videorecv(self):
        while self.prog:
            try:
                while not self.recvPicDataAvail:
                    sleep(.05)
                pic=self.getData("pic")
                img=self.getPILImage(pic,160,120,self.width,self.height,True)
                photo=ImageTk.PhotoImage(img)
##                self.mainCanvas.delete(tk.ALL)
                self.mainCanvas.create_image(self.width/2,self.height/2,image=photo)
                sleep(.05)
            except:
                debug("Error in videorecv")

    def audiosnd(self):
        while self.prog:
            try:
                data=self.audStream.read(self.chunk)
                self.setSendData(data,"aud")
            except:
                debug("Error in audiosnd")

    def audiorecv(self):
        while self.prog:
            try:
                while not self.recvAudDataAvail:
                    sleep(.05)
                data=self.getData("aud")
                self.audStream.write(data)
            except:
                debug("Error in audiorecv")
##              stream.write(data)

    def showMe(self):
        while not self.exitProg:
            try:
                pic,w,h=self.cam.getBuffer()
                img=self.getPILImage(pic,w,h,self.width/4,self.height/4)
                photo=ImageTk.PhotoImage(img)
                self.mainCanvas.create_image(self.width/8,self.height-self.height/8,image=photo)
                sleep(.05)
            except:
                debug("Error in showMe")

    def safeExit(self):
        self.exitProg=True
        sleep(2)
        self.sock.close()
        self.root.destroy()

def main():
    root=tk.Tk("Video Chat :P")
    a=gui(root)
    root.mainloop()

if __name__ == '__main__':
    main()
