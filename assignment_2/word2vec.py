#!/usr/bin/env python

import argparse
import numpy as np
import random

from utils.gradcheck import gradcheck_naive, grad_tests_softmax, grad_tests_negsamp
from utils.utils import normalizeRows, softmax


def sigmoid(x):
    """
    Compute the sigmoid function for the input here.
    Arguments:
    x -- A scalar or numpy array.
    Return:
    s -- sigmoid(x)
    """

    ### YOUR CODE HERE (~1 Line)

    s = 1./(1+np.exp(-x))

    ### END YOUR CODE

    return s


def naiveSoftmaxLossAndGradient(
    centerWordVec,
    outsideWordIdx,
    outsideVectors,
    dataset
):
    """ Naive Softmax loss & gradient function for word2vec models

    Implement the naive softmax loss and gradients between a center word's 
    embedding and an outside word's embedding. This will be the building block
    for our word2vec models. For those unfamiliar with numpy notation, note 
    that a numpy ndarray with a shape of (x, ) is a one-dimensional array, which
    you can effectively treat as a vector with length x.

    Arguments:
    centerWordVec -- numpy ndarray, center word's embedding
                    in shape (word vector length, )
                    (v_c in the pdf handout)
    outsideWordIdx -- integer, the index of the outside word
                    (o of u_o in the pdf handout)
    outsideVectors -- outside vectors is
                    in shape (num words in vocab, word vector length) 
                    for all words in vocab (tranpose of U in the pdf handout)
    dataset -- needed for negative sampling, unused here.

    Return:
    loss -- naive softmax loss
    gradCenterVec -- the gradient with respect to the center word vector
                     in shape (word vector length, )
                     (dJ / dv_c in the pdf handout)
    gradOutsideVecs -- the gradient with respect to all the outside word vectors
                    in shape (num words in vocab, word vector length) 
                    (dJ / dU)
    """

    ### YOUR CODE HERE (~6-8 Lines)

    loss_temp = np.dot(outsideVectors,centerWordVec)
    yh = softmax(loss_temp)
    loss = -np.log(yh)
    loss = loss[outsideWordIdx]

    y = np.zeros(outsideVectors.shape[0])
    y[outsideWordIdx]=1

    gradCenterVec = -np.dot(np.transpose(outsideVectors),y-yh)
    
    num_vocab, word_vec_length = outsideVectors.shape
    
    gradOutsideVecs = np.dot((yh-y)[:,np.newaxis],centerWordVec[np.newaxis,:])    
 
    ### Please use the provided softmax function (imported earlier in this file)
    ### This numerically stable implementation helps you avoid issues pertaining
    ### to integer overflow. 

    ### END YOUR CODE

    return loss, gradCenterVec, gradOutsideVecs


def getNegativeSamples(outsideWordIdx, dataset, K):
    """ Samples K indexes which are not the outsideWordIdx """

    negSampleWordIndices = [None] * K
    for k in range(K):
        newidx = dataset.sampleTokenIdx()
        while newidx == outsideWordIdx:
            newidx = dataset.sampleTokenIdx()
        negSampleWordIndices[k] = newidx
    return negSampleWordIndices


