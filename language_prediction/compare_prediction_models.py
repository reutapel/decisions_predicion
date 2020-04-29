import pandas as pd
import ray
import numpy as np
import logging
import os
import json
import utils
from datetime import datetime
import execute_cv_models
from collections import defaultdict
import torch


# define directories
base_directory = os.path.abspath(os.curdir)
condition = 'verbal'
data_directory = os.path.join(base_directory, 'data', condition, 'cv_framework')
run_dir = utils.set_folder(datetime.now().strftime(f'compare_prediction_models_%d_%m_%Y_%H_%M'), 'logs')


# @ray.remote
def execute_fold_parallel(participants_fold: pd.Series, fold: int):
    """
    This function get a dict that split the participant to train-val-test (for this fold) and run all the models
    we want to compare --> it train them using the train data and evaluate them using the val data
    :param participants_fold: split the participant to train-val-test (for this fold)
    :param fold: the fold number
    :return:
    """
    # get the train, test, validation participant code for this fold
    fold_split_dict = dict()
    for data_set in ['train', 'test', 'validation']:
        fold_split_dict[data_set] = participants_fold.loc[participants_fold == data_set].index.tolist()

    # models_to_compare should have for each row:
    # model_num, model_type, model_name, function_to_run, data_file_name, hyper_parameters
    # (strings of all parameters for the running function as dict: {'parameter_name': parameter_value})
    models_to_compare = pd.read_excel(os.path.join(base_directory, 'models_to_compare.xlsx'),
                                      sheet_name='table_to_load', skiprows=[0])
    fold_dir = utils.set_folder(f'fold_{fold}', run_dir)
    excel_models_results = utils.set_folder(folder_name='excel_models_results', father_folder_path=fold_dir)
    table_writer = pd.ExcelWriter(os.path.join(excel_models_results, f'Results_fold_{fold}_all_models.xlsx'),
                                  engine='xlsxwriter')
    log_file_name = os.path.join(fold_dir, f'LogFile_fold_{fold}.log')
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(filename=log_file_name,
                        level=logging.DEBUG,
                        format='%(asctime)s: %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        )
    all_model_types = models_to_compare.model_type.unique()
    # all_model_types = ['Transformer_avg', 'Transformer_avg_turn']
    all_models_results = pd.DataFrame()
    for model_type in all_model_types:  # compare all versions of each model type
        model_type_versions = models_to_compare.loc[models_to_compare.model_type == model_type]
        for index, row in model_type_versions.iterrows():  # iterate over all the models to compare
            # get all model parameters
            model_num = row['model_num']
            if model_num not in [386, 387]:
                continue
            model_type = row['model_type']
            model_name = row['model_name']
            function_to_run = row['function_to_run']
            data_file_name = row['data_file_name']
            hyper_parameters_str = row['hyper_parameters']
            metadata_dict = {'model_num': model_num, 'model_type': model_type, 'model_name': model_name,
                             'data_file_name': data_file_name, 'hyper_parameters_str': hyper_parameters_str}
            metadata_df = pd.DataFrame.from_dict(metadata_dict, orient='index').T
            # get hyper parameters as dict
            if type(hyper_parameters_str) == str:
                hyper_parameters_dict = json.loads(hyper_parameters_str)
            else:
                hyper_parameters_dict = None

            if hyper_parameters_dict is not None and 'features_max_size' in hyper_parameters_dict.keys():
                if int(hyper_parameters_dict['features_max_size']) > 1000:
                    continue
            # elif hyper_parameters_dict is not None and 'features_max_size' not in hyper_parameters_dict.keys():
            #     continue
            # each function need to get: model_num, fold, fold_dir, model_type, model_name, data_file_name,
            # fold_split_dict, table_writer, data_directory, hyper_parameters_dict.
            # During running it needs to write the predictions to the table_writer and save the trained model with
            # the name: model_name_model_num to the fold_dir.
            # it needs to return a dict with the final results over the evaluation data: {measure_name: measure}
            model_class = getattr(execute_cv_models, function_to_run)(
                model_num, fold, fold_dir, model_type, model_name, data_file_name, fold_split_dict, table_writer,
                data_directory, hyper_parameters_dict, excel_models_results)
            model_class.load_data_create_model()
            model_class.fit_predict()
            results_dict = model_class.eval_model()
            results_df = pd.DataFrame.from_dict(results_dict).T
            results_df['raisha_round'] = results_df.index
            results_df[['Raisha', 'Round']] = results_df.raisha_round.str.split(expand=True)
            results_df = results_df.drop('raisha_round', axis=1)
            results_df.index = np.zeros(shape=(results_df.shape[0],))
            results_df = metadata_df.join(results_df)
            all_models_results = pd.concat([all_models_results, results_df], sort='False')
            utils.write_to_excel(model_class.model_table_writer, 'Model results', ['Model results'], results_df)
            model_class.model_table_writer.save()
            del model_class
            # torch.cuda.empty_cache()

    utils.write_to_excel(table_writer, 'All models results', ['All models results'], all_models_results)
    table_writer.save()

    logging.info(f'fold {fold} finish compare models')
    print(f'fold {fold} finish compare models')

    return f'fold {fold} finish compare models'


def parallel_main():
    print(f'Start run in parallel: for each fold compare all the models')
    logging.info(f'Start run in parallel: for each fold compare all the models')

    # participants_fold_split should have the following columns: fold_0, fold_1,...,fold_5
    # the index should be the participant code
    # the values will be train/test/validation
    participants_fold_split = pd.read_csv(os.path.join(data_directory, 'pairs_folds.csv'))
    participants_fold_split.index = participants_fold_split.pair_id
    # participants_fold_split = participants_fold_split.iloc[:50]
    # ray.init()
    # all_ready_lng =\
    #     ray.get([execute_fold_parallel.remote(participants_fold_split[f'fold_{i}'], i) for i in range(6)])

    for fold in range(6):
        execute_fold_parallel(participants_fold_split[f'fold_{fold}'], fold=fold)

    # print(f'Done! {all_ready_lng}')
    # logging.info(f'Done! {all_ready_lng}')

    return


if __name__ == '__main__':
    parallel_main()
