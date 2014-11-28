import os,sys
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import utils as cu

params = cu.loadParams("logdir")

fig, ax = plt.subplots(nrows=2, ncols=3)
fig.set_size_inches(18.5,10.5)

# Parse Caffe Log
loss = []
for l in open(params['logdir'] + '/caffe.log'):
  if l.find('loss =') != -1:
    loss.append( float(l.split()[-1]) )
i = np.argmax(loss)
loss[i] = np.average(loss)
ax[0,0].plot(range(len(loss)), loss)
ax[0,0].set_title('QNetwork Loss')

# Parse RL output
avgRewards = []
epochRecall = []
epochIoU = []
positives = dict([ (i,0) for i in range(9) ])
negatives = dict([ (i,0) for i in range(9) ])
for l in open(params['logdir'] + '/rl.log'):
  if l.find('Agent::MemoryRecord') != -1:
    parts = l.split()
    action = int(parts[7])
    reward = float(parts[9])
    if reward > 0:
      positives[action] += 1
    else:
      negatives[action] += 1
  elif l.find('reset') != -1:
    avgRewards.append( float(l.split()[-1]) )
  elif l.find('Epoch Recall') != -1:
    epochRecall.append( float(l.split()[-1]) )
  elif l.find('MaxIoU') != -1:
    epochIoU.append( float(l.split()[-1]) )
ax[1,0].plot(range(len(avgRewards)), avgRewards)
ax[1,0].set_title('Average Reward Per Episode')
ax[0,1].plot(range(len(epochRecall)), epochRecall)
ax[0,1].set_title('Recall per Epoch')
ax[1,1].plot(range(len(epochIoU)), epochIoU)
ax[1,1].set_title('MaxIoU per Epoch')
pos = positives.keys()
pos.sort()
ax[0,2].barh(range(len(pos)), [positives[k] for k in pos] )
ax[0,2].set_title('Distribution of positive rewards')
neg = negatives.keys()
neg.sort()
ax[1,2].barh(range(len(neg)), [negatives[k] for k in neg] )
ax[1,2].set_title('Distribution of negative rewards')
plt.savefig(params['logdir'] + '/report.png')