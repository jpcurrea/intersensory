#!/usr/bin/env python
import subprocess
try:
    pid = subprocess.check_output(['pidof', 'pigpiod'])
except:
    subprocess.call(['sudo', 'pigpiod'])

# from RPi import GPIO
import pigpio
import time
import timeit
import math
import numpy as np
import struct
import wave
import threading
import sched

from scipy import signal, stats
from pygame import mixer, sndarray

    
def sine_audio(freq, dur=10, amplitude=1, sample_rate=44100):
    time = np.arange(0, dur, sample_rate**-1)
    s = amplitude*np.sin(2*np.pi*time*freq)
    return np.array([s, s]).T

def playAudio(output, sample_rate=44100):
    mixer.init(sample_rate)
    preview = output.copy(order='C')
    preview = sndarray.make_sound(preview.astype(np.int16))

    preview.play()
    return mixer, preview

        
class Light():
    """An object that plays a sequence of light levels based on an input array,
    resampling when necessary to fit the lights ideal sampling rate."""
    def __init__(self, arr, arr_rate=10, pwm_rate=50, pwm_pin=12,
                 max_light=100, delay=.1):
        self.delay = delay
        self.arr_rate = arr_rate
        self.pwm_rate = pwm_rate
        self.pwm_pin = pwm_pin
        self.max_light = max_light
        self.arr = arr
        if self.arr.max() != self.max_light:
            self.arr = (self.max_light
                        *(self.arr - self.arr.min())
                        /(self.arr.max() - self.arr.min()))
        self.duration = len(self.arr)*arr_rate**-1
        self.times = np.arange(0, self.duration, arr_rate**-1)

        # setup pwm outpin
        self.GPIO_setup()

        # make a scheduler instance for playing at fixed intervals
        self.player = sched.scheduler(time.time, time.sleep)
        self.play_thread = None

    def GPIO_setup(self):
        """Setup board pin numbers"""
        GPIO.setmode(GPIO.BOARD)

        # not sure why, but these setup methods were done before
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        GPIO.output(self.pwm_pin, GPIO.LOW)  # consider GPIO.HIGH

        # declares the pwm class the light at 0 intensity
        self.pwm = GPIO.PWM(self.pwm_pin, self.pwm_rate)
        self.pwm.start(0)

    def prep(self, delay=None):
        if delay is not None:
            t = delay
        elif self.delay is not None:
            t = self.delay
        else:
            t = 0
        for val in self.arr:
            self.player.enter(t, 1, self.pwm.ChangeDutyCycle, argument=(val,))
            t += self.arr_rate**-1

    def play(self, delay=.1):
        self.player.run()
        self.GPIO_setup()
        
    def play_parallel(self, delay=.1):
        self.prep(delay)
        self.play_thread = threading.Thread(target = self.play, args=(delay,))
        self.playing = self.play_thread.isAlive
        # self.play_thread.daemon = True
        self.play_thread.start()
        self.play_thread.joi

    def stop(self):
        while len(self.player.queue) > 0:
            self.player.cancel(self.player.queue[0])
            
    def playing(self):
        return len(self.player.queue) > 0

    def close(self):
        self.pwm.stop()


class Motor():
    """An object that plays a sequence of motor positions based on an input array,
    resampling when necessary to fit the lights ideal sampling rate."""
    def __init__(self, arr, arr_rate=10, pwm_rate=50, pwm_pin=17,
                 max_light=1850, min_light=1200, cutoff_freq=20, delay=.1,
                 smooth=11):
        self.delay = delay
        self.cutoff = cutoff_freq
        self.arr_rate = arr_rate
        self.pwm_rate = pwm_rate
        self.pwm_pin = pwm_pin
        self.max_light = max_light
        self.min_light = min_light
        self.arr = arr
        if self.arr.max() != self.max_light:
            self.arr = self.min_light + ((self.max_light - self.min_light)
                                         *(self.arr - self.arr.min())
                                         /(self.arr.max() - self.arr.min()))
        self.duration = len(self.arr)*arr_rate**-1
        self.times = np.arange(0, self.duration, arr_rate**-1)

        # setup pwm outpin
        self.GPIO_setup()

        # make a scheduler instance for playing at fixed intervals
        self.player = sched.scheduler(time.time, time.sleep)

        self.smooth(window=smooth)

    def GPIO_setup(self):
        """Setup board pin numbers"""
        self.pwm = pigpio.pi()

    def smooth(self, window=11):
        self.arr = signal.medfilt(self.arr, window)

    def prep(self, delay=None):
        if delay is not None:
            t = delay
        elif self.delay is not None:
            t = self.delay
        else:
            t = 0
        for val in self.arr:
            self.player.enter(t, 1, self.pwm.set_servo_pulsewidth,
                              argument=(self.pwm_pin, val,))
            t += self.arr_rate**-1

    def play(self):
        self.thread = threading.Thread(target=self.play_thread)
        self.thread.start()

    def play_thread(self):
        self.player.run()
        # self.GPIO_setup()
        
    def stop(self):
        while len(self.player.queue) > 0:
            self.player.cancel(self.player.queue[0])
            
    def playing(self):
        return len(self.player.queue) > 0

    def close(self):
        self.pwm.stop()


