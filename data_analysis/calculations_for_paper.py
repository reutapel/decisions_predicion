from collections import defaultdict
import scipy.stats
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from data_analysis import autolabel
import seaborn as sns
import matplotlib.lines as mlines


# Say, "the default sans-serif font is Times New Roman Bold"
# fonts = {'fontname': 'Times New Roman Bold'}
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = "Times New Roman Bold"

base_directory = os.path.abspath(os.curdir)
data_directory = os.path.join(base_directory, 'results')
orig_data_analysis_directory = os.path.join(base_directory, 'analysis')
date_directory = 'text_exp_2_tests'
data_analysis_directory = os.path.join(orig_data_analysis_directory, date_directory)
conditions = ['numeric', 'both', 'num_only', 'verbal']
# can be: group_average_score or avg_most_close_score
column_to_define_exaggerate = 'avg_most_close_score'


all_conditions = ['num_only', 'both', 'numeric', 'verbal']
conditions_per_study = {1: ['numeric', 'verbal'], 2: ['num_only', 'both']}
condition_names_per_study = {1: ['Numerical', 'Verbal'],
                             2: ['Only Numerical', 'Verbal+Numerical']}
base_directory = os.path.abspath(os.curdir)
analysis_directory = os.path.join(base_directory, 'analysis', 'text_exp_2_tests')
colors = {'verbal': 'purple', 'numeric': 'darkgreen', 'num_only': 'crimson', 'both': 'darkblue'}
markers = {'verbal': 's', 'numeric': 'o', 'num_only': 'v', 'both': 'd'}
graph_directory = os.path.join(base_directory, 'per_study_graphs')
computation_paper_dir = os.path.join(base_directory, 'computation_paper_graphs')

strategies_dict = {'none': 'None of the strategies', 'pct_always_exaggerate': 'Always exaggerate',
                   'pct_always_lower_exaggerate': 'Always Lower Than Average', 'pct_honest': 'Honest',
                   'pct_strategic_exaggeration': 'Strategic Exaggeration',
                   'pct_switch_exaggerate': 'Switch exaggeration sign between rounds'}


# verbal condition only: for the computation paper
enterence_per_round_dict = {
    'All': [77, 65, 76, 71, 73, 69, 74, 67, 68, 68],
    'Female': [76, 70, 76, 73, 73, 72, 75, 67, 69, 69],
    'Male': [79, 61, 77, 70, 74, 67, 74, 68, 68, 68]
}
x = [2.5, 3.3, 3.8, 4.2, 5, 5.4, 5.8, 6.3, 7.1, 7.5, 7.9, 8.3, 8.8, 9.2, 9.6, 10]

enterenc_per_score_dict = {
    'All': [7, 9, 18, 9, 14, 21, 22, 19, 53, 69, 40, 65, 71, 80, 76, 84],
    'Female': [12, 0, 14, 13, 0, 22, 24, 17, 50, 75, 25, 63, 73, 83, 77, 85],
    'Male': [0, 18, 22, 3, 16, 16, 20, 21, 58, 64, 50, 67, 69, 78, 75, 83],
}

enterence_per_round_dict_test_data = {
    'All': [76, 74, 72, 78, 73, 69, 74, 67, 68, 68],

}

pct_dm_per_number_of_rounds_enter_dict = {
    'All': [0.73, 1.22, 2.69, 9.8, 15.68, 25.24, 25.73, 14.21, 4.65]
}

pct_dm_per_number_of_rounds_enter_dict_test_data = {
    'All': [0, 0, 1.98, 6.93, 17.82, 26.73, 22.77, 19.8, 3.96]
}

pre_round_dict = {
    'Previous Trial Chose And Lose': [59, 82, 74, 76, 69, 75, 64, 69, 72],
    "Previous Trial Didn't Choose And Could Lose": [86, 80, 64, 73, 64, 75, 65, 66, 73],
    'Previous Trial Chose And Earn': [63, 72, 72, 74, 72, 76, 68, 68, 69],
    "Previous Trial Didn't Choose And Could Earn": [64, 74, 65, 65, 67, 69, 62, 70, 56],
}

markers_colors_models = {
    'SVM-CR': ['o', 'grey'],
    'LSTM-TR': ['v', 'darkgreen'],
    'LSTM-CR': ['D', 'darkblue'],
    'LSTM-TRCR': ['s', 'crimson'],
    'Transformer-CR': ['p', 'violet'],
    'Transformer-TRCR': ['*', 'purple'],
    'Transformer-TR': ['h', 'pink'],
    'MVC': ['d', 'black'],
    'EWG': ['X', 'lightgreen'],
    'AVG': ['^', 'orange'],
    'MED': ['<', 'deepskyblue']
}

models_index_rmse = ['SVM-CR', 'LSTM-TR', 'LSTM-CR', 'LSTM-TRCR', 'Transformer-TR', 'Transformer-CR', 'Transformer-TRCR']
bert_domain_compare_rmse = {
    'HCF': [29.8, 26.6, 24.7, 29.7, 33.1, 25.2, 25.2],
    'BERT': [27.2, 34, 28.4, 33.8, 37.2, 25.5, 25.3],
    'BERT + HCF': [27.4, 30.4, 25.6, 28.3, 37.2, 25.46, 25.4]
}

models_index_macro = ['SVM-CR', 'LSTM-TR', 'LSTM-CR', 'LSTM-TRCR', 'Transformer-TR', 'Transformer-CR', 'Transformer-TRCR']
bert_domain_compare_f_macro = {
    'HCF': [29.8, 48.3, 34.5, 31.7, 33.9, 16.7, 31.6],
    'BERT': [20.8, 32.8, 27.7, 23.9, 16.3, 12.3, 12.1],
    'BERT + HCF': [21.9, 39.2, 27.5, 26.2, 16.3, 12.8, 12.3]
}

models_index_accuracy = ['LSTM-TR', 'LSTM-TRCR', 'Transformer-TR', 'Transformer-TRCR']
bert_domain_compare_per_trial_accuracy = {
    'HCF': [76.5, 76.9, 75.3, 76.2],
    'BERT': [61.3, 62.6, 73.2, 73.2],
    'BERT + HCF': [70.2, 71.8, 73.2, 73.2]
}

models_index_trial_macro = ['LSTM-TR', 'LSTM-TRCR', 'Transformer-TR', 'Transformer-TRCR']
bert_domain_compare_per_trial_macro = {
    'HCF': [70, 70.5, 60.1, 55.5],
    'BERT': [51.8, 51.5, 42.3, 42.3],
    'BERT + HCF': [60, 61.2, 42.3, 42.3]
}

raisha_results_rmse = {
    'SVM-CR': [18.85, 27.4, 27.14, 26.34, 26.4, 27.56, 28.95, 30.82, 34.8, 42.86],
    # 'CRF-TR' : [],
    'LSTM-TR': [16.5, 17.3, 19.06, 19.12, 22.0, 23.89, 24.93, 29.74, 34.82, 44.89],
    'LSTM-CR': [20.05, 17.12, 17.23, 16.03, 19.0, 21.12, 24.87, 27.77, 31.01, 40.08],
    'LSTM-TRCR': [20.93, 26.14, 24.15, 22.53, 26.92, 29.53, 28.12, 31.28, 33.93, 40.4],
    'Transformer-TR': [None, 25.18, 26.0, 25.9, 28.08, 29.21, 29.96, 33.16, 40.53, 50.73],
    'Transformer-CR': [None, 14.9, 15.46, 15.65, 17.54, 20.09, 22.53, 26.57, 32.24, 45.31],
    'Transformer-TRCR': [None, 16.07, 16.61, 16.82, 19.16, 21.09, 23.03, 26.8, 32.71, 42.65],
    # 'MVC': [29.6, 30.34, 30.69, 30.65, 32.41, 33.42, 34.2, 38.11, 42.51, 55.4],
    # 'EWG': [29.6, 30.34, 30.69, 30.65, 32.41, 33.42, 34.2, 38.11, 42.51, 55.4],
    'AVG': [14.16, 15.13, 15.58, 15.81, 17.52, 20.02, 22.58, 26.98, 32.76, 46.13],
    'MED': [13.8, 14.86, 15.34, 15.54, 17.45, 19.87, 22.29, 26.9, 32.7, 46.37],
}

raisha_results_macro = {
    # 'CRF-TR' : [],
    'SVM-CR': [22.36, 27.0, 19.52, 28.37, 17.83, 19.31, 19.13, 29.63, 30.82, 18.44],
    'LSTM-TR': [31.7, 34.5, 34.2, 41.08, 37.13, 30.45, 37.3, 35.46, 50.34, 75.73],
    'LSTM-CR': [23.34, 26.08, 31.15, 34.29, 28.98, 25.32, 29.62, 26.65, 27.78, 26.51],
    'LSTM-TRCR': [26.33, 24.17, 22.71, 26.32, 24.77, 22.24, 27.02, 26.95, 27.72, 30.62],
    'Transformer-TR': [None, 31.96, 25.44, 30.95, 25.13, 22.12, 27.01, 31.47, 40.25, 59.02],
    'Transformer-CR': [None, 24.14, 24.78, 26.13, 19.77, 17.4, 17.82, 19.09, 7.65, 8.74],
    'Transformer-TRCR': [None, 33.41, 32.02, 31.58, 30.45, 23.82, 26.47, 28.59, 25.18, 24.62],
    # 'MVC': [21.48, 24.32, 25.86, 20.23, 21.78, 17.63, 27.06, 14.69, 23.5, 40.94],
    # 'EWG': [21.48, 24.32, 25.86, 20.23, 21.78, 17.63, 27.06, 14.69, 23.5, 40.94],
    'AVG': [22.66, 17.87, 17.16, 22.66, 22.08, 12.59, 14.06, 13.67, 17.87, 0.0],
    'MED': [21.67, 21.99, 22.96, 20.83, 21.88, 15.95, 22.73, 14.35, 21.62, 27.29],
}

raisha_results_micro = {
    # 'CRF-TR' : [],
    'SVM-CR': [24.26, 38.61, 40.1, 37.78, 50.5, 49.5, 37.62, 61.39, 51.98, 33.33],
    'LSTM-TR': [42.57, 48.02, 45.05, 51.98, 44.55, 49.34, 44.72, 48.68, 57.43, 77.56],
    'LSTM-CR': [46.28, 46.12, 46.2, 47.77, 44.47, 50.66, 39.35, 42.98, 39.02, 46.78],
    'LSTM-TRCR': [45.71, 47.36, 44.72, 47.36, 30.69, 38.78, 41.42, 45.87, 34.65, 46.86],
    # 'Transformer-TR': [None, 8.91, 7.42, 8.42, 6.6, 8.25, 10.23, 9.4, 15.84, 37.29],
    'Transformer-CR': [None, 42.73, 48.51, 52.97, 37.62, 48.02, 41.25, 47.03, 43.23, 51.49],
    'Transformer-TRCR': [None, 42.74, 50.83, 53.47, 37.29, 45.71, 41.08, 46.36, 42.08, 52.14],
    'MVC': [73.27, 57.43, 63.37, 68.32, 48.51, 54.46, 68.32, 41.58, 54.46, 69.31],
    'EWG': [73.27, 57.43, 63.37, 68.32, 48.51, 54.46, 68.32, 41.58, 54.46, 69.31],
    'AVG': [73.27, 56.44, 63.37, 68.32, 48.51, 54.46, 68.32, 41.58, 54.46, 69.31],
    'MED': [73.27, 56.44, 63.37, 68.32, 48.51, 54.46, 68.32, 41.58, 54.46, 69.31],
}

raisha_results_accuracy_per_trail = {
    # 'CRF-TR' : [],
    'LSTM-TR': [76.47, 75.84, 76.01, 76.76, 76.07, 76.34, 77.23, 77.34, 77.31, 79.7],
    'LSTM-TRCR': [77.49, 77.16, 76.94, 76.94, 76.15, 76.3, 76.65, 76.02, 76.48, 77.72],
    'Transformer-TR': [None, 75.34, 75.14, 75.25, 74.48, 74.98, 76.16, 77.06, 75.0, 74.1],
    'Transformer-TRCR': [None, 76.28, 76.88, 77.02, 75.88, 75.21, 75.74, 76.57, 74.01, 74.92],
    'MVC': [73.76, 73.49, 73.39, 73.55, 72.61, 73.07, 74.01, 72.94, 72.77, 69.31],
    'EWG': [73.76, 73.49, 73.39, 73.55, 72.61, 73.07, 74.01, 72.94, 72.77, 69.31],
}

round_results_accuracy_per_trail = {
    # 'CRF-TR' : [],
    'LSTM-TR': [80.2, 77.84, 73.27, 69.31, 78.3, 75.28, 73.07, 77.39, 79.95, 75.95],
    'LSTM-TRCR': [78.22, 77.92, 72.69, 71.4, 81.1, 76.54, 71.81, 79.28, 79.39, 75.8],
    'Transformer-TR': [None, 73.47, 77.56, 72.36, 80.2, 73.39, 70.79, 75.33, 80.36, 75.19],
    'Transformer-TRCR': [None, 74.65, 76.08, 72.03, 80.64, 77.6, 72.84, 74.81, 81.99, 74.55],
    'MVC': [76.24, 69.31, 74.26, 72.28, 79.21, 70.3, 69.31, 77.23, 73.27, 76.24],
    'EWG': [76.24, 69.31, 74.26, 72.28, 79.21, 70.3, 69.31, 77.23, 73.27, 76.24],
}

raisha_results_macro_per_trail = {
    # 'CRF-TR' : [],
    'LSTM-TR': [69.74, 69.19, 69.48, 70.1, 69.79, 69.9, 70.79, 70.95, 70.88, 75.73],
    'LSTM-TRCR': [70.73, 70.62, 70.4, 70.29, 69.83, 70.02, 70.48, 69.86, 70.66, 74.3],
    'Transformer-TR': [None, 59.16, 59.05, 59.41, 59.78, 60.65, 61.91, 62.98, 58.49, 59.02],
    'Transformer-TRCR': [None, 64.76, 65.81, 66.28, 65.52, 64.78, 65.28, 66.46, 63.56, 68.46],
    'MVC': [42.45, 42.36, 42.32, 42.38, 42.06, 42.22, 42.53, 42.18, 42.12, 40.94],
    'EWG': [42.45, 42.36, 42.32, 42.38, 42.06, 42.22, 42.53, 42.18, 42.12, 40.94],
}

round_results_macro_per_trail = {
    # 'CRF-TR' : [],
    'LSTM-TR': [71.17, 73.88, 65.67, 63.37, 68.66, 70.38, 66.68, 71.01, 73.28, 66.07],
    'LSTM-TRCR': [70.01, 74.16, 65.73, 65.01, 71.39, 71.87, 64.98, 73.43, 72.62, 66.12],
    'Transformer-TR': [None, 61.21, 61.67, 53.32, 59.96, 58.79, 55.24, 58.14, 68.14, 56.67],
    'Transformer-TRCR': [None, 67.2, 63.26, 57.26, 65.45, 69.08, 62.03, 62.68, 73.59, 59.51],
    'MVC': [43.26, 40.94, 42.62, 41.95, 44.2, 41.28, 40.94, 43.58, 42.28, 43.26],
    'EWG': [43.26, 40.94, 42.62, 41.95, 44.2, 41.28, 40.94, 43.58, 42.28, 43.26],
}


