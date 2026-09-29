"""
rag/retriever/retrieval_result.py

AutoSearch V7

RAG-5.5

Retrieval Result

功能：

    將 RAG-5.4 Final Top-K
    Raw Retrieval Result
    轉換成標準化 RetrievalResult。

資料流程：

    RAG-5.2 Query Embedding
            ↓
    RAG-5.3 ChromaDB Candidate Retrieval
            ↓
    RAG-5.4 Final Top-K
            ↓
    Raw Retrieval Result
            ↓
    RAG-5.5 Retrieval Result
            ↓
    List[RetrievalResult]

RetrievalResult：

    1. chunk
    2. distance
    3. similarity
    4. document_id
    5. chunk_index
    6. metadata

本階段不負責：

    1. Query Embedding
    2. ChromaDB Search
    3. Candidate-K
    4. Top-K Selection
    5. Reranking
    6. Duplicate Removal
    7. Metadata Normalization
    8. LLM
    9. Context Building
"""


from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class RetrievalResult:
    """
    RAG-5.5 Retrieval Result。

    表示一筆最終 Retrieval Result。

    Attributes
    ----------
    chunk : str
        ChromaDB retrieved chunk。

    distance : float
        ChromaDB returned distance。

    similarity : float | None
        相似度欄位。

        RAG-5.5 目前不自行轉換 distance，
        因此預設可以為 None。

    document_id : str
        原始文章 document_id。

    chunk_index : int
        Chunk 在原始文件中的 index。

    metadata : dict
        原始 ChromaDB metadata。
    """

    chunk: str
    distance: float
    similarity: float | None
    document_id: str
    chunk_index: int
    metadata: dict

    # Post Init Validation

    def __post_init__(self):
        """
        建立 RetrievalResult 時進行基本資料驗證。
        """

        # Chunk

        if not isinstance(
            self.chunk,
            str
        ):
            raise TypeError(
                "chunk must be a str."
            )

        if not self.chunk.strip():
            raise ValueError(
                "chunk cannot be empty."
            )

        # Distance

        if not isinstance(
            self.distance,
            (int, float)
        ):
            raise TypeError(
                "distance must be an int or float."
            )

        if not isfinite(
            float(self.distance)
        ):
            raise ValueError(
                "distance must be finite."
            )

        # Similarity

        if self.similarity is not None:

            if not isinstance(
                self.similarity,
                (int, float)
            ):
                raise TypeError(
                    "similarity must be an int, "
                    "float, or None."
                )

            if not isfinite(
                float(self.similarity)
            ):
                raise ValueError(
                    "similarity must be finite."
                )

        # Document ID

        if not isinstance(
            self.document_id,
            str
        ):
            raise TypeError(
                "document_id must be a str."
            )

        if not self.document_id.strip():
            raise ValueError(
                "document_id cannot be empty."
            )

        # Chunk Index

        if not isinstance(
            self.chunk_index,
            int
        ):
            raise TypeError(
                "chunk_index must be an int."
            )

        if self.chunk_index < 0:
            raise ValueError(
                "chunk_index must be >= 0."
            )

        # Metadata

        if not isinstance(
            self.metadata,
            dict
        ):
            raise TypeError(
                "metadata must be a dict."
            )

        metadata_document_id = (
            self.metadata.get(
                "document_id"
            )
        )

        if metadata_document_id is not None:

            if not isinstance(
                metadata_document_id,
                str
            ):
                raise TypeError(
                    "metadata.document_id "
                    "must be a str."
                )

            if (
                metadata_document_id
                != self.document_id
            ):
                raise ValueError(
                    "document_id does not match "
                    "metadata.document_id."
                )

    # Getters

    def get_chunk(self):
        """
        取得 chunk。
        """

        return self.chunk

    def get_distance(self):
        """
        取得 distance。
        """

        return self.distance

    def get_similarity(self):
        """
        取得 similarity。
        """

        return self.similarity

    def get_document_id(self):
        """
        取得 document_id。
        """

        return self.document_id

    def get_chunk_index(self):
        """
        取得 chunk_index。
        """

        return self.chunk_index

    def get_metadata(self):
        """
        取得 metadata。
        """

        return self.metadata