def negSamplingLossAndGradient(
    centerWordVec,
    outsideWordIdx,
    outsideVectors,
    dataset,
    K=10
):
    """ Negative sampling loss function for word2vec models

    Implement the negative sampling loss and gradients for a centerWordVec
    and a outsideWordIdx word vector as a building block for word2vec
    models. K is the number of negative samples to take.

    Note: The same word may be negatively sampled multiple times. For
    example if an outside word is sampled twice, you shall have to
    double count the gradient with respect to this word. Thrice if
    it was sampled three times, and so forth.

    Arguments/Return Specifications: same as naiveSoftmaxLossAndGradient
    """

    # Negative sampling of words is done for you. Do not modify this if you
    # wish to match the autograder and receive points!
    negSampleWordIndices = getNegativeSamples(outsideWordIdx, dataset, K)
    indices = [outsideWordIdx] + negSampleWordIndices

    ### YOUR CODE HERE (~10 Lines)
    #print(f'negative word indices are: {negSampleWordIndices}')

    outsideVectors_neg = outsideVectors[indices,:]
    outsideVectors_neg[1:,:] = -outsideVectors_neg[1:,:]
    Uv = np.dot(outsideVectors_neg,centerWordVec) 
    
    loss = np.sum(-np.log(sigmoid(np.dot(outsideVectors_neg,centerWordVec))))
    gradCenterVec = -np.matmul(np.transpose(outsideVectors_neg),(1-sigmoid(Uv)))
    
    gradOutsideVecs_temp = -1*np.dot((1-sigmoid(Uv))[:,np.newaxis],centerWordVec[np.newaxis,:])
    gradOutsideVecs = np.zeros_like(outsideVectors)


    for o in [outsideWordIdx]:
        gradOutsideVecs[o,:] += gradOutsideVecs_temp[0,:]

    for i, s in enumerate(negSampleWordIndices,1):
        gradOutsideVecs[s,:] += -gradOutsideVecs_temp[i,:]



   # loss = 0
   # loss += -np.log(sigmoid(np.dot(outsideVectors[outsideWordIdx,:],centerWordVec)))

   # for s in negSampleWordIndices:
   #     loss += -np.log(sigmoid(np.dot(-1*outsideVectors[s,:],centerWordVec)))

    #print(f'Losses: ({loss-lossV0})')

   # gradCenterVec = -(1-sigmoid(np.dot(outsideVectors[outsideWordIdx,:],centerWordVec)))*outsideVectors[outsideWordIdx,:]
   # for s in negSampleWordIndices:
     #   gradCenterVec += (1-sigmoid(np.dot(-outsideVectors[s,:],centerWordVec)))*outsideVectors[s,:]
   # print(f'gradcenterVec diff: {gradCenterVecV0-gradCenterVec}')
    #gradOutsideVecs = np.zeros_like(outsideVectors)   
    
    #for s in negSampleWordIndices:
     #   gradOutsideVecs[s,:] += (1-sigmoid(np.dot(-1*outsideVectors[s,:],centerWordVec)))*centerWordVec
#
   # for o in [outsideWordIdx]:
   #     gradOutsideVecs[o,:] += -(1-sigmoid(np.dot(outsideVectors[o,:],centerWordVec)))*centerWordVec

  #  print(f'gradoutsidevec diff: {gradOutsideVecs-gradOutsideVecsV0}')


    ### Please use your implementation of sigmoid in here.

    ### END YOUR CODE

    return loss, gradCenterVec, gradOutsideVecs


def skipgram(currentCenterWord, windowSize, outsideWords, word2Ind,
             centerWordVectors, outsideVectors, dataset,
             word2vecLossAndGradient=naiveSoftmaxLossAndGradient):
    """ Skip-gram model in word2vec

    Implement the skip-gram model in this function.

    Arguments:
    currentCenterWord -- a string of the current center word
    windowSize -- integer, context window size
    outsideWords -- list of no more than 2*windowSize strings, the outside words
    word2Ind -- a dictionary that maps words to their indices in
              the word vector list
    centerWordVectors -- center word vectors (as rows) is in shape 
                        (num words in vocab, word vector length) 
                        for all words in vocab (V in pdf handout)
    outsideVectors -- outside vectors is in shape 
                        (num words in vocab, word vector length) 
                        for all words in vocab (transpose of U in the pdf handout)
    word2vecLossAndGradient -- the loss and gradient function for
                               a prediction vector given the outsideWordIdx
                               word vectors, could be one of the two
                               loss functions you implemented above.

    Return:
    loss -- the loss function value for the skip-gram model
            (J in the pdf handout)
    gradCenterVec -- the gradient with respect to the center word vector
                     in shape (num words in vocab, word vector length)
                     (dJ / dv_c in the pdf handout)
    gradOutsideVecs -- the gradient with respect to all the outside word vectors
                    in shape (num words in vocab, word vector length) 
                    (dJ / dU)
    """


    loss = 0.0
    gradCenterVecs = np.zeros(centerWordVectors.shape)
    gradOutsideVectors = np.zeros(outsideVectors.shape)

    ### YOUR CODE HERE (~8 Lines)

    center_word_index = word2Ind[currentCenterWord]
    center_word_vec = centerWordVectors[center_word_index,:]
    outside_word_indices = [word2Ind[outside] for outside in outsideWords] 

   # print(center_word_vec)
   # print(outside_word_indices)

   # print(f'diff: {len(outside_word_indices)/2-windowSize}')

    #print(f'center word index is: {word2Ind[currentCenterWord]}')
    #print(f'outside word indices are: {outside_word_indices}')

    for ind in outside_word_indices:
        gradCenterVecs_temp = np.zeros(outsideVectors.shape)
        loss_temp = 0
        gradOutsideVectors_temp = np.zeros(outsideVectors.shape)

        loss_temp, gradCenterVecs_temp, gradOutsideVectors_temp = word2vecLossAndGradient(center_word_vec,ind,outsideVectors,dataset)
        
        loss += loss_temp
        gradCenterVecs[center_word_index,:] += gradCenterVecs_temp
        gradOutsideVectors += gradOutsideVectors_temp

    ### END YOUR CODE
    
    #print(f'shape of gradCenterVecs: {gradCenterVecs.shape}')
    #print(f'shape of gradOutsideVectors: {gradOutsideVectors.shape}')

    return loss, gradCenterVecs, gradOutsideVectors


