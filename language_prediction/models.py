import torch
import torch.nn as nn
from typing import *
from torch.autograd import Variable

from allennlp.models import Model
from allennlp.modules.text_field_embedders import TextFieldEmbedder
from allennlp.modules.seq2vec_encoders import Seq2VecEncoder
from allennlp.modules import FeedForward
from allennlp.modules.matrix_attention import MatrixAttention, DotProductMatrixAttention
from allennlp.data.vocabulary import Vocabulary
from allennlp.nn.regularizers.regularizer_applicator import RegularizerApplicator
from allennlp.nn.initializers import InitializerApplicator
from allennlp.nn.util import masked_softmax
import torch.nn.functional as F
import pandas as pd
import numpy as np
import joblib
from allennlp.nn.util import get_text_field_mask, sequence_cross_entropy_with_logits
from allennlp.modules.seq2seq_encoders import Seq2SeqEncoder
from collections import defaultdict
from allennlp.modules.attention.dot_product_attention import DotProductAttention
from allennlp.modules.attention.attention import Attention
from torch.nn.modules.transformer import TransformerEncoder, TransformerEncoderLayer, TransformerDecoder,\
    TransformerDecoderLayer
from torch.nn.modules.normalization import LayerNorm
from torch.nn.init import xavier_uniform_
from allennlp.nn.util import add_positional_features
from allennlp.data.iterators import DataIterator
from tqdm import tqdm
from allennlp.data import Instance
from allennlp.nn import util as nn_util
from allennlp.nn.util import masked_softmax
import copy


def save_predictions_seq_models(prediction_df: dict, predictions: torch.Tensor, gold_labels: torch.Tensor,
                                metadata, epoch: int, is_train: bool, mask: torch.Tensor, use_raisha_lstm: bool=False) \
        -> dict:
    """
    This function get the predictions class and save with the gold labels for sequence models where each sample had a
    list of predictions and labels
    :param prediction_df: dataframe with all the predictions by now
    :param predictions: the predictions for a specific batch in a specific epoch
    :param gold_labels: the labels for a specific batch
    :param metadata: the metadata for a specific batch
    :param epoch: the number of epoch
    :param is_train: if this is train data or not
    :param mask: mask for each sample- which index is a padding
    :param use_raisha_lstm: these models labels are upper Triangular matrix
    :return:
    """

    for i in range(predictions.shape[0]):  # go over each sample
        if epoch == 0:  # if this is the first epoch - keep the label
            if use_raisha_lstm:
                gold_labels_list = gold_labels[i][(mask[i] != 0).nonzero().T[0]].tolist()
            else:
                gold_labels_list = gold_labels[i][:mask[i].sum()].tolist()
            # if hotel_label_0:
            #     gold_labels_list = [0 if label == 1 else 1 for label in gold_labels_list]
            prediction_df[metadata[i]['sample_id']] = \
                {'is_train': is_train, f'labels': gold_labels_list,
                 f'total_payoff_label': sum(gold_labels_list) / len(gold_labels_list)}
            if 'raisha' in metadata[i].keys():
                prediction_df[metadata[i]['sample_id']]['raisha'] = metadata[i]['raisha']
        # most_frequent_mask will have 1 for every trial that the prediction is 0.5, 0.5 --> the model did not decide
        temp_prediction_list = predictions[i][(mask[i] != 0).nonzero().T[0]]
        most_frequent_tensor = torch.tensor([0.5, 0.5])
        if torch.cuda.is_available():
            most_frequent_tensor = most_frequent_tensor.cuda()
        most_frequent_mask = torch.tensor(~((most_frequent_tensor == temp_prediction_list).sum(1) == 2),
                                          dtype=int).tolist()
        predictions_list = temp_prediction_list.argmax(1).tolist()
        predictions_list = (np.array(predictions_list) * np.array(most_frequent_mask)).tolist()
        # if hotel_label_0:
        #     predictions_list = [0 if prediction == 1 else 1 for prediction in predictions_list]
        prediction_df[metadata[i]['sample_id']][f'predictions_{epoch}'] = predictions_list
        prediction_df[metadata[i]['sample_id']][f'total_payoff_prediction_{epoch}'] =\
            sum(predictions_list) / len(predictions_list)

    # prediction_df_temp = pd.DataFrame.from_dict(predictions_dict, orient='index')
    #
    # if epoch != 0:
    #     prediction_df = prediction_df.merge(prediction_df_temp, how='left', right_index=True, left_index=True)
    # else:
    #     prediction_df = pd.concat([prediction_df, prediction_df_temp])

    return prediction_df


def save_predictions(prediction_df: pd.DataFrame, predictions: torch.Tensor, gold_labels: torch.Tensor, metadata,
                     epoch: int, is_train: bool, int_label: bool=True) -> pd.DataFrame:
    """
    This function get the predictions class and save with the gold labels
    :param prediction_df: dataframe with all the predictions by now
    :param predictions: the predictions for a specific batch in a specific epoch
    :param gold_labels: the labels for a specific batch
    :param metadata: the metadata for a specific batch
    :param epoch: the number of epoch
    :param is_train: if this is train data or not
    :param int_label: if the label type is int
    :return:
    """

    metadata_df = pd.DataFrame(metadata)
    # Create a data frame with the sample ID, the prediction, the label and if the prediction is correct
    if int_label:
        gold_labels = gold_labels.view(gold_labels.shape[0], -1).argmax(1)
        predictions = predictions.view(predictions.shape[0], -1).argmax(1)
    else:
        predictions = predictions.view(predictions.shape[0]).tolist()
    label_prediction = \
        pd.concat([metadata_df.sample_id,
                   pd.DataFrame(gold_labels, columns=['total_payoff_label']),
                   pd.DataFrame(predictions, columns=[f'prediction_{epoch}'])], axis=1)
    if 'raisha' in metadata_df.columns:
        label_prediction = label_prediction.merge(metadata_df[['sample_id', 'raisha']], how='left', on='sample_id')
    label_prediction[f'correct_{epoch}'] =\
        np.where(label_prediction[f'prediction_{epoch}'] == label_prediction.total_payoff_label, 1, 0)
    if epoch == 0:  # if this is the first epoch - keep the label
        train = pd.DataFrame(pd.Series([is_train], name='is_train').repeat(label_prediction.shape[0]))
        train.index = label_prediction.index
        label_prediction = pd.concat([train, label_prediction], axis=1)
        prediction_df = pd.concat([prediction_df, label_prediction])

    else:  # if this is not the first label drop the label
        label_prediction = label_prediction.drop(['total_payoff_label', 'raisha'], axis=1)
        prediction_df = prediction_df.merge(label_prediction, how='left', on='sample_id')
        if f'prediction_{epoch}_x' in prediction_df.columns:
            prediction_df[f'prediction_{epoch}_x'] = np.where(prediction_df[f'prediction_{epoch}_x'].isnull(),
                                                              prediction_df[f'prediction_{epoch}_y'],
                                                              prediction_df[f'prediction_{epoch}_x'])
            prediction_df[f'correct_{epoch}_x'] = np.where(prediction_df[f'correct_{epoch}_x'].isnull(),
                                                           prediction_df[f'correct_{epoch}_y'],
                                                           prediction_df[f'correct_{epoch}_x'])
            prediction_df = prediction_df.drop([f'correct_{epoch}_y', f'prediction_{epoch}_y'], axis=1)
            prediction_df.rename(columns={f'correct_{epoch}_x': f'correct_{epoch}',
                                          f'prediction_{epoch}_x': f'prediction_{epoch}'}, inplace=True)

    return prediction_df


