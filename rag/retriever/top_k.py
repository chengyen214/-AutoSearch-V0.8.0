"""
rag/retriever/top_k.py

AutoSearch V7

RAG-5.4
Final Top-K Retrieval

功能：

    RAG-5.3 Candidate Results
        ↓
    Final Top-K Selection
        ↓
    Final Retrieval Results

本階段不負責：

    - Query Embedding
    - ChromaDB Query
    - Similarity Search
    - Similarity Threshold
    - Ranking
    - Context Builder
    - LLM
"""


from rag.retriever.config import (
    TOP_K,
)


class TopKRetrieval:
    """
    RAG-5.4 Final Top-K Retrieval。
    """

    # Initialize

    def __init__(
        self,
        top_k=None,
    ):
        """
        初始化 Final Top-K。

        Parameters
        ----------
        top_k:
            最終保留結果數量。
        """

        if top_k is None:
            top_k = TOP_K

        try:
            top_k = int(
                top_k
            )
        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "top_k must be an integer."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        self.top_k = top_k

    # Validate Result

    @staticmethod
    def _validate_result(
        result
    ):
        """
        驗證 RAG-5.3 Candidate Result。
        """

        if result is None:
            raise ValueError(
                "Retrieval result cannot be None."
            )

        if not isinstance(
            result,
            dict,
        ):
            raise TypeError(
                "Retrieval result must be a dict."
            )

        required_fields = [
            "ids",
            "documents",
            "metadatas",
            "distances",
        ]

        for field in required_fields:

            if field not in result:
                raise ValueError(
                    "Retrieval result is missing "
                    f"'{field}'."
                )

        return True

    # Get First Group

    @staticmethod
    def _get_first_group(
        result,
        field,
    ):
        """
        ChromaDB single query result：

            field[0]
        """

        values = result[field]

        if values is None:
            raise ValueError(
                f"Retrieval field '{field}' "
                "cannot be None."
            )

        if not isinstance(
            values,
            list,
        ):
            raise TypeError(
                f"Retrieval field '{field}' "
                "must be a list."
            )

        if not values:
            return []

        first_group = values[0]

        if first_group is None:
            return []

        if not isinstance(
            first_group,
            list,
        ):
            raise TypeError(
                f"Retrieval field '{field}' "
                "first group must be a list."
            )

        return first_group

    # Select Final Top-K

    def select(
        self,
        result,
        top_k=None,
    ):
        """
        從 RAG-5.3 Candidate Results
        選出 Final Top-K。

        Returns
        -------
        dict

            {
                "ids": [...],
                "documents": [...],
                "metadatas": [...],
                "distances": [...]
            }
        """

        self._validate_result(
            result
        )

        if top_k is None:
            top_k = self.top_k
        else:

            try:
                top_k = int(
                    top_k
                )
            except (
                TypeError,
                ValueError,
            ):
                raise ValueError(
                    "top_k must be an integer."
                )

            if top_k <= 0:
                raise ValueError(
                    "top_k must be greater than 0."
                )

        ids = self._get_first_group(
            result,
            "ids",
        )

        documents = self._get_first_group(
            result,
            "documents",
        )

        metadatas = self._get_first_group(
            result,
            "metadatas",
        )

        distances = self._get_first_group(
            result,
            "distances",
        )

        lengths = {
            len(ids),
            len(documents),
            len(metadatas),
            len(distances),
        }

        if len(lengths) != 1:
            raise ValueError(
                "Retrieval result count mismatch."
            )

        # Final Top-K

        return {
            "ids": ids[:top_k],
            "documents": documents[:top_k],
            "metadatas": metadatas[:top_k],
            "distances": distances[:top_k],
        }

    # Top-K

    def get_top_k(
        self
    ):
        """
        取得預設 Final Top-K。
        """

        return self.top_k


__all__ = [
    "TopKRetrieval",
]