# all conditions: for the behavior paper
rounds_dict = {
    'all rounds': {
        'numeric_p_enter': [0.27, 0.11, 0.11, 0.19, 0.11, 0.6, 0.32, 0.36, 0.53, 0.59, 0.75, 0.72, 0.76, 0.83, 0.84, 0.89],
        'both_p_enter': [0, 0.2, 0, 0, 0, 0, 0.21, 0.23, 0.5, 0.25, 0.5, 0.66, 0.83, 0.85, 0.8, 0.89],
        'numeric_experts': [22, 52, 17, 61, 9, 15, 166, 158, 66, 77, 37, 274, 177, 431, 658, 1669],
        'both_experts': [3, 5, 2, 12, 1, 0, 33, 21, 14, 12, 2, 30, 31, 75, 102, 249],
        'verbal_p_enter': [0.08, 0.09, 0.19, 0.09, 0.14, 0.21, 0.23, 0.19, 0.54, 0.69, 0.4, 0.65, 0.71, 0.81, 0.77, 0.85],
        'verbal_experts': [13, 33, 16, 55, 7, 19, 184, 185, 67, 55, 25, 236, 156, 426, 713, 1835],
        'num_only_p_enter': [0.0, 0.33, 0.29, 0.36, 0.0, 0.0, 0.3, 0.29, 0.5, 0.57, 0.5, 0.73, 0.81, 0.88, 0.85, 0.91],
        'num_only_experts': [2, 9, 7, 11, 1, 2, 10, 35, 16, 30, 18, 52, 42, 77, 126, 148]},
    'round 1': {
        'numeric_p_enter': [0.33, 0.0, 0.0, 0.25, 0.5, 0.8, 0.42, 0.62, 1.0, 0.94, 0.62, 0.94, 1.0, 0.91, 0.93, 0.95],
        'both_p_enter': [None, 1.0, None, None, None, None, None, 0.67, 0.5, 0.33, None, 0.78, 1.0, 0.78, 0.75, 0.9],
        'numeric_experts': [3, 2, 2, 4, 2, 5, 12, 13, 4, 18, 8, 32, 18, 47, 72, 148],
        'both_experts': [0, 1, 0, 0, 0, 0, 0, 3, 2, 3, 0, 9, 4, 9, 8, 20],
        'verbal_p_enter': [0.0, 0.0, 0.4, 0.18, None, 0.0, 0.45, 0.15, 0.33, 1.0, 0.67, 0.68, 0.76, 0.92, 0.86, 0.93],
        'verbal_experts': [1, 3, 5, 11, 0, 1, 20, 26, 3, 6, 3, 19, 17, 48, 85, 153],
        'num_only_p_enter': [None, 0.0, 1.0, 0.5, None, None, None, None, 1.0, 0.88, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        'num_only_experts': [0, 1, 1, 2, 0, 0, 0, 0, 2, 8, 1, 5, 5, 5, 14, 15]},
    'round 2': {
        'numeric_p_enter': [0.0, 0.4, 0.0, 0.12, None, 0.5, 0.56, 0.26, 0.67, 1.0, 1.0, 0.78, 0.86, 0.84, 0.89, 0.92],
        'both_p_enter': [None, None, 0.0, 0.0, None, None, 0.0, 0.5, None, 0.33, 1.0, None, 1.0, 0.75, 0.62, 1.0],
        'numeric_experts': [1, 5, 5, 8, 0, 2, 18, 19, 9, 3, 3, 32, 21, 45, 65, 155],
        'both_experts': [0, 0, 1, 4, 0, 0, 3, 2, 0, 3, 1, 0, 4, 8, 8, 26],
        'verbal_p_enter': [0.0, 0.33, 0.0, 0.11, None, None, 0.23, 0.28, 0.5, 0.57, 1.0, 0.74, 0.65, 0.74, 0.81, 0.81],
        'verbal_experts': [1, 3, 3, 9, 0, 0, 31, 32, 12, 7, 1, 34, 20, 31, 78, 143],
        'num_only_p_enter': [None, None, 0.0, 0.67, None, None, 0.33, 0.0, 1.0, 1.0, 0.5, 1.0, 1.0, 0.83, 0.8, 1.0],
        'num_only_experts': [0, 0, 1, 3, 0, 0, 3, 3, 2, 1, 2, 5, 2, 18, 5, 14]},

    'round 3': {
        'numeric_p_enter': [0.0, 0.5, 0.0, 0.15, None, 0.0, 0.2, 0.18, 0.14, 0.75, 1.0, 0.83, 0.54, 0.87, 0.88, 0.89],
        'both_p_enter': [None, None, None, None, 0.0, None, 0.14, 0.5, None, 0.0, None, 0.57, 0.75, 0.75, 0.62, 0.88],
        'numeric_experts': [3, 4, 1, 13, 0, 1, 15, 11, 7, 4, 3, 18, 13, 45, 57, 196],
        'both_experts': [0, 0, 0, 0, 1, 0, 7, 2, 0, 1, 0, 7, 4, 12, 8, 17],
        'verbal_p_enter': [0.0, 0.0, None, 0.0, None, 0.2, 0.11, 0.21, 0.67, 0.43, None, 0.86, 0.78, 0.82, 0.8, 0.88],
        'verbal_experts': [5, 1, 0, 5, 0, 5, 9, 14, 6, 7, 0, 22, 18, 40, 61, 207],
        'num_only_p_enter': [None, 1.0, None, None, None, None, 0.0, 0.29, 0.0, 0.4, 1.0, 0.71, 1.0, 0.8, 0.64, 0.8],
        'num_only_experts': [0, 1, 0, 0, 0, 0, 2, 7, 1, 5, 1, 7, 4, 5, 11, 15]},

    'round 4': {
        'numeric_p_enter': [0.0, 0.0, 0.5, 0.25, 0.0, 1.0, 0.41, 0.4, 0.67, 0.67, 1.0, 0.62, 0.78, 0.81, 0.85, 0.9],
        'both_p_enter': [None, None, None, 0.0, None, None, 0.5, 0.0, 0.25, None, None, 0.0, 1.0, 0.78, 0.7, 0.96],
        'numeric_experts': [1, 6, 2, 4, 2, 1, 17, 10, 6, 6, 5, 26, 32, 47, 67, 158],
        'both_experts': [0, 0, 0, 3, 0, 0, 4, 2, 4, 0, 0, 2, 1, 9, 10, 24],
        'verbal_p_enter': [0.0, 0.0, 0.0, 0.0, 0.5, None, 0.09, 0.27, 0.43, 1.0, 0.0, 0.6, 0.85, 0.78, 0.78, 0.85],
        'verbal_experts': [2, 3, 2, 5, 2, 0, 22, 15, 7, 2, 2, 15, 13, 32, 79, 202],
        'num_only_p_enter': [None, 0.5, 0.33, 0.0, None, None, 0.5, 0.0, None, 0.5, 1.0, 0.5, 0.5, 1.0, 0.78, 1.0],
        'num_only_experts': [0, 2, 3, 3, 0, 0, 2, 3, 0, 4, 1, 2, 6, 6, 18, 8]},

    'round 5': {
        'numeric_p_enter': [0.25, 0.17, None, 0.0, 0.0, None, 0.25, 0.27, 0.5, 0.5, 1.0, 0.76, 0.7, 0.86, 0.84, 0.9],
        'both_p_enter': [0.0, 0.0, 0.0, 0.0, None, None, 0.0, None, 0.0, 0.0, None, 1.0, 0.67, 0.8, 0.67, 0.81],
        'numeric_experts': [4, 6, 0, 5, 3, 0, 20, 15, 6, 10, 1, 34, 23, 35, 76, 152],
        'both_experts': [1, 2, 1, 2, 0, 0, 1, 0, 2, 1, 0, 4, 3, 5, 12, 26],
        'verbal_p_enter': [None, 0.11, 0.0, 0.4, None, 0.0, 0.31, 0.21, 0.75, 0.83, 0.0, 0.62, 0.89, 0.85, 0.77, 0.86],
        'verbal_experts': [0, 9, 1, 5, 0, 1, 16, 19, 4, 6, 3, 24, 9, 53, 70, 180],
        'num_only_p_enter': [None, 0.0, None, 0.0, None, 0.0, 1.0, 0.67, 0.5, 0.0, 1.0, 1.0, 1.0, 1.0, 0.88, 0.85],
        'num_only_experts': [0, 3, 0, 2, 0, 1, 1, 3, 2, 1, 2, 5, 3, 7, 8, 20]},

    'round 6': {
        'numeric_p_enter': [0.5, 0.14, 0.0, 0.25, None, None, 0.35, 0.45, 0.71, 0.5, 0.67, 0.7, 0.6, 0.74, 0.85, 0.86],
        'both_p_enter': [0.0, None, None, None, None, None, 0.33, 0.33, 0.67, 1.0, None, 0.0, 1.0, 0.5, 0.85, 0.9],
        'numeric_experts': [4, 7, 1, 4, 0, 0, 31, 22, 7, 4, 3, 27, 15, 38, 71, 156],
        'both_experts': [1, 0, 0, 0, 0, 0, 3, 3, 3, 1, 0, 1, 4, 2, 13, 29],
        'verbal_p_enter': [0.0, 0.2, None, 0.0, 0.0, 0.0, 0.67, 0.11, 0.62, 0.86, 0.8, 0.45, 0.62, 0.79, 0.68, 0.81],
        'verbal_experts': [1, 5, 0, 4, 2, 1, 9, 9, 8, 7, 5, 33, 13, 34, 80, 193],
        'num_only_p_enter': [0.0, None, 0.0, None, None, None, None, 0.0, 0.0, 0.67, 0.0, 0.5, 0.67, 0.83, 0.91, 0.89],
        'num_only_experts': [1, 0, 1, 0, 0, 0, 0, 6, 1, 3, 1, 6, 3, 6, 11, 19]},

    'round 7': {
        'numeric_p_enter': [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.27, 0.36, 0.33, 0.0, 1.0, 0.65, 0.94, 0.84, 0.83, 0.92],
        'both_p_enter': [None, None, None, 0.0, None, None, 0.5, 0.0, 1.0, 0.0, None, 1.0, 0.5, 1.0, 1.0, 0.93],
        'numeric_experts': [2, 6, 1, 2, 1, 1, 11, 11, 6, 6, 1, 31, 18, 38, 75, 179],
        'both_experts': [0, 0, 0, 1, 0, 0, 4, 1, 1, 1, 0, 1, 2, 5, 14, 28],
        'verbal_p_enter': [None, 0.0, 0.0, 0.0, 0.0, 0.5, 0.33, 0.19, 0.67, 0.6, 0.0, 0.52, 0.64, 0.91, 0.75, 0.86],
        'verbal_experts': [0, 4, 1, 4, 1, 2, 9, 16, 3, 5, 2, 21, 14, 47, 73, 200],
        'num_only_p_enter': [None, 0.0, 0.0, None, 0.0, None, 0.0, 0.33, 0.0, 1.0, 0.5, 0.8, 0.83, 0.92, 0.9, 0.85],
        'num_only_experts': [0, 1, 1, 0, 1, 0, 1, 3, 1, 1, 4, 5, 6, 12, 10, 13]},

    'round 8': {
        'numeric_p_enter': [None, 0.0, 0.0, 0.29, None, 0.5, 0.25, 0.25, 0.5, 0.69, 0.8, 0.6, 0.58, 0.82, 0.66, 0.91],
        'both_p_enter': [0.0, 0.0, None, 0.0, None, None, 0.0, 0.0, None, 0.0, None, 1.0, 1.0, 1.0, 0.8, 0.88],
        'numeric_experts': [0, 7, 2, 7, 0, 2, 16, 16, 4, 13, 5, 15, 12, 40, 56, 192],
        'both_experts': [1, 1, 0, 2, 0, 0, 6, 1, 0, 1, 0, 1, 4, 12, 5, 25],
        'verbal_p_enter': [1.0, 0.0, 0.0, 0.0, None, 0.2, 0.15, 0.15, 0.56, 0.8, 0.5, 0.64, 0.62, 0.69, 0.76, 0.82],
        'verbal_experts': [1, 1, 1, 7, 0, 5, 26, 13, 9, 5, 2, 22, 16, 45, 58, 191],
        'num_only_p_enter': [None, None, None, 1.0, None, 0.0, None, 0.5, 0.75, 1.0, None, 0.6, 0.83, 1.0, 1.0, 0.87],
        'num_only_experts': [0, 0, 0, 1, 0, 1, 0, 2, 4, 1, 0, 5, 6, 6, 18, 15]},

    'round 9': {
        'numeric_p_enter': [1.0, 0.0, 0.0, 0.17, None, 1.0, 0.21, 0.38, 0.5, 0.17, 0.67, 0.69, 0.82, 0.82, 0.9, 0.88],
        'both_p_enter': [None, None, None, None, None, None, 0.0, 0.0, 1.0, 0.0, 0.0, None, 0.5, 1.0, 1.0, 0.86],
        'numeric_experts': [1, 2, 1, 6, 0, 1, 14, 13, 8, 6, 3, 26, 17, 40, 52, 196],
        'both_experts': [0, 0, 0, 0, 0, 0, 1, 3, 2, 1, 1, 0, 4, 7, 11, 28],
        'verbal_p_enter': [0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.08, 0.0, 0.33, 0.67, 0.2, 0.71, 0.65, 0.7, 0.79, 0.84],
        'verbal_experts': [1, 1, 2, 3, 1, 2, 24, 13, 3, 3, 5, 24, 23, 53, 61, 184],
        'num_only_p_enter': [None, 1.0, None, None, None, None, 0.0, 0.33, 0.0, 0.0, 0.2, 0.86, 0.67, 0.75, 0.69, 0.92],
        'num_only_experts': [0, 1, 0, 0, 0, 0, 1, 3, 2, 1, 5, 7, 3, 8, 16, 12]},

    'round 10': {
        'numeric_p_enter': [0.33, 0.0, 0.5, 0.38, 0.0, 0.0, 0.25, 0.43, 0.44, 0.29, 0.4, 0.67, 0.62, 0.84, 0.79, 0.89],
        'both_p_enter': [None, 0.0, None, None, None, None, 0.25, 0.0, None, None, None, 0.6, 1.0, 1.0, 0.85, 0.85],
        'numeric_experts': [3, 7, 2, 8, 1, 2, 12, 28, 9, 7, 5, 33, 8, 56, 67, 137],
        'both_experts': [0, 1, 0, 0, 0, 0, 4, 4, 0, 0, 0, 5, 1, 6, 13, 26],
        'verbal_p_enter': [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.17, 0.21, 0.5, 0.43, 0.5, 0.73, 0.77, 0.86, 0.65, 0.84],
        'verbal_experts': [1, 3, 1, 2, 1, 2, 18, 28, 12, 7, 2, 22, 13, 43, 68, 182],
        'num_only_p_enter': [0.0, None, None, None, None, None, None, 0.6, 0.0, 0.2, 0.0, 0.2, 0.75, 0.75, 0.87, 0.94],
        'num_only_experts': [1, 0, 0, 0, 0, 0, 0, 5, 1, 5, 1, 5, 4, 4, 15, 17]},
}


honesty_dict = {'numeric': [5.21, 8.45, 8.87, 9.13, 9.33, 9.59, 9.58, 9.59, 9.8, 9.86],
                'verbal': [5.47, 8.56, 9.04, 9.24, 9.4, 9.6, 9.6, 9.66, 9.82, 9.87],
                'num_only': [5.02, 8.16, 8.45, 8.89, 8.82, 8.95, 9.59, 9.38, 9.65, 9.75],
                'both': [5.24, 8.58, 8.89, 9.24, 9.44, 9.48, 9.29, 9.68, 9.79, 9.85]}

# laying_dict = {
#     'numeric': [0.48692153, 0.70301703, 0.66246221, 0.57085051, 0.64515171, 0.75223023, 0.59929727, 0.49672462, 0.55856256, 0.38331854],
#     'verbal': [0.61221578, 0.74679636, 0.74139887, 0.62607457, 0.68487395, 0.76253376, 0.62032926, 0.58212297, 0.61210571, 0.43734015],
#     'num_only': [0.39762871,  0.58961698,  0.46641557,  0.45478834,  0.37494395,  0.37277986,0.61144867,  0.22996443,  0.23360354, -0.09064112],
#     'both': [0.50156495, 0.75656168, 0.66898148, 0.62479475, 0.7010582,  0.68862275, 0.33176101, 0.60493827, 0.55072464, 0.36231884]
#
# }


def clean_data(data: pd.DataFrame) -> pd.DataFrame:
    data = data.loc[(data.status == 'play') & (data.player_id_in_group == 1)]
    data['dm_expected_payoff'] = np.where(data.group_sender_payoff == 1, data.group_average_score - 8, 0)
    data = data[['group_sender_payoff',	'group_receiver_payoff', 'pair_id', 'group_lottery_result',
                 'group_average_score', 'group_sender_answer_scores', 'dm_expected_payoff', 'subsession_round_number',
                 'group_score_6', 'avg_most_close_score', 'previous_round_lottery_result', 'previous_round_decision']]  # expert_strategy
    data['honesty'] = data['group_sender_answer_scores'] - data['group_average_score']
    data['expert_answer_above_8'] = np.where(data.group_sender_answer_scores > 8, 1, 0)
    data['best_reply'] = np.where((data['expert_answer_above_8'] == 1) & (data.group_sender_payoff == 1), 1,
                                  (np.where((data['expert_answer_above_8'] == 0) &
                                            (data.group_sender_payoff == 0), 1, 0)))
    data['first_half'] = np.where(data.subsession_round_number < 6, 1, 0)
    data['laying'] = data.apply(lambda x: (x['group_sender_answer_scores'] - x[column_to_define_exaggerate]) /
                                          (x['group_score_6'] - x[column_to_define_exaggerate]), axis=1)
    data['expert_want_to_persuade'] = np.where(data.group_sender_answer_scores > data.group_average_score, 1,
                                               np.where(data['expert_answer_above_8'] == 1, 1, 0))
    data['expected_outcome_taking_hotel'] = data.group_average_score - 8
    data['previous_round_dm_payoff'] = data.previous_round_decision * data.previous_round_lottery_result

    return data


def significant_tests(data_1: pd.DataFrame, data_2: pd.DataFrame, criterion: str):
    statistic = scipy.stats.f_oneway(data_1, data_2)
    print(criterion)
    print(f'Groups criterion vars: {np.var(data_1), np.var(data_2)}')
    print(f'Groups criterion means: {np.mean(data_1), np.mean(data_2)}')
    print(f'Groups size: {data_1.shape}, {data_2.shape}')
    kruskal = scipy.stats.kruskal(data_1, data_2)
    ttest = scipy.stats.ttest_ind(data_1, data_2)
    print(f'ANOVA test: {statistic},\nKruskal test: {kruskal}\nT_test: {ttest}\n')

    return


def trust_graphs(study: int, data_1_p_enter_list_all_rounds: list=None, data_2_p_enter_list_all_rounds: list = None):
    """

    :param study:
    :param data_1_p_enter_list_all_rounds: [average_p_enter_est<8, average_p_enter_est>8] for data 1
    :param data_2_p_enter_list_all_rounds: [average_p_enter_est<8, average_p_enter_est>8] for data 2
    :return:
    """
    condition_1 = conditions_per_study[study][0]
    condition_2 = conditions_per_study[study][1]
    index = ['Half 1\nEst < 8', 'Half 1\nEst > 8', 'Half 2\nEst < 8', 'Half 2\nEst > 8']
    data_dict = {condition_names_per_study[study][0]: list(), condition_names_per_study[study][1]: list()}
    x = [2.5, 3.3, 3.8, 4.2, 5, 5.4, 5.8, 6.3, 7.1, 7.5, 7.9, 8.3, 8.8, 9.2, 9.6, 10]

    for rng, in_title in [[range(1, 6), 'First 5'], [range(6, 11), 'Last'], [range(1, 11), 'All']]:
        fig100, ax100 = plt.subplots()
        data_1_p_enter_list = list()
        data_2_p_enter_list = list()
        data_1_experts_list = list()
        data_2_experts_list = list()

        for idx in range(len(x)):
            values = [rounds_dict[f'round {j}'][f'{condition_1}_p_enter'][idx] for j in rng]
            values = [x for x in values if x is not None]
            data_1_p_enter_list.append(round(np.average(values), 2))
            data_1_experts_list.append(sum([rounds_dict[f'round {j}'][f'{condition_1}_experts'][idx] for j in rng]))

            values = [rounds_dict[f'round {z}'][f'{condition_2}_p_enter'][idx] for z in rng]
            values = [x for x in values if x is not None]
            data_2_p_enter_list.append(round(np.average(values), 2))
            data_2_experts_list.append(sum([rounds_dict[f'round {j}'][f'{condition_2}_experts'][idx] for j in rng]))

        ax100.plot(x, data_1_p_enter_list, color=colors[condition_1], label=condition_names_per_study[study][0],
                   marker=markers[condition_1], linestyle='-')
        ax100.plot(x, data_2_p_enter_list, color=colors[condition_2], label=condition_names_per_study[study][1],
                   marker=markers[condition_2], linestyle='-')

        # plt.title(f"P(DM chose hotel) as a function of the experts\nnumerical estimate by Condition in {in_title}"
        #           f" rounds for study {study}")
        plt.xlabel('Experts Numerical Estimate', fontsize=15)
        plt.ylabel('P(DM chose hotel)', fontsize=15)
        ax100.legend(loc='upper left', shadow=True, fontsize=8)
        plt.xticks(x)
        # Add a table at the bottom of the axes
        the_table = ax100.table(cellText=[x, data_1_experts_list, data_2_experts_list],
                                rowLabels=['Experts Numerical Estimate', condition_names_per_study[study][0],
                                           condition_names_per_study[study][1]],
                                bbox=(0, -0.5, 1, 0.3))
        the_table.auto_set_font_size(False)
        the_table.set_fontsize(10)
        # plt.yticks(range(4, 11))
        # plt.show()
        fig100.savefig(os.path.join(
            graph_directory, f'P_enter_as_a_function_of_the_experts_numerical_estimate_by_Condition_in_{in_title}'
                             f'_rounds_for_study_{study}.png'), bbox_inches='tight')

        fig1000, ax1000 = plt.subplots()
        combine_dict = {
            'est<8': {f'{condition_1}_p_enter_list': [], f'{condition_2}_p_enter_list': [],
                      f'{condition_1}_experts_list': [], f'{condition_2}_experts_list': []},
            'est>8': {f'{condition_1}_p_enter_list': [], f'{condition_2}_p_enter_list': [],
                      f'{condition_1}_experts_list': [], f'{condition_2}_experts_list': []}
        }
        # split per est < 8:
        for idx, est in enumerate(x):
            if est < 8:  # for est<8 use the 1-data_1_p_enter_list --> the probability to reject
                if not np.isnan(data_1_p_enter_list[idx]):
                    combine_dict['est<8'][f'{condition_1}_p_enter_list'].append(1 - data_1_p_enter_list[idx])
                if not np.isnan(data_2_p_enter_list[idx]):
                    combine_dict['est<8'][f'{condition_2}_p_enter_list'].append(1 - data_2_p_enter_list[idx])
                combine_dict['est<8'][f'{condition_1}_experts_list'].append(data_1_experts_list[idx])
                combine_dict['est<8'][f'{condition_2}_experts_list'].append(data_2_experts_list[idx])
            else:
                if not np.isnan(data_1_p_enter_list[idx]):
                    combine_dict['est>8'][f'{condition_1}_p_enter_list'].append(data_1_p_enter_list[idx])
                if not np.isnan(data_2_p_enter_list[idx]):
                    combine_dict['est>8'][f'{condition_2}_p_enter_list'].append(data_2_p_enter_list[idx])
                combine_dict['est>8'][f'{condition_1}_experts_list'].append(data_1_experts_list[idx])
                combine_dict['est>8'][f'{condition_2}_experts_list'].append(data_2_experts_list[idx])

        data_1_p_enter_list = [round(np.average(combine_dict['est<8'][f'{condition_1}_p_enter_list']), 2),
                               round(np.average(combine_dict['est>8'][f'{condition_1}_p_enter_list']), 2)]
        data_2_p_enter_list = [round(np.average(combine_dict['est<8'][f'{condition_2}_p_enter_list']), 2),
                               round(np.average(combine_dict['est>8'][f'{condition_2}_p_enter_list']), 2)]
        data_1_experts_list = [np.sum(combine_dict['est<8'][f'{condition_1}_experts_list']),
                               np.sum(combine_dict['est>8'][f'{condition_1}_experts_list'])]
        data_2_experts_list = [np.sum(combine_dict['est<8'][f'{condition_2}_experts_list']),
                               np.sum(combine_dict['est>8'][f'{condition_2}_experts_list'])]

        if in_title == 'All':
            data_1_p_enter_list = data_1_p_enter_list_all_rounds
            data_2_p_enter_list = data_2_p_enter_list_all_rounds
        else:
            data_dict[condition_names_per_study[study][0]].extend(data_1_p_enter_list)
            data_dict[condition_names_per_study[study][1]].extend(data_2_p_enter_list)

        ax1000.plot(['est<8', 'est>8'], data_1_p_enter_list, color=colors[condition_1],
                    label=condition_names_per_study[study][0], marker=markers[condition_1], linestyle='-')
        ax1000.plot(['est<8', 'est>8'], data_2_p_enter_list, color=colors[condition_2],
                    label=condition_names_per_study[study][1], marker=markers[condition_2], linestyle='-')

        # plt.title(f"P(DM chose hotel) as a function of the experts\nnumerical estimate by Condition in "
        #           f"{in_title} rounds for study {study}")
        plt.xlabel('Experts Numerical Estimate', fontsize=15)
        plt.ylabel('P(DM chose hotel)', fontsize=15)
        ax1000.legend(loc='upper left', shadow=True, fontsize=8)
        # plt.xticks(['est<8', 'est>8'])
        # Add a table at the bottom of the axes
        data_1_experts_list = [(data_1_experts_list[idx], data_1_p_enter_list[idx]) for idx in
                               range(len(data_1_p_enter_list))]
        data_2_experts_list = [(data_2_experts_list[idx], data_2_p_enter_list[idx]) for idx in
                               range(len(data_2_p_enter_list))]
        the_table = ax1000.table(
            cellText=[['est<8', 'est>8'], data_1_experts_list, data_2_experts_list],
            rowLabels=['Experts Numerical Estimate', condition_names_per_study[study][0],
                       condition_names_per_study[study][1]],
            bbox=(0, -0.5, 1, 0.3))
        the_table.auto_set_font_size(False)
        the_table.set_fontsize(10)
        plt.yticks(np.arange(0.1, 1, 0.1))
        # plt.show()
        fig1000.savefig(
            os.path.join(graph_directory, f'P_enter_as_a_function_of_the_experts_numerical_estimate_by_Condition_in_'
                                          f'{in_title}_rounds_est_8__for_study_{study}.png'), bbox_inches='tight')

    # plt.figure(figsize=(10, 5))
    data_df = pd.DataFrame.from_dict(data_dict)
    data_df.index = index
    data_df = data_df.reindex(['Half 1\nEst < 8', 'Half 2\nEst < 8', 'Half 1\nEst > 8', 'Half 2\nEst > 8'])
    ax2 = data_df.plot(kind="bar", stacked=False, rot=0,
                       color=[colors[condition_1], colors[condition_2]])
    # plt.title("The Decision Makers' Average Expected Payoff Throughout the Experiment")
    # plt.xlabel('Round Number')
    plt.ylabel('Average Best Reply Rate')
    # rects = ax2.patches
    # autolabel(rects, ax2, rotation='horizontal', max_height=data_df.max(), convert_to_int=False)
    ax2.legend(loc='upper left', shadow=True)
    # plt.show()
    fig_to_save = ax2.get_figure()
    fig_to_save.savefig(
        os.path.join(graph_directory,
                     f'trust_rates_(below_and_above_estimation_of_8)_first_and_last_5_trials_study{study}.png'),
        bbox_inches='tight')


def honesty_graph(study: int):
    """The Communication Type Effect on the Experts Cheating Level"""
    fig1, ax1 = plt.subplots()
    ax1.axis([4, 10, 4, 10])
    x = [4.17, 6.66, 7.44, 7.97, 8.11, 8.33, 8.94, 9.19, 9.54, 9.77]

    ax1.plot(x, honesty_dict[conditions_per_study[study][0]], color=colors[conditions_per_study[study][0]],
             label=condition_names_per_study[study][0], marker=markers[conditions_per_study[study][0]], linestyle='-')
    ax1.plot(x, honesty_dict[conditions_per_study[study][1]], color=colors[conditions_per_study[study][1]],
             label=condition_names_per_study[study][1], marker=markers[conditions_per_study[study][1]], linestyle='-')
    ax1.plot(x, x, color='darkviolet', marker='.', linestyle='-', label='Truth Telling')

    # plt.title(f"The Selected Score as a Function of the Hotels' Average Score\nby Condition for study {study}")
    plt.xlabel('Hotel Average Score', fontsize=15)
    plt.ylabel('Expert Average Signal', fontsize=15)
    ax1.legend(loc='upper left', shadow=True, fontsize=8)
    plt.xticks(range(4, 11))
    plt.yticks(range(4, 11))
    # plt.show()
    fig1.savefig(os.path.join(graph_directory,
                              f'The_Communication_Type_Effect_on_the_Experts_Cheating_Level_study_{study}.png'),
                 bbox_inches='tight')


def both_exp_laying_graph(role_dict: dict, ylabel: str, title: str, laying_dict: dict):
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    x = [4.17, 6.66, 7.44, 7.97, 8.11, 8.33, 8.94, 9.19, 9.54, 9.77]

    ax1.plot(x, laying_dict[conditions_per_study[1][0]], color=colors[conditions_per_study[1][0]],
             label=condition_names_per_study[1][0], marker=markers[conditions_per_study[1][0]])
    ax1.plot(x, laying_dict[conditions_per_study[1][1]], color=colors[conditions_per_study[1][1]],
             label=condition_names_per_study[1][1], marker=markers[conditions_per_study[1][1]])
    ax1.plot(x, laying_dict[conditions_per_study[2][0]], color=colors[conditions_per_study[2][0]],
             label=condition_names_per_study[2][0], marker=markers[conditions_per_study[2][0]])
    ax1.plot(x, laying_dict[conditions_per_study[2][1]], color=colors[conditions_per_study[2][1]],
             label=condition_names_per_study[2][1], marker=markers[conditions_per_study[2][1]])

    ax1.set_title(f"(a) Experts Dishonesty as a function of the Hotel's average score")
    ax1.set(xlabel='Hotel Average Score: Decision-Maker Expected Payoff', ylabel='Expert Dishonesty Measure')
    ax1.legend(loc='lower left', shadow=True, fontsize=8)

    index = list(range(1, 11))
    ax2.plot(index, role_dict[conditions_per_study[1][0]], color=colors[conditions_per_study[1][0]],
             label=condition_names_per_study[1][0], marker=markers[conditions_per_study[1][0]], linestyle='-')
    ax2.plot(index, role_dict[conditions_per_study[1][1]], color=colors[conditions_per_study[1][1]],
             label=condition_names_per_study[1][1], marker=markers[conditions_per_study[1][1]], linestyle='-')

    ax2.plot(index, role_dict[conditions_per_study[2][0]], color=colors[conditions_per_study[2][0]],
             label=condition_names_per_study[2][0], marker=markers[conditions_per_study[2][0]], linestyle='-')
    ax2.plot(index, role_dict[conditions_per_study[2][1]], color=colors[conditions_per_study[2][1]],
             label=condition_names_per_study[2][1], marker=markers[conditions_per_study[2][1]], linestyle='-')

    # plt.title(title)
    ax2.set_title(f"(b) {title}")
    ax2.set(xlabel='Trial Number', ylabel=ylabel)
    ax2.legend(loc='upper right', shadow=True, fontsize=8)
    plt.xticks(index)
    # plt.show()
    fig1.savefig(os.path.join(graph_directory, f'{title}.png'), bbox_inches='tight')

    plt.xticks(range(4, 11))
    # plt.show()
    fig1.savefig(os.path.join(graph_directory, f'Laying_graph_both_exps.png'), bbox_inches='tight')


def payoff_graph(study: int, role_dict: dict, ylabel: str, title: str):
    fig1, ax1 = plt.subplots()
    index = list(range(1, 11))

    ax1.plot(index, role_dict[conditions_per_study[study][0]], color=colors[conditions_per_study[study][0]],
             label=condition_names_per_study[study][0], marker=markers[conditions_per_study[study][0]], linestyle='-')
    ax1.plot(index, role_dict[conditions_per_study[study][1]], color=colors[conditions_per_study[study][1]],
             label=condition_names_per_study[study][1], marker=markers[conditions_per_study[study][1]], linestyle='-')

    # plt.title(title)
    plt.xlabel('Trial Number', fontsize=10)
    plt.ylabel(ylabel, fontsize=10)
    if ylabel == 'Average acceptance rate':
        ax1.legend(loc='upper right', shadow=True, fontsize=8)
        plt.yticks(np.arange(0.55, 1.05, 0.05))
    else:
        plt.yticks(np.arange(0.0, 0.65, 0.05))
        if study == 1:
            ax1.legend(loc='upper right', shadow=True, fontsize=8)
        else:
            ax1.legend(loc='upper left', shadow=True, fontsize=8)

    plt.xticks(index)
    # plt.show()
    fig1.savefig(os.path.join(graph_directory, f'{title}.png'), bbox_inches='tight')


def both_studies_graphs(role_dict: dict, ylabel: str, title: str, expert_payoff: bool, laying_dict: dict=None,
                        implied_score_5_8: bool=False, laying_per_trial: bool=False,
                        equilibrium_data_dict: defaultdict(dict)=None):
    fig1, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [1, 1]})
    index = list(range(1, 11))

    for study in [1, 2]:
        axes[study - 1].plot(index, role_dict[conditions_per_study[study][0]],
                             color=colors[conditions_per_study[study][0]],
                             label=condition_names_per_study[study][0],
                             marker=markers[conditions_per_study[study][0]], linestyle='-')
        axes[study - 1].plot(index, role_dict[conditions_per_study[study][1]],
                             color=colors[conditions_per_study[study][1]],
                             label=condition_names_per_study[study][1],
                             marker=markers[conditions_per_study[study][1]], linestyle='-')
        axes[study - 1].set_title(f'Experiment {study}', fontsize=15, )
        axes[study - 1].set_xticks(index)
        axes[study - 1].set_xlabel('Trial Number', fontsize=12, )

        if study == 1:
            axes[study - 1].set_ylabel(ylabel=ylabel, fontsize=12, )

        if expert_payoff:
            axes[study - 1].legend(loc='upper right', shadow=True, fontsize=8)
            if implied_score_5_8:
                axes[study - 1].set_yticks(np.arange(-0.05, 0.96, 0.1))
            else:
                axes[study - 1].set_yticks(np.arange(0.6, 1.05, 0.05))
        else:
            axes[study - 1].set_yticks(np.arange(-0.1, 0.7, 0.05))
            if study == 1:
                axes[study - 1].legend(loc='upper right', shadow=True, fontsize=8)
            else:
                axes[study - 1].legend(loc='upper left', shadow=True, fontsize=8)

    # plt.show()
    fig1.savefig(os.path.join(graph_directory, f'{title}_2_exps.png'), bbox_inches='tight')

    # lying graph
    if laying_dict is not None:
        fig1, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [1, 1]})
        if laying_per_trial:
            x = list(range(1, 11))
            x_lable = 'Trial Number'
            y_ticks = np.arange(0.2, 0.9, 0.1)
            x_ticks = range(1, 11)
        else:
            x = [4.17, 6.66, 7.44, 7.97, 8.11, 8.33, 8.94, 9.19, 9.54, 9.77]
            x_lable = "Hotel's Expected Value"
            y_ticks = np.arange(-0.2, 0.9, 0.1)
            x_ticks = range(4, 11)

        for study in [1, 2]:
            axes[study - 1].plot(x, laying_dict[conditions_per_study[study][0]],
                                 color=colors[conditions_per_study[study][0]],
                                 label=condition_names_per_study[study][0],
                                 marker=markers[conditions_per_study[study][0]])
            axes[study - 1].plot(x, laying_dict[conditions_per_study[study][1]],
                                 color=colors[conditions_per_study[study][1]],
                                 label=condition_names_per_study[study][1],
                                 marker=markers[conditions_per_study[study][1]])
            axes[study - 1].legend(loc='upper left', shadow=True, fontsize=8)
            axes[study - 1].set_title(f'Experiment {study}', fontsize=15, )
            axes[study - 1].set_xticks(x_ticks)
            axes[study - 1].set_yticks(y_ticks)
            axes[study - 1].set_xlabel(x_lable, fontsize=12, )

            if study == 1:
                axes[study - 1].set_ylabel(ylabel='Exaggeration', fontsize=12, )

        # plt.title(f"The Selected Score as a Function of the Hotels' Average Score\nby Condition for study {study}")
        # plt.show()
        fig1.savefig(os.path.join(graph_directory, f'Laying_graph_2_exps_laying_per_{x_lable}.png'), bbox_inches='tight')

        # equilibrium graphs
        if equilibrium_data_dict is not None:
            x = list(range(1, 11))
            x_lable = 'Trial Number'
            x_ticks = range(1, 11)
            for y_lable, data_dict in equilibrium_data_dict.items():
                fig1, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [1, 1]})
                for study in [1, 2]:
                    axes[study - 1].plot(x, data_dict[conditions_per_study[study][0]],
                                         color=colors[conditions_per_study[study][0]],
                                         label=condition_names_per_study[study][0],
                                         marker=markers[conditions_per_study[study][0]])
                    axes[study - 1].plot(x, data_dict[conditions_per_study[study][1]],
                                         color=colors[conditions_per_study[study][1]],
                                         label=condition_names_per_study[study][1],
                                         marker=markers[conditions_per_study[study][1]])
                    axes[study - 1].legend(loc='lower left', shadow=True, fontsize=10)
                    axes[study - 1].set_title(f'Experiment {study}', fontsize=15, )
                    axes[study - 1].set_xticks(x_ticks)
                    y_ticks = np.arange(data_dict['min']-0.1, data_dict['max']+0.15, 0.1)
                    axes[study - 1].set_yticks(y_ticks)
                    axes[study - 1].set_xlabel(x_lable, fontsize=12, )

                    if study == 1:
                        axes[study - 1].set_ylabel(ylabel=y_lable, fontsize=12, )
                fig1.savefig(os.path.join(graph_directory, f'equilibrium_graph_2_exp_per_{y_lable}.png'),
                             bbox_inches='tight')

    # difference between experts payoff per trial
    # fig1, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [1, 1]})
    #
    # if expert_payoff:
    #     for study in [1, 2]:
    #         study_diff = list()
    #         for round_num in range(1, 11):
    #             study_diff.append(role_dict[conditions_per_study[study][0]][round_num-1]/
    #                               role_dict[conditions_per_study[study][1]][round_num-1])
    #         x = list(range(1, 11))
    #         axes[study - 1].plot(x, study_diff, color='black', marker='.',
    #                              label=f'Fraction in {condition_names_per_study[study][0]}-'
    #                                    f'Fraction in {condition_names_per_study[study][1]}')
    #         axes[study - 1].set_title(f'Experiment {study}', fontsize=15)
    #         axes[study - 1].set_xlabel('Trial Number', fontsize=15)
    #         if study == 1:
    #             axes[study - 1].set_ylabel('Difference in Fraction of Hotel Choices', fontsize=15)
    #         axes[study - 1].legend(loc='upper right', shadow=True, fontsize=8)
    #         axes[study - 1].set_xticks(x)
    #         axes[study - 1].set_yticks(np.arange(0.85, 0.05, 1.26))
    #
    #     plt.show()
    #     fig1.savefig(os.path.join(graph_directory, f'Difference_persuasion_2_axes.png'), bbox_inches='tight')