class Audio():
    """An object that generates a waveform array and can play through the
    appropriate channels."""
    def __init__(self, wav, rate=44100, dur=10, amp=100, volume=1, delay=None):
        self.delay = delay
        self.sample_rate = rate
        if isinstance(wav, str):
            self.filename = wav
            self.get_file()
        elif isinstance(wav, np.ndarray):
            self.arr = wav
            self.duration = len(self.arr)*(self.sample_rate**-1)
        else:
            print("{} object type not supported yet".format(type(wav)))
            return

        mixer.init(self.sample_rate)
        self.player = self.arr.copy(order='C')
        self.player = sndarray.make_sound(self.player.astype('int16'))
        self.player.set_volume(volume)
        self.times = np.arange(0, self.duration, self.sample_rate**-1)

    def get_file(self):
        wav = wave.open(self.filename, 'rb')
        (nchannels, sampwidth, self.sample_rate,
         nframes, comptype, compname) = wav.getparams()
        self.arr = wav.readframes(nframes*nchannels)
        wav.close()
        self.arr = struct.unpack_from("%dh" % nframes * nchannels, self.arr)
        self.arr = np.array(self.arr, int).reshape((nframes, nchannels))
        # self.arr = self.arr.mean(-1)
        self.duration = nframes*(self.sample_rate**-1)

    def prep(self):
        if self.playing:
            self.stop()
        if mixer.get_busy():
            mixer.stop()    
        
    def thread_play(self, dur=None, loops=0, fade=0, delay=None):
        if delay is not None:
            time.sleep(delay)
        elif self.delay is not None:
            time.sleep(self.delay)
        if dur is None:
            dur = int(self.duration/1000.)
        self.player.play(loops, dur, fade)

    def play(self, dur=None, loops=0, fade=0, delay=None):
        threading.Thread(target=self.thread_play,
                         args=(dur, loops, fade, delay)).start()

    def stop(self):
        if self.playing:
            self.player.stop()

    def playing(self):
        return mixer.get_busy()

class A_V_ISR():
    """Object that takes in waveform and combines and light and audio object so
    they can play in or out of synchrony.
    """
    def __init__(self, wav, aud_rate=44100, volume=1, pwm_pin=12,
                 max_light=100, corr=1, corr_err=.01, audio_delay=None,
                 light_delay=.3):
        self.audio_delay = audio_delay
        self.light_delay = light_delay
        self.audio = Audio(wav, rate=aud_rate, volume=volume,
                           delay=self.audio_delay)
        self.audio2light(corr, corr_err)
        self.light = Light(self.light_signal, arr_rate=self.light_rate,
                           pwm_pin=pwm_pin, max_light=max_light,
                           delay=self.light_delay)
        self.light.GPIO_setup()
    def play(self):
        self.light.prep()
        self.audio.prep()
        self.audio.play()
        self.light.play()
        self.light.pwm.ChangeDutyCycle(0)

    def audio2light(self, corr=1, err=.01):
        """Generate a light sequence that is corr correlated with audio signal.
        """
        light_samples = round(self.audio.duration*60)
        light_signal = abs(self.audio.arr.mean(-1))
        self.light_signal = signal.resample(light_signal, light_samples)
        if corr < 1:
            self.light_signal = vcorr(self.light_signal, corr, err)
        ls = self.light_signal
        self.light_signal = 100*(ls - ls.min())/(ls.max() - ls.min())
        self.light_signal[self.light_signal < 5] = 0
        self.light_rate = float(light_samples)/float(self.audio.duration)

    def stop(self):
        self.light.stop()
        self.light.GPIO_setup()
        self.audio.stop()

    def close(self):
        self.light.close()

    def playing(self):
        return any((self.light.playing(), self.audio.playing()))


