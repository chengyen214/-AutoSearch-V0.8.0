"""
rag/rag_pipeline.py

AutoSearch V7

RAG Pipeline

目前支援:
    RAG-1 Document Preparation
        ↓
    RAG-2 Chunking
        ↓
    RAG-3 Embedding
        ↓
    Embedding Mapping
        ↓
    Embedding Validation
        ↓
    RAG-4 ChromaDB Index

用途:
    負責文件準備後的切塊、Embedding 與 ChromaDB 索引。
    Retriever、Context Builder 與 LLM 由其他模組負責。
"""

from rag.document_preparation import DocumentPreparation
from rag.chunking.document_chunking import DocumentChunking
from rag.embedding.embedding_pipeline import EmbeddingPipeline
from rag.chroma.indexer import ChromaIndexer


class RAGPipeline:
    """串聯 RAG-1 至 RAG-4 的文件索引流程。"""

    def __init__(
        self,
        document_preparation=None,
        document_chunking=None,
        embedding_pipeline=None,
        chroma_indexer=None,
    ):
        """
        初始化 RAG Pipeline。

        支援 Dependency Injection，方便測試與未來擴充。
        """
        self.document_preparation = (
            document_preparation
            if document_preparation is not None
            else DocumentPreparation()
        )

        self.document_chunking = (
            document_chunking
            if document_chunking is not None
            else DocumentChunking()
        )

        self.embedding_pipeline = (
            embedding_pipeline
            if embedding_pipeline is not None
            else EmbeddingPipeline()
        )

        self.chroma_indexer = (
            chroma_indexer
            if chroma_indexer is not None
            else ChromaIndexer()
        )

    def process_document(
        self,
        document,
    ):
        """
        對已準備的 Document 執行 RAG-2 至 RAG-4。

        Returns:
            dict: document、chunks、embeddings、mappings、
                  record_ids 與 indexed_count。
        """
        if document is None:
            raise ValueError(
                "Document cannot be None."
            )

        chunks = self.document_chunking.chunk(
            document
        )

        embedding_result = (
            self.embedding_pipeline.process_chunks(
                chunks
            )
        )

        embeddings = embedding_result["embeddings"]
        mappings = embedding_result["mappings"]

        record_ids = self.chroma_indexer.index_mappings(
            mappings
        )

        return {
            "document": document,
            "chunks": chunks,
            "embeddings": embeddings,
            "mappings": mappings,
            "record_ids": record_ids,
            "indexed_count": len(record_ids),
        }

    def process_by_document_id(
        self,
        document_id,
    ):
        """依 Document ID 執行 RAG-1 至 RAG-4。"""
        if document_id is None:
            raise ValueError(
                "Document ID cannot be None."
            )

        document_id = str(
            document_id
        ).strip()

        if not document_id:
            raise ValueError(
                "Document ID cannot be empty."
            )

        document = (
            self.document_preparation.prepare_by_document_id(
                document_id
            )
        )

        return self.process_document(
            document
        )

    def process_by_url(
        self,
        url,
    ):
        """依 URL 執行 RAG-1 至 RAG-4。"""
        if url is None:
            raise ValueError(
                "URL cannot be None."
            )

        url = str(
            url
        ).strip()

        if not url:
            raise ValueError(
                "URL cannot be empty."
            )

        document = (
            self.document_preparation.prepare_by_url(
                url
            )
        )

        return self.process_document(
            document
        )


__all__ = [
    "RAGPipeline"
]