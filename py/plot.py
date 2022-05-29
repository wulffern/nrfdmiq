#!/usr/bin/env python3

#!/usr/bin/env python3

import click
import serial
import numpy as np
import matplotlib.pyplot as plt
import json


class report:

    def __init__(self):

        pass

    def readFromFileOrCom(self,filename = None,com = None):
        if(com is not None):
            self.readFromCom(com)
        else:
            self.readFromFile(filename)

    def readFromFile(self,com):
        with open(filename) as fi:
            self.obj = json.load(fi)

    def readFromCom(self,com):
        with serial.Serial(com, baudrate=115200, timeout=10) as ser:
            ser.write(bytes('0','utf-8'))
            ret = ser.read_until(bytes("\n",'utf-8'))
        self.obj = json.loads(ret.decode('utf-8'))

    def save(self,filename):
        with open(filename,"w") as fo:
            fo.write(json.dumps(self.obj))

    def load(self):
        self.quality = self.obj["quality"]
        self.ifft = self.obj["ifft[mm]"]/1000.0
        self.phase_slope = self.obj["phase_slope[mm]"]/1000.0
        self.rssi_openspace = self.obj["rssi_openspace[mm]"]/1000.0
        self.best = self.obj["best[mm]"]/1000.0
        self.highpres = self.obj["highpres[mm]"]/1000.0

        self.link_loss = self.obj["link_loss[dB]"]

        self.i_local = np.array(self.obj["i_local"])
        self.q_local = np.array(self.obj["q_local"])
        self.i_remote = np.array(self.obj["i_remote"])
        self.q_remote = np.array(self.obj["q_remote"])

    #- Calculate transferfunction of channel squared
    def calcTransfer2(self):

        l = self.i_local +  np.multiply(1j,self.q_local)
        r = self.i_remote +  np.multiply(1j,self.q_remote)

        self.transfer2 = np.multiply(l,r)

    def calcImpulse2(self):

        N = 2048
        yfft = np.fft.ifft(self.transfer2,N)
        yf = yfft[1:((int)(len(yfft)/2))]
        self.impulse2 = yf
        self.impulse2_x = np.arange(0,N/2-1)/N/2/1e6




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
@click.option("--filename",default=None)
@click.option("--com",default=None,help= "Which serial port to read")
def impulse(filename,com):

    r = report()
    r.readFromFileOrCom(filename,com)
    r.load()
    r.calcTransfer2()
    r.calcImpulse2()

    plt.plot(r.impulse2_x*1e9,abs(r.impulse2)**2)
    plt.ylabel("Impulse Magnitude Squared")
    plt.xlabel("Delay [ns]")
    plt.title("Distance [m]= %.2f, Link Loss [dB] = %d" % (r.ifft,r.link_loss))

    plt.grid()
    plt.show()





if(__name__ == "__main__"):
    cli()