class A_M_ISR():
    """Object that takes in waveform and combines and light and audio object so
    they can play in or out of synchrony.
    """
    def __init__(self, wav, aud_rate=44100, volume=1, pwm_pin=11,
                 max_light=1850, corr=1, corr_err=.01, motor_rate=50,
                 audio_delay=0, motor_delay=0):
        self.audio_delay = audio_delay
        self.motor_delay = motor_delay
        self.motor_rate= motor_rate
        self.audio = Audio(wav, rate=aud_rate, volume=volume,
                           delay=self.audio_delay)
        self.audio2motor(corr, corr_err)
        self.motor = Motor(self.motor_signal, arr_rate=self.motor_rate,
                           pwm_pin=pwm_pin, max_light=max_light,
                           delay=self.motor_delay)
        self.motor.GPIO_setup()

    def play(self):
        self.motor.prep()
        self.audio.prep()
        self.audio.play()
        self.motor.play()
        self.motor.pwm.set_servo_pulsewidth(self.motor.pwm_pin, 1200)

    def audio2motor(self, corr=1, err=.01):
        """Generate a motor position sequence that is corr correlated with audio
        signal.
        """
        motor_samples = round(self.audio.duration*self.motor_rate)
        motor_signal = abs(self.audio.arr.mean(-1))
        self.motor_signal = signal.resample(motor_signal, motor_samples)
        if corr < 1:
            self.motor_signal = vcorr(self.motor_signal, corr, err)
        ms = self.motor_signal
        self.motor_signal = (ms - ms.min())/(ms.max() - ms.min())
        self.motor_signal[self.motor_signal < .05] = 0

    def stop(self):
        self.motor.stop()
        # self.motor.GPIO_setup()
        self.audio.stop()

    def close(self):
        self.motor.close()

    def playing(self):
        return any((self.motor.playing(), self.audio.playing()))

class A_2M_ISR():
    """Object that takes in waveform and displays 2 motor and 1 audio objects so
    they can play in or out of synchrony.
    """
    def __init__(self, wav, aud_rate=44100, volume=1, pwm_pin1=17,
                 pwm_pin2=18, max_light=1850, corr=1, corr_err=.01,
                 motor_rate=50, audio_delay=0,
                 motor1_delay=0, motor2_delay=.5, smooth=21):
        self.pwm_pin1=pwm_pin1
        self.pwm_pin2=pwm_pin2
        self.smooth=smooth
        self.audio_delay = audio_delay
        self.motor1_delay = motor1_delay
        self.motor2_delay = motor2_delay
        self.motor_rate= motor_rate
        self.audio = Audio(wav, rate=aud_rate, volume=volume,
                           delay=self.audio_delay)
        self.audio2motor(corr, corr_err)
        self.motor1 = Motor(self.motor_signal, arr_rate=self.motor_rate,
                            pwm_pin=self.pwm_pin1, max_light=max_light,
                            delay=self.motor1_delay, smooth=self.smooth)
        self.motor2 = Motor(self.motor_signal, arr_rate=self.motor_rate,
                            pwm_pin=self.pwm_pin2, max_light=max_light,
                            delay=self.motor2_delay, smooth=self.smooth)
        self.motor1.GPIO_setup()
        self.motor2.GPIO_setup()

    def play(self):
        if not self.playing():
            self.motor1.prep()
            self.motor2.prep()
            self.audio.prep()
            self.audio.play()
            self.motor1.play()
            self.motor2.play()
        # self.motor1.pwm.set_servo_pulsewidth(self.motor1.pwm_pin, 1000)
        # self.motor2.pwm.set_servo_pulsewidth(self.motor2.pwm_pin, 1000)

    def audio2motor(self, corr=1, err=.01):
        """Generate a motor position sequence that is corr correlated with audio
        signal.
        """
        motor_samples = round(self.audio.duration*self.motor_rate)
        motor_signal = abs(self.audio.arr.mean(-1))
        self.motor_signal = signal.resample(motor_signal, motor_samples)
        if corr < 1:
            self.motor_signal = vcorr(self.motor_signal, corr, err)
        ms = self.motor_signal
        self.motor_signal = (ms - ms.min())/(ms.max() - ms.min())
        self.motor_signal[self.motor_signal < .05] = 0

    def stop(self):
        self.motor1.stop()
        self.motor2.stop()
        # self.motor.GPIO_setup()
        self.audio.stop()

    def close(self):
        self.motor.close()

    def playing(self):
        return any((self.motor1.playing(),
                    self.motor2.playing(),
                    self.audio.playing()))


        
def vcorr(signal, corr, err=.01):
    cval = 1. - (corr/2. + .5)
    ncorr = 1
    sigfft = np.fft.rfft(signal)
    newsig = np.copy(signal)
    corrs = []
    # for x in range(100):
    while abs(ncorr - corr) > err:
        # randangs = 2*(np.random.rand(len(signal)) - .5)
        # randangs *= 2*np.pi*cval
        randangs = np.pi/6.*np.random.randn(len(signal)) + cval*np.pi
        randangcnums = np.cos(randangs) + 1j*np.sin(randangs)
        newsigfft = sigfft * randangcnums[:len(signal)/2 + 1]
        newsig = np.fft.irfft(newsigfft)
        ncorr = stats.pearsonr(newsig, signal)[0]
        corrs += [ncorr]
    # return corrs
    return newsig

isr = A_2M_ISR("./maternal_call.wav", corr=-1, corr_err=.1, audio_delay=0)
# m2 = Motor(isr.motor2.arr, arr_rate=50,
#           pwm_pin=17, max_light=1800, min_light=1000,
#            delay=0, smooth=21)

