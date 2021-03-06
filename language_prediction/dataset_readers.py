from typing import *
import json
import logging
import pandas as pd
import numpy as np
import tqdm
from overrides import overrides
from allennlp.data.dataset_readers.dataset_reader import DatasetReader
from allennlp.data.fields import LabelField, TextField, MetadataField, ListField, ArrayField, SequenceLabelField
from float_label_field import FloatLabelField
from allennlp.data.instance import Instance
from allennlp.data.tokenizers import Tokenizer, WordTokenizer, Token
from allennlp.data.tokenizers.word_splitter import SpacyWordSplitter
from allennlp.data.token_indexers import TokenIndexer, SingleIdTokenIndexer
import joblib
import math
import copy

class TextExpDataSetReader(DatasetReader):
    """
    This class create a data set reader to a csv file with the following columns:
    0-8 or 0-9: sequence of reviews for a specific k-size and a pair
    k-size: the number of reviews in this row
    pair_id: the pair of this data sample
    sample_id: pairID_Ksize
    label: the total payoff of the experts of the pair (in all 10 trials)
    """
    def __init__(self,
                 lazy: bool = False,
                 tokenizer: Callable[[str], List[str]]=None,
                 token_indexers: Dict[str, TokenIndexer] = None,
                 max_seq_len: Optional[int] = 10,
                 label_column: Optional[str] = 'label',
                 add_numeric_data: bool = False,
                 use_only_prev_round: bool = False,
                 single_round_label: bool = False,
                 three_losses: bool = False,
                 fix_text_features: bool = False,
                 no_history: bool = False,
                 numbers_columns_name: list = None) -> None:
        super().__init__(lazy)
        self._tokenizer = tokenizer or SpacyWordSplitter()
        self._token_indexers = token_indexers or {"tokens": SingleIdTokenIndexer()}
        self.max_seq_len = max_seq_len
        self._label_column = label_column
        self._add_numeric_data = add_numeric_data
        self._use_only_prev_round = use_only_prev_round
        self._single_round_label = single_round_label
        self._three_losses = three_losses
        self.max_tokens_len = 0
        self.number_length = 0
        self._fix_text_features = fix_text_features
        self._no_history = no_history
        self.numbers_columns_name = numbers_columns_name

    @overrides
    def _read(self, file_path: str) -> Iterator[Instance]:
        """
        This function takes a filename, read the data and produces a stream of Instances
        :param str file_path: the path to the file with the data
        :return:
        """
        # Load the data
        if 'csv' in file_path:
            df = pd.read_csv(file_path)
        else:
            df = joblib.load(file_path)
        if 'text_9' not in df.columns:
            self.max_seq_len = 9
        # get the reviews and label columns -> no metadata, and metadata columns
        metadata_columns = ['k_size', 'pair_id', 'sample_id']

        # df = df.loc[df.k_size == 5]

        # if we use numbers and single round label- the first round is not relevant- only if we use history data
        if self._add_numeric_data and self._single_round_label and not self._no_history:
            df = df.loc[df.k_size > 1]
            self.max_seq_len = 9
        for i, row in tqdm.tqdm(df.iterrows()):
            text_list = list()
            numbers_list = list()
            if self._use_only_prev_round:
                rounds = [row.k_size-2, row.k_size-1]  # use the current and the previous rounds
                self.max_seq_len = 2
            elif self._no_history:  # only current round
                rounds = [row.k_size-1]
                self.max_seq_len = 1
            else:
                rounds = list(range(1, self.max_seq_len+1))  # rounds 2-10
            for round_num in rounds:
                # use only available rounds
                if row[f'text_{round_num}'] is not np.nan and not\
                        (type(row[f'text_{round_num}']) == float and math.isnan(row[f'text_{round_num}'])):
                    if self._fix_text_features:  # if this is True-text features are fixed (e.g BERT or manual)
                        text_list.append(row[f'text_{round_num}'])
                    else:
                        text_list.append([Token(x) for x in self._tokenizer(row[f'text_{round_num}'].lower())])
                    # these are the numbers of the previous round so we can use the current round number as well
                    if self._add_numeric_data and round_num > 0:  # for the first round we don't have previous round
                        append_list = [row[f'{column}_{round_num}'] for column in self.numbers_columns_name]
                        numbers_list.append(append_list)
                        self.number_length = len(append_list)
                    elif self._add_numeric_data and round_num == 0:
                        numbers_list.append([])
                    else:
                        numbers_list = None
            # the label should use also the numbers of the current round if we use 3 losses
            if self._add_numeric_data and self._three_losses:
                numbers_label = np.array([row[f'curr_result'], row[f'curr_expected_dm_payoff']])
            else:
                numbers_label = None
            yield self.text_to_instance(text_list,
                                        row[self._label_column],
                                        {column: row[column] for column in metadata_columns},
                                        numbers_list,
                                        numbers_label=numbers_label
                                        )

    @overrides
    def text_to_instance(self, reviews_seq: List[Union[List[Token], np.array]],
                         labels: Union[int, float, list]=None,
                         metadata: Dict=None,
                         numbers_seq: List[List[float]]=None,
                         numbers_label: np.array=None) -> Instance:
        """
        This function takes the inputs corresponding to a training example,
        instantiates the corresponding Fields, and returns the Instance containing those fields.
        :param reviews_seq: a list of reviews, each review represents as list of token
        :param labels: the label of this sequence
        :param metadata: list of information of this sequence
        :param numbers_seq: a list of 2 lists: one with the payoffs and one with the lottery results
        :param numbers_label: if we use 3 losses - the label should use the numbers from the predicted round
        :return: Instance: the input to the model
        if use 3 losses, the order of the label is: decision, result, expected_payoff
        """

        # create the ListField with the TextField of each review in the sequence
        max_tokens_len = len(max(reviews_seq, key=len))
        if max_tokens_len > self.max_tokens_len:
            self.max_tokens_len = max_tokens_len
        review_textfield_list = list()
        for review in reviews_seq:
            if self._fix_text_features:
                review_textfield_list.append(ArrayField(review))
            else:
                review_textfield_list.append(TextField(review, self._token_indexers))
        sentence_field = ListField(review_textfield_list)
        fields = {'sequence_review': sentence_field}

        # add numeric features to fields
        if numbers_seq is not None:
            numbers_listfield_list = list()
            for row in numbers_seq:
                numbers_listfield_list.append(ArrayField(np.array(row)))
            numbers_field = ListField(numbers_listfield_list)
            fields['numbers'] = numbers_field
        elif not self._add_numeric_data:
            no_num = True
        else:
            fields['numbers'] = ListField([ArrayField(np.nan)])

        # add labels and metadata to fields
        if labels is not None:
            if type(labels) == float:
                label_field = FloatLabelField(labels)
            elif type(labels) == list:
                label_field = ArrayField(np.array(labels))
            else:
                label_field = LabelField(labels, skip_indexing=True)  # skip_indexing=True to skip indexing for int label

            if numbers_label is not None:
                lottery_ep_label_field = ArrayField(numbers_label)
                fields['lottery_ep_label_field'] = lottery_ep_label_field
            elif not self._add_numeric_data:
                no_num = True
            else:
                lottery_ep_label_field = ArrayField(np.nan)
                fields['lottery_ep_label_field'] = lottery_ep_label_field

            fields['label'] = label_field

        if metadata is not None:
            fields['metadata'] = MetadataField(metadata)

        return Instance(fields)