def get_reviews_representation(word_embedding: TextFieldEmbedder, review_representation_layer: Model,
                               sequence_review: Dict[str, torch.LongTensor], fc_layer: Model, max_tokens_len: int=None)\
        -> list:
    """
    Get sequnce of reviews and create its representation by creating a representation for each review
    by creating a representation for each token in the review and average these representations
    :param word_embedding: TextFieldEmbedder model to represent tokens as vector
    :param review_representation_layer: a model that get tensor with each reviews' tokens representation and
    :param sequence_review: dict with one key: 'tokens': this is a tensor with shape:
    [batch_size, max_seq_length (in this batch), 124, 50]
    :param fc_layer: fully connected layer to convert from [10, 124] to [10, 10] each review
    :param max_tokens_len: the max number of tokens in a review - for padding
    :return: the seq reviews shape: [seq_length, seq_length, max_num_words]
    """

    sequence_reviews_representation = list()
    for seq in sequence_review[list(word_embedding._token_embedders.keys())[0]]:
        # create emnedding for each token in each review
        tokens = {'tokens': seq}
        mask = get_text_field_mask(tokens)  # shape: [seq_length, max_num_words]
        embeddings = word_embedding(tokens)  # shape: [seq_length, max_num_words, embedding_size]
        # attention and average each review's tokens
        # shape: [seq_length, max_num_words, max_num_words]
        reviews_representation = review_representation_layer(embeddings, mask)
        # convert reviews_representation to have the max size of num_tokens
        if max_tokens_len is not None:
            padding_size = max_tokens_len - reviews_representation.shape[1]
            reviews_representation = torch.nn.functional.pad(input=reviews_representation, pad=[0, padding_size, 0, 0],
                                                             value=0)
            reviews_representation_final = fc_layer(reviews_representation)
            sequence_reviews_representation.append(reviews_representation_final)

        else:
            sequence_reviews_representation.append(reviews_representation)

    return sequence_reviews_representation


def calculate_loss_metrics(class_logits, class_probabilities, label, loss, metrics) -> dict:
    """
    This function calculate the loos and other metrics and return the output dict
    :param class_logits:
    :param class_probabilities:
    :param label:
    :param loss:
    :param metrics:
    :return:
    """

    output_dict = dict()
    output_dict['class_logits'] = class_logits
    output_dict['class_probabilities'] = class_probabilities

    # predictions = class_probabilities.cpu().data.numpy()

    if label is not None:
        # if class_logits.shape != label.squeeze(-1).shape:
        loss = loss(class_logits.squeeze(-1), label.squeeze(-1).float())
        for metric_name, metric in metrics.items():
            metric(class_logits.squeeze(-1), label.squeeze(-1))
        output_dict["loss"] = loss

    return output_dict


def calculate_loss(logits, label, criterion):
    """
    This function calculate the loos and other metrics and return the output dict
    :param logits: the prediction
    :param label: the truth label
    :param criterion: the criterion to use
    :return:
    """

    # if class_logits.shape != label.squeeze(-1).shape:
    # loss = criterion(logits.squeeze(-1), torch.max(label, -1)[1].float())
    loss = criterion(logits.squeeze(-1), label.squeeze(-1).float())

    return loss


