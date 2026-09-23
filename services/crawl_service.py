"""
services/crawl_service.py

AutoSearch V5

V5.6.x

Crawl Service

用途：

    將 V5 Pipeline 的 URL
    交給底層 crawler.py 執行 HTTP Download。

架構：

    SearchResult / Target
            ↓
        CrawlService
            ↓
        crawler.py
            ↓
        Raw HTML
            │
            ├──────────────────────────────┐
            │                              │
            ▼                              ▼
    KeywordProcessor                 原本 Crawl 流程
            ↓                              │
    Processed Keyword                      │
            ↓                              ▼
    KeywordLinkDetector               Content Hash
            ↓                              │
      Related URLs                         ▼
            ↓                        Resource Download
    RelatedCrawlService                    │
            │                              ▼
            │                         CrawlResult
            │                              │
            │                              ▼
            │                     RawHTMLRepository
            │                              │
            │                              ▼
            │                           MongoDB
            │
            └──→ Related Crawl
                     ↓
                   Crawl
                     ↓
                   Parser
                     ↓
                  Article


Raw HTML MongoDB Structure：

    raw_html
    ├── url
    ├── html
    ├── content_hash
    ├── resolved_url
    ├── article_id
    ├── document_id
    ├── created_at
    ├── updated_at
    │
    └── resources
        ├── css[]
        └── images[]


責任：

    - Crawl URL
    - 呼叫 crawler.download()
    - 呼叫 crawler.download_resources()
    - 保留原始 URL
    - 保留 Redirect 後 URL
    - 取得 Raw HTML
    - 計算 Raw HTML Content Hash
    - 取得 CSS / Image Resources
    - Keyword Processing
    - Keyword Link Detection
    - 取得 Related URLs
    - 呼叫 RelatedCrawlService
    - 建立 CrawlResult
    - 將成功 CrawlResult 保存至 MongoDB
    - Crawl Error Handling
    - 基本 URL Validation


不負責：

    - SQL
    - Job
    - Target Repository
    - Search
    - Search Provider
    - SearchAdapter
    - Parser
    - Article
    - ArticleService
    - MongoDB implementation
    - Archive Business Logic
    - Duplicate Detection
    - Archive Version
    - RelatedCrawlService implementation
    - AI
    - AI Task


設計原則：

    crawler.py
        負責：

            URL
             ↓
            HTTP
             ↓
            HTML
             ↓
            Resource Download


    CrawlService
        負責：

            V5 Pipeline
                ↓
            Crawl
                ↓
            Raw HTML
                ↓
            KeywordProcessor
                ↓
            KeywordLinkDetector
                ↓
            Related URLs
                ↓
            RelatedCrawlService
                ↓
            回到原本 Crawl Flow
                ↓
            Hash
                ↓
            Resources
                ↓
            CrawlResult
                ↓
            Raw HTML Persistence


    KeywordLinkDetector
        負責：

            HTML
              +
            Processed Keyword
              ↓
            Related URLs

        SQL Priority：

            MySQL
                ↓
            articles.url
                ↓
            未存在 URL 優先


    RelatedCrawlService
        負責：

            Related URLs
                ↓
            Crawl
                ↓
            Parser
                ↓
            Article


    RawHTMLRepository
        負責：

            CrawlResult
                ↓
            MongoDB Raw HTML


    ParserService
        負責：

            Raw HTML
                ↓
            Parsed Article


Hash Policy：

    CrawlService
        ↓
    SHA-256(Raw HTML)
        ↓
    CrawlResult.content_hash

    content_hash 是 Raw HTML Content Identity。


MongoDB Metadata Policy：

    Crawl 階段：

        article_id = None
        document_id = None

    Article 建立後：

        RawHTMLRepository.update_metadata()

    補回：

        article_id
        document_id


Repository Save Failure：

    MongoDB 儲存失敗：

        不視為 HTTP Crawl Failure。

    因此：

        CrawlResult.success
            仍代表 HTTP Crawl 是否成功。


Keyword Link Detection Policy：

    HTML 成功取得後：

        HTML
          ↓
        KeywordProcessor
          ↓
        Processed Keyword
          ↓
        KeywordLinkDetector
          ↓
        Related URLs
          ↓
        RelatedCrawlService


    CrawlService：

        不直接操作 SQL。

        不直接實作 Related Crawl。

        只負責：

            Related URLs
                ↓
            RelatedCrawlService


Related Crawl Policy：

    Original Crawl 與 Related Crawl 是兩條流程。


    Original Crawl：

        原始 URL
            ↓
        Original HTML
            ↓
        Hash
            ↓
        Resources
            ↓
        CrawlResult
            ↓
        MongoDB
            ↓
        原本 Parser / Article 流程


    Related Crawl：

        Original HTML
            ↓
        KeywordProcessor
            ↓
        KeywordLinkDetector
            ↓
        SQL articles.url Priority
            ↓
        Related URLs
            ↓
        RelatedCrawlService
            ↓
        Crawl
            ↓
        Parser
            ↓
        Article


    Related Crawl：

        - 不取代 Original HTML
        - 不取代 Original CrawlResult
        - 不修改 Original CrawlResult
        - 不回到 JobExecutorBridge
        - 不重新進入 Original Crawl URL
        - 完成後 Original CrawlService 繼續


Circular Import Policy：

    不使用：

        from services.related_crawl_service import RelatedCrawlService

    於檔案頂部。

    原因：

        related_crawl_service
            ↓
        ParserService
            ↓
        CrawlService

    若 CrawlService 再於 module import 階段
    import RelatedCrawlService，

        CrawlService
            ↓
        RelatedCrawlService
            ↓
        ParserService
            ↓
        CrawlService

    可能形成 Circular Import。

    因此：

        RelatedCrawlService
            ↓
        Runtime Lazy Import


Pipeline：

    SearchResult
          ↓
         URL
          ↓
    CrawlService
          ↓
    crawler.resolve_url()
          ↓
    crawler.download()
          ↓
       Raw HTML
          │
          ├────────────────────────────┐
          │                            │
          ▼                            ▼
    KeywordProcessor               SHA-256 Hash
          │                            │
          ▼                            ▼
    Processed Keyword            Content Hash
          │                            │
          ▼                            │
    KeywordLinkDetector                │
          │                            │
          │                            │
          ▼                            │
    SQL articles.url                   │
          │                            │
          ▼                            │
   未存在 URL 優先                     │
          │                            │
          ▼                            │
      Related URLs                     │
          │                            │
          ▼                            │
  RelatedCrawlService                  │
          │                            │
      Crawl / Parser / Article         │
                                       │
                         Resource Download
                                       │
                                       ▼
                                  CrawlResult
                                       │
                                       ▼
                                RawHTMLRepository
                                       │
                                       ▼
                                    MongoDB
"""