class RetrievalResultBuilder:
    """
    RAG-5.5 Retrieval Result Builder。

    將 RAG-5.4 Raw Retrieval Result：

        {
            "ids": [...],
            "documents": [...],
            "metadatas": [...],
            "distances": [...]
        }

    轉換成：

        List[RetrievalResult]

    本 Builder 不重新執行：

        ChromaDB Query
        Embedding
        Top-K
        Reranking
    """

    RECORD_ID_SEPARATOR = "::chunk_"

    # Validate Raw Result

    @staticmethod
    def _validate_raw_result(
        result
    ):
        """
        驗證 Raw Retrieval Result。
        """

        if result is None:
            raise ValueError(
                "retrieval result cannot be None."
            )

        if not isinstance(
            result,
            dict
        ):
            raise TypeError(
                "retrieval result must be a dict."
            )

        required_fields = (
            "ids",
            "documents",
            "metadatas",
            "distances",
        )

        for field in required_fields:

            if field not in result:
                raise ValueError(
                    f"retrieval result missing field: "
                    f"{field}"
                )

        for field in required_fields:

            if not isinstance(
                result[field],
                list
            ):
                raise TypeError(
                    f"retrieval result '{field}' "
                    "must be a list."
                )

        lengths = {
            field: len(result[field])
            for field in required_fields
        }

        if len(
            set(lengths.values())
        ) != 1:
            raise ValueError(
                "retrieval result fields "
                "must have equal lengths."
            )

    # Parse Record ID

    @classmethod
    def _parse_record_id(
        cls,
        record_id
    ):
        """
        從 ChromaDB Record ID：

            document_id::chunk_3

        解析：

            document_id
            chunk_index
        """

        if not isinstance(
            record_id,
            str
        ):
            raise TypeError(
                "record_id must be a str."
            )

        if not record_id.strip():
            raise ValueError(
                "record_id cannot be empty."
            )

        if cls.RECORD_ID_SEPARATOR not in record_id:

            raise ValueError(
                "Invalid record_id format. "
                "Expected "
                "'document_id::chunk_index'."
            )

        document_id, chunk_index_text = (
            record_id.rsplit(
                cls.RECORD_ID_SEPARATOR,
                1
            )
        )

        if not document_id:
            raise ValueError(
                "record_id document_id cannot be empty."
            )

        if not chunk_index_text:
            raise ValueError(
                "record_id chunk_index cannot be empty."
            )

        try:

            chunk_index = int(
                chunk_index_text
            )

        except ValueError as error:

            raise ValueError(
                "record_id chunk_index must be an int."
            ) from error

        if chunk_index < 0:
            raise ValueError(
                "record_id chunk_index must be >= 0."
            )

        return (
            document_id,
            chunk_index
        )

    # Build Single Result

    @classmethod
    def build_one(
        cls,
        record_id,
        chunk,
        metadata,
        distance,
        similarity=None
    ):
        """
        建立單一 RetrievalResult。
        """

        if not isinstance(
            metadata,
            dict
        ):
            raise TypeError(
                "metadata must be a dict."
            )

        (
            document_id,
            chunk_index
        ) = cls._parse_record_id(
            record_id
        )

        metadata_document_id = (
            metadata.get(
                "document_id"
            )
        )

        if metadata_document_id is not None:

            if (
                metadata_document_id
                != document_id
            ):
                raise ValueError(
                    "record_id document_id "
                    "does not match metadata.document_id."
                )

        return RetrievalResult(
            chunk=chunk,
            distance=distance,
            similarity=similarity,
            document_id=document_id,
            chunk_index=chunk_index,
            metadata=metadata,
        )

    # Build All Results

    @classmethod
    def build(
        cls,
        result,
        similarities=None
    ):
        """
        將 Raw Retrieval Result
        轉換成 List[RetrievalResult]。

        Parameters
        ----------
        result : dict
            RAG-5.4 Raw Retrieval Result。

        similarities : list | None
            Optional similarity list。

            目前預設為 None，
            不主動轉換 distance。
        """

        cls._validate_raw_result(
            result
        )

        ids = result["ids"]
        documents = result["documents"]
        metadatas = result["metadatas"]
        distances = result["distances"]

        result_count = len(ids)

        # Validate Similarities

        if similarities is not None:

            if not isinstance(
                similarities,
                list
            ):
                raise TypeError(
                    "similarities must be a list "
                    "or None."
                )

            if len(similarities) != result_count:

                raise ValueError(
                    "similarities count must match "
                    "retrieval result count."
                )

        # Build Results

        results = []

        for index in range(
            result_count
        ):

            similarity = None

            if similarities is not None:

                similarity = (
                    similarities[index]
                )

            retrieval_result = (
                cls.build_one(
                    record_id=ids[index],
                    chunk=documents[index],
                    metadata=metadatas[index],
                    distance=distances[index],
                    similarity=similarity,
                )
            )

            results.append(
                retrieval_result
            )

        return results

    # Result Count

    @staticmethod
    def count(
        results
    ):
        """
        取得 RetrievalResult 數量。
        """

        if not isinstance(
            results,
            list
        ):
            raise TypeError(
                "results must be a list."
            )

        return len(results)


__all__ = [
    "RetrievalResult",
    "RetrievalResultBuilder",
]