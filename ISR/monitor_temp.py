#!/usr/bin/env python

from matplotlib import pyplot as plt
import numpy as np
import subprocess
import time
import datetime
import os


# fig = plt.figure()
# ax = fig.add_subplot(111)
# plt.xlim(-120, 0)
# ax, = plt.plot([], [])
# plt.show()

fn = "./temps.csv"
if os.path.isfile(fn) is False:
    log = open(fn, 'w')
    log.write("\n")
    log.close()

temps = []
while True:
    x = 0
    temp = subprocess.check_output(['/opt/vc/bin/vcgencmd', 'measure_temp'])
    temp = float(temp[5:].split("'C\n")[0])
    print(str(temp))
    # temps += [[datetime.datetime.now(), temp]]
    log = open(fn, 'a')
    log.write("\n{},{}".format(str(datetime.datetime.now()),
                                str(temp)))
    log.close()
    # if x == 60:
    #     temps = np.array(temps)
    #     old_temps = np.load(fn)
    #     temps = np.append(old_temps, temps)
    #     np.save(fn, temps)
    #     temps = []
    #     x = 0
    # x += 1
    time.sleep(5)
