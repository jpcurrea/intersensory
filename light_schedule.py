#!/usr/bin/env python

import os
import sched
import time
import datetime
import logging

import numpy as np

import ISR as isr


class DaySched():
    """A scheduler for presenting stimuli randomly or regularly within regular
    intervals.
    """
    def __init__(self, stimulus, num_bouts=3, bout_duration=10*60,
                 total_duration=12*60*60, random=True, log=True):
        """Setup scheduler to play stimulus object. Stimulus must have a play()
        method.
        """
        self.stimulus = stimulus
        self.bout_duration = bout_duration
        self.total_duration = total_duration
        self.num_bouts = num_bouts
        self.random = random

        self.player = sched.scheduler(timefunc=time.time, delayfunc=time.sleep)
    
        self.log = log
        if self.log:
            self.fn = os.path.join(os.getcwd(),
                                   "log_{}.txt".format(
                                       str(datetime.date.today())))

    def play_bout(self):
        self.log_text("\n{}, start ISR".format(
            str(datetime.datetime.now())))
        try:
            self.stimulus.play(duration=self.bout_duration)
        except:
            self.log_text("\nFailed to play stimulus")            
        self.log_text("\n{}, stop ISR".format(str(datetime.datetime.now())))

    def log_text(self, text):
        if self.log:
            log = open(self.fn, 'a')
            log.write(text)
            log.close()

    def schedule(self):
        if self.log:
            log = open(self.fn, 'a')
            log.write("\n{}, start scheduler".format(
                str(datetime.datetime.now())))
            log.close()

        interval_length = float(self.total_duration)/float(self.num_bouts)
        # self.available_times = np.arange(self.total_duration - self.bout_duration)
        # for bout in range(self.num_bouts):
        #     if self.random:
        #         start_time = np.random.choice(self.available_times)
        #     else:
        #         start_time = 

        if self.random:
            self.times = np.random.rand(self.num_bouts)
        else:
            self.times = np.repeat(.5, self.num_bouts)
        self.times *= (interval_length - self.bout_duration)
        self.times += interval_length*np.arange(self.num_bouts)
	self.times += time.time()
        for bout_time in self.times:
            self.player.enter(delay=bout_time, priority=1, action=self.play_bout,
                              argument=())
    def play(self, ):
        for bout_time in self.times:
            delay = bout_time - time.time()
            time.sleep(delay)
            self.play_bout()
        # self.player.run()
        
if __name__ == "__main__":
    # stim = isr.A_V_ISR("/home/pi/Desktop/maternal_call.wav", light_delay=.34)
    stim = isr.A_V_ISR("/home/pi/Desktop/maternal_call.wav", light_delay=.84)
    day_sequence = DaySched(stim, 3, 10*60, 11.5*60*60)
    # long duration test:
    # day_sequence = DaySched(stim, 12, 10*60, 48*60*60)
    # for calibration/troubleshooting:
    # day_sequence = DaySched(stim, 10, 3, 10*60)
    day_sequence.schedule()
    # import pdb; pdb.set_trace()
    day_sequence.play()
