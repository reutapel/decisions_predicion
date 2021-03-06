#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import Counter

import numpy as np


STARTING_LABEL = '*'        # Label of t=-1
STARTING_LABEL_INDEX = 0


class VectorRepresentationInput:
    def __init__(self, features_names):
        self.features_names = features_names

    def __call__(self, x, t):
        """
        Return a list of features as given in the input
        :param x: An observation vector
        :param t: time
        :return: A list of feature strings
        """
        features = list()
        for i, feature in enumerate(x[t]):
            if feature == 1:  # the feature exists in this sample
                features.append(self.features_names[i])
        return features


def default_feature_func(x, t):
    """
    Returns a list of feature strings.
    (Default feature function)
    :param x: An observation vector
    :param t: time
    :return: A list of feature strings
    """
    length = len(x)

    features = list()
    features.append('U[0]:%s' % x[t][0])
    features.append('POS_U[0]:%s' % x[t][1])
    if t < length-1:
        features.append('U[+1]:%s' % (x[t+1][0]))
        features.append('B[0]:%s %s' % (x[t][0], x[t+1][0]))
        features.append('POS_U[1]:%s' % x[t+1][1])
        features.append('POS_B[0]:%s %s' % (x[t][1], x[t+1][1]))
        if t < length-2:
            features.append('U[+2]:%s' % (x[t+2][0]))
            features.append('POS_U[+2]:%s' % (x[t+2][1]))
            features.append('POS_B[+1]:%s %s' % (x[t+1][1], x[t+2][1]))
            features.append('POS_T[0]:%s %s %s' % (x[t][1], x[t+1][1], x[t+2][1]))
    if t > 0:
        features.append('U[-1]:%s' % (x[t-1][0]))
        features.append('B[-1]:%s %s' % (x[t-1][0], x[t][0]))
        features.append('POS_U[-1]:%s' % (x[t-1][1]))
        features.append('POS_B[-1]:%s %s' % (x[t-1][1], x[t][1]))
        if t < length-1:
            features.append('POS_T[-1]:%s %s %s' % (x[t-1][1], x[t][1], x[t+1][1]))
        if t > 1:
            features.append('U[-2]:%s' % (x[t-2][0]))
            features.append('POS_U[-2]:%s' % (x[t-2][1]))
            features.append('POS_B[-2]:%s %s' % (x[t-2][1], x[t-1][1]))
            features.append('POS_T[-2]:%s %s %s' % (x[t-2][1], x[t-1][1], x[t][1]))

    return features


