import json, os, re, sys
import pandas as pd

# REPORT_TYPE = 1
# INSTANCE = 4
# RING = 6
# MODE = 7
# PROMPT = 8
# MODEL = 9
# REPORT = 10
# CLAIMS = 12
# FACTUAL = 13
# REFUTED = 14
# HALLUCINATED = 15

directory = 'annotation_round_2_evaluated'

files = os.listdir(directory)

columns = ['unique_id', 'blame', 'domain', 'generation_mode', 'filename', 'prompt', 'report', 'claims', 'factual', 'confabulated', 'refuted', 'unieval_coherence', 'unieval_fluency']

totals_df = pd.DataFrame(columns=columns)

for filename in files:
    # print(filename)
    f = os.path.join(directory, filename)
    if os.path.isfile(f) and filename.endswith('.csv'):
        report_eval_df = pd.read_csv(f, encoding='latin1')

        # if directory in ['GPT4', 'Mixtral', 'Mistral']:
        #     file_identifier = re.match(r'full_report_(.*?)_baseline_with_facts', filename).group(1)
        #     matches = list(filter(lambda fname: file_identifier in fname, base_files))
        #     if len(matches) != 2:
        #         raise Exception
        #
        #     if 'template' in filename:
        #         base_file = next(filter(lambda fname: 'template' in fname, matches))
        #     elif 'table' in filename:
        #         base_file = next(filter(lambda fname: 'table' in fname, matches))
        #     else:
        #         raise Exception
        #
        #     # try:
        #     #     base_file = next(filter(lambda fname: fname.endswith(f"{report_eval_df['report_id'][0]}.csv"), base_files))
        #     # except StopIteration as e:
        #     #     print(filename, report_eval_df['report_id'][0])
        #     base_report_df = pd.read_csv(os.path.join('initial_46_facts_only', base_file), encoding='latin1')
        #
        #     request_info = json.loads(base_report_df['request'][0])
        #     domain = base_report_df['domain'][0]
        # else:
        #     request_info = json.loads(report_eval_df['request'][0])
        #     domain = report_eval_df['domain'][0]

        try:
            assert(report_eval_df['# of claims'].sum() == report_eval_df['# of factual'].sum() + report_eval_df['# of confabulated'].sum() + report_eval_df['# of refuted'].sum())
        except Exception as e:
            print(report_eval_df['annotator'][0], '- report:', filename)
            # raise e

        totals_df = pd.concat([totals_df, pd.DataFrame([[
            report_eval_df['unique_id'][0],
            report_eval_df['annotator'][0],
            report_eval_df['domain'][0],
            report_eval_df['gen_mode'][0],
            filename,
            report_eval_df['prompt'][0],
            report_eval_df['report'][0],
            report_eval_df['# of claims'].sum(),
            report_eval_df['# of factual'].sum(),
            report_eval_df['# of confabulated'].sum(),
            report_eval_df['# of refuted'].sum(),
            report_eval_df['unieval_coherence'][0],
            report_eval_df['unieval_fluency'][0]
        ]], columns=columns)])
print(totals_df)

output_dict = {'factual_accuracy': {}, 'reports': []}

if False:
    metric_columns = ['claims', 'factual', 'refuted', 'confabulated']
    ##################### Factual Accuracy #####################
    totals_dict = {}
    for col in metric_columns:
        totals_dict[col] = totals_df[col].sum()
    output_dict['factual_accuracy']['totals'] = totals_dict
    groupbys = ['ring', 'generation_mode', 'model_type']
    for groupby in groupbys:
        aggregated_df = totals_df.groupby([groupby]).sum()
        print(aggregated_df)
        aggregated_dict = {}
        for domain in aggregated_df.index:
            aggregated_dict[domain] = {}
            for col in metric_columns:
                aggregated_dict[domain][col] = aggregated_df[col][domain]
        output_dict['factual_accuracy'][groupby] = aggregated_dict


############### Prompt Length vs Hallucinations ############

for index, row in totals_df.iterrows():
    # print(f"{len(row['report'])}: {row['report']}")
    output_dict['reports'].append({
        'unique_id': row['unique_id'],
        'blame': row['blame'],
        'domain': row['domain'],
        'mode': row['generation_mode'],
        'filename': row['filename'],
        'prompt_length': len(row['prompt']),
        'report_length': len(row['report']),
        'claims': row['claims'],
        'factual': row['factual'],
        'refuted': row['refuted'],
        'confabulated': row['confabulated'],
        'unieval_coherence': row['unieval_coherence'],
        'unieval_fluency': row['unieval_fluency']
    })

columns = ['unique_id', 'blame', 'domain', 'generation_mode', 'filename', 'prompt', 'report', 'claims', 'factual', 'confabulated', 'refuted', 'unieval_coherence', 'unieval_fluency']

def sort_by_unique_id(annotation):
    return annotation['unique_id']

output_dict['reports'].sort(key=sort_by_unique_id)

with open(f'satyrn_report_stats_{directory}.json', 'w') as out_file:
    json.dump(output_dict, out_file, indent=4)
