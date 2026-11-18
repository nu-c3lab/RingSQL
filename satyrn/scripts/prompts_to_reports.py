import csv, os
import spacy
from satyrn.core.LanguageGeneration.GPT4Interface import GPT4Interface
from satyrn.core.LanguageGeneration.Mixtral8x7BInterface import Mixtral8x7BInterface

directory = 'generated_documents/temp'
nlp = spacy.load('en_core_web_sm')
reports = []

model_name = 'mixtral'
if model_name == 'gpt4':
    llm = GPT4Interface()
else:
    llm = Mixtral8x7BInterface('https://france-actual-appears-holder.trycloudflare.com/v1/completions')

for filename in os.listdir(directory):
    if not filename.endswith('.csv'):
        continue
    f = os.path.join(directory, filename)
    if os.path.isfile(f):
        with open(f, 'r') as infile:
            reader = csv.reader(infile)
            prompt = list(reader)[1][3]
        report = llm.generate(prompt)
        uid = filename.split('_')[-1].split('.')[0]
        report_sents = list(nlp(report).sents)

        # Write out a CSV file for each of the reports
        csv_header = ['report_id', 'prompt', 'report', 'report_sentences', '# of claims', '# of factual', '# of confabulated', '# of refuted']
        csv_data = [
            [
                uid,
                prompt,
                report,
                report_sents[0],
                '',
                '',
                '',
                ''
            ],
            *[['', '', '', report_sent, '', '', '', ''] for report_sent in report_sents[1:]]
        ]

        out_filename = 'full_report_' + filename.replace('_none_', f'_{model_name}_')
        with open('generated_documents/' + out_filename, 'w', encoding='UTF8', newline='') as outfile:
            writer = csv.writer(outfile)

            # Write the header
            writer.writerow(csv_header)

            # Write the data
            writer.writerows(csv_data)

print('done')


