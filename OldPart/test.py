import matplotlib.pyplot as plt 
from collections import deque 
import random 
import numpy as np

data_points = deque(maxlen=100) 

fig, ax = plt.subplots() 
line, = ax.plot([], [], color='black') 

ax.set_xlim(0, 100)
ax.set_ylim(-10, 10) 

i=0
while 1: 
    ax.set_xlim(i-10, i)


    new_x = i
    new_y = np.sin(i)
    data_points.append((new_x, new_y)) 

    x_values = [x for x, y in data_points] 
    y_values = [y for x, y in data_points] 
    line.set_data(x_values, y_values) 
    plt.pause(0.01)


    i+=0.1


    line.set_data([], []) 

plt.show() 