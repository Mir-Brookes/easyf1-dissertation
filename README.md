# EasyF1 — An Agentic RAG System for Formula 1 Race-Strategy Recommendation and LLM Comparison

EasyF1 is a decision-support system that grounds Formula 1 mid-race strategy
recommendations in real historical data using Retrieval-Augmented Generation (RAG),
and empirically compares the recommendation quality of two large language models —
a proprietary model (Google Gemini 2.5 Flash-Lite) and an open-weight model
(NVIDIA Nemotron 3 Ultra).

This repository accompanies an MSc dissertation submitted for the module
**COMP7039 — MSc Dissertation in Computing Subjects** at Oxford Brookes University.

> **Author:** Mir Mustafa Ali
> **Supervisor:** Hong Zhu
> **Programme:** MSc Data Science & Artificial Intelligence

---

## Overview

A user builds a hypothetical mid-race scenario — circuit, lap, tyre compound and age,
track position, and whether a safety car is deployed. EasyF1 retrieves relevant
historical precedent from a knowledge base built from three seasons of Formula 1 data,
and both language models produce a structured recommendation (verdict, confidence,
reasoning, and risk), presented side by side for comparison.

The system is intended as an aid to informed human judgement: **it advises, the human decides.**

---

## Key Features

- **Two-tier chunking** of FastF1 data into 6,204 strategic chunks across 53 races
  (2021–2023), capturing strategic moments (pit stops, stints, safety-car periods)
  and race outcomes.
- **Venue-weighted retrieval** over a local ChromaDB vector store, boosting the
  selected circuit while still surfacing strong cross-circuit precedent.
- **A ReAct agent** (built with LangGraph) with three tools: race-data retrieval,
  pit-loss calculation, and tyre-condition assessment.
- **A controlled two-model comparison** — both models receive identical retrieved
  context via direct calls, isolating the model as the only variable.
- **A bias-resistant evaluation** — a blind, position-randomised LLM-as-judge with a
  neutral third-party judge model, plus RAGAS-style retrieval metrics.
- **Fully local and zero-cost** — local embeddings (fastembed), no paid APIs required
  for the core pipeline.
- **An interactive Streamlit interface** for building scenarios and comparing outputs.

---

## Architecture

```
Scenario  ->  Retrieval (venue-weighted)  ->  Prompt  ->  Two LLMs  ->  Side-by-side comparison
                        |
            ChromaDB vector store
   (FastF1 data -> two-tier chunking -> local embeddings)
```

---

## Repository Structure

```
easyf1/
├── app/
│   ├── engine.py          # Core logic: retrieval, prompts, both model callers
│   └── easyf1_app.py      # Streamlit user interface
├── notebooks/             # Development notebooks (data, RAG, agent, evaluation)
├── data/                  # Chunk files (Parquet)
├── chromadb/              # Persistent vector store
├── results/               # Evaluation results, scores, and metrics
├── src/                   # Supporting modules (prompts, etc.)
├── .env.example           # Template for required API keys
├── requirements.txt       # Python dependencies
└── README.md
```

---

## Requirements

- **Python 3.11**
- The dependencies listed in `requirements.txt`
- API keys (see **Setup** below):
  - A Google Gemini API key
  - An OpenRouter API key (for the open-weight model)

---

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Mir-Brookes/easyf1-dissertation.git
   cd easyf1
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS / Linux
   # venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys**
   Copy `.env.example` to `.env` and add your own keys:
   ```
   GEMINI_API_KEY=your_gemini_key_here
   OPENROUTER_API_KEY=your_openrouter_key_here
   ```

---

## Running the Application

From the project root, launch the Streamlit interface:

```bash
cd app
streamlit run easyf1_app.py
```

The application will open in your browser. Build a mid-race scenario using the
sidebar and select **Get Strategy** to see both models' recommendations side by side.

---

## Building the Knowledge Base (optional)

The repository includes a pre-built ChromaDB knowledge base. To rebuild it from
source, the development notebooks in `notebooks/` cover, in order:

1. Downloading and caching FastF1 race data
2. Two-tier chunking of the data
3. Generating local embeddings and populating ChromaDB

---

## Evaluation

The evaluation methodology and results are documented in the accompanying
dissertation. The evaluation comprises:

- A **blind, position-randomised LLM-as-judge** scoring each model's answers on five
  dimensions (correctness, completeness, clarity, faithfulness, reasoning quality).
- **RAGAS-style metrics** (faithfulness, answer relevancy, context recall) assessing
  the retrieval layer.

Evaluation scripts and results are located in `notebooks/` and `results/`.

---

## Notes and Limitations

- The knowledge base covers 53 of 66 scheduled races (2021–2023); the remainder failed
  to load owing to intermittent gaps in the public F1 timing API, and this is disclosed
  as a data-availability limitation.
- The comparison relies on free-tier model access, which is subject to rate limits and
  the possibility of models being withdrawn; the design is provider-agnostic to
  accommodate this.

---

## Acknowledgements

Built with FastF1, ChromaDB, fastembed, LangGraph, Streamlit, the Google Gemini API,
and OpenRouter.

---

*This project was developed as part of an MSc dissertation at Oxford Brookes University.*