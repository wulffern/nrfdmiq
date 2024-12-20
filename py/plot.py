#!/usr/bin/env python3

import click
import serial
import numpy as np
import matplotlib.pyplot as plt
import json
import os
import datetime
import glob
import time
import re
import pandas as pd

class report:

    def __init__(self):

        self.quality = 100
        self.ifft = -1
        self.phase_slope = -1
        self.best = -1
        self.c =299792458

        pass

    def isOk(self):
        if(self.quality > 0):
            return False

        sinr = self.sinr_local.sum() + self.sinr_remote.sum()
        if(sinr > 0):
            return False
        return True

    def readFromFileOrCom(self,filename = None,com = None):
        
        if(com is not None):
            self.readFromCom(com)
        else:
            self.readFromFile(filename)

    def readFromFile(self,filename):
        self.filename = filename
        with open(filename) as fi:
            self.obj = json.load(fi)

    def readFromCom(self,com):
        with serial.Serial(com, baudrate=115200, timeout=10) as ser:
            ser.write(bytes('0','utf-8'))
            ret = ser.read_until(bytes("\n",'utf-8'))
            #print(ret)

        try:
            self.obj = json.loads(ret.decode('utf-8'))
        except Exception as e:
            print(ret.decode('utf-8'))
            raise(e)

    def save(self,filename):
        with open(filename,"w") as fo:
            fo.write(json.dumps(self.obj))

    def load(self):
        self.quality = self.obj["quality"]
        self.ifft = self.obj["ifft[mm]"]/1000.0
        self.phase_slope = self.obj["phase_slope[mm]"]/1000.0
        self.rssi_openspace = self.obj["rssi_openspace[mm]"]/1000.0
        self.best = self.obj["best[mm]"]/1000.0

        if("highprec[mm]" in self.obj):
            self.highprec = self.obj["highprec[mm]"]/1000.0
        else:
            self.highprec = 100
        if("duration[us]" in self.obj):
            self.duration =  self.obj["duration[us]"]
        else:
            self.duration = -1

        if("hopping_sequence" in self.obj):
            self.hopping_sequence =  self.obj["hopping_sequence"]
        else:
            self.hopping_sequence = list()

        self.link_loss = self.obj["link_loss[dB]"]

        self.i_local = np.array(self.obj["i_local"])
        self.q_local = np.array(self.obj["q_local"])
        self.i_remote = np.array(self.obj["i_remote"])
        self.q_remote = np.array(self.obj["q_remote"])

        self.sinr_remote = np.zeros(2)
        if("sinr_remote" in self.obj):
            self.sinr_remote = np.array(self.obj["sinr_remote"])

        self.sinr_local = np.zeros(2)
        if("sinr_local" in self.obj):
            self.sinr_local = np.array(self.obj["sinr_local"])


    #- Calculate transferfunction of channel squared
    def calcTransfer2(self):

        l = self.i_local +  np.multiply(1j,self.q_local)
        r = self.i_remote +  np.multiply(1j,self.q_remote)
        self.remote = r
        self.local = l

        self.transfer2 = np.multiply(l,r)

    def calcTransfer(self):
        fstart = 4
        fstop = 78

        tr = np.zeros(len(self.transfer2),dtype=complex)

        #- Do a linear regression to find an optimum slope
        x = np.arange(fstart,fstop,1)
        ang = np.unwrap(np.angle(self.transfer2))
        A = np.vstack([x, np.ones(len(x))]).T
        xang = np.linalg.lstsq(A,ang[fstart:fstop],rcond=None)[0]
        xall = np.arange(0,80,1)
        th_ideal = xang[0]/2*xall + xang[1]/2
        smag = np.sqrt(np.abs(self.transfer2))
        sang = ang/2

        for i in range(fstart,fstop):
            at = th_ideal[i]
            diff = sang[i] - th_ideal[i]
            if(diff > np.pi):
                sang[i]  = sang[i] - np.pi
            elif(diff < -np.pi):
                sang[i] = sang[i] + np.pi

        self.transfer = np.multiply(smag, np.exp( 1j * sang ) )


    def calcImpulse2(self):
        N = 2048
        yfft = np.fft.ifft(self.transfer2,N)
        yf = yfft[0:((int)(len(yfft)/2))]
        self.impulse2 = yf
        self.impulse2_x = np.arange(0,N/2)/N/2/1e6

    def calcImpulse(self):
        N = 2048
        yfft = np.fft.ifft(self.transfer,N)
        yf = yfft[0:((int)(len(yfft)/2))]
        self.impulse = yf
        self.impulse_x = np.arange(0,N/2)/N/1e6

        am = np.argmax(np.abs(self.impulse))



    # Based on Statistical Properties of the RMS Delay-Spread of Mobile Radio Channels with Independent Rayleigh-Fading Paths
    # IEEE TRANSACTIONS ON VEHICULAR TECHNOLOGY, VOL. 45, NO. 1, FEBRUARY 1996
    def calcDelaySpread2(self):
        s = np.abs(self.impulse2)**2

        pwr = np.sum(s)
        p1 = np.sum(np.multiply(s,self.impulse2_x))
        p2 = np.sum(np.multiply(s,self.impulse2_x**2))
        rms = np.sqrt(p2/pwr - (p1/pwr)**2)
        self.delaySpread2 = rms

    def calcDelaySpread(self):

        y = self.impulse

        s = np.abs(y**2)

        s = s/np.max(s)

        #- Remove the lowest values. They are likely artifacts of IFFT.
        s[s < 0.01] = 0

        pwr = np.sum(s)
        p1 = np.sum(np.multiply(s,self.impulse_x))
        p2 = np.sum(np.multiply(s,self.impulse_x**2))
        rms = np.sqrt(p2/pwr - (p1/pwr)**2)

        self.delaySpread = rms


    def calc(self):
        self.calcTransfer2()
        self.calcTransfer()
        self.calcImpulse()
        self.calcImpulse2()
        self.calcDelaySpread()
        self.calcDelaySpread2()


