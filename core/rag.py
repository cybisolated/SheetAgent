from typing import List, Optional

from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.milvus import Milvus


class MilvusStore:
    def __init__(
        self, host: str, port: str, collection_name: str, embedding_model: str = "text-embedding-ada-002"
    ) -> None:
        embeddings = OpenAIEmbeddings(model=embedding_model)
        self.instance = Milvus(
            embeddings,
            collection_name=collection_name,
            connection_args={"host": host, "port": port},
        )

    def mmr_search(self, query: str, k: int) -> List[str]:
        docs = self.instance.max_marginal_relevance_search(query, k=20, fetch_k=k)
        contents = [doc.page_content for doc in docs]
        return contents

    def similarity_search(self, query: str, k: int, threshold: float = 0.0) -> Optional[List[str]]:
        docs = self.instance.similarity_search_with_score(query, k)
        if len(docs) == 0:
            return None
        contents = [doc[0].page_content for doc in docs if doc[1] >= threshold]
        return None if len(contents) == 0 else contents
