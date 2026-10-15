<div align="center">
<h1>RingSQL: Schema-Independent Synthetic Data Generation for Text-to-SQL Reinforcement Learning</h1>
</div>

<div align="center">
<p>
    <a href="https://github.com/MarkoSterbentz">Marko Sterbentz</a><sup>1</sup>&nbsp;&nbsp;
    <a href="https://github.com/nu-c3lab/RingSQL">Kevin Cushing</a><sup>2</sup>&nbsp;&nbsp;
    <a href="https://github.com/nu-c3lab/RingSQL">Cameron Barrie</a><sup>1</sup>&nbsp;&nbsp;
    <a href="https://github.com/nu-c3lab/RingSQL">Kristian J. Hammond</a><sup>1</sup>&nbsp;&nbsp;
</p>

<p>
    <sup>1</sup>Northwestern University &nbsp;&nbsp;&nbsp;&nbsp;
    <sup>2</sup>Purdue University
</p>
</div>

<div align="center" style="display: flex; gap: 5px; justify-content: center;">
<a href="https://arxiv.org/abs/2601.05451"><img src="https://img.shields.io/badge/arXiv-red?style=for-the-badge&logo=arxiv"/></a>
<a href="https://github.com/nu-c3lab/RingSQL"><img src="https://img.shields.io/badge/GitHub-black?style=for-the-badge&logo=github"/></a>
<a href="https://huggingface.co/datasets/sterbentzm/RingSQL-Gen"><img src="https://img.shields.io/badge/HuggingFace-FF9D00?style=for-the-badge&logo=huggingface"/></a>
</div>
<br>

## 📖 Overview

Recent advances in text-to-SQL have been driven by larger models, better datasets, and new training methods like RLVR. However, progress remains limited by scarce high-quality training data, a problem RLVR is especially sensitive to since noisy data can produce spurious rewards. Manual data creation is expensive, and existing synthetic methods trade off reliability for scalability: template-based approaches guarantee correct SQL but need schema-specific templates and lack diversity, while LLM-based generation scales easily but lacks quality guarantees. We introduce RingSQL, a hybrid framework for generating question-SQL pairs that combines schema-independent query templates with LLM-based paraphrasing of natural language questions. By grounding question generation in complete template questions, RingSQL preserves question-query correctness across all levels of query complexity, a property purely LLM-based methods fail to maintain. RingSQL also produces the only synthetic dataset that improves RLVR training performance across all tested model architectures and benchmarks, achieving 69.8% average accuracy and surpassing both the next-best synthetic dataset by 2.1% and human-annotated data from Spider and BIRD.

## 📊 Data

You can find the RingSQL data used in our experiments on HuggingFace:

| Dataset     | Size (train/dev) | HuggingFace Link |
|-------------|------------------|------------------|
| RingSQL-Gen | 5000 (4000/1000) | [🤗 Download](https://huggingface.co/datasets/sterbentzm/RingSQL-Gen)  |

## 🤖 Model Weights

You can find the weights for models trained on data produced by RingSQL on HuggingFace:

| Model                                 | Size | HuggingFace Link                                                                       |
|---------------------------------------|------|----------------------------------------------------------------------------------------|
| Qwen2.5-Coder-3B-Instruct-RingSQL-Gen | 3B | [🤗 Download](https://huggingface.co/sterbentzm/Qwen2.5-Coder-3B-Instruct-RingSQL-Gen) |
| Qwen2.5-Coder-7B-Instruct-RingSQL-Gen | 7B | [🤗 Download](https://huggingface.co/sterbentzm/Qwen2.5-Coder-7B-Instruct-RingSQL-Gen) |


### Installation

#### Satyrn Setup
Coming soon.

[//]: # (See the installation and usage instructions in the ```satyrn``` directory.)

#### Data Generation Setup
Coming soon.

[//]: # (See the installation and usage instructions in the ```data_generation``` directory.)

#### Training Setup
See the installation and usage instructions in the ```training``` directory.

## 📚 Citation

If you found RingSQL useful in your own work, please consider citing our paper:

```bibtex
@misc{sterbentz2026ringsql,
      title={RingSQL: Schema-Independent Synthetic Data Generation for Text-to-SQL Reinforcement Learning},
      author={Marko Sterbentz and Kevin Cushing and Cameron Barrie and Kristian J. Hammond},
      year={2026},
      eprint={2601.05451},
      archivePrefix={arXiv},
      url={https://arxiv.org/abs/2601.05451}
}
```
