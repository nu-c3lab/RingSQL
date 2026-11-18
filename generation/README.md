# Generation Scripts

## Generating Datasets

### Generating A Dataset Using Spider DBs

To generate data using the databases from Spider, first adjust the parameters in the `generate_dataset_from_spider.py` script. These include sample rates for different types of plans, as well as the scale of the dataset size compared to Spider. Update the `DATASET_NAME` variable in the `create_and_process_dataset.sh` script to the desired name of the dataset and run the script (make sure the Satyrn API is running). This script will generate data, clean it, and compare its coverage to that of Spider.

### Question Rephrasing

To rephrase questions, run `python rephrase_questions.py --dir_in <standardized_data_dir> --dir_out <output_dir>` where `<standardized_data_dir>` is the directory containing the standardized dataset splits (again, make sure Satyrn API is running).

### Generating A Dataset Using Satyrn Rings

To generate data for a given Satyrn ring, run `generate_training_data.py` with the necessary arguments to specify the types of examples generated and how many examples to generate.

#### Preprocessing Existing Data

First, copy the satdb dataset into the `generated_data` directory. To generate the `tables.json` and `db_configs.json` files used in the training scripts, follow the instructions in `../evaluation/README.md` using the path to the `rings` directory in the satdb dataset.

To combine the data for each split of the dataset (train, dev, and test) into a single file, run `python python extract_examples_from_data.py --dataset_dir generated_data/<satdb-dir-name>/data/ --output_dir generated_data/<satdb-dir-name>/splits`.

To augment each split with a list of tokens from the queries and questions required for DAILSQL and RESDSQL models, run `python process_raw_examples.py --dir_in generated_data/<satdb-dir-name>/splits --dir_out generated_data/<satdb-dir-name>/tokenized_splits`