class FeatureSet:
    def __init__(self, feature_func=None, features_names=None):
        # Sets a custom feature function.
        if feature_func is not None:
            self.feature_func = feature_func(features_names)
        else:
            self.feature_func = default_feature_func
        self.feature_dic = dict()
        self.observation_set = set()
        self.empirical_counts = Counter()
        self.num_features = 0

        self.label_dic = {STARTING_LABEL: STARTING_LABEL_INDEX}
        self.label_array = [STARTING_LABEL]

        return

    def scan(self, data):
        """
        Constructs a feature set, a label set,
            and a counter of empirical counts of each feature from the input data.
        :param data: A list of (x, Y) pairs. (x: observation vector , Y: label vector)
        """

        # Constructs a feature set, and counts empirical counts.
        for data_list in data:  # x=data_list[0], y=data_list[1]
            prev_y = STARTING_LABEL_INDEX
            for t in range(len(data_list[0])):
                # Gets a label id
                try:
                    len_y = self.label_dic[data_list[1][t]]
                except KeyError:
                    len_y = len(self.label_dic)
                    self.label_dic[data_list[1][t]] = len_y
                    self.label_array.append(data_list[1][t])
                # Adds features
                self._add(prev_y, len_y, data_list[0], t)
                prev_y = len_y

    def load(self, feature_dic, num_features, label_array, empirical_counts, observation_set):
        self.num_features = num_features
        self.label_array = label_array
        self.label_dic = {label: i for label, i in enumerate(label_array)}
        self.feature_dic = self.deserialize_feature_dic(feature_dic)
        self.empirical_counts = empirical_counts
        self.observation_set = observation_set

    def __len__(self):
        return self.num_features

    def _add(self, prev_y, y, x, t):
        """
        Generates features, constructs feature_dic.
        :param prev_y: previous label
        :param y: present label
        :param x: observation vector
        :param t: time
        """
        for feature_string in self.feature_func(x, t):
            if feature_string in self.feature_dic.keys():
                if (prev_y, y) in self.feature_dic[feature_string].keys():
                    self.empirical_counts[self.feature_dic[feature_string][(prev_y, y)]] += 1
                else:
                    feature_id = self.num_features
                    self.feature_dic[feature_string][(prev_y, y)] = feature_id
                    self.empirical_counts[feature_id] += 1
                    self.num_features += 1
                if (-1, y) in self.feature_dic[feature_string].keys():
                    self.empirical_counts[self.feature_dic[feature_string][(-1, y)]] += 1
                else:
                    feature_id = self.num_features
                    self.feature_dic[feature_string][(-1, y)] = feature_id
                    self.empirical_counts[feature_id] += 1
                    self.num_features += 1
            else:
                self.feature_dic[feature_string] = dict()
                # Bigram feature
                feature_id = self.num_features
                self.feature_dic[feature_string][(prev_y, y)] = feature_id
                self.empirical_counts[feature_id] += 1
                self.num_features += 1
                # Unigram feature
                feature_id = self.num_features
                self.feature_dic[feature_string][(-1, y)] = feature_id
                self.empirical_counts[feature_id] += 1
                self.num_features += 1

    def get_feature_vector(self, prev_y, y, x, t):
        """
        Returns a list of feature ids of given observation and transition.
        :param prev_y: previous label
        :param y: present label
        :param x: observation vector
        :param t: time
        :return: A list of feature ids
        """
        feature_ids = list()
        for feature_string in self.feature_func(x, t):
            try:
                feature_ids.append(self.feature_dic[feature_string][(prev_y, y)])
            except KeyError:
                pass
        return feature_ids

    def get_labels(self):
        """
        Returns a label dictionary and array.
        """
        return self.label_dic, self.label_array

    def calc_inner_products(self, params, x, t):
        """
        Calculates inner products of the given parameters and feature vectors of the given observations at time t.
        :param params: parameter vector
        :param x: observation vector
        :param t: time
        :return:
        """
        inner_products = Counter()
        for feature_string in self.feature_func(x, t):
            try:
                for (prev_y, y), feature_id in self.feature_dic[feature_string].items():
                    inner_products[(prev_y, y)] += params[feature_id]
            except KeyError:
                pass
        return [((prev_y, y), score) for (prev_y, y), score in inner_products.items()]

    def get_empirical_counts(self):
        empirical_counts = np.ndarray((self.num_features,))
        for feature_id, counts in self.empirical_counts.items():
            empirical_counts[feature_id] = counts
        return empirical_counts

    def get_feature_list(self, x, t):
        feature_list_dic = dict()
        for feature_string in self.feature_func(x, t):
            for (prev_y, y), feature_id in self.feature_dic[feature_string].items():
                if (prev_y, y) in feature_list_dic.keys():
                    feature_list_dic[(prev_y, y)].add(feature_id)
                else:
                    feature_list_dic[(prev_y, y)] = {feature_id}
        return [((prev_y, y), feature_ids) for (prev_y, y), feature_ids in feature_list_dic.items()]

    def serialize_feature_dic(self):
        serialized = dict()
        for feature_string in self.feature_dic.keys():
            serialized[feature_string] = dict()
            for (prev_y, y), feature_id in self.feature_dic[feature_string].items():
                serialized[feature_string]['%d_%d' % (prev_y, y)] = feature_id
        return serialized

    def deserialize_feature_dic(self, serialized):
        feature_dic = dict()
        for feature_string in serialized.keys():
            feature_dic[feature_string] = dict()
            for transition_string, feature_id in serialized[feature_string].items():
                prev_y, y = transition_string.split('_')
                feature_dic[feature_string][(int(prev_y), int(y))] = feature_id
        return feature_dic