def equilibrium_data_table(df: pd.DataFrame, condition: str):
    # new table data
    mean_implied_score = pd.DataFrame(df.groupby(by='group_average_score').group_sender_answer_scores.mean())
    all = df.groupby(by='group_average_score').pair_id.count()
    hotel_rate = df.groupby(by='group_average_score').group_sender_payoff.mean()
    exaggerate = df.loc[df.laying > 0]
    exaggerate = exaggerate.groupby(by='group_average_score').pair_id.count()
    exaggerate.name = 'exaggerate_above_0'
    above_8 = df.loc[df.group_sender_answer_scores > 8]
    above_8 = above_8.groupby(by='group_average_score').pair_id.count()
    above_8.name = 'above_8'
    final_for_table = mean_implied_score.merge(all, how='left', right_index=True, left_index=True). \
        merge(hotel_rate, how='left', right_index=True, left_index=True). \
        merge(exaggerate, how='left', right_index=True, left_index=True). \
        merge(above_8, how='left', right_index=True, left_index=True)
    final_for_table['prop_above_8'] = final_for_table.above_8 / final_for_table.pair_id
    final_for_table['exaggerate_above_0'] = final_for_table.exaggerate_above_0 / final_for_table.pair_id
    final_for_table = final_for_table[['prop_above_8', 'exaggerate_above_0', 'group_sender_answer_scores',
                                       'group_sender_payoff']]
    final_for_table.columns = ['prop_above_8', 'exaggerate_above_0', 'mean_implied_score', 'hotel_rate']
    final_for_table = final_for_table.round(2)
    final_for_table.to_csv(os.path.join(graph_directory, f'{condition}_table.csv'))


