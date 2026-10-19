"""Generate and validate Java clones for the RQ1 HumanEval dataset."""

import json
import os
import re
import subprocess
import tempfile
from itertools import combinations
from pathlib import Path

from codebleu import calc_codebleu

from src.config import (
    ALL_MODELS,
    CLONES_PER_ENTRY,
    COMBINATIONS_PER_SET,
    LLM_OPTS,
    NUM_COMBINATIONS_TOUSE,
    RANDOM_SEED,
    REFACS,
)
from src.steps.clone_gen import (
    _select_balanced_combinations,
    call_ollama_chat,
    test_LLM_connection,
)


ROOT = Path(__file__).resolve().parents[2]
INPUT_DATASET = ROOT / "results" / "RQ1" / "human_eval_clone_dataset.json"
LEGACY_INPUT_DATASET = ROOT / "results" / "RQ1" / "humaneval_clone_dataset.json"
JAVA_DATASET = Path(__file__).resolve().parent / "humaneval_java.json"
OUTPUT_DATASET = ROOT / "results" / "RQ1" / "human_eval_clone_dataset.json"

JAVA_REFACTORING = {
    "refac_1": "Use a substantially different algorithmic approach, using idiomatic Java constructs.",
    "refac_2": (
        "Use a different Java standard-library API where appropriate. Do not introduce "
        "third-party dependencies."
    ),
    "refac_3": (
        "Change the data structures or representation where appropriate, while "
        "preserving the required behavior."
    ),
    "refac_4": (
        "Vary the Java coding style and organization while keeping the implementation "
        "clear and behaviorally equivalent."
    ),
    "refac_5": (
        "Separate side effects from computation where applicable; preserve the method "
        "signature and required behavior."
    ),
    "refac_6": (
        "Improve input validation and robustness where appropriate without changing "
        "the required behavior."
    ),
    "refac_7": (
        "Deliberately introduce a common code smell, such as duplicated logic or an "
        "unnecessarily long method, while still satisfying the method contract."
    ),
}


def _entry_index(entry_id):
    match = re.search(r"/(\d+)$", str(entry_id))
    if not match:
        raise ValueError(f"Cannot map dataset entry to HumanEval index: {entry_id}")
    return int(match.group(1))