class LSTMDatasetReader(DatasetReader):
    """
    DatasetReader for LSTM models that predict for each round the DM's decision
    """
    def __init__(self,
                 lazy: bool = False,
                 label_column: Optional[str] = 'labels',
                 pair_ids: list = None,
                 num_attention_heads: int=8,
                 use_transformer: bool=False,
                 use_raisha_attention: bool=False,
                 use_raisha_LSTM: bool=False,
                 raisha_num_features: int=0) -> None:
        """

        :param lazy:
        :param label_column:
        :param pair_ids:
        :param num_attention_heads:
        :param use_transformer: if the model is a transformer
        :param use_raisha_attention: if the model first use attention to create a raisha vector
        :param use_raisha_LSTM: add the raisha rounds as is to the LSTM --> need to put -1 in the saifa features to
        get the same vector shape in all rounds
        """
        super().__init__(lazy)
        self._label_column = label_column
        self.num_features = 0
        self.raisha_num_features = raisha_num_features
        self.num_labels = 2
        self.pair_ids = pair_ids
        self.input_dim = 0
        self.use_transformer = use_transformer
        self.num_attention_heads = num_attention_heads
        self.use_raisha_attention = use_raisha_attention
        self.use_raisha_LSTM = use_raisha_LSTM

        if self.use_raisha_LSTM and self.raisha_num_features == 0:
            print(f'When using use_raisha_LSTM, raisha_num_features must be the correct number and not 0')
            raise TypeError

    @overrides
    def text_to_instance(self, features_list: List[ArrayField], raisha_text_list: List[ArrayField],
                         labels: List[str] = None, metadata: Dict=None) -> Instance:
        sentence_field = ListField(features_list)
        fields = {'sequence_review': sentence_field}

        if raisha_text_list is not None:
            fields['raisha_sequence_review'] = ListField(raisha_text_list)

        if labels is not None:
            sentence_field_for_labels = copy.deepcopy(sentence_field)
            if self.use_raisha_LSTM:
                sentence_field_for_labels.field_list = sentence_field_for_labels.field_list[metadata['raisha']:]
            seq_labels_field = SequenceLabelField(labels=labels, sequence_field=sentence_field_for_labels)
            fields['seq_labels'] = seq_labels_field
            reg_labels = [0 if label == 'hotel' else 1 for label in labels]
            reg_label_field = FloatLabelField(sum(reg_labels) / len(reg_labels))
            fields['reg_labels'] = reg_label_field

        if metadata is not None:
            fields['metadata'] = MetadataField(metadata)

        return Instance(fields)

    @overrides
    def _read(self, file_path: str) -> Iterator[Instance]:
        """
        This function takes a filename, read the data and produces a stream of Instances
        :param str file_path: the path to the file with the data
        :return:
        """
        # Load the data
        if 'csv' in file_path:
            df = pd.read_csv(file_path)
        else:
            df = joblib.load(file_path)

        # if we run with CV we need the pair ids to use
        if self.pair_ids is not None:
            df = df.loc[df.pair_id.isin(self.pair_ids)]

        # get the reviews and label columns -> no metadata, and metadata columns
        metadata_columns = ['raisha', 'pair_id', 'sample_id']
        rounds = list(range(1, 11))  # rounds 1-10

        for i, row in tqdm.tqdm(df.iterrows()):
            text_list = list()
            if self.use_raisha_attention:
                raisha_text_list = list()
            else:
                raisha_text_list = None
            raisha = row['raisha']
            for round_num in rounds:
                # use only available rounds
                if row[f'features_round_{round_num}'] is not None:
                    if self.use_raisha_attention and round_num <= raisha:
                        if self.raisha_num_features == 0:
                            self.raisha_num_features = len(row[f'features_round_{round_num}'])
                        raisha_text_list.append(ArrayField(np.array(row[f'features_round_{round_num}']),
                                                           padding_value=-1))
                    else:
                        if self.num_features == 0:
                            self.num_features = len(row[f'features_round_{round_num}'])
                            # for transformer the input dim should be // self.num_attention_heads
                            if self.use_transformer:
                                if self.use_raisha_LSTM:  # the max size of features is raisha_num_features
                                    num_features_to_use = self.raisha_num_features
                                else:
                                    num_features_to_use = self.num_features
                                check = num_features_to_use // self.num_attention_heads
                                if check * self.num_attention_heads != num_features_to_use:
                                    self.input_dim = (check + 1) * self.num_attention_heads
                                else:
                                    self.input_dim = num_features_to_use
                        if self.use_transformer:
                            extra_columns = [-1] * (self.input_dim - len(row[f'features_round_{round_num}']))
                            raisha_data = row[f'features_round_{round_num}'] + extra_columns
                        # add -1 to saifa rounds to get the same vector length
                        elif self.use_raisha_LSTM and round_num > raisha and \
                                self.raisha_num_features > self.num_features:
                            extra_columns = [-1] * (self.raisha_num_features - self.num_features)
                            raisha_data = row[f'features_round_{round_num}'] + extra_columns
                        else:
                            raisha_data = row[f'features_round_{round_num}']
                        text_list.append(ArrayField(np.array(raisha_data), padding_value=-1))
            labels = row[self._label_column]
            metadata_dict = {column: row[column] for column in metadata_columns}
            if raisha_text_list is not None and len(raisha_text_list) == 0:  # raisha = 0 and use_raisha_attention
                raisha_text_list.append(ArrayField(np.array([-1] * self.raisha_num_features), padding_value=-1))
            yield self.text_to_instance(text_list, raisha_text_list, labels, metadata_dict)


