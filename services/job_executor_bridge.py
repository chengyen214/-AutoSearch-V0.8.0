"""
services/job_executor_bridge.py

AutoSearch V5

V5.6.3

Job Executor Bridge

用途：

    將 V5.5 BatchExecutionService
    與 V5.6 Search / Crawl / Parser Integration Layer
    以及 Article Persistence Layer
    建立完整 Pipeline Bridge。

核心 Pipeline：

    Job
      ↓
    Target
      ↓
    TargetSourceService
      ↓
    SourceResolutionBridge
      ↓
    SearchExecutionBridge
      ↓
    SearchResult[]
      ↓
    CrawlService
      ↓
    ParserService
      ↓
    ArticleService
      ↓
    SQL / Archive / AI Task

R4.2：

    SearchResult[]
      ↓
    Crawler Concurrency
      ↓
    CrawlService

重要：

    單一 SearchResult Crawl / Parser / ArticleService 失敗：

        不應中斷整個 Search Pipeline。

    應：

        Failure
            ↓
        記錄失敗原因
            ↓
        continue
            ↓
        下一個 SearchResult

    Search Pipeline 最後會提供完整 Status Summary。
"""

from concurrent.futures import ThreadPoolExecutor

from config.settings import (
    CRAWLER_CONCURRENCY,
)

from services.target_source_service import (
    TargetSourceService,
)

from services.source_resolution_bridge import (
    SourceResolutionBridge,
)

from services.search_execution_bridge import (
    SearchExecutionBridge,
)

from services.crawl_service import (
    CrawlService,
)

from services.parser_service import (
    ParserService,
)

from services.article_service import (
    ArticleService,
)

from utils.logger import (
    logger,
)