@click.group()
def cli():
    pass

@cli.command()
@click.argument("filename")
@click.option("--com",default=None,help= "Which serial port to read")
def save(filename,com):
    r = report()
    r.readFromCom(com)
    r.save(filename)

@cli.command()
@click.argument("dirname")
@click.option("--com",default=None,help= "Which serial port to read")
@click.option("--count",default=10,help= "")
def msave(dirname,com,count):

    if( not os.path.exists(dirname)):
        os.makedirs(dirname)

    for i in range(1,count):
        fname = str(datetime.datetime.now().timestamp()) + ".json"
        r = report()
        r.readFromCom(com)
        r.load()
        sinr_r = r.sinr_remote.sum()
        sinr_l = r.sinr_local.sum()

        print("Distance [m]: %.2f, Quality : %d, SINR Remote : %d, SINR Local : %d" % (r.ifft,r.quality,sinr_r,sinr_l))
        if(r.quality == 0 and sinr_r < 5 and sinr_l < 5 ):
            r.save(dirname + os.path.sep +  fname)
        time.sleep(0.1)

@cli.command()
@click.option("--filename",default=None)
@click.option("--com",default=None,help= "Which serial port to read")
def impulse(filename,com):

    r = report()
    r.readFromFileOrCom(filename,com)
    r.load()

    if(r.quality > 1 ):
        print("Ignoring, bad quality = %d" %r.quality)
        return -1
    r.calcTransfer2()
    r.calcImpulse2()

    plt.plot(r.impulse2_x*1e9,abs(r.impulse2)**2)
    plt.ylabel("Impulse Magnitude Squared")
    plt.xlabel("Delay [ns]")
    plt.title("Distance [m]= %.2f, Link Loss [dB] = %d" % (r.highprec,r.link_loss))

    plt.grid()
    plt.show()

