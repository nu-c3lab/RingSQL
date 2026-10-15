# Huggingface Documentation for Trainer: https://huggingface.co/docs/transformers/en/main_classes/trainer
import argparse
import wandb
import torch
from datasets import Dataset
from trl import SFTConfig, SFTTrainer

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SFT for text completion / instruction tuning models.")
    parser.add_argument(
        "--model",
        required=True,
        # default="Qwen/Qwen3-0.6B",
        help="Model identifier to train.",
    )
    parser.add_argument(
        "--train-dataset",
        required=True,
        help="Path to the training parquet dataset file with prompt/completion columns.",
    )
    parser.add_argument(
        "--validation-dataset",
        required=True,
        help="Path to the validation parquet dataset file with prompt/completion columns.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where checkpoints and outputs are written.",
    )
    parser.add_argument(
        "--per-device-train-batch-size",
        type=int,
        default=2,
        help="Training batch size per device.",
    )
    parser.add_argument(
        "--gradient-accumulation-steps",
        type=int,
        default=8,
        help="Number of gradient accumulation steps.",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-5,
        help="Optimizer learning rate.",
    )
    parser.add_argument(
        "--lr-scheduler-type",
        type=str,
        default="linear",
        help="Learning rate scheduler type."
    )
    parser.add_argument(
        "--num-train-epochs",
        type=float,
        default=3,
        help="Number of training epochs.",
    )
    parser.add_argument(
        "--logging-steps",
        type=int,
        default=10,
        help="Log every N update steps.",
    )
    parser.add_argument(
        "--save-steps",
        type=int,
        default=None,
        help="Save checkpoint every N update steps.",
    )
    parser.add_argument(
        "--bf16",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable bf16 training when supported.",
    )
    parser.add_argument(
        "--completion-only-loss",
        type=str,
        default="True",
        help="Train loss only on completion tokens.",
    )
    parser.add_argument(
        "--eval-strategy",
        default="steps",
        choices=["no", "steps", "epoch"],
        help="Evaluation schedule to use when a validation dataset is provided.",
    )
    parser.add_argument(
        "--eval-on-start",
        type=str,
        default="False",
        help="Evaluate at step 0 or not."
    )
    parser.add_argument(
        "--load-best-model-at-end",
        type=str,
        default="False",
        help="Make sure the best model is saved at the end."
    )
    parser.add_argument(
        "--metric-for-best-model",
        type=str,
        default="loss",
        help="The metric to use when determining which model is best and therefore should be saved."
    )
    parser.add_argument(
        "--greater-is-better",
        type=str,
        default="False",
        help="Whether a higher value for the chosen metric is considered better or not."
    )
    parser.add_argument(
        "--save-total-limit",
        type=int,
        default=1,
        help="The maximum number of model checkpoints to save."
    )
    parser.add_argument(
        "--eval-steps",
        type=int,
        default=200,
        help="Run evaluation every N update steps when using step-based evaluation.",
    )
    parser.add_argument(
        "--save-strategy",
        default="steps",
        choices=["no", "steps", "epoch"],
        help="Checkpoint save schedule.",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=2048,
        help="The max length of the prompt/completion.",
    )
    parser.add_argument(
        "--wandb_project_name",
        type=str,
        required=True,
        help="Name of the wandb project."
    )
    parser.add_argument(
        "--wandb_experiment_name",
        type=str,
        required=True,
        help="Name of the wandb experiment within the specified project."
    )
    return parser.parse_args()

def validate_columns(dataset: Dataset, name: str) -> None:
    required_cols = {"prompt", "completion"}
    missing = required_cols - set(dataset.column_names)
    if missing:
        raise ValueError(
            f"{name} dataset is missing required columns: {sorted(missing)}. "
            f"Found columns: {dataset.column_names}"
        )

def str_to_bool(s):
    # Remove leading/trailing spaces and convert to lowercase
    s = s.strip().lower()
    if s in ('yes', 'true', 't', '1'):
        return True
    elif s in ('no', 'false', 'f', '0'):
        return False
    else:
        # Handle invalid input gracefully (e.g., raise ValueError or return None)
        raise ValueError(f"'{s}' is not a valid boolean string")

if __name__ == "__main__":
    args = parse_args()

    wandb.init(
        project=args.wandb_project_name,
        name=args.wandb_experiment_name,
        config=vars(args)
    )

    # Load the training dataset
    train_dataset = Dataset.from_parquet(args.train_dataset)
    validate_columns(train_dataset, "train")

    # Load the eval/validation dataset
    eval_dataset = Dataset.from_parquet(args.validation_dataset)

    use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    use_fp16 = torch.cuda.is_available() and not use_bf16

    config = SFTConfig(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        num_train_epochs=args.num_train_epochs,
        logging_steps=args.logging_steps,
        bf16=use_bf16,
        fp16=use_fp16,
        completion_only_loss=str_to_bool(args.completion_only_loss),
        eval_strategy=args.eval_strategy,
        eval_steps=args.eval_steps if args.eval_strategy == "steps" else None,
        eval_on_start=str_to_bool(args.eval_on_start),
        load_best_model_at_end=str_to_bool(args.load_best_model_at_end),
        metric_for_best_model=args.metric_for_best_model,
        greater_is_better=str_to_bool(args.greater_is_better),
        save_total_limit=args.save_total_limit,
        save_strategy=args.save_strategy,
        save_steps=args.save_steps if args.save_strategy == "steps" else None,
        logging_strategy="steps",
        report_to="wandb",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_length=args.max_length
    )

    trainer = SFTTrainer(
        model=args.model,
        args=config,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
    )

    trainer.train()
    trainer.save_model(args.output_dir)