import hashlib

from dataclasses import (
    dataclass,
    field,
)

from datetime import (
    datetime,
    timezone,
)

from typing import (
    Optional,
)

from crawler.crawler import (
    download,
    resolve_url,
    download_resources,
)

from database.raw_html_repository import (
    RawHTMLRepository,
)

from utils.keyword_processor import (
    KeywordProcessor,
)

from services.keyword_link_detector import (
    KeywordLinkDetector,
)

from utils.logger import (
    logger,
)


@dataclass
class CrawlResult:
    """
    CrawlService 的 Crawl 結果。

    保存：

        - 原始 URL
        - Redirect 後 URL
        - Raw HTML
        - Content Hash
        - Article ID
        - Document ID
        - Resources
        - Success
        - Error
        - Crawl Time

    注意：

        本 Model 不負責：

            MongoDB
            Parser
            Article
            Duplicate Detection
            Archive Version
            Related Crawl
    """

    url: str

    resolved_url: Optional[str] = None

    html: Optional[str] = None

    content_hash: Optional[str] = None

    article_id: Optional[int] = None

    document_id: Optional[str] = None

    resources: dict = field(
        default_factory=lambda: {
            "css": [],
            "images": [],
        }
    )

    success: bool = False

    error: Optional[str] = None

    crawl_time: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    @property
    def has_html(self):
        """
        判斷是否成功取得 Raw HTML。
        """

        return bool(
            self.success
            and self.html
        )

    @property
    def has_hash(self):
        """
        判斷是否已產生 Content Hash。
        """

        return bool(
            self.content_hash
        )

    @property
    def has_resources(self):
        """
        判斷是否存在 Resource。

        注意：

            沒有 Resource
            不代表 Crawl Failure。
        """

        if not self.resources:
            return False

        css = self.resources.get(
            "css",
            [],
        )

        images = self.resources.get(
            "images",
            [],
        )

        return bool(
            css
            or images
        )

    @property
    def final_url(self):
        """
        取得最終 URL。

        若沒有 resolved_url，
        則退回原始 URL。
        """

        return (
            self.resolved_url
            or self.url
        )


