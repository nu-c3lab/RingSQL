## Overview

This directory contains the training code for RingSQL. It is organized as follows:

```
training/
├── data/                             # Datasets
│   ├── Spider/      
│   └── BIRD/        
├── models/                           # Base models or checkpoints
│   ├── Qwen2.5-Coder-3B-Instruct/   
│   └── Qwen2.5-Coder-7B-Instruct/   
......
├── sh/                               # Scripts for data processing, training, inference and evaluation
├── sh_ringsql/                       # Scripts for RingSQL data processing
├── src/                              # Source code
└── verl/                             # Verl framework
```

## Environment Setup

> Before getting started, make sure your computing environment supports the following settings:
> - Environment: Python 3.9+
> - CUDA Version: 12.0+ (for verl and vllm integration)
> - GPU Prerequisites: 8 x 80GB+ GPU (for training) / 2 x 40GB GPU (for inference)

### Installation

1. Create and activate a virtual environment (recommended):
```bash
conda create -n sqlr1 python=3.9
```

2. Install dependencies:
```bash
pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu121
pip install vllm==0.6.3 ray
pip install flash-attn --no-build-isolation
pip install -e .  # For verl integration
pip install wandb IPython matplotlib sqlparse func_timeout nltk ijson
```

3. Download the model weights from HuggingFace and put them in the `models/` directory. 

4. For training, copy the training dataset in the `example_data` directory to the `data` directory. For inference, copy the database information in the `db_info` directory (including files forSpider-dev, Spider-test and BIRD-dev) to the related dataset (`data/Spider`, `data/BIRD`) directory.

## Quick Start

1. Run training:
```bash
sh sh/train.sh
```

2. Run inference:
```bash
sh sh/inference.sh
```

3. Run evaluation:
```bash
# evaluate spider
sh sh/eval_spider.sh
# evaluate bird
sh sh/eval_bird.sh
```

## Acknowledgment

This training code is an adaptation of the [SQL-R1](https://github.com/DataArcTech/SQL-R1) codebase, and we thank them for their excellent work.