def _extract_response(text):
    fenced = re.search(r"```(?:java)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    return (fenced.group(1) if fenced else text).strip()


def _method_body(response):
    code = _extract_response(response)
    declaration = re.search(r"(?:public|private|protected)?\s*static\s+[^{;]+\{", code)
    if not declaration:
        return code

    opening = code.find("{", declaration.start())
    depth = 0
    for position in range(opening, len(code)):
        if code[position] == "{":
            depth += 1
        elif code[position] == "}":
            depth -= 1
            if depth == 0:
                return code[opening + 1:position].strip()
    raise ValueError("Generated Java method has unbalanced braces")


def _java_source(java_entry, body):
    prompt = java_entry["prompt"].replace("import org.javatuples.*;\n", "")
    return f"{prompt}{body}\n{java_entry['tests']}"


def _generation_prompt(java_entry, refacs):
    unknown_refacs = sorted(set(refacs) - JAVA_REFACTORING.keys())
    if unknown_refacs:
        raise ValueError(f"Unsupported Java refactoring(s): {', '.join(unknown_refacs)}")

    prompt = (
        "Complete the Java method in the supplied Problem class. Output only the "
        "method body, without markdown, the method signature, or the class. "
        "The implementation must pass the main-method assertions.\n\n"
    )
    if refacs:
        instructions = "\n".join(
            f"- {JAVA_REFACTORING[refac]}" for refac in refacs
        )
        prompt += f"Apply these refactoring requirements:\n{instructions}\n\n"
    return prompt + java_entry["prompt"]


def _validate_java(source):
    with tempfile.TemporaryDirectory(prefix="kamino_java_") as directory:
        source_path = Path(directory) / "Problem.java"
        source_path.write_text(source, encoding="utf-8")
        try:
            compile_result = subprocess.run(
                ["javac", str(source_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except FileNotFoundError as error:
            raise RuntimeError("Java JDK is required: javac was not found") from error
        if compile_result.returncode != 0:
            return False, compile_result.stderr.strip() or "javac failed"

        run_result = subprocess.run(
            ["java", "-ea", "-cp", directory, "Problem"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if run_result.returncode != 0:
            return False, run_result.stderr.strip() or "Java tests failed"
    return True, ""


def _similarity(first, second):
    try:
        return float(calc_codebleu([first], [second], lang="java")["codebleu"])
    except (ImportError, TypeError) as error:
        raise RuntimeError(
            "CodeBLEU Java support requires the Java tree-sitter grammar. "
            "Install the project requirements, including tree-sitter-java==0.21.0, "
            "before running the Java RQ1 pipeline."
        ) from error


def _cluster_representatives(clones, threshold=0.4):
    """Keep one medoid per connected similarity group."""
    groups = []
    for clone in clones:
        matching = [group for group in groups if any(
            _similarity(clone["code"], member["code"]) >= threshold
            for member in group
        )]
        if not matching:
            groups.append([clone])
            continue
        target = matching[0]
        target.append(clone)
        for other in matching[1:]:
            target.extend(other)
            groups.remove(other)

    representatives = []
    for cluster_id, group in enumerate(groups):
        representative = max(
            group,
            key=lambda candidate: sum(
                _similarity(candidate["code"], other["code"])
                for other in group if other is not candidate
            ),
        )
        representative["cluster"] = cluster_id
        representatives.append(representative)
    return representatives


def run_java_rq1(input_dataset=INPUT_DATASET, java_dataset=JAVA_DATASET, output_dataset=OUTPUT_DATASET):
    unknown_refacs = sorted(set(REFACS) - JAVA_REFACTORING.keys())
    if unknown_refacs:
        raise ValueError(f"Unsupported Java refactoring(s): {', '.join(unknown_refacs)}")
    all_refac_combinations = (
        list(combinations(REFACS, COMBINATIONS_PER_SET)) if REFACS else [()]
    )
    selected_refac_combinations = _select_balanced_combinations(
        all_refac_combinations,
        NUM_COMBINATIONS_TOUSE,
        REFACS,
        RANDOM_SEED,
    )

    if not test_LLM_connection():
        raise RuntimeError("Ollama is unavailable")

    input_path = Path(input_dataset)
    if not input_path.exists() and input_path == INPUT_DATASET:
        input_path = LEGACY_INPUT_DATASET
    final_entries = json.loads(input_path.read_text(encoding="utf-8"))
    java_entries = json.loads(Path(java_dataset).read_text(encoding="utf-8"))
    generated = []

    for entry_number, entry in enumerate(final_entries, 1):
        index = _entry_index(entry["id"])
        java_entry = java_entries[index]
        candidates = []
        for model in ALL_MODELS:
            for refac_tuple in selected_refac_combinations:
                selected_refacs = list(refac_tuple)
                prompt = _generation_prompt(java_entry, selected_refacs)
                refac_label = "+".join(selected_refacs) if selected_refacs else "no-refac"
                for clone_number in range(CLONES_PER_ENTRY):
                    response = call_ollama_chat(
                        [{"role": "user", "content": prompt}], model, LLM_OPTS
                    )
                    body = _method_body(response)
                    source = _java_source(java_entry, body)
                    valid, error = _validate_java(source)
                    if not valid:
                        print(
                            f"Skipped {entry['id']} ({model}, {refac_label}): {error}"
                        )
                        continue
                    candidates.append({
                        "model": model,
                        "context": "java_prompt",
                        "strategy": "zero-shot",
                        "refacs": selected_refacs,
                        "clone_id": (
                            f"zero-shot {model}-java {refac_label} "
                            f"{clone_number + 1}"
                        ),
                        "code": source,
                        "test_results": {"main": "PASS"},
                        "metrics": {"codebleu": {}},
                    })

        java_representatives = _cluster_representatives(candidates)
        output_entry = dict(entry)
        output_entry["language"] = "java"
        output_entry["original_code"] = java_entry["prompt"] + java_entry["tests"]
        output_entry["test"] = [java_entry["tests"]]
        output_entry["clones"] = java_representatives
        generated.append(output_entry)
        print(f"[{entry_number}/{len(final_entries)}] {entry['id']}: {len(java_representatives)} clones")

    Path(output_dataset).parent.mkdir(parents=True, exist_ok=True)
    Path(output_dataset).write_text(json.dumps(generated, indent=2), encoding="utf-8")
    print(f"Java RQ1 dataset saved to {output_dataset}")


if __name__ == "__main__":
    run_java_rq1()