#############################################
# Testing functions below. DO NOT MODIFY!   #
#############################################

def word2vec_sgd_wrapper(word2vecModel, word2Ind, wordVectors, dataset,
                         windowSize,
                         word2vecLossAndGradient=naiveSoftmaxLossAndGradient):
    batchsize = 50
    loss = 0.0
    grad = np.zeros(wordVectors.shape)
    N = wordVectors.shape[0]
    centerWordVectors = wordVectors[:int(N/2),:]
    outsideVectors = wordVectors[int(N/2):,:]
    for i in range(batchsize):
        windowSize1 = random.randint(1, windowSize)
        centerWord, context = dataset.getRandomContext(windowSize1)

        c, gin, gout = word2vecModel(
            centerWord, windowSize1, context, word2Ind, centerWordVectors,
            outsideVectors, dataset, word2vecLossAndGradient
        )
        loss += c / batchsize
        grad[:int(N/2), :] += gin / batchsize
        grad[int(N/2):, :] += gout / batchsize

    return loss, grad

def test_sigmoid():
    """ Test sigmoid function """
    print("=== Sanity check for sigmoid ===")
    assert sigmoid(0) == 0.5
    assert np.allclose(sigmoid(np.array([0])), np.array([0.5]))
    assert np.allclose(sigmoid(np.array([1,2,3])), np.array([0.73105858, 0.88079708, 0.95257413]))
    print("Tests for sigmoid passed!")

def getDummyObjects():
    """ Helper method for naiveSoftmaxLossAndGradient and negSamplingLossAndGradient tests """

    def dummySampleTokenIdx():
        return random.randint(0, 4)

    def getRandomContext(C):
        tokens = ["a", "b", "c", "d", "e"]
        return tokens[random.randint(0,4)], \
            [tokens[random.randint(0,4)] for i in range(2*C)]

    dataset = type('dummy', (), {})()
    dataset.sampleTokenIdx = dummySampleTokenIdx
    dataset.getRandomContext = getRandomContext

    random.seed(31415)
    np.random.seed(9265)
    dummy_vectors = normalizeRows(np.random.randn(10,3))
    dummy_tokens = dict([("a",0), ("b",1), ("c",2),("d",3),("e",4)])

    return dataset, dummy_vectors, dummy_tokens

def test_naiveSoftmaxLossAndGradient():
    """ Test naiveSoftmaxLossAndGradient """
    dataset, dummy_vectors, dummy_tokens = getDummyObjects()

    print("==== Gradient check for naiveSoftmaxLossAndGradient ====")
    def temp(vec):
        loss, gradCenterVec, gradOutsideVecs = naiveSoftmaxLossAndGradient(vec, 1, dummy_vectors, dataset)
        return loss, gradCenterVec
    gradcheck_naive(temp, np.random.randn(3), "naiveSoftmaxLossAndGradient gradCenterVec")

    centerVec = np.random.randn(3)
    def temp(vec):
        loss, gradCenterVec, gradOutsideVecs = naiveSoftmaxLossAndGradient(centerVec, 1, vec, dataset)
        return loss, gradOutsideVecs
    gradcheck_naive(temp, dummy_vectors, "naiveSoftmaxLossAndGradient gradOutsideVecs")