class CrawlService:
    """
    V5 Crawl Service。

    負責：

        URL
         ↓
        crawler.py
         ↓
        Raw HTML
         ↓
        KeywordProcessor
         ↓
        KeywordLinkDetector
         ↓
        RelatedCrawlService
         ↓
        SHA-256
         ↓
        Resources
         ↓
        CrawlResult
         ↓
        RawHTMLRepository
         ↓
        MongoDB


    本 Service 不直接處理：

        SQL
        Parser
        Article
        AI
        Archive Business Logic
        RelatedCrawlService implementation


    Related Crawl：

        RelatedCrawlService
        由本 Service 在 Runtime
        Lazy Import 後直接呼叫。


    注意：

        不在 Module Import 階段
        直接 import RelatedCrawlService。

        避免 Circular Import。
    """

    def __init__(
        self,
        downloader=None,
        url_resolver=None,
        resource_downloader=None,
        raw_html_repository=None,
        save_raw_html=True,
        keyword_processor=None,
        keyword_link_detector=None,
        related_crawl_service=None,
    ):
        """
        建立 CrawlService。

        Parameters
        ----------

        downloader :

            底層 HTML Downloader。

            預設：

                crawler.download


        url_resolver :

            Redirect URL Resolver。

            預設：

                crawler.resolve_url


        resource_downloader :

            CSS / Image Resource Downloader。

            預設：

                crawler.download_resources


        raw_html_repository :

            Raw HTML Repository。

            預設：

                RawHTMLRepository()


        save_raw_html :

            是否在 Crawl 成功後
            將 Raw HTML 保存至 MongoDB。

            預設 True。


        keyword_processor :

            KeywordProcessor。

            預設：

                KeywordProcessor()


        keyword_link_detector :

            KeywordLinkDetector。

            預設：

                KeywordLinkDetector()


        related_crawl_service :

            RelatedCrawlService。

            可由外部注入。

            若未提供：

                在 _handle_related_urls()
                執行 Runtime Lazy Import。

            必須提供：

                process_many(
                    related_urls,
                    keyword,
                )
        """

        if downloader is None:
            downloader = download

        if not callable(
            downloader
        ):
            raise TypeError(
                "downloader must be callable"
            )

        self.downloader = downloader

        if url_resolver is None:
            url_resolver = resolve_url

        if not callable(
            url_resolver
        ):
            raise TypeError(
                "url_resolver must be callable"
            )

        self.url_resolver = url_resolver

        if resource_downloader is None:
            resource_downloader = download_resources

        if not callable(
            resource_downloader
        ):
            raise TypeError(
                "resource_downloader "
                "must be callable"
            )

        self.resource_downloader = (
            resource_downloader
        )

        if raw_html_repository is None:
            raw_html_repository = (
                RawHTMLRepository()
            )

        self.raw_html_repository = (
            raw_html_repository
        )

        self.save_raw_html = bool(
            save_raw_html
        )

        if keyword_processor is None:
            keyword_processor = (
                KeywordProcessor()
            )

        if not hasattr(
            keyword_processor,
            "process",
        ):
            raise TypeError(
                "keyword_processor "
                "must provide process()"
            )

        self.keyword_processor = (
            keyword_processor
        )

        if keyword_link_detector is None:
            keyword_link_detector = (
                KeywordLinkDetector()
            )

        if not hasattr(
            keyword_link_detector,
            "detect",
        ):
            raise TypeError(
                "keyword_link_detector "
                "must provide detect()"
            )

        self.keyword_link_detector = (
            keyword_link_detector
        )

        if (
            related_crawl_service
            is not None
        ):
            if not hasattr(
                related_crawl_service,
                "process_many",
            ):
                raise TypeError(
                    "related_crawl_service "
                    "must provide "
                    "process_many()"
                )

        self.related_crawl_service = (
            related_crawl_service
        )

    def detect_related_urls(
        self,
        html,
        keyword,
        target_language=None,
        base_url=None,
    ):
        """
        使用現有 KeywordProcessor
        與 KeywordLinkDetector
        找出 Related URLs。

        Pipeline：

            HTML
              ↓
            KeywordProcessor
              ↓
            Processed Keyword
              ↓
            KeywordLinkDetector
              ↓
            Related URLs

        注意：

            KeywordLinkDetector
            自己負責 SQL：

                articles.url

            未存在 URL 優先。
        """

        if not isinstance(
            html,
            str,
        ):
            return []

        if not html.strip():
            return []

        if keyword is None:
            return []

        keyword = str(
            keyword
        ).strip()

        if not keyword:
            return []

        try:
            processed_keyword = (
                self.keyword_processor.process(
                    keyword,
                    target_language,
                )
            )

        except Exception as exc:
            logger.exception(
                "Keyword processing failed: "
                f"keyword={keyword}, "
                f"error={exc}"
            )

            return []

        if not isinstance(
            processed_keyword,
            dict,
        ):
            logger.warning(
                "KeywordProcessor returned "
                "invalid result type: "
                f"type="
                f"{type(processed_keyword).__name__}"
            )

            return []

        try:
            related_urls = (
                self.keyword_link_detector.detect(
                    html,
                    processed_keyword,
                    base_url=(
                        base_url
                    ),
                )
            )

        except Exception as exc:
            logger.exception(
                "Keyword link detection failed: "
                f"keyword={keyword}, "
                f"base_url={base_url}, "
                f"error={exc}"
            )

            return []

        if related_urls is None:
            return []

        if not isinstance(
            related_urls,
            list,
        ):
            logger.warning(
                "Keyword link detector returned "
                "invalid result type: "
                f"type={type(related_urls).__name__}"
            )

            return []

        return related_urls

    def _handle_related_urls(
        self,
        related_urls,
        keyword,
    ):
        """
        將 Related URLs
        傳給 RelatedCrawlService。

        Pipeline：

            Related URLs
                 ↓
            RelatedCrawlService
                 ↓
               Crawl
                 ↓
               Parser
                 ↓
              Article


        Related Crawl 是 Original Crawl
        的獨立 Side Branch。

        不修改：

            Original HTML
            Original CrawlResult
            Original Crawl flow

        不回到：

            JobExecutorBridge
        """

        if not related_urls:
            return None

        try:
            related_crawl_service = (
                self.related_crawl_service
            )

            if (
                related_crawl_service
                is None
            ):
                from services.related_crawl_service import (
                    RelatedCrawlService,
                )

                related_crawl_service = (
                    RelatedCrawlService()
                )

            result = (
                related_crawl_service.process_many(
                    related_urls,
                    keyword,
                )
            )

            logger.info(
                "Related Crawl completed: "
                f"keyword={keyword}, "
                f"related_urls={len(related_urls)}"
            )

            return result

        except Exception as exc:
            logger.exception(
                "Related Crawl failed: "
                f"keyword={keyword}, "
                f"related_urls={len(related_urls)}, "
                f"error={exc}"
            )

            return None

    def crawl(
        self,
        url,
        keyword=None,
        target_language=None,
    ):
        """
        Crawl 單一 URL。

        Pipeline：

            URL
             ↓
            URL Validation
             ↓
            resolve_url()
             ↓
            download()
             ↓
            Raw HTML
             │
             ├───────────────────────┐
             │                       │
             ▼                       ▼
        KeywordProcessor         SHA-256
             ↓                       ↓
        Processed Keyword       Content Hash
             ↓                       │
        KeywordLinkDetector          │
             ↓                       │
        Related URLs                 │
             ↓                       │
        RelatedCrawlService          │
             ↓                       │
        Crawl / Parser / Article     │
                                     │
                          Resource Download
                                     ↓
                                CrawlResult
                                     ↓
                              RawHTMLRepository
                                     ↓
                                  MongoDB
        """

        try:
            normalized_url = (
                self.normalize_url(
                    url
                )
            )

        except Exception as exc:
            return CrawlResult(
                url=str(
                    url
                ),
                resolved_url=None,
                html=None,
                content_hash=None,
                article_id=None,
                document_id=None,
                resources={
                    "css": [],
                    "images": [],
                },
                success=False,
                error=str(
                    exc
                ),
            )

        resolved_url = normalized_url

        try:
            resolved_url = (
                self.url_resolver(
                    normalized_url
                )
            )

            resolved_url = (
                self.normalize_url(
                    resolved_url
                )
            )

        except Exception as exc:
            resolved_url = normalized_url

            logger.warning(
                "URL resolution failed: "
                f"url={normalized_url}, "
                f"error={exc}"
            )

        try:
            html = (
                self.downloader(
                    normalized_url
                )
            )

        except Exception as exc:
            logger.exception(
                "Crawl download failed: "
                f"url={normalized_url}, "
                f"error={exc}"
            )

            return CrawlResult(
                url=normalized_url,
                resolved_url=resolved_url,
                html=None,
                content_hash=None,
                article_id=None,
                document_id=None,
                resources={
                    "css": [],
                    "images": [],
                },
                success=False,
                error=str(
                    exc
                ),
            )

        if html is None:
            logger.warning(
                "Crawl download returned None: "
                f"url={normalized_url}"
            )

            return CrawlResult(
                url=normalized_url,
                resolved_url=resolved_url,
                html=None,
                content_hash=None,
                article_id=None,
                document_id=None,
                resources={
                    "css": [],
                    "images": [],
                },
                success=False,
                error=(
                    "Failed to download HTML"
                ),
            )

        if not isinstance(
            html,
            str,
        ):
            logger.error(
                "Crawler returned invalid HTML type: "
                f"url={normalized_url}, "
                f"type={type(html).__name__}"
            )

            return CrawlResult(
                url=normalized_url,
                resolved_url=resolved_url,
                html=None,
                content_hash=None,
                article_id=None,
                document_id=None,
                resources={
                    "css": [],
                    "images": [],
                },
                success=False,
                error=(
                    "Downloader must return "
                    "HTML string or None"
                ),
            )

        if not html.strip():
            logger.warning(
                "Downloaded HTML is empty: "
                f"url={normalized_url}"
            )

            return CrawlResult(
                url=normalized_url,
                resolved_url=resolved_url,
                html=None,
                content_hash=None,
                article_id=None,
                document_id=None,
                resources={
                    "css": [],
                    "images": [],
                },
                success=False,
                error=(
                    "Downloaded HTML is empty"
                ),
            )

        if keyword:
            related_urls = (
                self.detect_related_urls(
                    html=html,
                    keyword=keyword,
                    target_language=target_language,
                    base_url=(
                        resolved_url
                        or normalized_url
                    ),
                )
            )

            if related_urls:
                logger.info(
                    "Related URLs detected: "
                    f"url={normalized_url}, "
                    f"keyword={keyword}, "
                    f"count={len(related_urls)}"
                )

                self._handle_related_urls(
                    related_urls,
                    keyword,
                )

            else:
                logger.info(
                    "No related URLs detected: "
                    f"url={normalized_url}, "
                    f"keyword={keyword}"
                )

        try:
            content_hash = (
                self.generate_content_hash(
                    html
                )
            )

        except Exception as exc:
            logger.exception(
                "Content hash generation failed: "
                f"url={normalized_url}, "
                f"error={exc}"
            )

            return CrawlResult(
                url=normalized_url,
                resolved_url=resolved_url,
                html=html,
                content_hash=None,
                article_id=None,
                document_id=None,
                resources={
                    "css": [],
                    "images": [],
                },
                success=False,
                error=str(
                    exc
                ),
            )

        resources = {
            "css": [],
            "images": [],
        }

        try:
            resources = (
                self.resource_downloader(
                    html,
                    resolved_url,
                )
            )

            if resources is None:
                resources = {
                    "css": [],
                    "images": [],
                }

            elif not isinstance(
                resources,
                dict,
            ):
                logger.warning(
                    "Resource downloader returned "
                    "invalid result type: "
                    f"url={normalized_url}, "
                    f"type={type(resources).__name__}"
                )

                resources = {
                    "css": [],
                    "images": [],
                }

            else:
                resources = {
                    "css": resources.get(
                        "css",
                        [],
                    ),
                    "images": resources.get(
                        "images",
                        [],
                    ),
                }

        except Exception as exc:
            logger.exception(
                "Resource download failed: "
                f"url={normalized_url}, "
                f"error={exc}"
            )

            resources = {
                "css": [],
                "images": [],
            }

        result = CrawlResult(
            url=normalized_url,
            resolved_url=resolved_url,
            html=html,
            content_hash=content_hash,
            article_id=None,
            document_id=None,
            resources=resources,
            success=True,
            error=None,
        )

        if self.save_raw_html:
            self._save_raw_html(
                result
            )

        return result

    @staticmethod
    def generate_content_hash(
        html,
    ):
        """
        產生 Raw HTML Content Hash。

        Algorithm：

            SHA-256
        """

        if html is None:
            raise ValueError(
                "html cannot be None"
            )

        if not isinstance(
            html,
            str,
        ):
            html = str(
                html
            )

        return hashlib.sha256(
            html.encode(
                "utf-8"
            )
        ).hexdigest()

    def _save_raw_html(
        self,
        crawl_result,
    ):
        """
        將成功 CrawlResult
        保存至 RawHTMLRepository。
        """

        if crawl_result is None:
            return None

        if not crawl_result.success:
            return None

        if not crawl_result.html:
            return None

        if not crawl_result.content_hash:
            return None

        if self.raw_html_repository is None:
            logger.warning(
                "Raw HTML repository is not configured."
            )

            return None

        repository = (
            self.raw_html_repository
        )

        try:
            save_crawl_result_method = getattr(
                repository,
                "save_crawl_result",
                None,
            )

            if callable(
                save_crawl_result_method
            ):
                mongo_id = (
                    save_crawl_result_method(
                        crawl_result
                    )
                )

                if mongo_id:
                    logger.info(
                        "CrawlResult saved to "
                        "Raw HTML MongoDB: "
                        f"mongo_id={mongo_id}, "
                        f"url={crawl_result.url}"
                    )

                else:
                    logger.warning(
                        "Raw HTML repository "
                        "did not return MongoDB ID: "
                        f"url={crawl_result.url}"
                    )

                return mongo_id

            save_raw_html_method = getattr(
                repository,
                "save_raw_html",
                None,
            )

            if callable(
                save_raw_html_method
            ):
                return (
                    save_raw_html_method(
                        crawl_result
                    )
                )

            save_method = getattr(
                repository,
                "save",
                None,
            )

            if callable(
                save_method
            ):
                try:
                    return (
                        save_method(
                            url=(
                                crawl_result.url
                            ),
                            html=(
                                crawl_result.html
                            ),
                            content_hash=(
                                crawl_result.content_hash
                            ),
                            resolved_url=(
                                crawl_result.resolved_url
                            ),
                            article_id=(
                                crawl_result.article_id
                            ),
                            document_id=(
                                crawl_result.document_id
                            ),
                            resources=(
                                crawl_result.resources
                            ),
                        )
                    )

                except TypeError:
                    return (
                        save_method(
                            crawl_result
                        )
                    )

            raise TypeError(
                "raw_html_repository must provide "
                "save_crawl_result(), "
                "save_raw_html(), or save()"
            )

        except Exception as exc:
            logger.exception(
                "Raw HTML MongoDB save failed: "
                f"url={crawl_result.url}, "
                f"error={exc}"
            )

            return None

    def crawl_result(
        self,
        search_result,
        keyword=None,
        target_language=None,
    ):
        """
        從 SearchResult 取得 URL 後進行 Crawl。

        keyword：

            優先使用明確傳入的 keyword。

            若沒有，
            嘗試從 search_result.keyword 取得。

        target_language：

            優先使用明確傳入的 target_language。

            若沒有，
            嘗試從 search_result.target_language 取得。
        """

        if search_result is None:
            raise ValueError(
                "search_result cannot be None"
            )

        url = getattr(
            search_result,
            "url",
            None,
        )

        if url is None:
            raise ValueError(
                "search_result must "
                "provide url"
            )

        if keyword is None:
            keyword = getattr(
                search_result,
                "keyword",
                None,
            )

        if target_language is None:
            target_language = getattr(
                search_result,
                "target_language",
                None,
            )

        return self.crawl(
            url,
            keyword=keyword,
            target_language=target_language,
        )

    def crawl_target(
        self,
        target,
        keyword=None,
        target_language=None,
    ):
        """
        Direct URL Target Crawl。
        """

        if target is None:
            raise ValueError(
                "target cannot be None"
            )

        url = getattr(
            target,
            "url",
            None,
        )

        if url is None:
            raise ValueError(
                "target must provide url"
            )

        if keyword is None:
            keyword = getattr(
                target,
                "keyword",
                None,
            )

        if target_language is None:
            target_language = getattr(
                target,
                "target_language",
                None,
            )

        return self.crawl(
            url,
            keyword=keyword,
            target_language=target_language,
        )

    def crawl_many(
        self,
        urls,
        keyword=None,
        target_language=None,
    ):
        """
        Crawl 多個 URL。
        """

        if urls is None:
            return []

        results = []

        for url in urls:
            try:
                result = self.crawl(
                    url,
                    keyword=keyword,
                    target_language=target_language,
                )

            except Exception as exc:
                result = CrawlResult(
                    url=str(
                        url
                    ),
                    resolved_url=None,
                    html=None,
                    content_hash=None,
                    article_id=None,
                    document_id=None,
                    resources={
                        "css": [],
                        "images": [],
                    },
                    success=False,
                    error=str(
                        exc
                    ),
                )

            results.append(
                result
            )

        return results

    def crawl_search_results(
        self,
        search_results,
        keyword=None,
        target_language=None,
    ):
        """
        Crawl 一批 SearchResult。

        Pipeline：

            SearchResult[]
                    ↓
              CrawlService
                    ↓
              CrawlResult[]
                    │
                    ├──→ KeywordProcessor
                    │          ↓
                    │   KeywordLinkDetector
                    │          ↓
                    │      SQL articles.url
                    │          ↓
                    │   Related URLs
                    │          ↓
                    │   RelatedCrawlService
                    │
                    ├──→ RawHTMLRepository
                    │          ↓
                    │       MongoDB
                    │
                    └──→ ParserService
        """

        if search_results is None:
            return []

        results = []

        for search_result in search_results:
            try:
                result = (
                    self.crawl_result(
                        search_result,
                        keyword=keyword,
                        target_language=target_language,
                    )
                )

            except Exception as exc:
                url = getattr(
                    search_result,
                    "url",
                    "",
                )

                result = CrawlResult(
                    url=str(
                        url
                    ),
                    resolved_url=None,
                    html=None,
                    content_hash=None,
                    article_id=None,
                    document_id=None,
                    resources={
                        "css": [],
                        "images": [],
                    },
                    success=False,
                    error=str(
                        exc
                    ),
                )

            results.append(
                result
            )

        return results

    @staticmethod
    def normalize_url(
        url,
    ):
        """
        Normalize URL。

        目前只做：

            1. None Validation
            2. str Conversion
            3. strip()
        """

        if url is None:
            raise ValueError(
                "url cannot be None"
            )

        url = str(
            url
        ).strip()

        if not url:
            raise ValueError(
                "url cannot be empty"
            )

        return url

    @staticmethod
    def is_success(
        crawl_result,
    ):
        """
        判斷 Crawl 是否成功。
        """

        if not isinstance(
            crawl_result,
            CrawlResult,
        ):
            return False

        return (
            crawl_result.success
            and crawl_result.has_html
            and crawl_result.has_hash
        )

    @staticmethod
    def get_html(
        crawl_result,
    ):
        """
        從 CrawlResult 取得 Raw HTML。
        """

        if not isinstance(
            crawl_result,
            CrawlResult,
        ):
            raise TypeError(
                "crawl_result must be "
                "a CrawlResult"
            )

        if not crawl_result.success:
            raise ValueError(
                "crawl did not succeed"
            )

        if crawl_result.html is None:
            raise ValueError(
                "crawl result has no html"
            )

        return crawl_result.html

    @staticmethod
    def get_content_hash(
        crawl_result,
    ):
        """
        從 CrawlResult 取得 Content Hash。
        """

        if not isinstance(
            crawl_result,
            CrawlResult,
        ):
            raise TypeError(
                "crawl_result must be "
                "a CrawlResult"
            )

        if not crawl_result.success:
            raise ValueError(
                "crawl did not succeed"
            )

        if not crawl_result.content_hash:
            raise ValueError(
                "crawl result has no content_hash"
            )

        return crawl_result.content_hash

    @staticmethod
    def get_resources(
        crawl_result,
    ):
        """
        從 CrawlResult 取得 Resources。

        Returns：

            {
                "css": [],
                "images": []
            }
        """

        if not isinstance(
            crawl_result,
            CrawlResult,
        ):
            raise TypeError(
                "crawl_result must be "
                "a CrawlResult"
            )

        if not crawl_result.success:
            raise ValueError(
                "crawl did not succeed"
            )

        resources = (
            crawl_result.resources
        )

        if resources is None:
            return {
                "css": [],
                "images": [],
            }

        return resources