class JobExecutorBridge:

    def __init__(
        self,
        target_source_service=None,
        source_resolution_bridge=None,
        search_execution_bridge=None,
        crawl_service=None,
        parser_service=None,
        article_service=None,
    ):

        if target_source_service is None:
            target_source_service = TargetSourceService()

        self.target_source_service = (
            target_source_service
        )

        if source_resolution_bridge is None:
            source_resolution_bridge = (
                SourceResolutionBridge()
            )

        self.source_resolution_bridge = (
            source_resolution_bridge
        )

        if search_execution_bridge is None:
            search_execution_bridge = (
                SearchExecutionBridge()
            )

        self.search_execution_bridge = (
            search_execution_bridge
        )

        if crawl_service is None:
            crawl_service = CrawlService()

        self.crawl_service = (
            crawl_service
        )

        if parser_service is None:
            parser_service = ParserService()

        self.parser_service = (
            parser_service
        )

        if article_service is None:
            article_service = ArticleService()

        self.article_service = (
            article_service
        )

        logger.info(
            "JobExecutorBridge initialized: "
            "Search -> Crawl -> Parser -> "
            "ArticleService"
        )

    def execute(
        self,
        job,
        target,
    ):

        self._validate_job(job)
        self._validate_target(target)

        source_definition = (
            self.target_source_service.resolve(
                target
            )
        )

        resolved_source = (
            self.source_resolution_bridge.resolve(
                source_definition
            )
        )

        context = {
            "job": job,
            "target": target,
            "source_definition":
                source_definition,
            "resolved_source":
                resolved_source,
            "search_results": [],
            "crawl_results": [],
            "parser_results": [],
            "article_results": [],
        }

        if self.source_resolution_bridge.is_direct_url(
            resolved_source
        ):

            return self._execute_direct_url_pipeline(
                target=target,
                context=context,
            )

        if self.source_resolution_bridge.is_search(
            resolved_source
        ):

            return self._execute_search_pipeline(
                target=target,
                resolved_source=resolved_source,
                context=context,
            )

        raise ValueError(
            "Resolved source is neither "
            "a direct URL nor a search source"
        )

    def _execute_direct_url_pipeline(
        self,
        target,
        context,
    ):

        try:

            crawl_result = (
                self.crawl_service.crawl_target(
                    target
                )
            )

        except Exception as e:

            logger.exception(
                "Direct URL crawl failed: "
                f"{e}"
            )

            context["crawl_results"] = [
                None
            ]

            context["article_results"] = [
                {
                    "article": None,
                    "article_id": None,
                    "status": "crawl_failed",
                    "archive_version": None,
                    "ai_task": None,
                    "error": str(e),
                }
            ]

            return context

        context["crawl_results"] = [
            crawl_result
        ]

        if crawl_result is None:

            logger.warning(
                "Direct URL crawl returned None: "
                "status=CRAWL_FAILED"
            )

            context["parser_results"] = []

            context["article_results"] = [
                {
                    "article": None,
                    "article_id": None,
                    "status": "crawl_failed",
                    "archive_version": None,
                    "ai_task": None,
                }
            ]

            return context

        keyword = self._get_keyword(target)

        try:

            parser_result = (
                self.parser_service
                .parse_crawl_result(
                    crawl_result,
                    keyword,
                )
            )

        except Exception as e:

            logger.exception(
                "Direct URL parser failed: "
                f"{e}"
            )

            context["parser_results"] = [
                None
            ]

            context["article_results"] = [
                {
                    "article": None,
                    "article_id": None,
                    "status": "parser_failed",
                    "archive_version": None,
                    "ai_task": None,
                    "error": str(e),
                }
            ]

            return context

        context["parser_results"] = [
            parser_result
        ]

        article_result = (
            self._persist_parser_result(
                parser_result=parser_result,
                crawl_result=crawl_result,
            )
        )

        context["article_results"] = [
            article_result
        ]

        logger.info(
            "Direct URL pipeline completed: "
            "Crawl -> Parser -> ArticleService"
        )

        return context

    def _execute_search_pipeline(
        self,
        target,
        resolved_source,
        context,
    ):

        search_results = (
            self.search_execution_bridge.execute(
                resolved_source
            )
        )

        if search_results is None:
            search_results = []

        search_results = list(
            search_results
        )

        context["search_results"] = (
            search_results
        )

        keyword = self._get_keyword(target)

        total = len(search_results)

        status_counts = {
            "success": 0,
            "updated": 0,
            "duplicate": 0,
            "crawl_failed": 0,
            "parser_failed": 0,
            "parser_result_invalid": 0,
            "html_missing": 0,
            "article_service_failed": 0,
            "other": 0,
        }

        crawl_results = self._crawl_search_results(
            search_results
        )

        parser_results = []
        article_results = []

        for index, search_result in enumerate(
            search_results,
            start=1,
        ):

            logger.info(
                "Processing SearchResult "
                f"{index}/{total}"
            )

            crawl_result = (
                crawl_results[index - 1]
            )

            if crawl_result is None:

                status_counts[
                    "crawl_failed"
                ] += 1

                logger.warning(
                    "SearchResult status: "
                    f"{index}/{total} | "
                    "CRAWL_FAILED | "
                    f"url={self._get_search_result_url(search_result)}"
                )

                parser_results.append(
                    None
                )

                article_results.append(
                    {
                        "article": None,
                        "article_id": None,
                        "status": "crawl_failed",
                        "archive_version": None,
                        "ai_task": None,
                        "search_result": search_result,
                    }
                )

                logger.info(
                    "SearchResult pipeline completed: "
                    f"{index}/{total} | "
                    "status=CRAWL_FAILED"
                )

                continue

            try:

                parser_result = (
                    self.parser_service
                    .parse_crawl_result(
                        crawl_result,
                        keyword,
                    )
                )

            except Exception as e:

                logger.exception(
                    "Parser failed for SearchResult "
                    f"{index}/{total}: "
                    f"{e}"
                )

                parser_result = None

            parser_results.append(
                parser_result
            )

            if parser_result is None:

                status_counts[
                    "parser_failed"
                ] += 1

                logger.warning(
                    "SearchResult status: "
                    f"{index}/{total} | "
                    "PARSER_FAILED | "
                    f"url={self._get_search_result_url(search_result)}"
                )

                article_results.append(
                    {
                        "article": None,
                        "article_id": None,
                        "status": "parser_failed",
                        "archive_version": None,
                        "ai_task": None,
                        "search_result": search_result,
                    }
                )

                logger.info(
                    "SearchResult pipeline completed: "
                    f"{index}/{total} | "
                    "status=PARSER_FAILED"
                )

                continue

            article_result = (
                self._persist_parser_result(
                    parser_result=parser_result,
                    crawl_result=crawl_result,
                )
            )

            article_results.append(
                article_result
            )

            status = self._normalize_article_status(
                article_result
            )

            if status in status_counts:

                status_counts[
                    status
                ] += 1

            else:

                status_counts[
                    "other"
                ] += 1

            article_id = None

            if isinstance(
                article_result,
                dict,
            ):

                article_id = (
                    article_result.get(
                        "article_id"
                    )
                )

            logger.info(
                "SearchResult status: "
                f"{index}/{total} | "
                f"{status.upper()} | "
                f"article_id={article_id} | "
                f"url={self._get_search_result_url(search_result)}"
            )

            logger.info(
                "SearchResult pipeline completed: "
                f"{index}/{total} | "
                f"status={status.upper()}"
            )

        context["crawl_results"] = (
            crawl_results
        )

        context["parser_results"] = (
            parser_results
        )

        context["article_results"] = (
            article_results
        )

        context["status_summary"] = (
            status_counts
        )

        logger.info(
            "Search Pipeline Result Summary: "
            f"total={len(search_results)}, "
            f"success={status_counts['success']}, "
            f"updated={status_counts['updated']}, "
            f"duplicate={status_counts['duplicate']}, "
            f"crawl_failed={status_counts['crawl_failed']}, "
            f"parser_failed={status_counts['parser_failed']}, "
            f"parser_result_invalid="
            f"{status_counts['parser_result_invalid']}, "
            f"html_missing={status_counts['html_missing']}, "
            f"article_service_failed="
            f"{status_counts['article_service_failed']}, "
            f"other={status_counts['other']}"
        )

        logger.info(
            "Search pipeline completed: "
            "Search -> Crawl -> Parser -> "
            "ArticleService"
        )

        return context

    def _crawl_search_results(
        self,
        search_results,
    ):

        total = len(search_results)

        if total == 0:
            return []

        concurrency = int(
            CRAWLER_CONCURRENCY
        )

        if concurrency < 1:
            concurrency = 1

        logger.info(
            "Crawler Concurrency: "
            f"{concurrency}"
        )

        if concurrency == 1:

            crawl_results = []

            for index, search_result in enumerate(
                search_results,
                start=1,
            ):

                crawl_results.append(
                    self._crawl_search_result(
                        search_result=search_result,
                        index=index,
                        total=total,
                    )
                )

            return crawl_results

        with ThreadPoolExecutor(
            max_workers=concurrency
        ) as executor:

            futures = [
                executor.submit(
                    self._crawl_search_result,
                    search_result,
                    index,
                    total,
                )
                for index, search_result in enumerate(
                    search_results,
                    start=1,
                )
            ]

            return [
                future.result()
                for future in futures
            ]

    def _crawl_search_result(
        self,
        search_result,
        index,
        total,
    ):

        logger.info(
            "Crawling SearchResult "
            f"{index}/{total} | "
            f"url={self._get_search_result_url(search_result)}"
        )

        try:

            crawl_result = (
                self.crawl_service
                .crawl_result(
                    search_result
                )
            )

            logger.info(
                "Crawl completed for SearchResult "
                f"{index}/{total} | "
                f"url={self._get_search_result_url(search_result)}"
            )

            return crawl_result

        except Exception as e:

            logger.exception(
                "Crawl failed for SearchResult "
                f"{index}/{total}: "
                f"{e}"
            )

            return None

    def _persist_parser_result(
        self,
        parser_result,
        crawl_result,
    ):

        article = self._extract_article(
            parser_result
        )

        if article is None:

            logger.warning(
                "Parser result does not contain "
                "an Article object"
            )

            return {
                "article": None,
                "article_id": None,
                "status": "parser_result_invalid",
                "archive_version": None,
                "ai_task": None,
            }

        html = self._extract_html(
            crawl_result
        )

        if html is None:

            logger.warning(
                "Crawl result does not contain "
                "raw HTML"
            )

            return {
                "article": article,
                "article_id": None,
                "status": "html_missing",
                "archive_version": None,
                "ai_task": None,
            }

        try:

            result = (
                self.article_service.create(
                    article=article,
                    html=html,
                )
            )

            if result is None:

                logger.error(
                    "ArticleService.create "
                    "returned None"
                )

                return {
                    "article": article,
                    "article_id": None,
                    "status": "article_service_failed",
                    "archive_version": None,
                    "ai_task": None,
                }

            logger.info(
                "Article persisted through "
                "ArticleService: "
                f"status={result.get('status')}"
                if isinstance(result, dict)
                else
                "Article persisted through "
                "ArticleService"
            )

            return result

        except Exception as e:

            logger.exception(
                "ArticleService persistence error: "
                f"{e}"
            )

            return {
                "article": article,
                "article_id": None,
                "status": "article_service_failed",
                "archive_version": None,
                "ai_task": None,
                "error": str(e),
            }

    @staticmethod
    def _normalize_article_status(
        article_result,
    ):

        if not isinstance(
            article_result,
            dict,
        ):

            return "other"

        status = article_result.get(
            "status"
        )

        if status is None:
            return "other"

        status = str(
            status
        ).strip().lower()

        if status in (
            "created",
            "success",
            "inserted",
            "new",
        ):

            return "success"

        if status in (
            "updated",
            "update",
        ):

            return "updated"

        if status in (
            "duplicate",
            "duplicated",
            "archive_duplicate",
        ):

            return "duplicate"

        if status in (
            "crawl_failed",
        ):

            return "crawl_failed"

        if status in (
            "parser_failed",
        ):

            return "parser_failed"

        if status in (
            "parser_result_invalid",
        ):

            return "parser_result_invalid"

        if status in (
            "html_missing",
        ):

            return "html_missing"

        if status in (
            "article_service_failed",
        ):

            return "article_service_failed"

        return "other"

    @staticmethod
    def _get_search_result_url(
        search_result,
    ):

        if search_result is None:
            return None

        if isinstance(
            search_result,
            dict,
        ):

            for key in (
                "url",
                "resolved_url",
                "link",
            ):

                value = search_result.get(
                    key
                )

                if value:
                    return str(
                        value
                    )

            return None

        for attribute in (
            "url",
            "resolved_url",
            "link",
        ):

            if hasattr(
                search_result,
                attribute,
            ):

                value = getattr(
                    search_result,
                    attribute,
                    None,
                )

                if value:
                    return str(
                        value
                    )

        return None

    def execute_search_and_crawl(
        self,
        target,
        max_results=None,
    ):

        self._validate_target(target)

        search_results = (
            self.execute_search(
                target,
                max_results=max_results,
            )
        )

        if search_results is None:
            search_results = []

        search_results = list(
            search_results
        )

        keyword = self._get_keyword(target)

        crawl_results = self._crawl_search_results(
            search_results
        )

        parser_results = []
        article_results = []

        status_counts = {
            "success": 0,
            "updated": 0,
            "duplicate": 0,
            "crawl_failed": 0,
            "parser_failed": 0,
            "parser_result_invalid": 0,
            "html_missing": 0,
            "article_service_failed": 0,
            "other": 0,
        }

        total = len(search_results)

        for index, search_result in enumerate(
            search_results,
            start=1,
        ):

            logger.info(
                "execute_search_and_crawl: "
                f"processing {index}/{total}"
            )

            crawl_result = (
                crawl_results[index - 1]
            )

            if crawl_result is None:

                status_counts[
                    "crawl_failed"
                ] += 1

                logger.warning(
                    "execute_search_and_crawl: "
                    f"status=CRAWL_FAILED "
                    f"{index}/{total} | "
                    f"url={self._get_search_result_url(search_result)}"
                )

                parser_results.append(
                    None
                )

                article_results.append(
                    {
                        "article": None,
                        "article_id": None,
                        "status": "crawl_failed",
                        "archive_version": None,
                        "ai_task": None,
                        "search_result": search_result,
                    }
                )

                continue

            try:

                parser_result = (
                    self.parser_service
                    .parse_crawl_result(
                        crawl_result,
                        keyword,
                    )
                )

            except Exception as e:

                logger.exception(
                    "execute_search_and_crawl parser failed: "
                    f"{e}"
                )

                parser_result = None

            parser_results.append(
                parser_result
            )

            if parser_result is None:

                status_counts[
                    "parser_failed"
                ] += 1

                logger.warning(
                    "execute_search_and_crawl: "
                    f"status=PARSER_FAILED "
                    f"{index}/{total} | "
                    f"url={self._get_search_result_url(search_result)}"
                )

                article_results.append(
                    {
                        "article": None,
                        "article_id": None,
                        "status": "parser_failed",
                        "archive_version": None,
                        "ai_task": None,
                        "search_result": search_result,
                    }
                )

                continue

            article_result = (
                self._persist_parser_result(
                    parser_result=parser_result,
                    crawl_result=crawl_result,
                )
            )

            article_results.append(
                article_result
            )

            status = self._normalize_article_status(
                article_result
            )

            if status in status_counts:

                status_counts[
                    status
                ] += 1

            else:

                status_counts[
                    "other"
                ] += 1

            logger.info(
                "execute_search_and_crawl: "
                f"status={status.upper()} "
                f"{index}/{total} | "
                f"url={self._get_search_result_url(search_result)}"
            )

        logger.info(
            "execute_search_and_crawl Summary: "
            f"total={len(search_results)}, "
            f"success={status_counts['success']}, "
            f"updated={status_counts['updated']}, "
            f"duplicate={status_counts['duplicate']}, "
            f"crawl_failed={status_counts['crawl_failed']}, "
            f"parser_failed={status_counts['parser_failed']}, "
            f"parser_result_invalid="
            f"{status_counts['parser_result_invalid']}, "
            f"html_missing={status_counts['html_missing']}, "
            f"article_service_failed="
            f"{status_counts['article_service_failed']}, "
            f"other={status_counts['other']}"
        )

        return {
            "search_results":
                search_results,
            "crawl_results":
                crawl_results,
            "parser_results":
                parser_results,
            "article_results":
                article_results,
            "status_summary":
                status_counts,
        }

    def execute_crawl(
        self,
        target,
    ):

        self._validate_target(target)

        if not self.is_direct_url(target):

            raise ValueError(
                "Target is not a direct URL target"
            )

        try:

            crawl_result = (
                self.crawl_service.crawl_target(
                    target
                )
            )

        except Exception as e:

            logger.exception(
                "Direct crawl failed: "
                f"{e}"
            )

            return {
                "crawl_result": None,
                "parser_result": None,
                "article_result": {
                    "article": None,
                    "article_id": None,
                    "status": "crawl_failed",
                    "archive_version": None,
                    "ai_task": None,
                    "error": str(e),
                },
            }

        if crawl_result is None:

            logger.warning(
                "Direct crawl returned None."
            )

            return {
                "crawl_result": None,
                "parser_result": None,
                "article_result": {
                    "article": None,
                    "article_id": None,
                    "status": "crawl_failed",
                    "archive_version": None,
                    "ai_task": None,
                },
            }

        try:

            parser_result = (
                self.parser_service
                .parse_crawl_result(
                    crawl_result,
                    self._get_keyword(target),
                )
            )

        except Exception as e:

            logger.exception(
                "Direct crawl parser failed: "
                f"{e}"
            )

            return {
                "crawl_result": crawl_result,
                "parser_result": None,
                "article_result": {
                    "article": None,
                    "article_id": None,
                    "status": "parser_failed",
                    "archive_version": None,
                    "ai_task": None,
                    "error": str(e),
                },
            }

        article_result = (
            self._persist_parser_result(
                parser_result=parser_result,
                crawl_result=crawl_result,
            )
        )

        return {
            "crawl_result":
                crawl_result,
            "parser_result":
                parser_result,
            "article_result":
                article_result,
        }

    @staticmethod
    def _extract_article(
        parser_result,
    ):

        if parser_result is None:
            return None

        if isinstance(
            parser_result,
            dict,
        ):

            for key in (
                "article",
                "parsed_article",
                "result",
            ):

                value = parser_result.get(key)

                if value is not None:
                    return value

            if "document_id" in parser_result:
                return parser_result

            return None

        for attribute in (
            "article",
            "parsed_article",
            "result",
        ):

            if hasattr(
                parser_result,
                attribute,
            ):

                value = getattr(
                    parser_result,
                    attribute,
                    None,
                )

                if value is not None:
                    return value

        if hasattr(
            parser_result,
            "document_id",
        ):

            return parser_result

        return None

    @staticmethod
    def _extract_html(
        crawl_result,
    ):

        if crawl_result is None:
            return None

        if isinstance(
            crawl_result,
            dict,
        ):

            for key in (
                "html",
                "raw_html",
                "content",
            ):

                value = crawl_result.get(key)

                if value is not None:
                    return value

            return None

        for attribute in (
            "html",
            "raw_html",
            "content",
        ):

            if hasattr(
                crawl_result,
                attribute,
            ):

                value = getattr(
                    crawl_result,
                    attribute,
                    None,
                )

                if value is not None:
                    return value

        return None

    def resolve_source(
        self,
        target,
    ):

        self._validate_target(target)

        return (
            self.target_source_service.resolve(
                target
            )
        )

    def resolve_resolved_source(
        self,
        target,
    ):

        self._validate_target(target)

        source_definition = (
            self.target_source_service.resolve(
                target
            )
        )

        return (
            self.source_resolution_bridge.resolve(
                source_definition
            )
        )

    def resolve_source_definition(
        self,
        source_definition,
    ):

        return (
            self.source_resolution_bridge.resolve(
                source_definition
            )
        )

    def execute_search(
        self,
        target,
        max_results=None,
    ):

        self._validate_target(target)

        resolved_source = (
            self.resolve_resolved_source(
                target
            )
        )

        if not self.source_resolution_bridge.is_search(
            resolved_source
        ):

            raise ValueError(
                "Target does not resolve "
                "to a search source"
            )

        return (
            self.search_execution_bridge.execute(
                resolved_source,
                max_results=max_results,
            )
        )

    def is_direct_url(
        self,
        target,
    ):

        self._validate_target(target)

        source_definition = (
            self.target_source_service.resolve(
                target
            )
        )

        return (
            self.source_resolution_bridge
            .is_direct_url(
                source_definition
            )
        )

    def is_search(
        self,
        target,
    ):

        self._validate_target(target)

        source_definition = (
            self.target_source_service.resolve(
                target
            )
        )

        return (
            self.source_resolution_bridge
            .is_search(
                source_definition
            )
        )

    def get_provider(
        self,
        target,
    ):

        self._validate_target(target)

        return (
            self.target_source_service
            .get_provider(
                target
            )
        )

    def get_resolved_provider(
        self,
        target,
    ):

        resolved_source = (
            self.resolve_resolved_source(
                target
            )
        )

        if not self.source_resolution_bridge.is_search(
            resolved_source
        ):

            raise ValueError(
                "Target does not resolve "
                "to a search source"
            )

        return (
            self.source_resolution_bridge
            .get_provider(
                resolved_source
            )
        )

    def get_resolved_adapter(
        self,
        target,
    ):

        resolved_source = (
            self.resolve_resolved_source(
                target
            )
        )

        if not self.source_resolution_bridge.is_search(
            resolved_source
        ):

            raise ValueError(
                "Target does not resolve "
                "to a search source"
            )

        return (
            self.source_resolution_bridge
            .get_adapter(
                resolved_source
            )
        )

    def get_resolved_search_source(
        self,
        target,
    ):

        resolved_source = (
            self.resolve_resolved_source(
                target
            )
        )

        if not self.source_resolution_bridge.is_search(
            resolved_source
        ):

            raise ValueError(
                "Target does not resolve "
                "to a search source"
            )

        return (
            self.source_resolution_bridge
            .get_search_source(
                resolved_source
            )
        )

    def is_supported_provider(
        self,
        provider,
    ):

        return (
            self.source_resolution_bridge
            .is_supported_provider(
                provider
            )
        )

    @staticmethod
    def _get_keyword(
        target,
    ):

        if hasattr(
            target,
            "keyword",
        ):

            keyword = getattr(
                target,
                "keyword",
            )

            if keyword is not None:

                keyword = str(
                    keyword
                ).strip()

                if keyword:
                    return keyword

        if isinstance(
            target,
            dict,
        ):

            keyword = target.get(
                "keyword"
            )

            if keyword is not None:

                keyword = str(
                    keyword
                ).strip()

                if keyword:
                    return keyword

        raise ValueError(
            "target must contain a non-empty keyword"
        )

    @staticmethod
    def _validate_target(
        target,
    ):

        if target is None:

            raise ValueError(
                "target cannot be None"
            )

        return True

    @staticmethod
    def _validate_job(
        job,
    ):

        if job is None:

            raise ValueError(
                "job cannot be None"
            )

        if not hasattr(
            job,
            "id",
        ):

            raise ValueError(
                "job must have id"
            )

        if job.id is None:

            raise ValueError(
                "job.id cannot be None"
            )

        return True


default_job_executor_bridge = (
    JobExecutorBridge()
)


def execute_job(
    job,
    target,
):

    return (
        default_job_executor_bridge.execute(
            job,
            target,
        )
    )


__all__ = [
    "JobExecutorBridge",
    "default_job_executor_bridge",
    "execute_job",
]