class SignificanceTests:
    def __init__(self):
        """Load data"""
        self.linear_scores = defaultdict(pd.DataFrame)
        self.all_data = defaultdict(pd.DataFrame)
        self.expert_payoff_dict = dict()
        self.expert_payoff_dict_below_8 = dict()
        self.dm_expected_payoff_dict = dict()
        self.laying_dict = dict()
        self.laying_dict_trial = dict()
        self.expert_payoff_dict_persuasion = dict()
        self.equilibrium_data_dict = defaultdict(dict)
        self.equilibrium_data_dict['Mean Implied Score']['max'] = 0
        self.equilibrium_data_dict['Mean Implied Score']['min'] = 10
        self.equilibrium_data_dict['Proportion Implied Score above 8']['max'] = 0
        self.equilibrium_data_dict['Proportion Implied Score above 8']['min'] = 1
        self.equilibrium_data_dict['Hotel Acceptance Rate']['max'] = 0
        self.equilibrium_data_dict['Hotel Acceptance Rate']['min'] = 1

        for condition in conditions:
            self.linear_scores[condition] = pd.read_csv(os.path.join(analysis_directory, condition, 'linear_scores.csv'))
            df = pd.read_csv(os.path.join(data_analysis_directory, condition, 'results_payments_status.csv'))
            df = clean_data(df)

            # equilibrium_data_table(df, condition)

            implied_lower_8 = df.loc[df.group_sender_answer_scores < 8]
            mean_ev_below_8 = implied_lower_8.expected_outcome_taking_hotel.mean()
            print(f'mean EV below 8 for condition {condition} is: {mean_ev_below_8}')

            self.all_data[condition] = df
            self.laying_dict[condition] = df.groupby(by='group_average_score').laying.mean().values.tolist()
            self.laying_dict_trial[condition] = df.groupby(by='subsession_round_number').laying.mean().values.tolist()
            self.expert_payoff_dict[condition] = df.groupby(by='subsession_round_number').\
                group_sender_payoff.mean().values.tolist()
            self.dm_expected_payoff_dict[condition] = df.groupby(by='subsession_round_number').\
                dm_expected_payoff.mean().values.tolist()
            df_persuasion = df.loc[df.expert_want_to_persuade == 1]
            self.expert_payoff_dict_persuasion[condition] = df_persuasion.groupby(by='subsession_round_number').\
                group_sender_payoff.mean().values.tolist()

            # expert payoff for implied score below 8
            temp_df = df.loc[df.group_sender_answer_scores < 8]
            self.expert_payoff_dict_below_8[condition] = temp_df.groupby(by='subsession_round_number').\
                group_sender_payoff.mean().values.tolist()
            df_below_8_take_hotel = temp_df.loc[temp_df.group_sender_payoff == 1]
            number_of_below_8_take_hotel = df_below_8_take_hotel.shape[0]
            df_below_8_take_hotel_gain = df_below_8_take_hotel.loc[df_below_8_take_hotel.group_lottery_result > 8]
            # print(f'% of trials with score lower than 8 that led to a gain for condition {condition} is: '
            #       f'{(df_below_8_take_hotel_gain.shape[0] / number_of_below_8_take_hotel)*100}')

            # hotels 2,3:
            hotels_2_3 = df.loc[df.group_average_score.between(6, 7.9)]
            # mean implied score:
            key = 'Mean Implied Score'
            self.equilibrium_data_dict[key][condition] = \
                hotels_2_3.groupby(by='subsession_round_number').group_sender_answer_scores.mean().values.tolist()
            self.equilibrium_data_dict[key]['max'] = max(round(max(self.equilibrium_data_dict[key][condition]), 1),
                                                         self.equilibrium_data_dict[key]['max'])
            self.equilibrium_data_dict[key]['min'] = min(round(min(self.equilibrium_data_dict[key][condition]), 1),
                                                         self.equilibrium_data_dict[key]['min'])
            # prop above 8
            key = 'Proportion Implied Score above 8'
            self.equilibrium_data_dict[key][condition] = \
                hotels_2_3.groupby(by='subsession_round_number').expert_answer_above_8.mean().values.tolist()
            self.equilibrium_data_dict[key]['max'] = max(round(max(self.equilibrium_data_dict[key][condition]), 1),
                                                         self.equilibrium_data_dict[key]['max'])
            self.equilibrium_data_dict[key]['min'] = min(round(min(self.equilibrium_data_dict[key][condition]), 1),
                                                         self.equilibrium_data_dict[key]['min'])

            # hotel rate
            key = 'Hotel Acceptance Rate'
            self.equilibrium_data_dict[key][condition] = \
                hotels_2_3.groupby(by='subsession_round_number').group_sender_payoff.mean().values.tolist()
            self.equilibrium_data_dict[key]['max'] = max(round(max(self.equilibrium_data_dict[key][condition]), 1),
                                                         self.equilibrium_data_dict[key]['max'])
            self.equilibrium_data_dict[key]['min'] = min(round(min(self.equilibrium_data_dict[key][condition]), 1),
                                                         self.equilibrium_data_dict[key]['min'])

        return

    def dm_individual_differences(self, study):
        study_1_cond = self.all_data[conditions_per_study[study][0]]
        study_2_cond = self.all_data[conditions_per_study[study][1]]
        study_1_dm_data = study_1_cond.groupby(by='pair_id').agg({'group_sender_payoff': 'mean',
                                                                  'dm_expected_payoff': 'mean'})
        study_1_dm_data['pair_id'] = study_1_dm_data.index
        study_2_dm_data = study_2_cond.groupby(by='pair_id').agg({'group_sender_payoff': 'mean',
                                                                  'dm_expected_payoff': 'mean'})
        study_2_dm_data['pair_id'] = study_2_dm_data.index

        # map sender payoff
        bins = [-0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
        names = ['<0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '>0.8']
        study_1_dm_data['proportion of hotel'] = pd.cut(study_1_dm_data['group_sender_payoff'], bins, labels=names)
        study_2_dm_data['proportion of hotel'] = pd.cut(study_2_dm_data['group_sender_payoff'], bins, labels=names)

        # map dm expected payoff
        bins = [-np.inf, -0.2, 0.0, 0.2, 0.4, np.inf]
        names = ['<-0.2', '-0.2-0', '0-0.2', '0.2-0.4', '>0.4']
        study_1_dm_data['average expected earning over trials'] = pd.cut(study_1_dm_data['dm_expected_payoff'], bins,
                                                                         labels=names)
        study_2_dm_data['average expected earning over trials'] = pd.cut(study_2_dm_data['dm_expected_payoff'], bins,
                                                                         labels=names)

        # pivot table
        study_1_dm_data_pivot = pd.pivot_table(study_1_dm_data, values='pair_id', index=['proportion of hotel'],
                                               columns='average expected earning over trials',
                                               aggfunc=lambda x: len(x.unique()), fill_value=0)
        study_1_dm_data_pivot.to_csv(os.path.join(graph_directory,
                                                  f'dm_pivot_table_{conditions_per_study[study][0]}.csv'))
        study_2_dm_data_pivot = pd.pivot_table(study_2_dm_data, values='pair_id', index=['proportion of hotel'],
                                               columns='average expected earning over trials',
                                               aggfunc=lambda x: len(x.unique()), fill_value=0)
        study_2_dm_data_pivot.to_csv(os.path.join(graph_directory,
                                                  f'dm_pivot_table_{conditions_per_study[study][1]}.csv'))

    def computation_paper_graphs(self, corr_data_path=None):
        parameters = {'axes.labelsize': 15,
                      'axes.titlesize': 15,
                      'xtick.labelsize': 12,
                      'ytick.labelsize': 12}

        # previous round results
        plt.rcParams.update(parameters)
        fig, ax = plt.subplots()
        decision_data = pd.DataFrame(self.all_data['verbal'][['previous_round_lottery_result', 'group_sender_payoff',
                                                              'previous_round_decision']])
        previous_round_choose = decision_data.loc[decision_data.previous_round_decision == 1]
        previous_round_choose = pd.DataFrame(previous_round_choose.
                                             groupby(by='previous_round_lottery_result').group_sender_payoff.mean()*100)
        previous_round_choose.columns = [f"Previous choice: 'Hotel'"]
        previous_round_not_choose = decision_data.loc[decision_data.previous_round_decision == 0]
        previous_round_not_choose = pd.DataFrame(previous_round_not_choose.
                                                 groupby(by='previous_round_lottery_result').group_sender_payoff.mean()*100)
        previous_round_not_choose.columns = [f"Previous choice: 'Stay Home'"]

        previous_round_analysis = previous_round_not_choose.merge(previous_round_choose, left_index=True,
                                                                  right_index=True, how='outer')
        previous_round_analysis.plot(kind="bar", stacked=False, rot=0, color=['lightgreen', 'deepskyblue'], ax=ax)
        ax.set(xlabel='Previous Trial random score', ylabel='Hotel Choices Rate')
        # plt.title('Hotel Choice Rates Per Previous Trial random score')
        bars = ax.patches
        hatches = ''.join(h * len(previous_round_analysis) for h in ' x')

        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)

        ax.legend(loc='lower center', shadow=True)
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "computation_paper_graphs_previous_trial.png"),
                    bbox_inches='tight')

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5), gridspec_kw={'width_ratios': [2, 3]})
        # first graph - enterance per round per gender
        decision_data = pd.DataFrame(enterence_per_round_dict, index=list(range(1, 11)))
        decision_data.plot(kind="bar", stacked=False, rot=0, color=['lightgreen', 'deepskyblue', 'violet'], ax=ax1)
        ax1.set_title("(a) Hotel Choice Rate Per Trial Number")
        ax1.set(xlabel='Trial Number', ylabel='Hotel Choice Rate')
        # rects = axes[0, 0].patches
        # autolabel(rects, axes[0, 0], rotation='horizontal', max_height=80, convert_to_int=True)
        bars = ax1.patches
        hatches = ''.join(h * len(decision_data) for h in ' xO')

        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)

        ax1.legend(loc='lower center', shadow=True)

        # second graph - enterance per score
        decision_data = pd.DataFrame(enterenc_per_score_dict, index=x)
        decision_data.plot(kind="bar", stacked=False, rot=0, color=['lightgreen', 'deepskyblue', 'violet'], ax=ax2)
        ax2.set_title("(b) Hotel Choices Rate Per Reviews' Score")
        ax2.set(xlabel="Reviews' Score")
        # rects = ax2.patches
        # autolabel(rects, ax2, rotation='horizontal', max_height=80, convert_to_int=True)
        bars = ax2.patches
        hatches = ''.join(h * len(decision_data) for h in ' xO')

        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)
        ax2.legend(loc='upper left', shadow=True)

        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "computation_paper_graphs_enterance_rate_1.png"),
                    bbox_inches='tight')

        # third graph - chose-lose
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        inner_colors = ['orange', 'green', 'red', 'blue']
        decision_data = pd.DataFrame(pre_round_dict, index=list(range(2, 11)))
        for i, column in enumerate(decision_data.columns):
            ax1.plot(list(range(2, 11)), decision_data[column], linestyle='-', color=inner_colors[i], label=column)
        # decision_data.plot(kind="bar", stacked=False, rot=0, color=['orange', 'green', 'red', 'blue'], ax=axes[1, 0])
        ax1.set_title("(a) Hotel Choices Rate Per Previous Trial Result")
        ax1.set(xlabel='Trial Number', ylabel='% Decision-Makers Chose the ’Hotel’ Option')
        # rects = ax3.patches
        # autolabel(rects, ax3, rotation='horizontal', max_height=80, convert_to_int=True)
        ax1.legend(loc='upper right', shadow=True, prop={"size": 8})

        """Analyze the correlation between rounds"""
        if corr_data_path is not None:
            data = pd.read_csv(corr_data_path)
            data = data.loc[data.raisha == 0]
            data.labels = np.where(data.labels == 1, 1, 0)
            avg_enter_rate = data.groupby(by='pair_id').labels.sum()
            print(f'avg_enter_rate is: {avg_enter_rate.mean()}, median_enter_rate is {avg_enter_rate.median()}, '
                  f'std_enter_rate is {avg_enter_rate.std()}')
            rounds_list = list(range(1, 11))
            df_list = list()
            for my_round in rounds_list:
                df = data.loc[data.round_number == my_round].labels
                df.reset_index(drop=True, inplace=True)
                df_list.append(df)

            labels = pd.concat(df_list, axis=1, ignore_index=True)
            labels.columns = list(range(1, 11))
            corr = labels.corr()
            mask = np.zeros_like(corr, dtype=np.bool)
            mask[np.triu_indices_from(mask)] = True
            # plt.figure(figsize=(5, 5))
            sns.heatmap(corr, cmap='coolwarm', annot=True, mask=mask, fmt='.2f', annot_kws={"size": 8}, ax=ax2)
            ax2.set(xlabel='Trial Number', ylabel='Trial Number')
            ax2.set_title('(b) Correlation Between Decisions in Different Trials')
            plt.rcParams.update(parameters)
            corr.to_csv(os.path.join(computation_paper_dir, 'rounds_correlation_analysis.csv'))
            plt.savefig(os.path.join(computation_paper_dir, 'correlation_heat_map.png'))

        # forth graph- % decision makers enters each number
        fig, ax = plt.subplots()
        decision_data = pd.DataFrame(pct_dm_per_number_of_rounds_enter_dict, index=list(range(2, 11)))
        decision_data.plot(kind="bar", stacked=False, rot=0, color=['deepskyblue'], ax=ax)
        # ax.set_title("% Decision-Makers Per Total Hotel Choices")
        ax.set(xlabel='Number of Hotel Choices',
               ylabel='% Decision-Makers Chose\nthe ’Hotel’ Option')
        ax.get_legend().remove()
        # rects = ax3.patches
        # autolabel(rects, ax3, rotation='horizontal', max_height=80, convert_to_int=True)
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "computation_paper_graphs_enterance_rate_2.png"),
                    bbox_inches='tight')

        # enterance rate per manual features
        enterance_rate_per_manual_features = pd.read_csv('/Users/reutapel/Documents/Documents/Technion/Msc/thesis/'
                                                         'experiment/decision_prediction/data_analysis/analysis/'
                                                         'text_exp_2_tests/verbal/% DM entered based on review '
                                                         'features for condition verbal and gender all genders for '
                                                         'graph.csv', index_col=1)
        axes = list()
        fig = plt.figure(figsize=(12, 5))
        axes.append(plt.subplot2grid((2, 6), (0, 1), colspan=2, fig=fig))
        axes.append(plt.subplot2grid((2, 6), (0, 3), colspan=2, fig=fig))
        axes.append(plt.subplot2grid(shape=(2, 6), loc=(1, 0), colspan=2, fig=fig))
        axes.append(plt.subplot2grid((2, 6), (1, 2), colspan=2, fig=fig))
        axes.append(plt.subplot2grid((2, 6), (1, 4), colspan=2, fig=fig))

        for i, high_level in enumerate(enterance_rate_per_manual_features.high_level.unique()):
            high_level_data = \
                enterance_rate_per_manual_features.loc[enterance_rate_per_manual_features.high_level == high_level]
            high_level_data.plot(kind="bar", stacked=False, rot=0, color=['forestgreen', 'crimson'], ax=axes[i],
                                 fontsize=8)
            axes[i].set_title(high_level, fontsize=8)
            axes[i].get_legend().remove()
            axes[i].set_xlabel('')

        ax.set_ylabel('% Decision-Makers',  fontdict={'size': 10})
        ax.set_xlabel("Attribute Number", fontdict={'size': 10})
        fig.text(0.5, 0.04, 'Attribute Number', ha='center')
        fig.text(0.08, 0.5, 'Hotel Choices Rate', va='center', rotation='vertical')
        fig.legend(axes,  # The line objects
                   labels=["Review doesn't have attribute", "Review has attribute"],  # The labels for each line
                   loc="upper center",  # Position of legend
                   shadow=True, prop={"size": 8})
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "enterance_rate_per_manual_features_train_data.png"),
                    bbox_inches='tight')

        # compare bert-domain features
        fig, ax = plt.subplots()
        results_data = pd.DataFrame(bert_domain_compare_rmse, index=models_index_rmse)
        results_data.plot(kind="bar", stacked=False, color=['forestgreen', 'crimson', 'purple'], ax=ax, alpha=0.75)
        plt.xticks(rotation=45)
        ax.set(ylabel='RMSE Score')
        bars = ax.patches
        hatches = ''.join(h * len(models_index_rmse) for h in ' +o')

        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)
        ax.legend(loc='lower center', shadow=True, fontsize=16)
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "bert_domain_features_compare_rmse.png"),
                    bbox_inches='tight')

        # compare bert-domain features f-beta macro
        fig, ax = plt.subplots()
        results_data = pd.DataFrame(bert_domain_compare_f_macro, index=models_index_macro)
        results_data.plot(kind="bar", stacked=False, color=['forestgreen', 'crimson', 'purple'], ax=ax, alpha=0.75)
        plt.xticks(rotation=45)
        ax.set(ylabel='Bin Macro F-score Score')
        bars = ax.patches
        hatches = ''.join(h * len(models_index_macro) for h in ' +o')

        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)
        ax.legend(loc='lower left', shadow=True, fontsize=16)
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "bert_domain_features_compare_f_score_macro.png"),
                    bbox_inches='tight')

        # compare bert-domain features per_trial accuracy
        fig, ax = plt.subplots()
        results_data = pd.DataFrame(bert_domain_compare_per_trial_accuracy, index=models_index_accuracy)
        results_data.plot(kind="bar", stacked=False, color=['forestgreen', 'crimson', 'purple'], ax=ax, alpha=0.75)
        plt.xticks(rotation=45)
        ax.set(ylabel='Per-Trial Accuracy')
        bars = ax.patches
        hatches = ''.join(h * len(models_index_accuracy) for h in ' +o')

        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)
        ax.legend(loc='lower center', shadow=True, fontsize=16)
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "bert_domain_features_compare_per_trial_accuracy.png"),
                    bbox_inches='tight')

        # compare bert-domain features per_trial macro f-score
        fig, ax = plt.subplots()
        results_data = pd.DataFrame(bert_domain_compare_per_trial_macro, index=models_index_trial_macro)
        results_data.plot(kind="bar", stacked=False, color=['forestgreen', 'crimson', 'purple'], ax=ax, alpha=0.75)
        plt.xticks(rotation=45)
        ax.set(ylabel='Per-Trial Macro Average F-score')
        bars = ax.patches
        hatches = ''.join(h * len(models_index_trial_macro) for h in ' +o')

        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)
        ax.legend(loc='lower center', shadow=True, fontsize=16)
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "bert_domain_features_compare_per_trial_macro_f_score.png"),
                    bbox_inches='tight')

        # per raisha comapre only RMSE
        fig, ax = plt.subplots()
        data = pd.DataFrame(raisha_results_rmse, index=list(range(10)))
        for i, column in enumerate(data.columns):
            ax.plot(list(range(10)), data[column], marker=markers_colors_models[column][0], label=column,
                    color=markers_colors_models[column][1])
        # ax.set_title(f"{measure} As a Function of the Prefix Size")
        ax.set(xlabel='Prefix Size', ylabel='RMSE Score')
        plt.xticks(list(range(10)))
        ax.legend(loc='upper left', shadow=True, ncol=2, fontsize=12)
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "raisha_compare_RMSE.png"), bbox_inches='tight')

        # per raisha comapre only Macro
        fig, ax = plt.subplots()
        data = pd.DataFrame(raisha_results_macro, index=list(range(10)))
        for i, column in enumerate(data.columns):
            ax.plot(list(range(10)), data[column], marker=markers_colors_models[column][0], label=column,
                    color=markers_colors_models[column][1])
        # ax.set_title(f"{measure} As a Function of the Prefix Size")
        ax.set(xlabel='Prefix Size', ylabel='Bin Macro Average F-score Score')
        plt.xticks(list(range(10)))
        ax.legend(loc='upper left', shadow=True, ncol=2, fontsize=12)
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "raisha_compare_macro_f1.png"), bbox_inches='tight')

        # per raisha comapre only per trial Accuracy
        fig, ax = plt.subplots()
        data = pd.DataFrame(raisha_results_accuracy_per_trail, index=list(range(10)))
        for i, column in enumerate(data.columns):
            ax.plot(list(range(10)), data[column], marker=markers_colors_models[column][0], label=column,
                    color=markers_colors_models[column][1])
        # ax.set_title(f"{measure} As a Function of the Prefix Size")
        ax.set(xlabel='Prefix Size', ylabel='Per-Trial Accuracy')
        plt.xticks(list(range(10)))
        ax.legend(loc='lower left', shadow=True, ncol=2, fontsize=12)
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "raisha_compare_per_trial_accuracy.png"), bbox_inches='tight')

        # per round comapre only per trial Accuracy
        fig, ax = plt.subplots()
        data = pd.DataFrame(round_results_accuracy_per_trail, index=list(range(1, 11)))
        for i, column in enumerate(data.columns):
            ax.plot(list(range(1, 11)), data[column], marker=markers_colors_models[column][0], label=column,
                    color=markers_colors_models[column][1])
        # ax.set_title(f"{measure} As a Function of the Prefix Size")
        ax.set(xlabel='Trial Number', ylabel='Per-Trial Accuracy')
        plt.xticks(list(range(1, 11)))
        ax.legend(loc='upper left', shadow=True, ncol=3, fontsize=12)
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "round_compare_per_trial_accuracy.png"), bbox_inches='tight')

        # per raisha comapre only per trial macro
        fig, ax = plt.subplots()
        data = pd.DataFrame(raisha_results_macro_per_trail, index=list(range(10)))
        for i, column in enumerate(data.columns):
            ax.plot(list(range(10)), data[column], marker=markers_colors_models[column][0], label=column,
                    color=markers_colors_models[column][1])
        # ax.set_title(f"{measure} As a Function of the Prefix Size")
        ax.set(xlabel='Prefix Size', ylabel='Per-Trial Macro Average F-Score')
        plt.xticks(list(range(10)))
        # ax.legend(loc='lower left', shadow=True)
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "raisha_compare_per_trial_macro_f_score.png"),
                    bbox_inches='tight')

        # per round comapre only per trial macro
        fig, ax = plt.subplots()
        data = pd.DataFrame(round_results_macro_per_trail, index=list(range(1, 11)))
        for i, column in enumerate(data.columns):
            ax.plot(list(range(1, 11)), data[column], marker=markers_colors_models[column][0], label=column,
                    color=markers_colors_models[column][1])
        # ax.set_title(f"{measure} As a Function of the Prefix Size")
        ax.set(xlabel='Trial Number', ylabel='Per-Trial Macro Average F-Score')
        plt.xticks(list(range(1, 11)))
        # ax.legend(loc='lower left', shadow=True)
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "round_compare_per_trial_macro_f_score.png"),
                    bbox_inches='tight')

        # per raisha comapre
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
        for results_dict, measure, ax in [[raisha_results_rmse, 'RMSE', ax1],
                                          [raisha_results_micro, 'Bin F-score Micro', ax2],
                                          [raisha_results_macro, 'Bin F-score Macro', ax3]]:
            data = pd.DataFrame(results_dict, index=list(range(10)))
            for i, column in enumerate(data.columns):
                ax.plot(list(range(10)), data[column], marker=markers_colors_models[column][0], label=column,
                        color=markers_colors_models[column][1])
            # ax.set_title(f"{measure} As a Function of the Prefix Size")
            ax.set(xlabel='Prefix Size', ylabel=measure)

        lines, labels = fig.axes[-1].get_legend_handles_labels()

        fig.legend(lines, labels, loc='upper center', shadow=True, prop={"size": 10})
        plt.xticks(list(range(10)))
        plt.rcParams.update(parameters)
        plt.savefig(os.path.join(computation_paper_dir, "raisha_compare.png"), bbox_inches='tight')

        # plt.show()

        return

    def understanding_graph(self, func_study: int, two_axes: bool=False,
                            column_to_group: str='group_sender_answer_scores', x_lable: str='Implied Score'):
        if two_axes:
            fig1, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [1, 1]})
            fig1.tight_layout(pad=10)
            studies = [1, 2]
        else:
            fig1, axes = plt.subplots(1, 1)
            axes = [axes, axes]
            studies = [func_study]

        for study in studies:
            if column_to_group == 'group_sender_answer_scores':
                axes[study - 1].axis([2, 10, 0, 1])
            else:
                axes[study - 1].axis([4, 10, 0, 1])
            study_1_x_list = self.all_data[conditions_per_study[study][0]][column_to_group].unique().tolist()
            study_2_x_list = self.all_data[conditions_per_study[study][1]][column_to_group].unique().tolist()

            study_1_x_list.extend(study_2_x_list)
            x = pd.DataFrame(sorted(list(set(study_1_x_list))), columns=[column_to_group])

            study_1_cond = self.all_data[conditions_per_study[study][0]]
            study_2_cond = self.all_data[conditions_per_study[study][1]]

            study_1_cond_understand = study_1_cond.groupby(by=column_to_group).group_sender_payoff.mean()
            study_2_cond_understand = study_2_cond.groupby(by=column_to_group).group_sender_payoff.mean()

            study_1_cond_understand_x = x.merge(study_1_cond_understand, left_on=column_to_group,
                                                right_index=True, how='left')
            study_2_cond_understand_x = x.merge(study_2_cond_understand, left_on=column_to_group,
                                                right_index=True, how='left')

            if column_to_group == 'group_sender_answer_scores':
                values_study_1 = study_1_cond.groupby(by=column_to_group).group_sender_payoff.count()/3
                values_study_2 = study_2_cond.groupby(by=column_to_group).group_sender_payoff.count()/3
                if values_study_1.shape[0] > values_study_2.shape[0]:  # add missing index to values_study_2
                    for i in values_study_1.index:
                        if i not in values_study_2.index:
                            values_study_2.loc[i] = 0
                    values_study_2 = values_study_2.sort_index()
                elif values_study_1.shape[0] < values_study_2.shape[0]:  # add missing index to values_study_1
                    for i in values_study_2.index:
                        if i not in values_study_1.index:
                            values_study_1.loc[i] = 0
                    values_study_1 = values_study_1.sort_index()

                values_study_1 = values_study_1.values
                values_study_2 = values_study_2.values

            else:
                values_study_1 = None
                values_study_2 = None

            axes[study - 1].scatter(x, study_1_cond_understand_x.group_sender_payoff, s=values_study_1,
                                    color=colors[conditions_per_study[study][0]],
                                    # label=condition_names_per_study[study][0],
                                    marker=markers[conditions_per_study[study][0]], linestyle='-')
            axes[study - 1].plot(x, study_1_cond_understand_x.group_sender_payoff,
                                 marker=markers[conditions_per_study[study][0]],
                                 label=condition_names_per_study[study][0], markersize=0,
                                 color=colors[conditions_per_study[study][0]], linestyle='-')
            axes[study - 1].scatter(x, study_2_cond_understand_x.group_sender_payoff, s=values_study_2,
                                    color=colors[conditions_per_study[study][1]],
                                    # label=condition_names_per_study[study][1],
                                    marker=markers[conditions_per_study[study][1]], linestyle='-')
            axes[study - 1].plot(x, study_2_cond_understand_x.group_sender_payoff,
                                 marker=markers[conditions_per_study[study][1]],
                                 label=condition_names_per_study[study][1], markersize=0,
                                 color=colors[conditions_per_study[study][1]], linestyle='-')

            # x is a pd.DataFrame with one column, x.T.values[0] are its values
            # cell_text = [x.T.values[0], values_study_1.values, values_study_2.values]
            # columns = values_study_1.index.values
            xlabel = x_lable
            # table_condition_names_per_study = {1: ['Numerical', 'Verbal'],
            #                                    2: ['Only\nNumerical', 'Verbal+\nNumerical']}
            # # Add a table at the bottom of the axes
            # the_table = axes[study - 1].table(cellText=cell_text,
            #                                   rowLabels=['Review\nScore',
            #                                              f'{table_condition_names_per_study[study][0]}',
            #                                              f'{table_condition_names_per_study[study][1]}'],
            #                                   # colLabels=columns,
            #                                   cellLoc='center',
            #                                   rowLoc='center',
            #                                   bbox=(0, -0.41, 1, 0.27),
            #                                   )
            # the_table.auto_set_font_size(False)
            # the_table.set_fontsize(8)

            # if study == 1:
            #     xlabel = 'Score (or score related to the review) Selected by The Expert'
            # else:
            axes[study - 1].set_xlabel(xlabel, fontsize=15)
            axes[study - 1].set_title(f'Experiment {study}', fontsize=15)
            if study == 1:
                axes[study - 1].set_ylabel('Fraction of Hotel Choices', fontsize=15)
            # Plot legend.
            exp1 = mlines.Line2D([], [], marker=markers[conditions_per_study[study][0]],
                                 label=condition_names_per_study[study][0], linestyle='-',
                                 color=colors[conditions_per_study[study][0]])
            exp2 = mlines.Line2D([], [], marker=markers[conditions_per_study[study][1]],
                                 label=condition_names_per_study[study][1], linestyle='-',
                                 color=colors[conditions_per_study[study][1]])

            axes[study - 1].legend(loc='upper left', shadow=True, fontsize=8, handles=[exp1, exp2])
            if column_to_group == 'group_sender_answer_scores':
                axes[study - 1].set_xticks(range(2, 11))
            else:
                axes[study - 1].set_xticks(range(4, 11))
            # plt.tick_params(
            #     axis='x',  # changes apply to the x-axis
            #     which='both',  # both major and minor ticks are affected
            #     bottom=False,  # ticks along the bottom edge are off
            #     top=False,  # ticks along the top edge are off
            #     labelbottom=False)  # labels along the bottom edge are off
            axes[study - 1].set_yticks(np.arange(0.0, 1.05, 0.1))
        # plt.show()
        if two_axes:
            title = f'understanding_level_2_axes_per_{x_lable}.png'
        else:
            title = f'understanding_level_study_{func_study}_per_{x_lable}.png'
        fig1.subplots_adjust(wspace=0.15)
        fig1.savefig(os.path.join(graph_directory, title), bbox_inches='tight')

        # significant tests:
        study_1_cond = self.all_data[conditions_per_study[func_study][0]]
        study_2_cond = self.all_data[conditions_per_study[func_study][1]]

        study_1_cond_low = study_1_cond.loc[study_1_cond.group_sender_answer_scores < 8]
        study_2_cond_low = study_2_cond.loc[study_2_cond.group_sender_answer_scores < 8]
        study_1_cond_low = pd.DataFrame(study_1_cond_low.groupby(by='pair_id').group_sender_payoff.mean())
        study_1_cond_low.columns = ['low']
        study_2_cond_low = pd.DataFrame(study_2_cond_low.groupby(by='pair_id').group_sender_payoff.mean())
        study_2_cond_low.columns = ['low']

        study_1_cond_high = study_1_cond.loc[study_1_cond.group_sender_answer_scores >= 8]
        study_2_cond_high = study_2_cond.loc[study_2_cond.group_sender_answer_scores >= 8]
        study_1_cond_high = pd.DataFrame(study_1_cond_high.groupby(by='pair_id').group_sender_payoff.mean())
        study_1_cond_high.columns = ['high']
        study_2_cond_high = pd.DataFrame(study_2_cond_high.groupby(by='pair_id').group_sender_payoff.mean())
        study_2_cond_high.columns = ['high']

        # merge high and low:
        study_1_cond = study_1_cond_low.join(study_1_cond_high)
        study_2_cond = study_2_cond_low.join(study_2_cond_high)

        study_1_cond['understanding'] = study_1_cond.high - study_1_cond.low
        study_2_cond['understanding'] = study_2_cond.high - study_2_cond.low

        significant_tests(study_1_cond, study_2_cond,
                          f'Understanding Level Study {func_study} '
                          f'{conditions_per_study[func_study][0]}, {conditions_per_study[func_study][1]}')

        # significant tests for lower than 5:
        study_1_cond = self.all_data[conditions_per_study[func_study][0]]
        study_2_cond = self.all_data[conditions_per_study[func_study][1]]
        study_1_cond_low = study_1_cond.loc[study_1_cond.group_sender_answer_scores < 5]
        study_2_cond_low = study_2_cond.loc[study_2_cond.group_sender_answer_scores < 5]
        study_1_cond_low = pd.DataFrame(study_1_cond_low.groupby(by='pair_id').group_sender_payoff.mean())
        study_1_cond_low.columns = ['low']
        study_2_cond_low = pd.DataFrame(study_2_cond_low.groupby(by='pair_id').group_sender_payoff.mean())
        study_2_cond_low.columns = ['low']
        significant_tests(study_1_cond_low.low, study_2_cond_low.low,
                          f'Understanding Level lower than 5 Study {func_study} '
                          f'{conditions_per_study[func_study][0]}, {conditions_per_study[func_study][1]}')

        return

    def laying_test(self, study: int):
        study_1_cond = self.all_data[conditions_per_study[study][0]]
        study_2_cond = self.all_data[conditions_per_study[study][1]]

        study_1_cond = study_1_cond.groupby(by='pair_id').laying.mean()
        study_2_cond = study_2_cond.groupby(by='pair_id').laying.mean()

        significant_tests(study_1_cond, study_2_cond,
                          f'Laying Level Study {study}: '
                          f'{conditions_per_study[study][0]}, {conditions_per_study[study][1]}')

    def trust_graph(self, study: int, split_half=True):
        data_dict = defaultdict(list)
        study_1_cond = self.all_data[conditions_per_study[study][0]]
        study_2_cond = self.all_data[conditions_per_study[study][1]]
        diff_values_study_1 = pd.DataFrame()
        diff_values_study_2 = pd.DataFrame()

        half = [1, 0] if split_half else ['all']

        for first_half in half:
            if first_half == 'all':
                study_1_cond_half = study_1_cond
                study_2_cond_half = study_2_cond
            else:
                study_1_cond_half = study_1_cond.loc[study_1_cond.first_half == first_half]
                study_2_cond_half = study_2_cond.loc[study_2_cond.first_half == first_half]

            study_1_cond_over_8 = study_1_cond_half.loc[study_1_cond_half['expert_answer_above_8'] == 1]
            study_1_cond_below_8 = study_1_cond_half.loc[study_1_cond_half['expert_answer_above_8'] == 0]
            study_1_cond_over_8 = pd.DataFrame(study_1_cond_over_8.groupby(by='pair_id').group_sender_payoff.mean())
            study_1_cond_over_8.columns = ['over_8_taking_rate']
            study_1_cond_below_8 = pd.DataFrame(study_1_cond_below_8.groupby(by='pair_id').group_sender_payoff.mean())
            study_1_cond_below_8.columns = ['below_8_taking_rate']
            study_1_cond_diff_score = study_1_cond_over_8.join(study_1_cond_below_8)
            study_1_cond_diff_score = study_1_cond_diff_score.fillna(0)
            study_1_cond_diff_score['diff'] = study_1_cond_diff_score.over_8_taking_rate -\
                                              study_1_cond_diff_score.below_8_taking_rate
            data_dict[condition_names_per_study[study][0]].append(study_1_cond_diff_score['diff'].mean())
            diff_values_study_1 = pd.concat([diff_values_study_1, study_1_cond_diff_score['diff']])

            study_2_cond_over_8 = study_2_cond_half.loc[study_2_cond_half['expert_answer_above_8'] == 1]
            study_2_cond_below_8 = study_2_cond_half.loc[study_2_cond_half['expert_answer_above_8'] == 0]
            study_2_cond_over_8 = pd.DataFrame(study_2_cond_over_8.groupby(by='pair_id').group_sender_payoff.mean())
            study_2_cond_over_8.columns = ['over_8_taking_rate']
            study_2_cond_below_8 = pd.DataFrame(study_2_cond_below_8.groupby(by='pair_id').group_sender_payoff.mean())
            study_2_cond_below_8.columns = ['below_8_taking_rate']
            study_2_cond_diff_score = study_2_cond_over_8.join(study_2_cond_below_8)
            study_2_cond_diff_score = study_2_cond_diff_score.fillna(0)
            study_2_cond_diff_score['diff'] = study_2_cond_diff_score.over_8_taking_rate - \
                                            study_2_cond_diff_score.below_8_taking_rate
            data_dict[condition_names_per_study[study][1]].append(study_2_cond_diff_score['diff'].mean())
            diff_values_study_2 = pd.concat([diff_values_study_2, study_2_cond_diff_score['diff']])

        data_df = pd.DataFrame.from_dict(data_dict)
        if split_half:
            data_df.index = ['Half 1', 'Half 2']
        else:
            data_df.index = ['All Rounds']
        ax2 = data_df.plot(kind="bar", stacked=False, rot=0,
                           color=[colors[conditions_per_study[study][0]], colors[conditions_per_study[study][1]]])
        # plt.title("The Decision Makers' Average Expected Payoff Throughout the Experiment")
        # plt.xlabel('Round Number')
        plt.ylabel('Average Understanding Level')
        # rects = ax2.patches
        # autolabel(rects, ax2, rotation='horizontal', max_height=data_df.max(), convert_to_int=False)
        ax2.legend(loc='lower center', shadow=True)
        # plt.yticks([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        # plt.show()
        fig_to_save = ax2.get_figure()
        fig_to_save.savefig(os.path.join(
            graph_directory, f'average_trust_level_first_and_last_5_trials_study_{study}_split_half_{split_half}.png'),
            bbox_inches='tight')

        significant_tests(diff_values_study_1, diff_values_study_2,
                          f'Understanding Level Study {study} Split Half {split_half}: '
                          f'{conditions_per_study[study][0]}, {conditions_per_study[study][1]}')

    def best_reply_graph(self, study: int):
        data_dict = defaultdict(list)
        study_1_cond = self.all_data[conditions_per_study[study][0]]
        study_2_cond = self.all_data[conditions_per_study[study][1]]
        study_1_cond_best_reply = study_1_cond.groupby(by='first_half').best_reply.mean()
        study_2_cond_best_reply = study_2_cond.groupby(by='first_half').best_reply.mean()

        data_dict[condition_names_per_study[study][0]] = [study_1_cond_best_reply[1], study_1_cond_best_reply[0]]
        data_dict[condition_names_per_study[study][1]] = [study_2_cond_best_reply[1], study_2_cond_best_reply[0]]
        # plt.figure(figsize=(10, 5))
        data_df = pd.DataFrame.from_dict(data_dict)
        data_df.index = ['Half 1', 'Half 2']
        ax2 = data_df.plot(kind="bar", stacked=False, rot=0,
                           color=[colors[conditions_per_study[study][0]], colors[conditions_per_study[study][1]]])
        # plt.title("The Decision Makers' Average Expected Payoff Throughout the Experiment")
        # plt.xlabel('Round Number')
        plt.ylabel('Average Best Reply Rate')
        # rects = ax2.patches
        # autolabel(rects, ax2, rotation='horizontal', max_height=data_df.max(), convert_to_int=False)
        ax2.legend(loc='lower center', shadow=True)
        plt.yticks(np.arange(0, 1, 0.1))
        # plt.show()
        fig_to_save = ax2.get_figure()
        fig_to_save.savefig(
            os.path.join(graph_directory, f'best_reply_first_and_last_5_trials_study{study}.png'), bbox_inches='tight')

        study_1_cond_best_reply = study_1_cond.groupby(by='pair_id').best_reply.mean()
        study_2_cond_best_reply = study_2_cond.groupby(by='pair_id').best_reply.mean()

        significant_tests(study_1_cond_best_reply, study_2_cond_best_reply,
                          f'Best Reply Study {study}: {conditions_per_study[study][0]}, '
                          f'{conditions_per_study[study][1]}')

    def expert_payoff_test(self, study: int, given_persuasion: bool=False):
        study_1_cond = self.all_data[conditions_per_study[study][0]]
        study_2_cond = self.all_data[conditions_per_study[study][1]]
        if given_persuasion:
            study_1_cond = study_1_cond.loc[study_1_cond.expert_want_to_persuade == 1]
            study_2_cond = study_2_cond.loc[study_2_cond.expert_want_to_persuade == 1]
        study_1_cond_mean_ex_payoff = study_1_cond.groupby(by='pair_id').group_sender_payoff.sum()
        study_2_cond_mean_ex_payoff = study_2_cond.groupby(by='pair_id').group_sender_payoff.sum()

        significant_tests(study_1_cond_mean_ex_payoff, study_2_cond_mean_ex_payoff,
                          f'Expert Payoff Study {study} given_persuasion: {given_persuasion}: '
                          f'{conditions_per_study[study][0]}, {conditions_per_study[study][1]}')

        return

    def two_hotels_test(self, study: int):
        study_1_cond = self.all_data[conditions_per_study[study][0]]
        study_2_cond = self.all_data[conditions_per_study[study][1]]

        study_1_cond = study_1_cond.loc[study_1_cond.group_average_score.between(6, 7.9)]
        study_2_cond = study_2_cond.loc[study_2_cond.group_average_score.between(6, 7.9)]

        study_1_cond_mean_ex_payoff = study_1_cond.groupby(by='pair_id').expert_answer_above_8.mean()
        study_2_cond_mean_ex_payoff = study_2_cond.groupby(by='pair_id').expert_answer_above_8.mean()

        significant_tests(study_1_cond_mean_ex_payoff, study_2_cond_mean_ex_payoff,
                          f'Two hotels above 8 implied score Study {study}: '
                          f'{conditions_per_study[study][0]}, {conditions_per_study[study][1]}')

        return

    def dm_payoff_test(self, study: int):
        study_1_cond = self.all_data[conditions_per_study[study][0]]
        study_2_cond = self.all_data[conditions_per_study[study][1]]
        study_1_cond_mean_dm_payoff = study_1_cond.groupby(by='pair_id').dm_expected_payoff.sum()
        study_2_cond_mean_dm_payoff = study_2_cond.groupby(by='pair_id').dm_expected_payoff.sum()

        significant_tests(study_1_cond_mean_dm_payoff, study_2_cond_mean_dm_payoff,
                          f'Decision Maker Payoff Study {study}: {conditions_per_study[study][0]}, '
                          f'{conditions_per_study[study][1]}')

        return

    def honesty_test(self, study: int):
        study_1_cond = self.all_data[conditions_per_study[study][0]]
        study_2_cond = self.all_data[conditions_per_study[study][1]]
        study_1_cond_mean_honesty = study_1_cond.groupby(by='pair_id').honesty.mean()
        study_2_cond_mean_honesty = study_2_cond.groupby(by='pair_id').honesty.mean()

        significant_tests(study_1_cond_mean_honesty, study_2_cond_mean_honesty,
                          f'Honesty Study {study}: {conditions_per_study[study][0]}, {conditions_per_study[study][1]}')

        honesty_graph(study=study)

        return

    def linear_score_test(self, study: int):
        study_1_cond = self.linear_scores[conditions_per_study[study][0]]
        study_2_cond = self.linear_scores[conditions_per_study[study][1]]
        study_1_cond_mean_honesty = study_1_cond.linear_expert_payoff
        study_2_cond_linear_score = study_2_cond.linear_expert_payoff

        significant_tests(study_1_cond_mean_honesty, study_2_cond_linear_score,
                          f'Linear Score Study {study}: {conditions_per_study[study][0]}, '
                          f'{conditions_per_study[study][1]}')

        return

    def trust_test(self, study: int):
        study_1_cond = self.all_data[conditions_per_study[study][0]]
        study_2_cond = self.all_data[conditions_per_study[study][1]]
        data_1_p_enter_list_all_rounds = list()
        data_2_p_enter_list_all_rounds = list()
        for name, number in [['expert estimation below 8', 0], ['expert estimation above 8', 1]]:
            study_1_cond_name = study_1_cond.loc[study_1_cond.expert_answer_above_8 == number]
            study_2_cond_name = study_2_cond.loc[study_2_cond.expert_answer_above_8 == number]

            study_1_cond_mean = study_1_cond_name.groupby(by='pair_id').group_sender_payoff.mean()
            study_2_cond_mean = study_2_cond_name.groupby(by='pair_id').group_sender_payoff.mean()

            significant_tests(study_1_cond_mean, study_2_cond_mean,
                              f'Trust Study {study} for {name}: {conditions_per_study[study][0]}, '
                              f'{conditions_per_study[study][1]}')

            data_1_p_enter_list_all_rounds.append(round(study_1_cond_name.group_sender_payoff.mean(), 2))
            data_2_p_enter_list_all_rounds.append(round(study_2_cond_name.group_sender_payoff.mean(), 2))

        trust_graphs(study=study, data_1_p_enter_list_all_rounds=data_1_p_enter_list_all_rounds,
                     data_2_p_enter_list_all_rounds=data_2_p_enter_list_all_rounds)

        return

    def laying_graph(self, study: int):
        """The Communication Type Effect on the Experts Cheating Level"""
        study_1_data = self.all_data[conditions_per_study[study][0]]
        study_2_data = self.all_data[conditions_per_study[study][1]]

        for by, xlabel, xticks in [['group_average_score', 'Expected Payoff', range(4, 11)],
                                   ['subsession_round_number', 'Trial Number', range(1, 11)]]:
            study_1_cond = study_1_data.groupby(by=by).laying.mean()
            study_2_cond = study_2_data.groupby(by=by).laying.mean()

            fig1, ax1 = plt.subplots()

            # x = [4.17, 6.66, 7.44, 7.97, 8.11, 8.33, 8.94, 9.19, 9.54, 9.77]
            x = study_1_cond.index.values

            ax1.plot(x, study_1_cond.values, color=colors[conditions_per_study[study][0]],
                     label=condition_names_per_study[study][0], marker=markers[conditions_per_study[study][0]])
            ax1.plot(x, study_2_cond.values, color=colors[conditions_per_study[study][1]],
                     label=condition_names_per_study[study][1], marker=markers[conditions_per_study[study][1]])

            plt.xlabel(xlabel, fontsize=15)
            plt.ylabel('Exaggeration', fontsize=15)
            ax1.legend(loc='upper left', shadow=True, fontsize=8)
            plt.xticks(xticks)
            plt.yticks(np.arange(-0.1, 0.9, 0.1))
            # plt.show()
            fig1.savefig(os.path.join(graph_directory, f'Laying_graph_{study}_by_{by}.png'), bbox_inches='tight')

    def score_5_4_analysis(self):
        fig, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [1, 1]})
        for study in [1, 2]:
            study_1_cond = self.all_data[conditions_per_study[study][0]].loc[
                self.all_data[conditions_per_study[study][0]].group_sender_answer_scores == 5.4]
            study_2_cond = self.all_data[conditions_per_study[study][1]].loc[
                self.all_data[conditions_per_study[study][1]].group_sender_answer_scores == 5.4]

            study_1_cond = study_1_cond.groupby(by='subsession_round_number').group_sender_payoff.mean()
            study_2_cond = study_2_cond.groupby(by='subsession_round_number').group_sender_payoff.mean()

            axes[study - 1].plot(study_1_cond.index, study_1_cond.values,
                                 color=colors[conditions_per_study[study][0]],
                                 label=condition_names_per_study[study][0],
                                 marker=markers[conditions_per_study[study][0]])
            axes[study - 1].plot(study_2_cond.index, study_2_cond.values,
                                 color=colors[conditions_per_study[study][1]],
                                 label=condition_names_per_study[study][1],
                                 marker=markers[conditions_per_study[study][1]])
            axes[study - 1].set_title(f'Experiment {study}', fontsize=15)
            axes[study - 1].set_xlabel('Trial Number', fontsize=15)
            if study == 1:
                axes[study - 1].set_ylabel('Fraction of Hotel choices', fontsize=15)
            axes[study - 1].legend(loc='upper right', shadow=True, fontsize=8)
            axes[study - 1].set_xticks(list(range(1, 11)))
            axes[study - 1].set_yticks(np.arange(0.0, 1.01, 0.1))

        fig.savefig(os.path.join(graph_directory, f'Entry_rate_score_5_4_2_axes.png'), bbox_inches='tight')

    def exaggerate_strategy_analysis(self):
        fig, axes = plt.subplots(2, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [1, 1]})
        for study in [1, 2]:
            study_1_cond = self.all_data[conditions_per_study[study][0]].loc[
                self.all_data[conditions_per_study[study][0]].expert_strategy == 'pct_always_exaggerate']
            study_2_cond = self.all_data[conditions_per_study[study][1]].loc[
                self.all_data[conditions_per_study[study][1]].expert_strategy == 'pct_always_exaggerate']

            study_1_cond = study_1_cond.loc[study_1_cond.group_average_score.between(5, 8)]
            study_2_cond = study_2_cond.loc[study_2_cond.group_average_score.between(5, 8)]

            study_1_cond_groupby = pd.DataFrame(study_1_cond.groupby(by='pair_id').expert_answer_above_8.mean())
            study_1_cond_groupby['always_above_8'] = np.where(study_1_cond_groupby.expert_answer_above_8 == 1, 1, 0)
            study_2_cond_groupby = pd.DataFrame(study_2_cond.groupby(by='pair_id').expert_answer_above_8.mean())
            study_2_cond_groupby['always_above_8'] = np.where(study_2_cond_groupby.expert_answer_above_8 == 1, 1, 0)

            study_1_cond = study_1_cond.merge(study_1_cond_groupby[['always_above_8']], left_on='pair_id',
                                              right_index=True)
            study_2_cond = study_2_cond.merge(study_2_cond_groupby[['always_above_8']], left_on='pair_id',
                                              right_index=True)

            study_1_cond = study_1_cond.groupby(by=['subsession_round_number', 'group_average_score'])\
                .always_above_8.mean()
            study_2_cond = study_2_cond.groupby(by=['subsession_round_number', 'group_average_score'])\
                .always_above_8.mean()

            study_1_cond.unstack().plot(kind="bar", stacked=False, rot=0, color=['lightgreen', 'deepskyblue', 'violet'],
                                        ax=axes[study - 1][0], legend=None)
            study_2_cond.unstack().plot(kind="bar", stacked=False, rot=0, color=['lightgreen', 'deepskyblue', 'violet'],
                                        ax=axes[study - 1][1], legend=None)

            for i in [0, 1]:
                axes[study - 1][i].set_title(f'Experiment {study} Condition {condition_names_per_study[study][i]}',
                                             fontsize=10)
                axes[study - 1][i].xaxis.set_label_text("")

            if study == 1:
                for i in [0, 1]:
                    axes[study - 1][i].tick_params(
                        axis='x',  # changes apply to the x-axis
                        which='both',  # both major and minor ticks are affected
                        bottom=False,  # ticks along the bottom edge are off
                        labelbottom=False)  # labels along the bottom edge are off

            # axes[study - 1].set_xticks(x)
            # axes[study - 1].set_yticks(np.arange(0.85, 0.05, 1.26))
        fig.text(0.5, 0.04, 'Trail Number', ha='center', fontsize=10)
        fig.text(0.08, 0.5, '% of Experts Always Above 8', va='center', rotation='vertical', fontsize=10)
        handles, labels = axes[study - 1][0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', shadow=True, fontsize=8, title='Average Score')
        fig.savefig(os.path.join(graph_directory, f'experts_always_above_8_bad_hotels.png'), bbox_inches='tight')

    def expert_payoff_per_expert_strategy(self):
        # expert payoff per expert strategy
        axes_dict = {0: (0, 0), 1: (0, 1), 2: (0, 2), 3: (1, 0), 4: (1, 1), 5: (1, 2)}
        for study in [1, 2]:
            fig, axes = plt.subplots(2, 3, figsize=(12, 5))
            study_1_cond = self.all_data[conditions_per_study[study][0]].loc[
                ~self.all_data[conditions_per_study[study][0]].expert_strategy.isna()]
            study_2_cond = self.all_data[conditions_per_study[study][1]].loc[
                ~self.all_data[conditions_per_study[study][1]].expert_strategy.isna()]
            strategies = list(set(study_1_cond.expert_strategy.unique().tolist() +
                                  study_2_cond.expert_strategy.unique().tolist()))
            for i, strategy in enumerate(strategies):
                study_1_cond_strategy = study_1_cond.loc[study_1_cond.expert_strategy == strategy]
                study_2_cond_strategy = study_2_cond.loc[study_2_cond.expert_strategy == strategy]

                study_1_cond_strategy_per_round = study_1_cond_strategy.groupby(by='subsession_round_number').\
                    group_sender_payoff.mean()
                study_2_cond_strategy_per_round = study_2_cond_strategy.groupby(by='subsession_round_number').\
                    group_sender_payoff.mean()

                if not study_1_cond_strategy.empty:
                    axes[axes_dict[i]].plot(study_1_cond_strategy_per_round.index,
                                            study_1_cond_strategy_per_round.values,
                                            color=colors[conditions_per_study[study][0]],
                                            label=condition_names_per_study[study][0],
                                            marker=markers[conditions_per_study[study][0]], linestyle='-')
                    study_2_cond_strategy_per_round.plot(
                        stacked=False, rot=0, color=colors[conditions_per_study[study][1]], ax=axes[axes_dict[i]],
                        marker=markers[conditions_per_study[study][1]], linestyle='-',
                        label=condition_names_per_study[study][1])
                else:
                    axes[axes_dict[i]].plot(study_2_cond_strategy_per_round.index,
                                            study_2_cond_strategy_per_round.values,
                                            color=colors[conditions_per_study[study][1]],
                                            label=condition_names_per_study[study][1],
                                            marker=markers[conditions_per_study[study][1]], linestyle='-')

                axes[axes_dict[i]].set_title(f'{strategies_dict[strategy]}', fontsize=8)
                # axes[i].get_legend().remove()
                axes[axes_dict[i]].set_xlabel('')
                if i in range(3):
                    axes[axes_dict[i]].tick_params(
                        axis='x',  # changes apply to the x-axis
                        which='both',  # both major and minor ticks are affected
                        bottom=False,  # ticks along the bottom edge are off
                        labelbottom=False)  # labels along the bottom edge are off

                # significant test
                study_1_cond_strategy_per_expert = study_1_cond_strategy.groupby(by='pair_id').\
                    group_sender_payoff.mean()
                study_2_cond_strategy_per_expert = study_2_cond_strategy.groupby(by='pair_id').\
                    group_sender_payoff.mean()
                significant_tests(study_1_cond_strategy_per_expert, study_2_cond_strategy_per_expert,
                                  f'Expert Payoff Study {study} and Strategy {strategies_dict[strategy]} '
                                  f'{conditions_per_study[study][0]}, {conditions_per_study[study][1]}')

            # ax.set_ylabel('% Decision-Makers',  fontdict={'size': 8})
            # ax.set_xlabel("Attribute Number", fontdict={'size': 8})
            fig.text(0.5, 0.04, 'Round Number', ha='center')
            fig.text(0.08, 0.5, 'Expert Average Payoff', va='center', rotation='vertical')
            fig.legend(axes,  # The line objects
                       labels=condition_names_per_study[study],  # The labels for each line
                       loc="upper left",  # Position of legend
                       shadow=True, prop={"size": 8})
            plt.savefig(os.path.join(graph_directory, f"Expert average payoff per strategy for study {study}.png"),
                        bbox_inches='tight')


class CalculationsForPaper:
    def __init__(self):
        self.all_data = defaultdict(pd.DataFrame)
        for condition in conditions:
            df = pd.read_csv(os.path.join(data_analysis_directory, condition, 'results_payments_status.csv'))
            df = df.loc[df.status == 'play']
            df = df.drop_duplicates()
            df['laying'] = df.apply(lambda x: (x['group_sender_answer_scores'] - x[column_to_define_exaggerate]) /
                                              (x['group_score_6'] - x[column_to_define_exaggerate]), axis=1)
            # print(f"condition: {condition}, average laying per hotel: "
            #       f"{df.groupby(by='group_average_score').laying.mean().values}")
            time_spent = pd.read_csv(os.path.join(data_directory, date_directory, condition, 'TimeSpent.csv'))
            time_spent = time_spent.groupby(by='participant_code').seconds_on_page.sum()
            if 'seconds_on_page' in df.columns:
                df = df.drop('seconds_on_page', axis=1)
            df = df.merge(time_spent, left_on='participant_code', right_index=True)
            self.all_data[condition] = df

    def number_participants(self):
        age = list()
        std_age = list()
        payment = list()
        male = list()
        female = list()
        participants = list()
        seconds_on_page = list()
        for condition in conditions:
            print(f'Numbers for condition {condition}')
            condition_data = self.all_data[condition]
            num_participants = condition_data.participant_code.unique().shape[0]
            participants.append(num_participants)
            print(f'Number of participant: {num_participants}')
            gender = condition_data.groupby(by='player_gender').participant_code.count()
            male.append(gender.Male)
            female.append(gender.Female)
            print(f'Gender split: {gender}')
            avg_age = condition_data.player_age.mean()
            age.append(avg_age)
            cur_std_age = condition_data.player_age.std()
            std_age.append(cur_std_age)
            print(f'Average age: {avg_age}, STD: {cur_std_age}')
            avg_pay = condition_data.total_pay.mean()
            payment.append(avg_pay)
            print(f'Average payment: {avg_pay}')
            avg_time = condition_data.seconds_on_page.mean()/60
            seconds_on_page.append(avg_time)
            print(f'Average time: {avg_time}')

        print('Total numbers')
        print(f'Number of participant {sum(participants)}')
        print(f'Number of males {sum(male)}')
        print(f'Number of females {sum(female)}')
        print(f'Average age: {sum(age)/len(age)}')
        print(f'Average payment: {sum(payment)/len(payment)}')
        print(f'Average time: {sum(seconds_on_page)/len(seconds_on_page)}')


def main():
    # calculation_obj = CalculationsForPaper()
    # calculation_obj.number_participants()
    tests_obj = SignificanceTests()
    # computation_paper_graphs(corr_data_path='/Users/reutapel/Documents/Documents/Technion/Msc/thesis/experiment/'
    #                                         'decision_prediction/language_prediction/data/verbal/cv_framework/'
    #                                         'all_data_single_round_label_crf_raisha_non_nn_turn_model_prev_round_label_'
    #                                         'all_history_features_all_history_text_manual_binary_features_predict_first_'
    #                                         'round_verbal_data.csv')
    tests_obj.computation_paper_graphs()
    # expert_payoff_dict = {'verbal': [0.77, 0.66, 0.77, 0.71, 0.74, 0.70, 0.75, 0.67, 0.68, 0.68],
    #                       'numeric': [0.88, 0.79, 0.76, 0.78, 0.75, 0.72, 0.78, 0.73, 0.78, 0.71],
    #                       'num_only': [0.97, 0.90, 0.70, 0.71, 0.75, 0.70, 0.87, 0.78, 0.57, 0.85],
    #                       'both': [0.79, 0.73, 0.64, 0.69, 0.65, 0.78, 0.86, 0.72, 0.79, 0.73]}
    #
    # dem_expected_payoff_dict = {'verbal': [0.31, 0.11, 0.38, 0.47, 0.2, 0.3, 0.32, 0.28, 0.21, 0.12],
    #                             'numeric': [0.22, 0.26, 0.53, 0.21, 0.2, 0.18, 0.32, 0.35, 0.36, -0.04],
    #                             'num_only': [0.28, 0.37, 0.15, 0.11, 0.23, 0.42, 0.29, 0.59, 0.15, 0.2],
    #                             'both': [0.26, 0.36, 0.03, 0.07, 0.36, 0.48, 0.5, 0.01, 0.42, 0.47]}
    # tests_obj.score_5_4_analysis()
    # tests_obj.exaggerate_strategy_analysis()
    # tests_obj.expert_payoff_per_expert_strategy()
    # both_exp_laying_graph(role_dict=tests_obj.expert_payoff_dict, ylabel='Fraction of Hotel choices',
    #                       title=f'Average acceptance rate as a function of trial', laying_dict=tests_obj.laying_dict)
    both_studies_graphs(role_dict=tests_obj.expert_payoff_dict, ylabel="Fraction of Hotel choices",
                        title=f'Average acceptance rate  as a function of trial', expert_payoff=True,
                        laying_dict=tests_obj.laying_dict, equilibrium_data_dict=tests_obj.equilibrium_data_dict)
    both_studies_graphs(role_dict=tests_obj.expert_payoff_dict, ylabel="Fraction of Hotel choices",
                        title=f'Average acceptance rate  as a function of trial', expert_payoff=True,
                        laying_dict=tests_obj.laying_dict_trial, laying_per_trial=True)
    both_studies_graphs(role_dict=tests_obj.expert_payoff_dict_below_8, ylabel="Fraction of Hotel choices",
                        title=f'Average acceptance rate average score below 8 as a function of trial', expert_payoff=True,
                        implied_score_5_8=True)
    both_studies_graphs(role_dict=tests_obj.dm_expected_payoff_dict, ylabel='Average DM expected payoff',
                        title=f'Average DM expected payoff as a function of trial', expert_payoff=False)
    both_studies_graphs(role_dict=tests_obj.expert_payoff_dict_persuasion,
                        ylabel="Fraction of Hotel choices given a persuasion intent",
                        title=f'Average acceptance rate a persuasion intent as a function of trial', expert_payoff=True)

    return

    for study in [1, 2]:
        print(f'Significant tests for study {study}')
        tests_obj.two_hotels_test(study=study)
        tests_obj.understanding_graph(func_study=study, two_axes=True, column_to_group='group_average_score',
                                      x_lable="Hotel's Expected Value")
        tests_obj.dm_individual_differences(study=study)
        tests_obj.laying_test(study=study)
        tests_obj.laying_graph(study=study)
        tests_obj.understanding_graph(func_study=study)
        tests_obj.trust_graph(study=study, split_half=False)
        tests_obj.trust_graph(study=study, split_half=True)
        tests_obj.best_reply_graph(study=study)
        tests_obj.expert_payoff_test(study=study)
        tests_obj.expert_payoff_test(study=study, given_persuasion=True)
        tests_obj.honesty_test(study=study)
        tests_obj.trust_test(study=study)
        tests_obj.dm_payoff_test(study=study)
        tests_obj.linear_score_test(study=study)
        payoff_graph(study, role_dict=tests_obj.expert_payoff_dict, ylabel='Average acceptance rate (expert payoff)',
                     title=f'Average acceptance rate (expert payoff) in Experiment {study} as a function of trial')
        payoff_graph(study, role_dict=tests_obj.dm_expected_payoff_dict, ylabel='Average DM expected payoff',
                     title=f'Average DM expected payoff in Experiment {study} as a function of trial')


if __name__ == '__main__':
    main()
