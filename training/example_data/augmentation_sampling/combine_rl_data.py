import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_1", type=str, required=True, help="Path to first input .parquet file")
    parser.add_argument("--input_2", type=str, required=True, help="Path to second input .parquet file")
    parser.add_argument("--output_file", type=str, required=True, help="Path to output .parquet file")
    args = parser.parse_args()

    df1 = pd.read_parquet(args.input_1)
    df2 = pd.read_parquet(args.input_2)

    combined = pd.concat([df1, df2], ignore_index=True)
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)

    combined.to_parquet(args.output_file, index=False)
    print(f"Combined {len(df1)} + {len(df2)} = {len(combined)} rows -> {args.output_file}")

if __name__ == "__main__":
    main()
