__author__ = "Juan C. Caicedo, caicedo@illinois.edu"

import RLConfig as config

import numpy as np
import scipy.io
import MemoryUsage

import RLConfig as config

NUM_ACTIONS = config.geti('outputActions')
TEMPORAL_WINDOW = config.geti('temporalWindow')
HISTORY_FACTOR = config.geti('historyFactor')

class BoxSearchAgent():

  image = None
  observation = None
  action = None
  reward = None
  timer = 0
  
  def __init__(self, qnet, learner=None):
    self.controller = qnet
    self.learner = learner
    self.avgReward = 0
    self.replayMemory = None

  def startReplayMemory(self, memoryImages, recordsPerImage, recordSize):
    self.replayMemory = ReplayMemory(memoryImages, recordsPerImage, recordSize)

  def integrateObservation(self, obs):
    if obs['image'] != self.image:
      self.actionsH = [0 for i in range(NUM_ACTIONS)]
      self.observation = np.zeros( (TEMPORAL_WINDOW,obs['state'].shape[0]), np.float32 )
      self.image = obs['image']
      self.timer = 0
      self.avgReward = 0.0
    for t in range(TEMPORAL_WINDOW-1):
      self.observation[t+1,:] = self.observation[t,:]
    self.observation[0,:] = obs['state']
    self.action = None
    self.reward = None

  def getAction(self):
    assert self.observation != None
    assert self.action == None
    assert self.reward == None

    self.timer += 1
    obs = self.observation.reshape( (1,self.observation.shape[0]*self.observation.shape[1]) )
    values = self.controller.getActionValues(obs)
    self.action = np.argmax(values, 1)[0]
    v = values[0,self.action]
    return (self.action,float(v))

  def giveReward(self, r):
    assert self.observation != None
    assert self.action != None
    assert self.reward == None

    self.reward = r
    self.avgReward = (self.avgReward*(self.timer-1) + r)/(self.timer)
    if self.replayMemory != None:
      obs = self.observation.reshape( (self.observation.shape[0]*self.observation.shape[1]))
      self.replayMemory.add(self.image, self.timer, self.action, obs, self.reward)
    self.actionsH[self.action] += 1
    print 'Agent::MemoryRecord => image:',self.image,'time:',self.timer,'action:',self.action,'reward',self.reward,'avgReward:',self.avgReward

  def reset(self):
    print 'Agent::reset',self.actionsH,self.avgReward
    self.image = ''
    self.observation = None
    self.action = None
    self.reward = None

  def learn(self):
    print 'Agent:learn:'
    if self.learner != None and self.replayMemory != None:
      self.learner.learn(self.replayMemory, self.controller)
      self.controller.loadNetwork()

class ReplayMemory():

  def __init__(self, numImages, recordsPerImage, recordSize):
    self.O = np.zeros( (HISTORY_FACTOR*numImages*recordsPerImage, recordSize), np.float32 )
    self.A = np.zeros( (HISTORY_FACTOR*numImages*recordsPerImage, 1), np.int )
    self.R = np.zeros( (HISTORY_FACTOR*numImages*recordsPerImage, 1), np.float32 )
    self.recordsPerImage = recordsPerImage
    self.pointer = -1
    self.usableRecords = 0

  def add(self, img, time, action, observation, reward):
    if self.pointer < self.O.shape[0]-1:
      self.pointer += 1
    else:
      self.pointer = 0

    self.A[self.pointer,0] = action
    self.O[self.pointer,:] = observation
    self.R[self.pointer,0] = reward

    if self.usableRecords < self.O.shape[0]:
      self.usableRecords += 1

