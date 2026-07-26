"""
RAGAS evaluation of the last daily run - scores generated stories for
faithfulness (did the story stick to the retrieved context, or invent
things?) and answer relevancy (does it actually address the question?).

Runs in its own isolated venv (evals_venv/) because the ragas package's
published dependencies conflict with the main agent's LangGraph 1.x stack
(see README "Known limitations"). This script never imports agent/* code -
it only reads the JSON output the main pipeline already produced.
"""

import json
import os

from datasets import Dataset
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_relevancy, faithfulness

RESULT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "latest_run.json")

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Groq's API is OpenAI-compatible, so ChatOpenAI works by just pointing
# base_url at Groq instead of OpenAI - no OpenAI key needed as the judge.
judge_llm = ChatOpenAI(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

# Reuses the same local embedding model the main agent uses for RAG/caching -
# no OpenAI key needed for embeddings either.
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

faithfulness.llm = LangchainLLMWrapper(judge_llm)
answer_relevancy.llm = LangchainLLMWrapper(judge_llm)
answer_relevancy.embeddings = LangchainEmbeddingsWrapper(embeddings)
# answer_relevancy normally asks for several (n>1) candidate completions per
# call to average over - Groq's API rejects n>1, so cap it to 1 per call.
answer_relevancy.strictness = 1


def load_eval_dataset() -> Dataset:
    """Builds a RAGAS-shaped dataset from the last real daily run's stories + context."""
    with open(RESULT_PATH, "r", encoding="utf-8") as f:
        run = json.load(f)

    movers_by_ticker = {m["ticker"]: m for m in run["classified_movers"]}

    questions, answers, contexts = [], [], []
    for story in run["stories"]:
        mover = movers_by_ticker[story["ticker"]]
        questions.append(f"Why did {story['ticker']} move {mover['pct_change']}% today?")
        answers.append(story["story"])
        contexts.append(story["context"])

    return Dataset.from_dict({"question": questions, "answer": answers, "contexts": contexts})


if __name__ == "__main__":
    dataset = load_eval_dataset()
    print(f"Scoring {len(dataset)} real stories from the last daily run...\n")

    result = evaluate(dataset, metrics=[faithfulness, answer_relevancy])
    print(result)

    df = result.to_pandas()
    print("\nPer-story scores:")
    print(df[["question", "faithfulness", "answer_relevancy"]].to_string(index=False))
