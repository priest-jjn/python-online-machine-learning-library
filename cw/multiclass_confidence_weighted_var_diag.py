import numpy as np
import scipy as sp
import logging as logger
import time
import pylab as pl
from collections import defaultdict
from sklearn.metrics import confusion_matrix
from scipy.stats import norm

class MCWVarDiag(object):
    """
    Diagonal elements of matrix version of Confidence-Weighted algorithm; 
    non-diagonal elements in covariance matrix are ignored.
    
    References:
    - http://www.aclweb.org/anthology/D/D09/D09-1052.pdf
    - https://alliance.seas.upenn.edu/~nlp/publications/pdf/dredze2008f.pdf
    
    Feature function F(x, y) is chosen as cartesian product of x and y.
    x is feature vector and y is 1-of-K vector.

    This model is applied to multiclass-multilabel classification, solved with
    single constraint update in http://www.aclweb.org/anthology/D/D09/D09-1052.pdf.
    """

    def __init__(self, eta = 0.9, epochs = 10):
        """
        model initialization.
        """
        logger.basicConfig(level=logger.DEBUG)
        logger.info("init starts")

        self.epochs = epochs
        self.data = defaultdict()
        self.model = defaultdict()
        self.cache = defaultdict()
        self._init_model(eta)
        
        logger.info("init finished")

    def _init_model(self, eta):
        """
        Initialize model.
        """
        logger.info("init model starts")
        self.model["mu"] = defaultdict()  # model parameter mean
        self.model["S"] = defaultdict()     # model parameter covariance
        self.model["eta"] = eta                  # confidence parameter
        self.model["phi"] = norm.ppf(norm.cdf(eta))  # inverse of cdf(eta)
        logger.info("init model finished")
        
    def _learn(self, ):
        """
        Learn internally.
        """

    def _update(self, sample, y, r):
        """
        Update model parameter internally.
        update rule is as follows,
        mu = mu + alpha * y * Sx
        S = (S^{-1} + 2 * alpha * phi * diag(g_{y, r}^2))^{-1}
        g_{y, r} = F(x, y) - F(x, r)

        Note: diagonal elements are only considered.
        
        Arguments:
        - `sample`: sample, or feature vector
        - `y`: true label
        - `r`: predicted label (!=y) with high rank value
        """

        # components
        phi = self.model["phi"]
        sample = self._add_bias(sample)
        g_y = sample
        g_r = -sample
        m = self.model["mu"][y].dot(g_y) + self.model["mu"][r].dot(g_r)
        first_term = (g_y * self.model["S"][y]).dot(g_y)
        second_term = (g_r * self.model["S"][r]).dot(g_r)
        v = first_term + second_term
        a = 1 + 2 * phi * m

        # gamma/alpha
        gamma = (-a + np.sqrt(a * a - 8 * phi * (m - phi * v))) / (4 * phi * v)
        alpha = max(0, gamma)

        # mu
        mu_y = self.model["mu"][y] + alpha * self.model["S"][y] * g_y
        mu_r = self.model["mu"][r] + alpha * self.model["S"][r] * g_r
        self.model["mu"][y] = mu_y
        self.model["mu"][r] = mu_r
        
        # S
        S_y = 1 / (1 / self.model["S"][y] + 2 * alpha * phi * g_y * g_y)
        S_r = 1 / (1 / self.model["S"][r] + 2 * alpha * phi * g_r * g_r)
        self.model["S"][y] = S_y
        self.model["S"][r] = S_r
        
    def _predict_values(self, sample):
        """
        predict value of \mu^T * x
        
        Arguments:
        - `sample`:
        """

        values = defaultdict()
        sample = self._add_bias(sample)
        for k in self.data["classes"]:
            values[k] = self.model["mu"][k].dot(sample)

        # return as list of tuple (class, ranking) in descending order
        return [(k, v) for k, v in sorted(values.items(),
                                          key=lambda x:x[1], reverse=True)]

    def _add_bias(self, sample):
        return np.hstack((sample, 1))
    
    def learn(self, X, y):
        """
        Learn.
        """
        self.data["n_samples"] = X.shape[0]
        self.data["f_dims"] = X.shape[1]
        self.data["classes"] = np.unique(y)

        logger.info("learn starts")
        for k in self.data["classes"]:
            self.model["mu"][k] = np.zeros(self.data["f_dims"] + 1)
            self.model["S"][k] = np.ones(self.data["f_dims"] + 1)   # only for diagonal
        
        # learn
        st = time.time()
        for i in xrange(0, self.epochs):
            logger.debug("iter: %d" % i)
            for i in xrange(0, self.data["n_samples"]):
                sample = X[i, :]
                label = y[i]
                pred_vals = self._predict_values(sample)
                high_rank_class = pred_vals[0][0]
                if high_rank_class != label:  # highest rank class
                    self._update(sample, label, high_rank_class)

        logger.info("learn finished")
        et = time.time()
        logger.info("learning time: %f[s]" % (et - st))

    def predict(self, sample):
        """
        predict class base on argmax_{z} w^T F(x, z)
        
        Arguments:
        - `sample`:
        """
        pred_vals = self._predict_values(sample)
        self.cache["pred_vals"] = pred_vals
        return pred_vals[0][0]
        
    ## TODO
    def update(self, label, sample):
        """
        update model.
        Arguments:
        - `label`: label
        - `sample`: sample, or feature vector
        """
def main():
    """
    Example of how to use
    """
    # data load
    #fname = "/home/kzk/datasets/uci_csv/iris.csv"
    fname = "/home/kzk/datasets/uci_csv/glass.csv"
    #fname = "/home/kzk/datasets/uci_csv/breast_cancer.csv"
    #fname = "/home/kzk/datasets/uci_csv/car.csv"
    #fname = "/home/kzk/datasets/uci_csv/credit.csv"
    #fname = "/home/kzk/datasets/uci_csv/usps.csv"
    #fname = "/home/kzk/datasets/uci_csv/liver.csv"
    #fname = "/home/kzk/datasets/uci_csv/haberman.csv"
    #fname = "/home/kzk/datasets/uci_csv/pima.csv"
    #fname = "/home/kzk/datasets/uci_csv/parkinsons.csv"
    #fname = "/home/kzk/datasets/uci_csv/ionosphere.csv"
    #fname = "/home/kzk/datasets/uci_csv/isolet.csv"
    #fname = "/home/kzk/datasets/uci_csv/magicGamaTelescope.csv"
    #fname = "/home/kzk/datasets/uci_csv/mammographic.csv"
    #fname = "/home/kzk/datasets/uci_csv/yeast.csv"
    print "dataset is", fname
    
    data = np.loadtxt(fname, delimiter=" ")
    X = data[:, 1:]
    y = data[:, 0]
    n_sample = X.shape[0]
    y_pred = np.ndarray(n_sample)

    # learn
    model = MCWVarDiag(eta=0.9, epochs=10)
    model.learn(X, y)

    # predict
    for i in xrange(0, n_sample):
        sample = data[i, 1:]
        y_pred[i] = model.predict(sample)

    # show result
    cm = confusion_matrix(y, y_pred)
    print cm
    print "accurary: %d [%%]" % (np.sum(cm.diagonal()) * 100.0 / np.sum(cm))

if __name__ == '__main__':
    main()
