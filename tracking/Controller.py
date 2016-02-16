import argparse as AP
import RecurrentTracker
import time
import numpy as NP

from CaffeCnn import CaffeCnn
from TheanoGruRnn import TheanoGruRnn
from GaussianGenerator import GaussianGenerator

def clock(m, st): 
    print m,(time.time()-st)

class Controller(object):
    
    def train(self, tracker, epochs, batches, batchSize, generator, imgHeight, trackerModelPath):
        for i in range(0, epochs):
            train_cost = 0
            et = time.time()
            for j in range(0, batches):
                st = time.time()
                data, label = generator.getBatch(batchSize)
        
                if generator.grayscale:
                    data = data[:, :, NP.newaxis, :, :]
                data /= 255.0
                label = label / (imgHeight / 2.) - 1.
                clock('Simulations',st)
        
                # TODO: We can also implement a 'replay memory' here to store previous simulations and reuse them again later during training.
                # The basic idea is to store sequences in a tensor of a predefined capacity, and when it's full we start sampling sequences
                # from the memory with certain probability. The rest of the time new sequences are simulated. This could save some processing time.
                
                st = time.time()                
                cost, bbox_seq = tracker.fit(data, label)
                clock('Training',st)
                
                print 'Cost', i, j, cost
                train_cost += cost
            print 'Epoch average loss (train, test)', train_cost / (batches*batchSize)
            clock('Epoch time',et)
            tracker.rnn.saveModel(trackerModelPath)
                
### Utility functions

def build_parser():
    parser = AP.ArgumentParser(description='Trains a RNN tracker')
    parser.add_argument('--dataDir', help='Directory of trajectory model', type=str, default='/home/fmpaezri/repos/localization-agent/notebooks')
    parser.add_argument('--epochs', help='Number of epochs with 32000 example sequences each', type=int, default=1)
    parser.add_argument('--batchSize', help='Number of elements in batch', type=int, default=4)
    parser.add_argument('--imgHeight', help='Image Height', type=int, default=224)
    parser.add_argument('--imgWidth', help='Image width', type=int, default=224)
    parser.add_argument('--gruStateDim', help='Dimension of GRU state', type=int, default=256)
    parser.add_argument('--seqLength', help='Length of sequences', type=int, default=60)
    #TODO: Check default values or make required
    parser.add_argument('--trackerModelPath', help='Name of model file', type=str, default='model.pkl')
    parser.add_argument('--caffeRoot', help='Root of Caffe dir', type=str, default='/home/jccaicedo/caffe/')
    parser.add_argument('--cnnModelPath', help='Name of model file', type=str, default='/home/jccaicedo/data/simulations/cnns/googlenet/bvlc_googlenet.caffemodel')
    parser.add_argument('--deployPath', help='Path to Protobuf deploy file for the network', type=str, default='/home/jccaicedo/data/simulations/cnns/googlenet/deploy.prototxt')
    parser.add_argument('--zeroTailFc', help='', type=bool, default=False)
    parser.add_argument('--meanImage', help='Path to mean image for ImageNet dataset relative to Caffe', default='python/caffe/imagenet/ilsvrc_2012_mean.npy')
    parser.add_argument('--layerKey', help='Key string of layer name to use as features', type=str, default='inception_5b/output')
    parser.add_argument('--learningRate', help='SGD learning rate', type=float, default=0.0005)
    parser.add_argument('--useCUDNN', help='Use CUDA CONV or THEANO', type=bool, default=False)
    parser.add_argument('--pretrained', help='Use pretrainde network (redundant)', type=bool, default=False)
    return parser

if __name__ == '__main__':
    
    # Configuration
    
    parser = build_parser()
    args = parser.parse_args()
    globals().update(vars(args))
    
    #TODO: make arguments not redundant
    if pretrained:
        cnn = CaffeCnn(imgHeight, imgWidth, deployPath, cnnModelPath, caffeRoot, batchSize, seqLength, meanImage, layerKey)
        gruInputDim = reduce(lambda a,b: a*b, cnn.outputShape()[-3:])
    else:
        cnn = gruInputDim = None
    rnn = TheanoGruRnn(gruInputDim, gruStateDim, batchSize, seqLength, zeroTailFc, learningRate, useCUDNN, imgHeight, pretrained)
    
    rnn.loadModel(trackerModelPath)
    
    tracker = RecurrentTracker(cnn, rnn)
    
    generator = GaussianGenerator(dataDir=dataDir, seqLength=seqLength, imageSize=imgHeight, grayscale=False)
    
    controller = Controller()
    M = 32000 # Constant number of example sequences per epoch
    batches = M/batchSize
    try:
        controller.train(tracker, epochs, batches, batchSize, generator, imgHeight, trackerModelPath)
    except KeyboardInterrupt:
        rnn.saveModel(trackerModelPath)
    
