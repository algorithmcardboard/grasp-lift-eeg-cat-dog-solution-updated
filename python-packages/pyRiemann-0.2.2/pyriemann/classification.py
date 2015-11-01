import numpy
from sklearn.base import BaseEstimator, ClassifierMixin, TransformerMixin

from .utils.mean import mean_covariance
from .utils.distance import distance
from .tangentspace import FGDA

#######################################################################


class MDM(BaseEstimator, ClassifierMixin, TransformerMixin):

    def __init__(self, metric='riemann', n_jobs=1):

        # store params for cloning purpose 
        self.metric = metric

        if isinstance(metric, str):
            self.metric_mean = metric
            self.metric_dist = metric

        elif isinstance(metric, dict):
            # check keys
            for key in ['mean', 'distance']:
                if key not in metric.keys():
                    raise KeyError('metric must contain "mean" and "distance"')

            self.metric_mean = metric['mean']
            self.metric_dist = metric['distance']

        else:
            raise TypeError('metric must be dict or str')

    def fit(self, X, y):

        self.classes = numpy.unique(y)

        self.covmeans = []

        for l in self.classes:
            self.covmeans.append(
                mean_covariance(X[y == l, :, :], metric=self.metric_mean))

        return self

    def _predict_distances(self, covtest):
        Nt = covtest.shape[0]
        Nc = len(self.covmeans)
        dist = numpy.empty((Nt, Nc))

        for m in range(Nc):
            for k in range(Nt):
                dist[k, m] = distance(covtest[k, :, :], self.covmeans[m],
                                      metric=self.metric_dist)
        return dist

    def predict(self, covtest):
        dist = self._predict_distances(covtest)
        return self.classes[dist.argmin(axis=1)]

    def transform(self, X):
        return self._predict_distances(X)

    def fit_predict(self, X, y):
        self.fit(X, y)
        return self.predict(X)

#######################################################################


class FgMDM(BaseEstimator, ClassifierMixin):

    def __init__(self, metric='riemann', tsupdate=False):
        self.metric = metric
        self.tsupdate = tsupdate
        self._mdm = MDM(metric=self.metric)
        self._fgda = FGDA(metric=self.metric, tsupdate=self.tsupdate)

    def fit(self, X, y):
        cov = self._fgda.fit_transform(X, y)
        self._mdm.fit(cov, y)
        return self

    def predict(self, X):
        cov = self._fgda.transform(X)
        return self._mdm.predict(cov)
