"""
rag/retriever/chroma_retrieval.py

AutoSearch V7

RAG-5.3
ChromaDB Candidate Retrieval

功能：

    Query
        ↓
    RAG-5.2 Query Embedding
        ↓
    Query Vector
        ↓
    ChromaDB
        ↓
    Candidate Retrieval Results

本階段負責：

    1. Query Validation
    2. Query Embedding
    3. ChromaDB Similarity Search
    4. 取得 Candidate Results
    5. URL Scoped Retrieval

本階段不負責：

    - Final Top-K Selection
    - Similarity Threshold
    - Ranking
    - Context Builder
    - LLM
"""


from rag.retriever.config import (
    CANDIDATE_K,
    EMBEDDING_DIMENSION,
)

from rag.retriever.query_embedding import (
    QueryEmbedding,
)


class ChromaDBRetrieval:
    """
    RAG-5.3 ChromaDB Candidate Retrieval。
    """

    # Initialize

    def __init__(
        self,
        chroma_collection,
        query_embedding=None,
        candidate_k=None,
    ):
        """
        初始化 ChromaDB Candidate Retrieval。

        Parameters
        ----------
        chroma_collection:
            RAG-4 ChromaCollection。

        query_embedding:
            RAG-5.2 QueryEmbedding。

        candidate_k:
            ChromaDB Candidate Result 數量。
        """

        if chroma_collection is None:
            raise ValueError(
                "Chroma collection cannot be None."
            )

        self.chroma_collection = (
            chroma_collection
        )

        self.query_embedding = (
            query_embedding
            if query_embedding is not None
            else QueryEmbedding()
        )

        self.dimension = (
            self.query_embedding.get_dimension()
        )

        if (
            self.dimension
            != EMBEDDING_DIMENSION
        ):
            raise ValueError(
                "Query embedding dimension mismatch: "
                f"expected {EMBEDDING_DIMENSION}, "
                f"got {self.dimension}"
            )

        if candidate_k is None:
            candidate_k = CANDIDATE_K

        try:
            candidate_k = int(
                candidate_k
            )
        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "candidate_k must be an integer."
            )

        if candidate_k <= 0:
            raise ValueError(
                "candidate_k must be greater than 0."
            )

        self.candidate_k = candidate_k

        self.collection = (
            self._get_collection()
        )

    # Get Collection

    def _get_collection(
        self
    ):
        """
        取得實際 ChromaDB Collection。
        """

        if not hasattr(
            self.chroma_collection,
            "get_collection",
        ):
            raise TypeError(
                "Chroma collection must provide "
                "get_collection()."
            )

        collection = (
            self.chroma_collection
            .get_collection()
        )

        if collection is None:
            raise ValueError(
                "ChromaDB collection cannot be None."
            )

        return collection

    # Validate Query

    @staticmethod
    def _validate_query(
        query
    ):
        """
        驗證 Query。
        """

        if query is None:
            raise ValueError(
                "Query cannot be None."
            )

        if not isinstance(
            query,
            str,
        ):
            raise TypeError(
                "Query must be a str."
            )

        query = query.strip()

        if not query:
            raise ValueError(
                "Query cannot be empty."
            )

        return query

    # Validate URLs

    @staticmethod
    def _validate_urls(
        urls
    ):
        """
        驗證 URL Scope。
        """

        if urls is None:
            return None

        if not isinstance(
            urls,
            list,
        ):
            raise TypeError(
                "urls must be a list."
            )

        validated_urls = []

        for url in urls:
            if not isinstance(
                url,
                str,
            ):
                raise TypeError(
                    "Each URL must be a str."
                )

            url = url.strip()

            if not url:
                raise ValueError(
                    "URL cannot be empty."
                )

            validated_urls.append(
                url
            )

        return validated_urls

    # Validate Query Embedding

    def _validate_query_embedding(
        self,
        embedding,
    ):
        """
        驗證 Query Embedding。
        """

        if embedding is None:
            raise ValueError(
                "Query embedding cannot be None."
            )

        if not isinstance(
            embedding,
            list,
        ):
            raise TypeError(
                "Query embedding must be a list."
            )

        if (
            len(embedding)
            != self.dimension
        ):
            raise ValueError(
                "Query embedding dimension mismatch: "
                f"expected {self.dimension}, "
                f"got {len(embedding)}"
            )

        return True

    # Retrieve Candidates

    def retrieve(
        self,
        query,
        candidate_k=None,
        urls=None,
    ):
        """
        執行 ChromaDB Candidate Retrieval。

        Parameters
        ----------
        query:
            使用者 Query。

        candidate_k:
            可覆寫預設 Candidate K。

        urls:
            Archive URL Scope。

            None:
                不限制 Archive 範圍。

            list:
                僅檢索指定 URL。

            []:
                不進行 Retrieval，回傳空結果。

        Returns
        -------
        dict

            ChromaDB 原始 Candidate Retrieval Result。
        """

        query = self._validate_query(
            query
        )

        urls = self._validate_urls(
            urls
        )

        if candidate_k is None:
            candidate_k = self.candidate_k
        else:
            try:
                candidate_k = int(
                    candidate_k
                )
            except (
                TypeError,
                ValueError,
            ):
                raise ValueError(
                    "candidate_k must be an integer."
                )

            if candidate_k <= 0:
                raise ValueError(
                    "candidate_k must be greater than 0."
                )

        if urls == []:
            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

        # RAG-5.2

        query_vector = (
            self.query_embedding.embed(
                query
            )
        )

        self._validate_query_embedding(
            query_vector
        )

        # RAG-5.3

        query_parameters = {
            "query_embeddings": [
                query_vector
            ],
            "n_results": candidate_k,
            "include": [
                "documents",
                "metadatas",
                "distances",
            ],
        }

        if urls is not None:
            query_parameters["where"] = {
                "url": {
                    "$in": urls
                }
            }

        result = (
            self.collection.query(
                **query_parameters
            )
        )

        if result is None:
            raise ValueError(
                "ChromaDB retrieval returned None."
            )

        return result

    # Candidate K

    def get_candidate_k(
        self
    ):
        """
        取得預設 Candidate K。
        """

        return self.candidate_k

    # Dimension

    def get_dimension(
        self
    ):
        """
        取得 Query Embedding Dimension。
        """

        return self.dimension


__all__ = [
    "ChromaDBRetrieval",
]