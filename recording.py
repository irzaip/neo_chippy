#!/usr/bin/env python3
"""Class Suara"""

import argparse
import logging
import numpy as np
import time
import soundfile as sf
import itertools
import sounddevice as sd



class Suara:
    """Class untuk merekam suara, dan manipulasi sewaktu capture.
    PARAMETERS:
    block_length : panjang block yang di capture.
    low_freq : frequency terendah yang di rekam
    high_freq: frequency tertiggi yang di rekam
    gain : penambahan gain pada input suara.
    threshold: batas rms minimum yang terekam.
    duration: durasi yang mau di capture (satuan detik)
    samplerate: sample rate default 44100
    device_id: nomor device input
    channels: jumlah channel (default 1)
    mode: 0. Merekam sampai ada input (q, Q atau ENTER)
          1. Merekam sepanjang durasi.
          2. Merekam sampai lewat beberapa kali threshold minimum
          3. Merekam sampai di panggil stop
          4. Check Threshold
    """
    def __init__(self, block_length = 50, gain = 0, low_freq = 100, high_freq = 2000,
    channels = 1, device_id = 1, samplerate = 44100, threshold = 0 , duration = 2, mode = 4,
    debug=False):
        self.block_length = block_length
        self.gain = gain
        self.low_freq = low_freq
        self.high_freq = high_freq
        self.channels = channels
        self.device_id = device_id
        self.threshold = threshold
        self.samplerate = samplerate
        self.duration = duration
        self.mode = mode
        self.audio = []
        self.cap = []
        self.recording = False
        self.c_thres = False
        self.debug = debug

    def check(self):
        print("samplerate:", self.samplerate)
        print("block_length:",self.block_length)
        print("gain:",self.gain)
        print("low_freq:",self.low_freq)
        print("channels:",self.channels)
        print("device_id:",self.device_id)
        print("threshold:", self.threshold)
        print("duration", self.duration)

    def query_devices(self):
        print(sd.query_devices())

    def rec(self):
        self.audio = []
        self.cap = []
        self.recording = True

        try:
            
            self.delta_f = (self.high_freq - self.low_freq) / (80 - 1)
            self.fftsize = np.ceil(self.samplerate / self.delta_f).astype(int)
            self.low_bin = int(np.floor(self.low_freq / self.delta_f))

            self.cumulated_status = sd.CallbackFlags()
            def callback(indata, frames, time, status):
                global cumulated_status
                
                self.indata = indata
                self.cumulated_status |= status
                if any(self.indata):
                    self.magnitude = np.abs(np.fft.rfft(self.indata[:, 0], n=self.fftsize))
                    self.magnitude *= self.gain / self.fftsize
                    self.get = self.indata.tolist()
                    self.power = int(np.sqrt(np.mean(np.square(self.get))) * 100)
                    if self.c_thres == True:
                        print("power: ",self.power)
                    if self.power >= self.threshold:
                        if self.debug: print('.', end='', flush=True)
                        self.audio.extend(self.get)
                        self.cap.append(self.magnitude)
                    else:
                        if self.debug: print('X', end='', flush=True)

                else:
                    pass
            
            with sd.InputStream(device=self.device_id, channels=self.channels, callback=callback,
                                blocksize=int(self.samplerate * self.block_length / 1000),
                                samplerate=self.samplerate):
                while self.recording:
                    if self.mode == 0:
                        response = input("tekan q untuk berhenti rekam:")
                        if response in ('', 'q', 'Q'):
                            self.recording = False
                            return self.audio, self.cap
                    if self.mode == 1:
                        time.sleep(self.duration)
                        self.recording == False
                        return self.audio, self.cap

                    if self.mode == 2:
                        pass
                    
                    if self.mode == 3:
                        self.recording = False

                    if self.mode == 4:
                        self.c_thres = True
                        response = input("tekan q untuk berhenti rekam:")
                        if response in ('', 'q', 'Q'):
                            self.recording = False
                            self.c_thres = False
                            return self.audio, self.cap

            if self.cumulated_status:
                logging.warning(str(self.cumulated_status))
        except Exception as e:
            print(e)
        
    def save(self, filename):
        sf.write(filename, self.audio, self.samplerate)

    def load(self, filename, channels=1, samplerate=44100):
        self.channels=channels
        
        self.audio, sr = sf.read(filename)
        self.samplerate=sr
        
    def play(self):
        sd.default.channels = self.channels
        sd.play(self.audio, samplerate=self.samplerate)
    
    def stop(self):
        self.recording = False

    def check_thres(self):
        self.c_thres = True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("rec", help="Merekam suara")
    parser.add_argument("-b","--block_length", help="Panjang block yang di rekam, def:50", type=int, default=50)
    parser.add_argument("-g", "--gain", help="Penambahan gain, def:0", type=int, default=0)
    parser.add_argument("-lf", "--low_freq", help="Frequensi terendah yang di rekam, def:50", type=int, default=50)
    parser.add_argument("-hf", "--high_freq",help="Frequensi tertinggi yang di rekam, def:2000", type=int, default=2000)
    parser.add_argument("-c", "--channels", help="Jumlah channel, def:1", type=int, default=1)
    parser.add_argument("-d", "--device_id", help="Nomor device untuk merekam, def:5", type=int, default=5)
    parser.add_argument("-s", "--samplerate", help="Sample rate perekaman, def:44100", type=int, default=44100)
    parser.add_argument("-t", "--threshold", help="Threshold minimal merekam, def:0", type=int, default=0)
    parser.add_argument("-dur","--duration", help="Lama perekaman dalam detik, def:2", type=int, default=2)
    parser.add_argument("-m","--mode", help="""
mode: 0. Merekam sampai ada input (q, Q atau ENTER)
1. Merekam sepanjang durasi.\n
2. Merekam sampai lewat beberapa kali threshold minimum\n
3. Merekam sampai di panggil stop
4. Check Threshold,
default:0.   
    """, type=int, choices=[0,1,2,3,4], default=0)
    parser.add_argument("-dbg", "--debug", help="Debug mode", type=bool, default=False )
    
    args = parser.parse_args()



    a = Suara(block_length=args.block_length, 
        gain=args.gain, 
        low_freq=args.low_freq, 
        high_freq=args.high_freq, 
        channels=args.channels, 
        device_id=args.device_id,
        samplerate=args.samplerate, 
        threshold=args.threshold, 
        duration=args.duration, 
        mode=args.mode,
        debug=args.debug)

    if args.rec:
        aud ,_ = a.rec()
        
        sd.default.samplerate = 44100
        sd.default.channels = 1
        sd.play(aud)
        a.save("test.wav")