class BasicTextModel(Model):
    """
    This model is a basic model that predict the label based only on the text
    1. represent the text of each review in the sequence using embedding model (e.g average of ELMO's vectors)
    2. average (or weight average) the reviews' representations
    3. projection layer
    4. classify the sequence (loss)
    """
    def __init__(self,
                 word_embedding: TextFieldEmbedder,
                 review_representation_layer: Model,
                 seq_representation_layer: Model,
                 vocab: Vocabulary,
                 classifier_feedforward: FeedForward,
                 fc_review_rep: FeedForward,
                 criterion,
                 metrics_dict: dict,
                 add_numbers: bool=False,
                 initializer: InitializerApplicator = InitializerApplicator()):
        """

        :param word_embedding: TextFieldEmbedder model to represent tokens as vector
        :param review_representation_layer: a model that get tensor with each reviews' tokens representation and
        return the review's representation, its input should be:
                matrix: torch.Tensor,
                matrix_mask: torch.Tensor = None
        :param seq_representation_layer: a model that get tensor with each seq's reviews representation and
        return the seq's representation, its input should be:
                matrix: torch.Tensor,
                matrix_mask: torch.Tensor = None
        :param vocab: the vocabulary to use
        :param classifier_feedforward: a feedforward layer with input_dim=10 (max_seq_length)
                and output_dim=(10 - number of classes or 1 --> according to the criterion)
        :param criterion: the loss to use
        :param add_numbers: whether to add numbers (trial payoff and trail lottery result)
        :param metrics_dict: dict with the metrics to measure
        :param fc_review_rep: fully connected layer to convert from [10, 124] to [10, 10] each review
        :param initializer:
        """
        super(BasicTextModel, self).__init__(vocab)
        self.word_embedding = word_embedding
        self.review_representation_layer = review_representation_layer
        self.seq_attention_layer = seq_representation_layer
        # self.projection = nn.Linear(self.encoder.get_output_dim(), out_size)
        self.classifier_feedforward = classifier_feedforward
        self.softmax = F.softmax
        self.metrics = metrics_dict
        self.loss = criterion
        self.add_numbers = add_numbers
        self.fc_review_rep = fc_review_rep
        self._epoch = 0
        self.predictions = pd.DataFrame()
        self._first_pair = None
        initializer(self)

    def forward(self,
                sequence_review: Dict[str, torch.LongTensor],
                metadata,
                label: torch.LongTensor = None,
                numbers: torch.FloatTensor = None,
                lottery_ep_label_field: torch.FloatTensor = None) -> Dict[str, torch.Tensor]:
        """
        :param sequence_review: dict with one key: 'tokens': this is a tensor with shape:
        [batch_size, max_seq_length (in this batch), 114, 50]
        :param metadata: list of dicts, each dict is the metadata of a single sequence of reviews
        :param label: tensor of size [batch_size] with the label for each sequence
        :param numbers: list of 2 floats: trial payoff and trail lottery result
        :param lottery_ep_label_field: 2 other labels to count loss on: lottery results and expected payoff
        :return: output_dict with loss, class_logits and class_probabilities
        """

        if self._first_pair is not None:
            if self._first_pair == metadata[0]['pair_id']:
                self._epoch += 1
        else:
            self._first_pair = metadata[0]['pair_id']

        sequence_reviews_representation =\
            get_reviews_representation(self.word_embedding, self.review_representation_layer, sequence_review,
                                       self.fc_review_rep)
        sequence_reviews_representation = torch.stack(sequence_reviews_representation)

        # attention over the seq representation
        seq_representation = self.seq_attention_layer(sequence_reviews_representation)

        class_logits = self.classifier_feedforward(seq_representation)
        class_probabilities = self.softmax(class_logits, dim=1)

        output_dict = calculate_loss_metrics(class_logits, class_probabilities, label, self.loss, self.metrics)

        self.predictions = save_predictions(prediction_df=self.predictions, predictions=class_logits,
                                            gold_labels=label, metadata=metadata, epoch=self._epoch,
                                            is_train=self.training)

        return output_dict

    def get_metrics(self, train=True, reset: bool = False) -> Dict[str, float]:
        return {metric_name: metric.get_metric(reset) for metric_name, metric in self.metrics.items()}

    def decode(self, output_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        predictions = output_dict['class_probabilities'].cpu().data.numpy()
        argmax_indices = np.argmax(predictions, axis=-1)
        labels = torch.tensor([self.vocab.get_token_from_index(x, namespace="labels") for x in argmax_indices])
        output_dict['label'] = labels
        return output_dict


class BasicTextDecisionResultModel(Model):
    """
    This model is the first model:
    1. represent the text of each review in the sequence using embedding model (e.g average of ELMO's vectors)
    2. average (or weight average) the reviews' representations
    3. projection layer
    4. classify the sequence (loss)
    """
    def __init__(self,
                 word_embedding: TextFieldEmbedder,
                 review_representation_layer: Model,
                 seq_representation_layer: Model,
                 vocab: Vocabulary,
                 classifier_feedforward_classification: FeedForward,
                 classifier_feedforward_regression: FeedForward,
                 fc_review_rep: FeedForward,
                 criterion_classification,
                 criterion_regression,
                 metrics_dict: dict,
                 add_numbers: bool=False,
                 max_tokens_len: int = None,
                 initializer: InitializerApplicator = InitializerApplicator()):
        """
        :param word_embedding: TextFieldEmbedder model to represent tokens as vector
        :param review_representation_layer: a model that get tensor with each reviews' tokens representation and
        return the review's representation, its input should be:
                matrix: torch.Tensor,
                matrix_mask: torch.Tensor = None
        :param seq_representation_layer: a model that get tensor with each seq's reviews representation and
        return the seq's representation, its input should be:
                matrix: torch.Tensor,
                matrix_mask: torch.Tensor = None
        :param vocab: the vocabulary to use
        :param classifier_feedforward_classification: a feedforward layer with input_dim=130
                and output_dim=(2 - number of classes)
        :param classifier_feedforward_regression: a feedforward layer with input_dim=130
                and output_dim=1
        :param criterion_classification: the loss to use for classification loss
        :param criterion_regression: the loss to use for regression loss
        :param add_numbers: whether to add numbers (trial payoff and trail lottery result)
        :param metrics_dict: dict with the metrics to measure
        :param max_tokens_len: the max number of tokens in a review - for padding
        :param initializer:
        """
        super(BasicTextDecisionResultModel, self).__init__(vocab)
        self.word_embedding = word_embedding
        self.review_representation_layer = review_representation_layer
        self.seq_attention_layer = seq_representation_layer
        # self.projection = nn.Linear(self.encoder.get_output_dim(), out_size)
        self.classifier_feedforward_decision = classifier_feedforward_classification
        self.classifier_feedforward_lottery = classifier_feedforward_regression
        self.classifier_feedforward_expected_payoff = classifier_feedforward_regression
        self.softmax = F.softmax
        self.metrics = metrics_dict
        self.loss_decision = criterion_classification
        self.loss_lottery = criterion_regression
        self.loss_expected_payoff = criterion_regression
        self.add_numbers = add_numbers
        self.fc_review_rep = fc_review_rep
        self.loss_weights = [1/3, 1/3, 1/3]
        self._max_tokens_len = max_tokens_len
        self.predictions = pd.DataFrame()
        self._epoch = 0
        self._first_pair = None
        initializer(self)

    def forward(self,
                sequence_review: Dict[str, torch.LongTensor],
                metadata,
                numbers: torch.FloatTensor,
                label: torch.LongTensor = None,
                lottery_ep_label_field: torch.FloatTensor = None) -> Dict[str, torch.Tensor]:
        """
        :param sequence_review: dict with one key: 'tokens': this is a tensor with shape:
        [batch_size, max_seq_length (in this batch), 114, 50]
        :param metadata: list of dicts, each dict is the metadata of a single sequence of reviews
        :param label: tensor of size [batch_size] with the label for each sequence
        :param numbers: list of 2 floats and 1 int: round expected payoff, round lottery result and DM decision
        :param lottery_ep_label_field: 2 other labels to count loss on: lottery results and expected payoff
        :return: output_dict with loss, class_logits and class_probabilities
        """

        if self._first_pair is not None:
            if self._first_pair == metadata[0]['pair_id']:
                self._epoch += 1
        else:
            self._first_pair = metadata[0]['pair_id']

        output_dict = dict()
        sequence_reviews_representation =\
            get_reviews_representation(self.word_embedding, self.review_representation_layer, sequence_review,
                                       self.fc_review_rep, self._max_tokens_len)
        sequence_reviews_representation = torch.stack(sequence_reviews_representation)

        # attention over the seq representation
        # seq_representation = self.seq_attention_layer(sequence_reviews_representation)

        # concat texts representation and numbers
        # TODO: from here to the end - create a function
        if numbers is not None:
            texts_numbers = list()
            for i in range(numbers.shape[0]):
                texts_numbers.append(torch.flatten(torch.cat((sequence_reviews_representation[i], numbers[i]), dim=1)))
            texts_numbers = torch.stack(texts_numbers)
        else:
            texts_numbers = sequence_reviews_representation

        # get predictions
        output_dict['decision_logits'] = self.classifier_feedforward_decision(texts_numbers)
        output_dict['lottery_logits'] = self.classifier_feedforward_lottery(texts_numbers)
        output_dict['expected_payoff_logits'] = self.classifier_feedforward_expected_payoff(texts_numbers)

        # class_probabilities = self.softmax(class_logits, dim=1)

        # calculate loss and metrics
        if label is not None:
            if lottery_ep_label_field is not None:
                decision_loss = calculate_loss(output_dict['decision_logits'], label, self.loss_decision)
                lottery_loss = torch.sqrt(calculate_loss(output_dict['lottery_logits'], lottery_ep_label_field[:, :1],
                                                         self.loss_lottery))
                expected_payoff_loss = torch.sqrt(calculate_loss(output_dict['expected_payoff_logits'],
                                                                 lottery_ep_label_field[:, 1:],
                                                                 self.loss_expected_payoff))

                losses = [decision_loss, lottery_loss, expected_payoff_loss]
                final_loss = list()
                for i in range(len(losses)):
                    final_loss.append(self.loss_weights[i] * losses[i])
                final_loss = sum(final_loss)
                output_dict['loss'] = final_loss

                for metric_name, metric in self.metrics.items():
                    metric(output_dict['decision_logits'], label.view(label.shape[0], -1).argmax(1))
            else:  # use only decision label # TODO: debug this
                class_probabilities = self.softmax(output_dict['decision_logits'], dim=1)
                output_dict = calculate_loss_metrics(output_dict['decision_logits'], class_probabilities, label,
                                                     self.loss, self.metrics)

        self.predictions = save_predictions(prediction_df=self.predictions, predictions=output_dict['decision_logits'],
                                            gold_labels=label, metadata=metadata, epoch=self._epoch,
                                            is_train=self.training)

        return output_dict

    def get_metrics(self, train=True, reset: bool = False) -> Dict[str, float]:
        return {metric_name: metric.get_metric(reset) for metric_name, metric in self.metrics.items()}

    def decode(self, output_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        predictions = output_dict['class_probabilities'].cpu().data.numpy()
        argmax_indices = np.argmax(predictions, axis=-1)
        labels = torch.tensor([self.vocab.get_token_from_index(x, namespace="labels") for x in argmax_indices])
        output_dict['label'] = labels
        return output_dict


class BasicFixTextFeaturesDecisionResultModel(Model):
    """
    This model is the first model:
    1. Represent the text of each review in the sequence using the fix features
    2. Concat the text and the numbers features
    3. Use 3 FF layers for the lottery results, decision and the DM expected payoff
    4. calculte the average loss
    """
    def __init__(self,
                 vocab: Vocabulary,
                 classifier_feedforward_classification: FeedForward,
                 classifier_feedforward_regression: FeedForward,
                 criterion_classification,
                 criterion_regression,
                 metrics_dict: dict,
                 add_numbers: bool = False,
                 max_tokens_len: int = None,
                 text_feedforward: FeedForward = None,
                 regularizer: RegularizerApplicator = None,
                 initializer: InitializerApplicator = InitializerApplicator()):
        """
        :param vocab: the vocabulary to use
        :param text_feedforward: if the text representation is too big- add this layer
        :param classifier_feedforward_classification: a feedforward layer with input_dim=130
                and output_dim=(2 - number of classes)
        :param classifier_feedforward_regression: a feedforward layer with input_dim=130
                and output_dim=1
        :param criterion_classification: the loss to use for classification loss
        :param criterion_regression: the loss to use for regression loss
        :param add_numbers: whether to add numbers (trial payoff and trail lottery result)
        :param metrics_dict: dict with the metrics to measure
        :param max_tokens_len: the max number of tokens in a review - for padding
        :param regularizer: regularizer to use
        :param initializer:
        """
        super(BasicFixTextFeaturesDecisionResultModel, self).__init__(vocab, regularizer)
        self.classifier_feedforward_decision = classifier_feedforward_classification
        self.classifier_feedforward_lottery = classifier_feedforward_regression
        self.classifier_feedforward_expected_payoff = classifier_feedforward_regression
        self.text_feedforward = text_feedforward
        self.softmax = F.softmax
        self.metrics = metrics_dict
        self.loss_decision = criterion_classification
        self.loss_lottery = criterion_regression
        self.loss_expected_payoff = criterion_regression
        self._add_numbers = add_numbers
        self._loss_weights = [1/3, 1 / 3, 1 / 3]
        self._max_tokens_len = max_tokens_len
        self.predictions = pd.DataFrame()
        self._epoch = 0
        self._first_pair = None
        initializer(self)

    def forward(self,
                sequence_review: torch.FloatTensor,
                metadata,
                numbers: torch.FloatTensor,
                label: torch.LongTensor = None,
                lottery_ep_label_field: torch.FloatTensor = None) -> Dict[str, torch.Tensor]:
        """
        :param sequence_review: dict with one key: 'tokens': this is a tensor with shape:
        [batch_size, max_seq_length (in this batch), 114, 50]
        :param metadata: list of dicts, each dict is the metadata of a single sequence of reviews
        :param label: tensor of size [batch_size] with the label for each sequence
        :param numbers: list of 2 floats and 1 int: round expected payoff, round lottery result and DM decision
        :param lottery_ep_label_field: 2 other labels to count loss on: lottery results and expected payoff
        :return: output_dict with loss, class_logits and class_probabilities
        """

        if self._first_pair is not None:
            if self._first_pair == metadata[0]['pair_id']:
                self._epoch += 1
        else:
            self._first_pair = metadata[0]['pair_id']

        output_dict = dict()
        if self.text_feedforward is None:
            sequence_reviews_representation = sequence_review
        else:
            sequence_reviews_representation = self.text_feedforward(sequence_review)
        # concat texts representation and numbers
        if numbers is not None:
            texts_numbers = torch.cat((sequence_reviews_representation, numbers), axis=-1)
            texts_numbers = texts_numbers.view(len(texts_numbers), -1)
        else:
            texts_numbers = sequence_reviews_representation

        # get predictions
        output_dict['decision_logits'] = self.classifier_feedforward_decision(texts_numbers)
        if numbers is not None:
            output_dict['lottery_logits'] = self.classifier_feedforward_lottery(texts_numbers)
            output_dict['expected_payoff_logits'] = self.classifier_feedforward_expected_payoff(texts_numbers)

        # class_probabilities = self.softmax(class_logits, dim=1)

        # calculate loss and metrics
        if label is not None:
            if lottery_ep_label_field is not None:
                decision_loss = calculate_loss(output_dict['decision_logits'], label, self.loss_decision)
                lottery_loss = torch.sqrt(calculate_loss(output_dict['lottery_logits'], lottery_ep_label_field[:, :1],
                                                         self.loss_lottery))
                expected_payoff_loss = torch.sqrt(calculate_loss(output_dict['expected_payoff_logits'],
                                                                 lottery_ep_label_field[:, 1:],
                                                                 self.loss_expected_payoff))

                losses = [decision_loss, lottery_loss, expected_payoff_loss]
                final_loss = list()
                for i in range(len(losses)):
                    final_loss.append(self._loss_weights[i] * losses[i])
                final_loss = sum(final_loss)
                output_dict['loss'] = final_loss

                predictions = (output_dict['decision_logits'].squeeze() > 0.5).type(label.dtype)
                for metric_name, metric in self.metrics.items():
                    metric(predictions, label.view(label.shape[0], -1).argmax(1))
            else:
                decision_loss = calculate_loss(output_dict['decision_logits'], label, self.loss_decision)
                output_dict['loss'] = decision_loss
                predictions = (output_dict['decision_logits'].squeeze() > 0.5).type(label.dtype)
                for metric_name, metric in self.metrics.items():
                    metric(predictions, label.view(label.shape[0], -1).argmax(1))

        self.predictions = save_predictions(prediction_df=self.predictions, predictions=output_dict['decision_logits'],
                                            gold_labels=label, metadata=metadata, epoch=self._epoch,
                                            is_train=self.training)

        return output_dict

    def get_metrics(self, train=True, reset: bool = False) -> Dict[str, float]:
        return {metric_name: metric.get_metric(reset) for metric_name, metric in self.metrics.items()}

    def decode(self, output_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        predictions = output_dict['class_probabilities'].cpu().data.numpy()
        argmax_indices = np.argmax(predictions, axis=-1)
        labels = torch.tensor([self.vocab.get_token_from_index(x, namespace="labels") for x in argmax_indices])
        output_dict['label'] = labels
        return output_dict


class BasicFixTextFeaturesDecisionModel(Model):
    """
    This model is the first model:
    1. Represent the text of each review in the sequence using the fix features
    2. Classify the DM decision and calculate the loss (classification task)
    """
    def __init__(self,
                 vocab: Vocabulary,
                 classifier_feedforward_classification: FeedForward,
                 criterion_classification,
                 metrics_dict: dict,
                 max_tokens_len: int = None,
                 text_feedforward: FeedForward = None,
                 regularizer: RegularizerApplicator = None,
                 initializer: InitializerApplicator = InitializerApplicator()):
        """
        :param vocab: the vocabulary to use
        :param text_feedforward: if the text representation is too big- add this layer
        :param classifier_feedforward_classification: a feedforward layer with input_dim=130
                and output_dim=(2 - number of classes)
        :param criterion_classification: the loss to use for classification loss
        :param metrics_dict: dict with the metrics to measure
        :param max_tokens_len: the max number of tokens in a review - for padding
        :param regularizer: regularizer to use
        :param initializer:
        """
        super(BasicFixTextFeaturesDecisionModel, self).__init__(vocab, regularizer)
        self.classifier_feedforward_decision = classifier_feedforward_classification
        self.text_feedforward = text_feedforward
        self.softmax = F.softmax
        self.metrics = metrics_dict
        self.loss_decision = criterion_classification
        self._max_tokens_len = max_tokens_len
        self.predictions = pd.DataFrame()
        self._epoch = 0
        self._first_pair = None
        initializer(self)

    def forward(self,
                sequence_review: torch.FloatTensor,
                metadata,
                label: torch.LongTensor = None) -> Dict[str, torch.Tensor]:
        """
        :param sequence_review: dict with one key: 'tokens': this is a tensor with shape:
        [batch_size, max_seq_length (in this batch), 114, 50]
        :param metadata: list of dicts, each dict is the metadata of a single sequence of reviews
        :param label: tensor of size [batch_size] with the label for each sequence
        :return: output_dict with loss, class_logits and class_probabilities
        """

        if self._first_pair is not None:
            if self._first_pair == metadata[0]['pair_id']:
                self._epoch += 1
        else:
            self._first_pair = metadata[0]['pair_id']

        output_dict = dict()
        if self.text_feedforward is None:
            sequence_reviews_representation = sequence_review
        else:
            sequence_reviews_representation = self.text_feedforward(sequence_review)
        # concat texts representation and numbers

        # get predictions
        output_dict['decision_logits'] = self.classifier_feedforward_decision(sequence_reviews_representation)
        output_dict['decision_logits'] = output_dict['decision_logits'].squeeze(1)

        # class_probabilities = self.softmax(class_logits, dim=1)

        # calculate loss and metrics
        if label is not None:
            decision_loss = calculate_loss(output_dict['decision_logits'], label, self.loss_decision)
            output_dict['loss'] = decision_loss
            predictions = (output_dict['decision_logits'].squeeze() > 0.5).type(label.dtype)
            for metric_name, metric in self.metrics.items():
                metric(predictions, label.view(label.shape[0], -1).argmax(1))

        # self.predictions = save_predictions(prediction_df=self.predictions, predictions=output_dict['decision_logits'],
        #                                     gold_labels=label, metadata=metadata, epoch=self._epoch,
        #                                     is_train=self.training)

        return output_dict

    def get_metrics(self, train=True, reset: bool = False) -> Dict[str, float]:
        return {metric_name: metric.get_metric(reset) for metric_name, metric in self.metrics.items()}

    def decode(self, output_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        predictions = output_dict['class_probabilities'].cpu().data.numpy()
        argmax_indices = np.argmax(predictions, axis=-1)
        labels = torch.tensor([self.vocab.get_token_from_index(x, namespace="labels") for x in argmax_indices])
        output_dict['label'] = labels
        return output_dict


class AttentionSoftMaxLayer(Model):
    """
    This model get a MatrixAttention model and return for each row in the input matrix
     a vector that represent the sentence in this row
    """

    def __init__(self,
                 matrix_attention_layer: MatrixAttention,
                 vocab=Vocabulary()):
        super(AttentionSoftMaxLayer, self).__init__(vocab)
        self.matrix_attention_layer = matrix_attention_layer()
        self.softmax = nn.Softmax(dim=-1)
        self.masked_softmax = masked_softmax

    def forward(self,
                matrix: torch.Tensor,
                matrix_mask: torch.Tensor = None):
        """
        :param matrix: tensor of shape: [max_seq_length (in this batch), max_num_words, dim_size] or
        [batch_size, seq_length (in this batch), max_num_words]
        :param matrix_mask: tensor with shape: [max_seq_length (in this batch), max_num_words] that tells which tokens
        are only padding
        and which are real
        :return: tensor of the reviews representation with shape: [seq_length, max_num_words]
        """
        attention_scores = self.matrix_attention_layer(matrix, matrix)
        attention_weights = self.masked_softmax(attention_scores, matrix_mask)

        output = attention_weights.mean(dim=1)

        return output


class LSTMAttention2LossesFixTextFeaturesDecisionResultModel(Model):
    """
    This is a LSTM model that predict the class for each 't' and the average total payoff of the saifa (2 losses)
    """
    def __init__(self,
                 encoder: Seq2SeqEncoder,
                 metrics_dict_seq: dict,
                 metrics_dict_reg: dict,
                 vocab: Vocabulary,
                 attention: Attention = DotProductAttention(),
                 seq_weight_loss: float=1.0,
                 reg_weight_loss: float=1.0,
                 reg_seq_weight_loss: float=1.0,
                 predict_seq: bool=True,
                 predict_avg_total_payoff: bool=True,
                 batch_size: int=10,
                 linear_dim=None,
                 dropout: float=None,
                 use_last_hidden_vec: bool=False,
                 use_transformer_encode: bool=False,
                 input_dim: int=0,
                 use_raisha_attention: bool=False,
                 raisha_num_features: int=0,
                 linear_layers_activation='relu',
                 use_raisha_LSTM: bool=False) -> None:
        super(LSTMAttention2LossesFixTextFeaturesDecisionResultModel, self).__init__(vocab)
        self.encoder = encoder
        self.use_raisha_LSTM = use_raisha_LSTM
        if use_transformer_encode:
            encoder_output_dim = input_dim
        else:
            encoder_output_dim = encoder.get_output_dim()

        self.use_raisha_LSTM = use_raisha_LSTM

        if use_raisha_attention and raisha_num_features > 0:  # add attention layer to create raisha representation
            self.raisha_attention_layer = attention
            self.raisha_attention_vector = torch.randn((batch_size, raisha_num_features), requires_grad=True)
            # linear layer: raisha num features -> saifa num features (encoder.get_input_dim())
            self.linear_after_raisha_attention_layer = LinearLayer(input_size=raisha_num_features,
                                                                   output_size=encoder.get_input_dim(),
                                                                   activation=linear_layers_activation)
            if torch.cuda.is_available():
                self.raisha_attention_vector = self.raisha_attention_vector.cuda()
        else:
            self.raisha_attention_layer = None
            self.raisha_attention_vector = None

        if predict_seq:  # need hidden2tag layer
            if linear_dim is not None:  # add linear layer before hidden2tag
                self.linear_layer = LinearLayer(input_size=encoder_output_dim, output_size=linear_dim, dropout=dropout,
                                                activation=linear_layers_activation)
                hidden2tag_input_size = linear_dim
            else:
                self.linear_layer = None
                hidden2tag_input_size = encoder_output_dim
            self.hidden2tag = LinearLayer(input_size=hidden2tag_input_size, output_size=vocab.get_vocab_size('labels'),
                                          dropout=dropout, activation=linear_layers_activation)

        if predict_avg_total_payoff:  # need attention and regression layer
            self.attention = attention
            self.linear_after_attention_layer = LinearLayer(input_size=encoder_output_dim, output_size=batch_size,
                                                            activation=linear_layers_activation)
            self.regressor = LinearLayer(input_size=batch_size, output_size=1, activation=linear_layers_activation)
            # self.sigmoid = nn.Sigmoid()
            self.attention_vector = torch.randn((batch_size, encoder_output_dim), requires_grad=True)
            if torch.cuda.is_available():
                self.attention_vector = self.attention_vector.cuda()
            self.mse_loss = nn.MSELoss()

        if predict_avg_total_payoff and predict_seq:  # for avg_turn models
            self.seq_reg_mse_loss = nn.MSELoss()

        if use_last_hidden_vec:
            if linear_dim is not None:  # add linear layer before last_hidden_reg
                self.linear_layer = LinearLayer(input_size=encoder_output_dim, output_size=linear_dim, dropout=dropout)
                self.last_hidden_reg = LinearLayer(input_size=linear_dim, output_size=1, dropout=dropout)
            else:
                self.linear_layer = None
                self.last_hidden_reg = LinearLayer(input_size=encoder_output_dim, output_size=1, dropout=dropout)

        self.metrics_dict_seq = metrics_dict_seq
        self.metrics_dict_reg = metrics_dict_reg
        self.seq_predictions = defaultdict(dict)
        self.reg_predictions = pd.DataFrame()
        self._epoch = 0
        self._first_pair = None
        self.seq_weight_loss = seq_weight_loss
        self.reg_weight_loss = reg_weight_loss
        self.reg_seq_weight_loss = reg_seq_weight_loss
        self.predict_seq = predict_seq
        self.predict_avg_total_payoff = predict_avg_total_payoff
        self.use_last_hidden_vec = use_last_hidden_vec

    def forward(self,
                sequence_review: torch.Tensor,
                metadata: dict,
                raisha_sequence_review: torch.Tensor = None,
                seq_labels: torch.Tensor=None,
                reg_labels: torch.Tensor=None) -> Dict[str, torch.Tensor]:

        if self._first_pair is not None:
            if self._first_pair == metadata[0]['pair_id']:
                self._epoch += 1
        else:
            self._first_pair = metadata[0]['pair_id']

        output = dict()
        mask = get_text_field_mask({'tokens': sequence_review})
        if torch.cuda.is_available():  # change to cuda
            mask = mask.cuda()
            sequence_review = sequence_review.cuda()
            if seq_labels is not None:
                seq_labels = seq_labels.cuda()
            if reg_labels is not None:
                reg_labels = reg_labels.cuda()

        if self.raisha_attention_layer is not None:
            raisha_mask = get_text_field_mask({'tokens': raisha_sequence_review})
            # (batch_size, max_raisha_len, raisha_dimensions) * (batch_size, raisha_dimensions, 1) ->
            # (batch_size, max_raisha_len)
            raisha_attention_outpus = self.raisha_attention_layer(self.raisha_attention_vector, raisha_sequence_review,
                                                                  raisha_mask)
            # (batch_size, 1, max_raisha_len) * (batch_size, max_raisha_len, raisha_dimensions) ->
            # (batch_size, raisha_dimensions)
            attention_output = torch.bmm(raisha_attention_outpus.unsqueeze(1), raisha_sequence_review).squeeze()
            # (batch_size, raisha_dimensions) -> (batch_size, saifa_dimensions)
            raisha_representation = self.linear_after_raisha_attention_layer(attention_output)
            all_raisha_saifa_representations = list()
            for seq_id in range(sequence_review.shape[0]):
                seq_raisha_saifa_representations = \
                    torch.cat([raisha_representation[seq_id].unsqueeze(0), sequence_review[seq_id]], dim=0)
                all_raisha_saifa_representations.append(seq_raisha_saifa_representations)
            sequence_review = torch.stack(all_raisha_saifa_representations, dim=0)
            # create the mask with all the first enter with 1 --> for the raisha representation
            ones_tensor = torch.ones(mask.shape[0]).type(torch.LongTensor).unsqueeze(0)
            original_mask = copy.deepcopy(mask)
            if torch.cuda.is_available():  # change to cuda
                ones_tensor = ones_tensor.cuda()
            mask = torch.cat((ones_tensor.T, mask), dim=1)
            mask[0][0] = 0  # for raisha 0 --> the first column is not really the raisha representation

        encoder_out = self.encoder(sequence_review, mask)
        # remove raisha hidden vectors from encoder_out and mask
        if self.raisha_attention_layer is not None:
            encoder_out = encoder_out[:, 1:, :]
            mask = original_mask

        if self.use_raisha_LSTM:  # change mask to cover the raisha rounds
            for seq_id in range(encoder_out.shape[0]):
                seq_raisha = metadata[seq_id]['raisha']
                mask[seq_id, :seq_raisha] = 0
            # for use raisha_LSTM --> the labels should look the same as the mask and results
            # TODO: change this to look better
            seq_labels = seq_labels[0].repeat(10, 1) * mask

        if self.predict_seq:
            if self.linear_layer is not None:
                encoder_out_linear = self.linear_layer(encoder_out)  # add linear layer before hidden2tag
                decision_logits = self.hidden2tag(encoder_out_linear)
            else:
                decision_logits = self.hidden2tag(encoder_out)
            output['decision_logits'] = masked_softmax(decision_logits, mask.unsqueeze(2))
            self.seq_predictions = save_predictions_seq_models(prediction_df=self.seq_predictions, mask=mask,
                                                               predictions=output['decision_logits'],
                                                               gold_labels=seq_labels, metadata=metadata,
                                                               epoch=self._epoch, is_train=self.training,
                                                               use_raisha_lstm=self.use_raisha_LSTM)
                                                               # hotel_label_0=self.hotel_label_0)

        if self.predict_avg_total_payoff:
            if self.use_last_hidden_vec:
                max_raisha = metadata[-1]['raisha']
                all_last_hidden_vectors = list()
                for seq_id in range(encoder_out.shape[0]):
                    seq_raisha = metadata[seq_id]['raisha']
                    last_hidden_vec = encoder_out[seq_id][max_raisha - seq_raisha]
                    all_last_hidden_vectors.append(last_hidden_vec)
                all_last_hidden_vectors = torch.stack(all_last_hidden_vectors, dim=0)
                if self.linear_layer is not None:
                    all_last_hidden_vectors = self.linear_layer(all_last_hidden_vectors)
                regression_output = self.last_hidden_reg(all_last_hidden_vectors)
            else:
                # (batch_size, seq_len, dimensions) * (batch_size, dimensions, 1) -> (batch_size, seq_len)
                attention_output = self.attention(self.attention_vector, encoder_out, mask)
                # (batch_size, 1, seq_len) * (batch_size, seq_len, dimensions) -> (batch_size, dimensions)
                attention_output = torch.bmm(attention_output.unsqueeze(1), encoder_out).squeeze()
                # (batch_size, dimensions) -> (batch_size, batch_size)
                linear_out = self.linear_after_attention_layer(attention_output)
                # (batch_size, batch_size) -> (batch_size, 1)
                regression_output = self.regressor(linear_out)
            output['regression_output'] = regression_output
            self.reg_predictions = save_predictions(prediction_df=self.reg_predictions,
                                                    predictions=output['regression_output'], gold_labels=reg_labels,
                                                    metadata=metadata, epoch=self._epoch, is_train=self.training,
                                                    int_label=False)

        if seq_labels is not None or reg_labels is not None:
            temp_loss = 0
            if self.predict_seq and seq_labels is not None:
                for metric_name, metric in self.metrics_dict_seq.items():
                    metric(decision_logits, seq_labels, mask)
                output['seq_loss'] = sequence_cross_entropy_with_logits(decision_logits, seq_labels, mask)
                temp_loss += self.seq_weight_loss * output['seq_loss']
            if self.predict_avg_total_payoff and reg_labels is not None:
                for metric_name, metric in self.metrics_dict_reg.items():
                    metric(regression_output, reg_labels.unsqueeze(1))
                output['reg_loss'] = self.mse_loss(regression_output, reg_labels.view(reg_labels.shape[0], -1))
                temp_loss += self.reg_weight_loss * output['reg_loss']
            # loss for avg_turn models
            if self.predict_seq and seq_labels is not None and self.predict_avg_total_payoff and reg_labels is not None:
                proportion_from_decisions = decision_logits.detach().clone()
                proportion_from_decisions = masked_softmax(proportion_from_decisions, mask.unsqueeze(2))
                proportion_from_decisions = proportion_from_decisions.max(2)[1] * mask
                proportion_from_decisions = proportion_from_decisions.sum(1).float() / mask.sum(1)
                output['reg_seq_loss'] = \
                    self.seq_reg_mse_loss(regression_output, proportion_from_decisions.view(reg_labels.shape[0], -1))
                temp_loss += self.reg_seq_weight_loss * output['reg_seq_loss']
            output['loss'] = temp_loss

        return output

    def get_metrics(self, reset: bool = False) -> Dict[str, float]:
        """
        merge the 2 metrics to get all the metrics
        :param reset:
        :return:
        """
        return_metrics = dict()
        if self.predict_seq:
            seq_metrics = dict()
            for metric_name, metric in self.metrics_dict_seq.items():
                if metric_name == 'F1measure_hotel_label':
                    seq_metrics['precision_hotel_label'], seq_metrics['recall_hotel_label'],\
                        seq_metrics['fscore_hotel_label'] = metric.get_metric(reset)
                elif metric_name == 'F1measure_home_label':
                    seq_metrics['precision_home_label'], seq_metrics['recall_home_label'],\
                        seq_metrics['fscore_home_label'] = metric.get_metric(reset)
                else:
                    seq_metrics[metric_name] = metric.get_metric(reset)
            return_metrics.update(seq_metrics)
        if self.predict_avg_total_payoff:
            reg_metrics =\
                {metric_name: metric.get_metric(reset) for metric_name, metric in self.metrics_dict_reg.items()}
            return_metrics.update(reg_metrics)
        return return_metrics


class AttentionFixTextFeaturesDecisionResultModel(Model):
    """
    This is an Attention model that predict the average total payoff of the saifa
    """
    def __init__(self,
                 metrics_dict_reg: dict,
                 vocab: Vocabulary,
                 input_size: int,
                 attention: Attention = DotProductAttention(),
                 batch_size: int=10,
                 dropout: float=None,
                 regularizer: RegularizerApplicator = None,) -> None:
        super(AttentionFixTextFeaturesDecisionResultModel, self).__init__(vocab)

        self.attention = attention
        self.regressor = LinearLayer(input_size=batch_size, output_size=1, dropout=dropout)
        # self.sigmoid = nn.Sigmoid()
        self.attention_vector = torch.randn((batch_size, input_size), requires_grad=True)
        if torch.cuda.is_available():
            self.attention_vector = self.attention_vector.cuda()
        self.mse_loss = nn.MSELoss()

        self.metrics_dict_reg = metrics_dict_reg
        self.reg_predictions = pd.DataFrame()
        self._epoch = 0
        self._first_pair = None

    def forward(self,
                sequence_review: torch.Tensor,
                metadata: dict,
                seq_labels: torch.Tensor = None,
                reg_labels: torch.Tensor = None) -> Dict[str, torch.Tensor]:

        if self._first_pair is not None:
            if self._first_pair == metadata[0]['pair_id']:
                self._epoch += 1
        else:
            self._first_pair = metadata[0]['pair_id']

        output = dict()
        mask = get_text_field_mask({'tokens': sequence_review})
        if torch.cuda.is_available():  # change to cuda
            mask = mask.cuda()
            sequence_review = sequence_review.cuda()
            if reg_labels is not None:
                reg_labels = reg_labels.cuda()

        attention_output = self.attention(self.attention_vector, sequence_review, mask)
        attention_output = sequence_review.bmm(attention_output.unsqueeze(-1)).squeeze(-1)
        # attention_output = self.attention(sequence_review, mask)
        regression_output = self.regressor(attention_output)
        # regression_output = self.sigmoid(regression_output)
        self.reg_predictions = save_predictions(prediction_df=self.reg_predictions,
                                                predictions=output['regression_output'], gold_labels=reg_labels,
                                                metadata=metadata, epoch=self._epoch, is_train=self.training,
                                                int_label=False)

        if reg_labels is not None:
            for metric_name, metric in self.metrics_dict_reg.items():
                metric(regression_output, reg_labels, mask)
            output['reg_loss'] = self.mse_loss(regression_output, reg_labels.view(reg_labels.shape[0], -1))
            output['loss'] = output['reg_loss']

        return output

    def get_metrics(self, reset: bool = False) -> Dict[str, float]:
        """
        merge the 2 metrics to get all the metrics
        :param reset:
        :return:
        """
        reg_metrics = {metric_name: metric.get_metric(reset) for metric_name, metric in self.metrics_dict_reg.items()}
        return reg_metrics


class LinearLayer(nn.Module):
    def __init__(self, input_size, output_size, dropout=None, activation: str='relu'):
        super().__init__()
        self.linear = nn.Linear(input_size, output_size)
        if type(dropout) is float and dropout > 0.0:
            self.dropout = nn.Dropout(dropout)
        else:
            self.dropout = None
        if activation == 'relu':
            self.activation = F.relu
        elif activation == 'leaky_relu':
            self.activation = F.leaky_relu
        else:
            self.activation = False

    def forward(self, x):
        linear_out = x
        if self.dropout is not None:
            linear_out = self.dropout(linear_out)
        linear_out = self.linear(linear_out)
        if self.activation:
            linear_out = self.activation(linear_out)
        return linear_out


class TransformerFixTextFeaturesDecisionResultModel(Model):
    """Implement encoder-decoder transformer. The architecture
    is based on the paper "Attention Is All You Need". Ashish Vaswani, Noam Shazeer,
    Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N Gomez, Lukasz Kaiser, and
    Illia Polosukhin. 2017. Attention is all you need. """
    def __init__(self,
                 vocab: Vocabulary,
                 metrics_dict_seq: dict,
                 metrics_dict_reg: dict,
                 input_dim=512,
                 num_attention_heads=8,
                 num_encoder_layers=6,
                 num_decoder_layers=6,
                 feedforward_hidden_dim=2048,
                 dropout=0.1,
                 transformer_dropout=0.1,
                 activation='relu',
                 linear_layers_activation='relu',
                 custom_encoder=None,
                 custom_decoder=None,
                 positional_encoding: Optional[str] = None,
                 predict_avg_total_payoff: bool=True,
                 predict_seq: bool = True,
                 attention: Attention = DotProductAttention(),
                 seq_weight_loss: float = 0.5,
                 reg_weight_loss: float = 0.5,
                 batch_size: int = 9,
                 linear_dim: int=None,
                 only_raisha: bool=False,  # if not saifa input is given
                 ):
        super(TransformerFixTextFeaturesDecisionResultModel, self).__init__(vocab)

        if custom_encoder is not None:
            self.encoder = custom_encoder
        else:
            encoder_layer = TransformerEncoderLayer(input_dim, num_attention_heads, feedforward_hidden_dim,
                                                    transformer_dropout, activation)
            encoder_norm = LayerNorm(input_dim)
            self.encoder = TransformerEncoder(encoder_layer, num_encoder_layers, encoder_norm)

        if custom_decoder is not None:
            self.decoder = custom_decoder
        else:
            decoder_layer = TransformerDecoderLayer(input_dim, num_attention_heads, feedforward_hidden_dim,
                                                    transformer_dropout, activation)
            decoder_norm = LayerNorm(input_dim)
            self.decoder = TransformerDecoder(decoder_layer, num_decoder_layers, decoder_norm)

        self._reset_parameters()

        self._input_dim = input_dim
        self.num_attention_heads = num_attention_heads

        if positional_encoding is None:
            self._sinusoidal_positional_encoding = False
            self._positional_embedding = None
        elif positional_encoding == "sinusoidal":
            self._sinusoidal_positional_encoding = True
            self._positional_embedding = None
        else:
            raise ValueError(
                "positional_encoding must be one of None, 'sinusoidal', or 'embedding'"
            )

        if predict_avg_total_payoff:  # need attention and regression layer
            self.attention = attention
            if linear_dim is not None and predict_seq:  # avg_turn_linear models
                input_dim_attention = linear_dim
            else:
                input_dim_attention = input_dim
            self.linear_after_attention_layer = LinearLayer(input_size=input_dim_attention, output_size=batch_size,
                                                            activation=linear_layers_activation)
            self.regressor = LinearLayer(input_size=batch_size, output_size=1, dropout=dropout,
                                         activation=linear_layers_activation)
            # self.sigmoid = nn.Sigmoid()
            self.attention_vector = torch.randn((batch_size, input_dim_attention), requires_grad=True)
            if torch.cuda.is_available():
                self.attention_vector = self.attention_vector.cuda()
            self.mse_loss = nn.MSELoss()

        if predict_seq:  # need hidden2tag layer
            if linear_dim is not None:  # add linear layer before hidden2tag
                self.linear_layer = LinearLayer(input_size=input_dim, output_size=linear_dim, dropout=dropout,
                                                activation=linear_layers_activation)
                hidden2tag_input_size = linear_dim
            else:
                self.linear_layer = None
                hidden2tag_input_size = input_dim
            self.hidden2tag = LinearLayer(input_size=hidden2tag_input_size, output_size=vocab.get_vocab_size('labels'),
                                          dropout=dropout, activation=linear_layers_activation)

        self.metrics_dict_seq = metrics_dict_seq
        self.metrics_dict_reg = metrics_dict_reg
        self.seq_predictions = defaultdict(dict)
        self.reg_predictions = pd.DataFrame()
        self._epoch = 0
        self._first_pair = None
        self.seq_weight_loss = seq_weight_loss
        self.reg_weight_loss = reg_weight_loss
        self.predict_avg_total_payoff = predict_avg_total_payoff
        self.predict_seq = predict_seq
        self.only_raisha = only_raisha

    def get_input_dim(self) -> int:
        return self._input_dim

    def get_output_dim(self) -> int:
        return 1

    def forward(self, source: torch.Tensor, target: torch.Tensor, metadata: dict, seq_labels: torch.Tensor = None,
                reg_labels: torch.Tensor = None, source_mask: Optional[torch.Tensor]=None,
                target_mask: Optional[torch.Tensor]=None, memory_mask: Optional[torch.Tensor]=None,
                src_key_padding_mask: Optional[torch.Tensor]=None, tgt_key_padding_mask: Optional[torch.Tensor]=None,
                memory_key_padding_mask: Optional[torch.Tensor]=None) -> Dict[str, torch.Tensor]:
        r"""Take in and process masked source/target sequences.
        Args:
            source: the sequence to the encoder (required).
            target: the sequence to the decoder (required).
            metadata: the metadata of the samples (required).
            seq_labels: the labels of each round (optional).
            reg_labels: the labels of the total future payoff (optional).
            source_mask: the additive mask for the src sequence (optional).
            target_mask: the additive mask for the tgt sequence (optional).
            memory_mask: the additive mask for the encoder output (optional).
            src_key_padding_mask: the ByteTensor mask for src keys per batch (optional).
            tgt_key_padding_mask: the ByteTensor mask for tgt keys per batch (optional).
            memory_key_padding_mask: the ByteTensor mask for memory keys per batch (optional).
        Shape:
            - source: :math:`(S, N, E)`.
            - target: :math:`(T, N, E)`.
            - source_mask: :math:`(S, S)`.
            - target_mask: :math:`(T, T)`.
            - memory_mask: :math:`(T, S)`.
            - src_key_padding_mask: :math:`(N, S)`.
            - tgt_key_padding_mask: :math:`(N, T)`.
            - memory_key_padding_mask: :math:`(N, S)`.
            Note: [src/tgt/memory]_mask should be filled with
            float('-inf') for the masked positions and float(0.0) else. These masks
            ensure that predictions for position i depend only on the unmasked positions
            j and are applied identically for each sequence in a batch.
            [src/tgt/memory]_key_padding_mask should be a ByteTensor where True values are positions
            that should be masked with float('-inf') and False values will be unchanged.
            This mask ensures that no information will be taken from position i if
            it is masked, and has a separate mask for each sequence in a batch.
            - output: :math:`(T, N, E)`.
            Note: Due to the multi-head attention architecture in the transformer model,
            the output sequence length of a transformer is same as the input sequence
            (i.e. target) length of the decode.
            where S is the source sequence length, T is the target sequence length, N is the
            batch size, E is the feature number
        """

        if self._first_pair is not None:
            if self._first_pair == metadata[0]['pair_id']:
                self._epoch += 1
        else:
            self._first_pair = metadata[0]['pair_id']

        output = dict()
        src_key_padding_mask = get_text_field_mask({'tokens': source})
        tgt_key_padding_mask = get_text_field_mask({'tokens': target})
        # The torch transformer takes the mask backwards.
        src_key_padding_mask_byte = ~src_key_padding_mask.bool()
        tgt_key_padding_mask_byte = ~tgt_key_padding_mask.bool()
        # create mask where only the first round is not masked --> need to be the same first round for all sequances
        if self.only_raisha:
            temp_mask = torch.ones(tgt_key_padding_mask_byte.shape, dtype=torch.bool)
            temp_mask[:, 0] = False
            tgt_key_padding_mask_byte = temp_mask

        if self._sinusoidal_positional_encoding:
            source = add_positional_features(source)
            target = add_positional_features(target)

        if torch.cuda.is_available():  # change to cuda
            source = source.cuda()
            target = target.cuda()
            tgt_key_padding_mask = tgt_key_padding_mask.cuda()
            src_key_padding_mask = src_key_padding_mask.cuda()
            tgt_key_padding_mask_byte = tgt_key_padding_mask_byte.cuda()
            src_key_padding_mask_byte = src_key_padding_mask_byte.cuda()
            if seq_labels is not None:
                seq_labels = seq_labels.cuda()
            if reg_labels is not None:
                reg_labels = reg_labels.cuda()

        # The torch transformer expects the shape (sequence, batch, features), not the more
        # familiar (batch, sequence, features), so we have to fix it.
        source = source.permute(1, 0, 2)
        target = target.permute(1, 0, 2)

        if source.size(1) != target.size(1):
            raise RuntimeError("the batch number of src and tgt must be equal")

        if source.size(2) != self._input_dim or target.size(2) != self._input_dim:
            raise RuntimeError("the feature number of src and tgt must be equal to d_model")

        encoder_out = self.encoder(source, src_key_padding_mask=src_key_padding_mask_byte)
        decoder_output = self.decoder(target, encoder_out, tgt_key_padding_mask=tgt_key_padding_mask_byte,
                                      memory_key_padding_mask=src_key_padding_mask_byte)
        decoder_output = decoder_output.permute(1, 0, 2)

        if self.predict_seq:
            if self.linear_layer is not None:
                decoder_output = self.linear_layer(decoder_output)  # add linear layer before hidden2tag
            decision_logits = self.hidden2tag(decoder_output)
            output['decision_logits'] = masked_softmax(decision_logits, tgt_key_padding_mask.unsqueeze(2))
            self.seq_predictions = save_predictions_seq_models(prediction_df=self.seq_predictions,
                                                               mask=tgt_key_padding_mask,
                                                               predictions=output['decision_logits'],
                                                               gold_labels=seq_labels, metadata=metadata,
                                                               epoch=self._epoch, is_train=self.training,)

        if self.predict_avg_total_payoff:
            # (batch_size, seq_len, dimensions) * (batch_size, dimensions, 1) -> (batch_size, seq_len)
            attention_output = self.attention(self.attention_vector, decoder_output, tgt_key_padding_mask)
            # (batch_size, 1, seq_len) * (batch_size, seq_len, dimensions) -> (batch_size, dimensions)
            attention_output = torch.bmm(attention_output.unsqueeze(1), decoder_output).squeeze()
            # (batch_size, dimensions) -> (batch_size, batch_size)
            linear_out = self.linear_after_attention_layer(attention_output)
            # (batch_size, batch_size) -> (batch_size, 1)
            regression_output = self.regressor(linear_out)
            output['regression_output'] = regression_output
            self.reg_predictions = save_predictions(prediction_df=self.reg_predictions,
                                                    predictions=output['regression_output'], gold_labels=reg_labels,
                                                    metadata=metadata, epoch=self._epoch, is_train=self.training,
                                                    int_label=False)

        if seq_labels is not None or reg_labels is not None:
            temp_loss = 0
            if self.predict_seq and seq_labels is not None:
                for metric_name, metric in self.metrics_dict_seq.items():
                    metric(decision_logits, seq_labels, tgt_key_padding_mask)
                output['seq_loss'] = sequence_cross_entropy_with_logits(decision_logits, seq_labels,
                                                                        tgt_key_padding_mask)
                temp_loss += self.seq_weight_loss * output['seq_loss']
            if self.predict_avg_total_payoff and reg_labels is not None:
                for metric_name, metric in self.metrics_dict_reg.items():
                    metric(regression_output, reg_labels, tgt_key_padding_mask)
                output['reg_loss'] = self.mse_loss(regression_output, reg_labels.view(reg_labels.shape[0], -1))
                temp_loss += self.reg_weight_loss * output['reg_loss']

            output['loss'] = temp_loss

        return output

    def _reset_parameters(self):
        r"""Initiate parameters in the transformer model."""
        for p in self.parameters():
            if p.dim() > 1:
                xavier_uniform_(p)

    def get_metrics(self, reset: bool = False) -> Dict[str, float]:
        """
        merge the 2 metrics to get all the metrics
        :param reset:
        :return:
        """
        return_metrics = dict()
        if self.predict_seq:
            seq_metrics = dict()
            for metric_name, metric in self.metrics_dict_seq.items():
                if metric_name == 'F1measure_hotel_label':
                    seq_metrics['precision_hotel_label'], seq_metrics['recall_hotel_label'],\
                        seq_metrics['fscore_hotel_label'] = metric.get_metric(reset)
                elif metric_name == 'F1measure_home_label':
                    seq_metrics['precision_home_label'], seq_metrics['recall_home_label'],\
                        seq_metrics['fscore_home_label'] = metric.get_metric(reset)
                else:
                    seq_metrics[metric_name] = metric.get_metric(reset)
            return_metrics.update(seq_metrics)
        if self.predict_avg_total_payoff:
            reg_metrics =\
                {metric_name: metric.get_metric(reset) for metric_name, metric in self.metrics_dict_reg.items()}
            return_metrics.update(reg_metrics)
        return return_metrics


def tonp(tsr): return tsr.detach().cpu().numpy()


class Predictor:
    def __init__(self, model: Model, iterator: DataIterator,
                 cuda_device: int = -1) -> None:
        self.model = model
        self.iterator = iterator
        self.cuda_device = cuda_device
        self.seq_predictions = defaultdict(dict)
        self.reg_predictions = pd.DataFrame()

    def _extract_data(self, batch):
        out_dict = self.model(**batch)
        if 'regression_output' in out_dict:
            self.reg_predictions = save_predictions(prediction_df=self.reg_predictions,
                                                    predictions=out_dict['regression_output'],
                                                    gold_labels=batch['reg_labels'],
                                                    metadata=batch['metadata'], epoch=0, is_train=False,
                                                    int_label=False)
            return
        elif 'decision_logits' in out_dict:
            if 'sequence_review' in batch:
                mask = get_text_field_mask({'tokens': batch['sequence_review']})
            elif 'target' in batch:
                mask = get_text_field_mask({'tokens': batch['target']})
            else:
                print('Error: either sequence_review or target need to be in batch')
                raise TypeError
            self.seq_predictions = save_predictions_seq_models(prediction_df=self.seq_predictions, mask=mask,
                                                               predictions=out_dict['decision_logits'],
                                                               gold_labels=batch['seq_labels'],
                                                               metadata=batch['metadata'],
                                                               epoch=0, is_train=False)
            return
        else:
            print('Error: regression_output and decision_logits are not in out_dict keys')
            raise TypeError

    def predict(self, ds: Iterable[Instance]):
        pred_generator = self.iterator(ds, num_epochs=1, shuffle=False)
        self.model.eval()
        pred_generator_tqdm = tqdm(pred_generator, total=self.iterator.get_num_batches(ds))
        with torch.no_grad():
            for batch in pred_generator_tqdm:
                batch = nn_util.move_to_device(batch, self.cuda_device)
                self._extract_data(batch)

        return