@cli.command()
@click.argument("dirname")
@click.option("--show",is_flag=True,default=False,help= "Show plot")
def impulsedir(dirname,show):

    files = glob.glob(dirname + os.path.sep +"*.json")

    reports = list()

    for f in files:
        r = report()
        r.readFromFile(f)
        r.load()
        if(not r.isOk()):
            continue
        r.calc()
        reports.append(r)

    fig, ax = plt.subplots(5,1,figsize=(10,10), gridspec_kw={'height_ratios': [0.3, 2,2,2,2]})
    cmap_name = "viridis_r"
    cmap = plt.get_cmap(cmap_name)
    colors = cmap.colors

    gradient = np.linspace(0, 1, 256)
    gradient = np.vstack((gradient, gradient))

    N = len(colors)
    maxdist = 50
    idmult = N/maxdist
    c= 299792458
    ns =1e9

    ax[0].set_title(dirname)
    ax[0].imshow(gradient, aspect='auto', cmap=plt.get_cmap(cmap_name),extent=[0,maxdist,1,0])
    ax[0].get_yaxis().set_visible(False)
    ax[0].set_xlabel("Distance [m]")
    dist_avg = 0
    for r in reports:

        dist = r.ifft
        if(dist < 1):
            continue
        dist_avg +=dist
        delay = dist/(c)*ns

        xx = r.impulse_x*ns - delay
        y = np.abs(r.impulse**2)
        y = y/np.max(y)

        ax[1].plot(xx,y,color=colors[int(idmult*dist)],marker="None",linestyle="solid",alpha=0.3)
        ax[2].plot(r.link_loss,r.delaySpread*ns,marker="o",color="black")
        ax[3].plot(r.ifft,r.delaySpread*ns,marker="o",color="black")
        ax[4].semilogx(r.ifft,r.link_loss,marker="o",color="black")
    dist_avg = dist_avg/len(reports)
    ax[0].set_title(dirname + ", Average distance = %.2f m, %d measurements" % (dist_avg,len(reports)))
    ax[1].set_ylabel("Power")
    ax[1].grid(True)
    ax[2].grid(True)
    ax[3].grid(True)
    ax[4].grid(True)
    ax[1].set_xlabel("Impulse response - delay of distance [ns]")
    ax[2].set_ylabel("RMS delay spread [ns]")
    ax[3].set_ylabel("RMS delay spread [ns]")
    ax[4].set_ylabel("Link loss [dB]")
    ax[2].set_xlabel(" Link loss [dB]")
    ax[3].set_xlabel(" Estimated distance [m]")
    ax[4].set_xlabel(" Estimated distance [m]")
    plt.tight_layout()


    if( not os.path.exists("media")):
       os.mkdir("media")
    try:
        plt.savefig("media"+ os.path.sep +  dirname.replace("/","_").replace("\\","_") + ".png")
    except Exception as e:
        print(e)
    if(show):
        plt.show()


@cli.command()
@click.option("--filename",default=None)
def magnitude(filename):

    r = report()
    r.readFromFile(filename)
    r.load()
    if(not r.isOk()):
        print(f"Could not read {filename}")
    r.calc()

    fig, axe = plt.subplots(1,1,figsize=(16,9))

    ax = list()
    ax.append(axe)
    ax[0].set_title(filename)
    dist_avg = 0

    dist = list()
    max = np.max(np.abs(r.transfer2))
    mag = np.abs(r.transfer2)
    ax[0].plot(20*np.log10(mag/max))

    ax[0].plot(dist)
    ax[0].grid(True)
    ax[0].set_ylabel("Magnitude [dBFS]")
    plt.tight_layout()
    plt.show()

@cli.command()
@click.argument("dirname")
@click.option("--show",is_flag=True,default=False,help= "Show plot")
def magnitudedir(dirname,show):

    files = glob.glob(dirname + os.path.sep +"*.json")

    reports = list()

    for f in files:
        r = report()
        r.readFromFile(f)
        r.load()
        if(not r.isOk()):
            continue
        r.calc()
        reports.append(r)

    fig, axe = plt.subplots(1,1,figsize=(10,10))

    ax = list()
    ax.append(axe)
    ax[0].set_title(dirname)
    dist_avg = 0

    dist = list()
    for r in reports:
        max = np.max(np.abs(r.transfer2))
        mag = np.abs(r.transfer2)
        ax[0].plot(20*np.log10(mag/max))

    ax[0].plot(dist)
    ax[0].grid(True)
    ax[0].set_ylabel("Magnitude [dBFS]")
    plt.tight_layout()

    if(show):
        plt.show()

@cli.command()
@click.argument("dirname")
@click.option("--show",default=False,help= "Show plot")
def timedir(dirname,show):

    files = glob.glob(dirname + os.path.sep +"*.json")

    distance = list()
    time = list()



    for f in files:
        r = report()
        r.readFromFile(f)
        r.load()
        distance.append(r.ifft)
        t = os.path.basename(f).replace(".json","")
        dt = datetime.datetime.fromtimestamp(int(float(t)))
        time.append(dt)


    s = pd.Series(data=distance,index=time)
    #plt.plot(time,distance)
    s.plot()
    plt.show()



if(__name__ == "__main__"):
    cli()