class TransformerDatasetReader(DatasetReader):
    """
    DatasetReader for LSTM models that predict for each round the DM's decision
    """
    def __init__(self,
                 features_max_size: int,
                 num_attention_heads: int=8,
                 lazy: bool = False,
                 label_column: Optional[str] = 'labels',
                 pair_ids: list = None,
                 only_raisha: bool=False) -> None:
        super().__init__(lazy)
        self._label_column = label_column
        self.num_labels = 2
        self.pair_ids = pair_ids
        self.input_dim = features_max_size
        self.only_raisha = only_raisha
        check = features_max_size // num_attention_heads
        if check * num_attention_heads != features_max_size:
            self.input_dim = (check + 1) * num_attention_heads

    @overrides
    def text_to_instance(self, saifa_text_list: List[ArrayField], raisha_text_list: List[ArrayField],
                         labels: List[str] = None, metadata: Dict=None) -> Instance:
        raisha_text_list = ListField(raisha_text_list)
        fields = {'source': raisha_text_list}

        saifa_text_list = ListField(saifa_text_list)
        fields['target'] = saifa_text_list

        if labels:
            seq_labels_field = SequenceLabelField(labels=labels, sequence_field=saifa_text_list)
            fields['seq_labels'] = seq_labels_field
            reg_labels = [0 if label == 'hotel' else 1 for label in labels]
            reg_label_field = FloatLabelField(sum(reg_labels) / len(reg_labels))
            fields['reg_labels'] = reg_label_field

        if metadata is not None:
            fields['metadata'] = MetadataField(metadata)

        return Instance(fields)

    @overrides
    def _read(self, file_path: str) -> Iterator[Instance]:
        """
        This function takes a filename, read the data and produces a stream of Instances
        :param str file_path: the path to the file with the data
        :return:
        """
        # Load the data
        if 'csv' in file_path:
            df = pd.read_csv(file_path)
        else:
            df = joblib.load(file_path)

        # if we run with CV we need the pair ids to use
        if self.pair_ids is not None:
            df = df.loc[df.pair_id.isin(self.pair_ids)]

        # get the reviews and label columns -> no metadata, and metadata columns
        metadata_columns = ['raisha', 'pair_id', 'sample_id']
        rounds = list(range(1, 11))  # rounds 1-10

        for i, row in tqdm.tqdm(df.iterrows()):
            raisha = row.raisha  # raisha is between 0 to 9 (the rounds in the raisha are rounds <= raisha)
            if raisha == 0:
                continue
            saifa_text_list, raisha_text_list = list(), list()
            for round_num in rounds:
                # use only available rounds
                if row[f'features_round_{round_num}'] is not None:
                    if round_num <= raisha:  # rounds in raisha
                        extra_columns = [-1] * (self.input_dim - len(row[f'features_round_{round_num}']))
                        raisha_data = row[f'features_round_{round_num}'] + extra_columns
                        raisha_text_list.append(ArrayField(np.array(raisha_data), padding_value=-1))
                    else:  # rounds in saifa
                        if self.only_raisha and round_num == raisha+1:
                            saifa_data = [100] * self.input_dim  # special vector to indicate the start of the saifa
                        else:
                            extra_columns = [-1] * (self.input_dim - len(row[f'features_round_{round_num}']))
                            saifa_data = row[f'features_round_{round_num}'] + extra_columns
                        saifa_text_list.append(ArrayField(np.array(saifa_data), padding_value=-1))
            labels = row[self._label_column]
            metadata_dict = {column: row[column] for column in metadata_columns}
            yield self.text_to_instance(saifa_text_list=saifa_text_list, raisha_text_list=raisha_text_list,
                                        labels=labels, metadata=metadata_dict)
