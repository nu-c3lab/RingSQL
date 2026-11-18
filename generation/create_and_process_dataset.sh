# creates a new dataset, cleans it, and compares its coverage
# rephrasing is done seperately after coverage is acceptable
# DATASET_NAME=ringsql_gen_from_spider
DATASET_NAME=ringsql_bp_from_spider

# generate dataset
# TODO: refactor the params for sampling plans into args
python generate_dataset_from_spider.py --output_dir_name $DATASET_NAME"/splits_raw"

# run initial simplification (re based version)
python simplify_sql.py --base_dir "generated_data/"$DATASET_NAME

# clean data - casting to julianday in TimeElapsed queries is handled here
python clean_satdb_data.py \
    --input_dir "generated_data/"$DATASET_NAME"/simplified_sql" \
    --output_dir "generated_data/"$DATASET_NAME"/splits_clean"

# standardize queries
python standardize_sql.py --input_dir "generated_data/"$DATASET_NAME


python verify_examples.py \
    --input_dir "generated_data/"$DATASET_NAME"/standardized" \
    --output_dir "generated_data/"$DATASET_NAME"/all_verified_data"