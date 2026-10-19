# Kamino Clone Dataset Generator

> A hybrid pipeline for generating **Type-IV (semantic) code clones** using Large Language Models (LLMs) and deterministic validation.

---

## 🧠 Overview

**Kamino** is a fully automated pipeline designed to generate **behaviorally equivalent but syntactically diverse implementations** of programs (Type-IV clones).

Unlike naive LLM-based generation, Kamino enforces:
- ✅ **Semantic correctness** (via test execution)
- ✅ **Syntactic diversity** (via CodeBLEU filtering)
- ✅ **Non-redundancy** (via clustering)

This makes it suitable for:
- Training ML-based clone detectors  
- Benchmark creation  
- Program transformation studies  

---

## 🏗️ Pipeline Architecture

The pipeline consists of six main stages: 
``Normalization → Generation → Syntactic Filtering → Testing → Repairing → Clustering``


---

## ⚙️ Detailed Pipeline 

The pipeline is organized into six modular steps.  
Each step is documented in detail in the [`doc/`](./doc) folder:

### 📦 Step 1: Normalization
Standardizes input data into a unified format, extracting code, tests, metadata, and generating AST representations.

➡️ See details: [Normalization](./doc/step1.md)

---

### 🤖 Step 2: Clone Generation
Generates diverse candidate implementations using configurable LLM prompting strategies and refactorings.

➡️ See details: [Clone Generation](./doc/step2.md)

---

### 🔍 Step 3: Syntactic Filtering
Removes clones that are too similar to the original using a CodeBLEU-based similarity threshold.

➡️ See details: [Syntactic Filtering](./doc/step3.md)

---

### 🧪 Step 4: Semantic Testing
Executes unit tests to ensure behavioral equivalence between generated clones and the original implementation.

➡️ See details: [Semantic Testing](./doc/step4.md)

---

### 🛠️ Step 5: Repairing Clone Candidates
Attempts to fix partially correct clones using LLM-based re-prompting and test feedback.

➡️ See details: [Repairing Clone Candidates](./doc/step5.md)

---

### 🧬 Step 6: Representative Selection
Applies clustering to select a diverse, non-redundant subset of valid clones.

➡️ See details: [Representative Selection](./doc/step6.md)

---

## Requirements 
* A hugging face token must be placed in a .env file in the root.
    * ```HF_TOKEN=token_here```
* Python 3.10 or newer
* Ollama installed and running (the service is external to Python dependencies)
    * Port configurations can be changed in ```pipeline/src/resources```
* A JDK with `javac` and `java` on `PATH` for Java RQ1 generation
* Inside the *pipeline* folder, run `pip install -r requirements.txt` to install the Python dependencies for the pipelines and notebooks
* [MS C++ build tools](https://visualstudio.microsoft.com/pt-br/visual-cpp-build-tools/) -- make sure to install Desktop development with C++ (include Win 10/11 SDK and C++ CMake tools for Windows) -- this is **required by Codebleu**
* For GPU fine-tuning, install a PyTorch build compatible with the machine's CUDA version if the default `torch` package does not provide the required accelerator support.
## Configuration
The pipeline is pre-configured with the setup used for the experiments. 
To change the configuration, modify [config.py](pipeline/src/config.py)

## Running
Inside *pipeline* folder, run ```python -m src.main```

## Replicating experiments
Inside the ```pipeline``` folder, there is a Jupyter Notebook for each RQ **follow the instructions there**. 

Results are saved in ```results``` folder per RQ.

The dataset is available on ```dataset/kamino_clones_dataset``` 