default_crawl_service = (
    CrawlService()
)


def crawl(
    url,
    keyword=None,
    target_language=None,
):
    """
    使用預設 CrawlService
    Crawl 單一 URL。

    Keyword 若存在：

        Raw HTML
            ↓
        KeywordProcessor
            ↓
        KeywordLinkDetector
            ↓
        RelatedCrawlService
            ↓
        原本 Crawl 流程
    """

    return (
        default_crawl_service.crawl(
            url,
            keyword=keyword,
            target_language=target_language,
        )
    )


def crawl_search_result(
    search_result,
    keyword=None,
    target_language=None,
):
    """
    使用預設 CrawlService
    Crawl 單一 SearchResult。
    """

    return (
        default_crawl_service
        .crawl_result(
            search_result,
            keyword=keyword,
            target_language=target_language,
        )
    )


def crawl_target(
    target,
    keyword=None,
    target_language=None,
):
    """
    使用預設 CrawlService
    Crawl Direct URL Target。
    """

    return (
        default_crawl_service
        .crawl_target(
            target,
            keyword=keyword,
            target_language=target_language,
        )
    )


__all__ = [
    "CrawlResult",
    "CrawlService",
    "default_crawl_service",
    "crawl",
    "crawl_search_result",
    "crawl_target",
]