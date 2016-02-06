import sys
#sys.path.insert(0, r'/home/fhdiaze/Code/localization-agent/tracking/')
import TrajectorySimulator as trsim
import numpy as np
import pickle

COCO_DIR = '/home/datasets/datasets1/mscoco'

import time
import os
import multiprocessing

SEQUENCE_LENGTH = 60
IMG_HEIGHT = 100
IMG_WIDTH = 100

# FUNCTION
# Make simulation of a single sequence given the simulator
def simulate(simulator, grayscale):
  data = []
  label = []
  simulator.start()
  for j, frame in enumerate(simulator):
    if grayscale:
      data += [np.asarray(frame.convert('L'))]
    else:
      data += [np.asarray(frame.convert('RGB'))]
    label += [simulator.getBox()]
  return data, label

def wrapped_simulate(params):
    simulator, grayscale = params
    return simulate(simulator, grayscale)

## CLASS
## Simulator with Gaussian mixture models of movement
class GaussianGenerator(object):
    def __init__(self, seqLength=60, imageSize=IMG_WIDTH, dataDir='.', grayscale=True):
        self.imageSize = imageSize
        self.seqLength = seqLength
        trajectoryModelPath = dataDir + '/gmmDenseAbsoluteNormalizedOOT.pkl'
        # Generates a factory to create random simulator instances
        #self.factory = trsim.SimulatorFactory(
        #    COCO_DIR,
        #    trajectoryModelPath=trajectoryModelPath,
        #    summaryPath = dataDir + '/cocoTrain2014Summary.pkl',
        #    scenePathTemplate='images/train2014', objectPathTemplate='images/train2014'
        #    )
        modelFile = open(trajectoryModelPath, 'r')
        self.trajectoryModel = pickle.load(modelFile)
        modelFile.close()
        self.pool = None
        self.grayscale = grayscale

    def getSimulator(self):
        if self.factory is None:
            simulator = self.getSingleSimulator()
        else:
            emptyPolygon = True
            while emptyPolygon:
                simulator = self.factory.createInstance(drawBox=False, camera=True, drawCam=False, cameraContentTransforms=None, camSize=(self.imageSize, self.imageSize))
                emptyPolygon = len(simulator.polygon) == 0
        return simulator

    def getSingleSimulator(self):
        scenePath = COCO_DIR + "/images/train2014/COCO_train2014_000000011826.jpg"
        objectPath = COCO_DIR + "/images/train2014/COCO_train2014_000000250067.jpg"
        polygon = [618.23, 490.13, 615.76, 488.48, 612.89, 488.48, 610.42, 491.36, 609.19, 494.65, 607.54, 498.35, 607.13, 503.29, 606.72, 510.28, 610.42, 512.33, 612.89, 513.15, 616.18, 513.98, 619.88, 513.57, 621.93, 510.28, 623.58, 506.58, 623.58, 503.7, 623.16, 500.0, 621.93, 496.71, 619.46, 493.42]
        simulator = trsim.TrajectorySimulator(scenePath, objectPath, polygon=polygon, trajectoryModel=self.trajectoryModel, camSize=(self.imageSize, self.imageSize))
        
        return simulator

    def initResults(self, batchSize):
        if self.grayscale:
            data = np.zeros((batchSize, self.seqLength, self.imageSize, self.imageSize), dtype=np.float32)
        else:
            #TODO: validate case of alpha channel
            data = np.zeros((batchSize, self.seqLength, self.imageSize, self.imageSize, 3), dtype=np.float32)
        label = np.zeros((batchSize, self.seqLength, 4))
        return data, label

    def getBatch(self, batchSize):
        data, label = self.initResults(batchSize)
        for i in range(batchSize):
            simulator = self.getSingleSimulator()
            simulator.start()
            for j, frame in enumerate(simulator):
                if self.grayscale:
                    data[i, j, :, :] = np.asarray(frame.convert('L'))
                else:
                    data[i, j, :, :, :] = np.asarray(frame.convert('RGB'))
                label[i, j] = simulator.getBox()
                
        return data, label

    def getBatchInParallel(self, batchSize):
        # Lazy initialization
        if self.pool is None:
            numProcs =  multiprocessing.cpu_count() # max number of cores
            self.pool = multiprocessing.Pool(numProcs)

        # Process simulations in parallel
        try:
            results = self.pool.map_async(wrapped_simulate, [(self.getSingleSimulator(), self.grayscale) for i in range(batchSize)]).get(9999)
        except Exception as e:
            print 'Exception raised during map_async: {}'.format(e)
            self.pool.terminate()
            sys.exit()

        # Collect results and put them in the output
        index = 0
        data, label = self.initResults(batchSize)
        for frames, targets in results:
            if self.grayscale:
                data[index,:,:,:] = frames
            else:
                data[index,:,:,:,:] = frames
            label[index,:,:] = targets
            index += 1
        
        return data, label
