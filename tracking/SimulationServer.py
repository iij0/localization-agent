import h5py
import numpy as np
import time
import VideoSequenceData as vsd
import os,sys
from multiprocessing import Process, JoinableQueue, Queue

GEN = 16 # Number of generator objects
SIM = 12 # Simulations per generator

# FUNCTION
# Distribute work in multiple cores
def worker(inQueue, outQueue, simulations, output):
  for data in iter(inQueue.get,'stop'):
    index,sequenceGenerator = data
    results = []
    for i in range(simulations):
      r = simulate(sequenceGenerator)
      results.append(r)
    outQueue.put(results)
    inQueue.task_done()
  inQueue.task_done()
  return True

# FUNCTION
# Coordination of multiple workers and their results
def processData(sequenceGenerators, simulations, output):
  numProcs = min(len(sequenceGenerators),GEN) # max number of cores: GEN
  taskQueue = JoinableQueue()
  resultQueue = Queue()
  processes = []
  # Start workers
  for i in range(numProcs):
    t = Process(target=worker, args=(taskQueue, resultQueue, simulations, output))
    t.daemon = True
    t.start()
    processes.append(t)

  # Assign tasks to workers
  i = 0
  for gen in sequenceGenerators:
    taskQueue.put( (i,gen) )
    i += simulations
  for i in range(len(processes)):
    taskQueue.put('stop')

  # Collect results and send them to an HDF5 file
  index = 0
  for k in range(numProcs):
    data = resultQueue.get()
    for frames,targets in data:
      output.create_dataset("frames"+str(index),data=frames)
      output.create_dataset("targets"+str(index),data=targets)
      index += 1

# FUNCTION
# Simulation of one sequence
def simulate(seq):
  seq.prepareSequence()
  # Store in a numpy array
  simFrames = np.zeros((vsd.totalFrames,vsd.channels,vsd.imgSize,vsd.imgSize))
  simTargets = np.zeros((vsd.totalFrames,4))
  step = 0
  while seq.nextStep():
    simFrames[step,:,:,:] = seq.getFrame()
    simTargets[step,:] = seq.getMove()
    step += 1
  return (simFrames,simTargets)

# USE
# Main Procedure
if __name__ == '__main__':

  if len(sys.argv) < 2:
    print 'Use: SimulationServer.py workingDir'
    sys.exit()

  workingDir = sys.argv[1]
  filePath = workingDir + 'simulation.hdf5' # Output filename

  processFile = filePath + '.running'
  os.system('touch ' + processFile)
  while os.path.exists(processFile):
    startTime = time.time()
    outFile = h5py.File(filePath,'w')
    generators = [vsd.VideoSequenceData(workingDir) for i in range(GEN)]
    processData(generators, SIM, outFile)
    outFile.close()
    os.system('touch ' + filePath + '.ready')
    print 'Simulations done in',(time.time() - startTime),'seconds'

    while os.path.exists(filePath) and os.path.exists(processFile):
      time.sleep(0.1)

  print 'Simulation server shut down'