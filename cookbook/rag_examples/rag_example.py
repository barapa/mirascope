"""A script using RAG to summarize relevant articles from a large database in 2 ways.

News articles from 2004 are embedded so they may be queried (in two ways) according to a
topic of choice. In the first way we manually calculate similarity between query and
embeddings. In the second, we set up Pinecone and efficiently use its search to find the
most relevant articles. In both cases, we use the Mirascope library to handle the logic
so as to streamline prompt creation.
"""
import os
from argparse import ArgumentParser

import pandas as pd
from config import FILENAME, MAX_TOKENS, URL
from rag_prompts.local_news_rag_prompt import LocalNewsRagPrompt
from rag_prompts.pinecone_news_rag_prompt import PineconeNewsRagPrompt
from setup_pinecone import setup_pinecone
from utils import embed_df_with_openai, load_data

from mirascope import OpenAIChat

chat = OpenAIChat(api_key=os.getenv("OPENAI_API_KEY"))


def summarize_news_local_embeddings(
    query: str, num_articles: int, df: pd.DataFrame
) -> str:
    """Summarizes 2004 news about retrieved context that is relevant to query.

    Locally calculates similarity between query and articles embeddings within pandas
    dataframe using dot product.

    Args:
        query: The query to compare against for similarity.
        num_articles: The number of articles to return.
        df: The dataframe containing the articles and embeddings.

    Returns:
        A summary of the most relevant articles to the query.
    """
    completion = chat.create(
        LocalNewsRagPrompt(num_statements=num_articles, topic=query, df=df)
    )
    return str(completion)


def summarize_news_pinecone_embeddings(
    query: str, num_articles: int, df: pd.DataFrame
) -> str:
    """Summarizes 2004 news about retrieved context that is relevant to query.

    Uses Pinecone to efficiently calculate similarity between query and article
    embeddings.

    Args:
        query: The query to compare against for similarity.
        num_articles: The number of articles to return.
        df: The dataframe containing the articles and embeddings.

    Returns:
        A summary of the most relevant articles to the query.
    """
    completion = chat.create(
        PineconeNewsRagPrompt(num_statements=num_articles, topic=query, df=df)
    )
    return str(completion)


def main(use_pinecone=False):
    if not os.path.exists(FILENAME):
        df = load_data(url=URL, max_tokens=MAX_TOKENS)
        df = embed_df_with_openai(df=df, chat=chat)
        df.to_pickle(FILENAME)
    else:
        df = pd.read_pickle(FILENAME)

    if use_pinecone:
        setup_pinecone(df=df)

    topics = [
        "soccer teams/players going through trouble",
        "environmental factors affecting economy",
        "celebrity or politician scandals",
    ]
    for topic in topics:
        if use_pinecone:
            print(summarize_news_pinecone_embeddings(topic, 3, df))
        else:
            print(summarize_news_local_embeddings(topic, 3, df))
        print("\n")


if __name__ == "__main__":
    parser = ArgumentParser(description="Process some flags.")
    parser.add_argument(
        "-pc", "--pinecone", action="store_true", help="Activate Pinecone mode"
    )
    args = parser.parse_args()
    main(use_pinecone=args.pinecone)