def test_negSamplingLossAndGradient():
    """ Test negSamplingLossAndGradient """
    dataset, dummy_vectors, dummy_tokens = getDummyObjects()

    print("==== Gradient check for negSamplingLossAndGradient ====")
    def temp(vec):
        loss, gradCenterVec, gradOutsideVecs = negSamplingLossAndGradient(vec, 1, dummy_vectors, dataset)
        return loss, gradCenterVec
    gradcheck_naive(temp, np.random.randn(3), "negSamplingLossAndGradient gradCenterVec")

    centerVec = np.random.randn(3)
    def temp(vec):
        loss, gradCenterVec, gradOutsideVecs = negSamplingLossAndGradient(centerVec, 1, vec, dataset)
        return loss, gradOutsideVecs
    gradcheck_naive(temp, dummy_vectors, "negSamplingLossAndGradient gradOutsideVecs")

def test_skipgram():
    """ Test skip-gram with naiveSoftmaxLossAndGradient """
    dataset, dummy_vectors, dummy_tokens = getDummyObjects()

    print("==== Gradient check for skip-gram with naiveSoftmaxLossAndGradient ====")
    gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
        skipgram, dummy_tokens, vec, dataset, 5, naiveSoftmaxLossAndGradient),
        dummy_vectors, "naiveSoftmaxLossAndGradient Gradient")
    grad_tests_softmax(skipgram, dummy_tokens, dummy_vectors, dataset)

    print("==== Gradient check for skip-gram with negSamplingLossAndGradient ====")
    gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
        skipgram, dummy_tokens, vec, dataset, 5, negSamplingLossAndGradient),
        dummy_vectors, "negSamplingLossAndGradient Gradient")
    grad_tests_negsamp(skipgram, dummy_tokens, dummy_vectors, dataset, negSamplingLossAndGradient)

def test_word2vec():
    """ Test the two word2vec implementations, before running on Stanford Sentiment Treebank """
    test_sigmoid()
    test_naiveSoftmaxLossAndGradient()
    test_negSamplingLossAndGradient()
    test_skipgram()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test your implementations.')
    parser.add_argument('function', nargs='?', type=str, default='all',
                        help='Name of the function you would like to test.')

    args = parser.parse_args()
    if args.function == 'sigmoid':
        test_sigmoid()
    elif args.function == 'naiveSoftmaxLossAndGradient':
        test_naiveSoftmaxLossAndGradient()
    elif args.function == 'negSamplingLossAndGradient':
        test_negSamplingLossAndGradient()
    elif args.function == 'skipgram':
        test_skipgram()
    elif args.function == 'all':
        test_word2vec()


    #loss = 0
    #loss += -np.log(sigmoid(np.dot(outsideVectors[outsideWordIdx,:],centerWordVec)))
#
 #   for s in negSampleWordIndices:
  #      loss += -np.log(sigmoid(np.dot(-1*outsideVectors[s,:],centerWordVec)))

    #print(f'Losses: ({loss-lossV0})')

    #gradCenterVec = -(1-sigmoid(np.dot(outsideVectors[outsideWordIdx,:],centerWordVec)))*outsideVectors[outsideWordIdx,:]
    #for s in negSampleWordIndices:
    #    gradCenterVec += (1-sigmoid(np.dot(-outsideVectors[s,:],centerWordVec)))*outsideVectors[s,:]
   # print(f'gradcenterVec diff: {gradCenterVecV0-gradCenterVec}')
  #   gradOutsideVecsV0 = np.zeros_like(outsideVectors)   
    #for s in negSampleWordIndices:
    #    gradOutsideVecs[s,:] += (1-sigmoid(np.dot(-1*outsideVectors[s,:],centerWordVec)))*centerWordVec
#
 #   for o in [outsideWordIdx]:
 #       gradOutsideVecs[o,:] += -(1-sigmoid(np.dot(outsideVectors[o,:],centerWordVec)))*centerWordVec
#
  #  print(f'gradoutsidevec diff: {gradOutsideVecs-gradOutsideVecsV0}')
