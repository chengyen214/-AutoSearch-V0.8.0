"""
site_profile_repository.py

AutoSearch V7

R2.5 Site Profile MongoDB Repository

用途：

    負責 Site Profile 的 MongoDB Storage。

Architecture：

    SiteProfile
        |
        v
    SiteProfileRepository
        |
        v
    MongoConnection
        |
        v
    MongoDB

Storage：

    只保存最終 Best Strategy：

        HTML  → Best Strategy
        CSS   → Best Strategy
        Image → Best Strategy

    不保存：

        - Strategy Probe Result
        - Completeness
        - Content Size
        - Elapsed Time
        - Probe History

Site Profile Identity：

    site.base_url

例如：

    https://www.digitimes.com.tw/

同一來源網站的不同 URL：

    https://www.digitimes.com.tw/
    https://www.digitimes.com.tw/news/...
    https://www.digitimes.com.tw/research/...

都使用：

    https://www.digitimes.com.tw/

作為 Site Profile 查詢鍵。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from crawler.retrieval.site_profile import (
    SiteProfile,
)

from database.mongo_connection import (
    get_mongo_collection,
)


class SiteProfileRepository:
    """
    Site Profile MongoDB Repository。
    """

    COLLECTION_NAME = "site_profiles"

    def __init__(self) -> None:
        self.collection = get_mongo_collection(
            self.COLLECTION_NAME
        )

        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """
        建立 Site Profile MongoDB Index。

        base_url 是 Site Profile 唯一識別。
        """

        self.collection.create_index(
            "site.base_url",
            unique=True,
        )

    def find_by_base_url(
        self,
        base_url: str,
    ) -> Optional[Dict[str, Any]]:
        """
        依 Site Profile base_url 查詢。

        Parameters
        ----------
        base_url:
            來源網站共同 URL。

        Returns
        -------
        Optional[Dict[str, Any]]
            找到：
                MongoDB Document

            找不到：
                None
        """

        if not base_url:
            raise ValueError(
                "base_url cannot be empty."
            )

        return self.collection.find_one(
            {
                "site.base_url": base_url,
            }
        )

    def exists(
        self,
        base_url: str,
    ) -> bool:
        """
        判斷 Site Profile 是否存在。
        """

        if not base_url:
            raise ValueError(
                "base_url cannot be empty."
            )

        document = self.collection.find_one(
            {
                "site.base_url": base_url,
            },
            {
                "_id": 1,
            },
        )

        return document is not None

    def save(
        self,
        profile: SiteProfile,
    ) -> Dict[str, Any]:
        """
        建立新的 Site Profile。

        Parameters
        ----------
        profile:
            SiteProfile instance。

        Returns
        -------
        Dict[str, Any]
            MongoDB Document。

        Raises
        ------
        ValueError
            Site Profile 不完整。
        """

        document = self._profile_to_document(
            profile
        )

        self.collection.insert_one(
            document
        )

        return document

    def update(
        self,
        profile: SiteProfile,
    ) -> Optional[Dict[str, Any]]:
        """
        更新既有 Site Profile。

        只更新 Best Strategy 與 updated_at。

        created_at 不會被修改。
        """

        document = self._profile_to_document(
            profile
        )

        updated_at = datetime.now(
            timezone.utc
        )

        result = self.collection.find_one_and_update(
            {
                "site.base_url":
                    document["site"]["base_url"],
            },
            {
                "$set": {
                    "html.best_strategy":
                        document[
                            "html"
                        ][
                            "best_strategy"
                        ],
                    "css.best_strategy":
                        document[
                            "css"
                        ][
                            "best_strategy"
                        ],
                    "image.best_strategy":
                        document[
                            "image"
                        ][
                            "best_strategy"
                        ],
                    "updated_at":
                        updated_at,
                },
            },
            return_document=True,
        )

        return result

    def upsert(
        self,
        profile: SiteProfile,
    ) -> Dict[str, Any]:
        """
        建立或更新 Site Profile。

        base_url 不存在：
            建立新的 Site Profile。

        base_url 已存在：
            回傳既有 Site Profile。

        注意：

            這裡不重新執行 Probe。

            是否重新建立 Profile
            由 SiteProfileService 決定。
        """

        document = self._profile_to_document(
            profile
        )

        existing = self.find_by_base_url(
            document["site"]["base_url"]
        )

        if existing is not None:
            return existing

        now = datetime.now(
            timezone.utc
        )

        document["created_at"] = now
        document["updated_at"] = now

        self.collection.insert_one(
            document
        )

        return document

    @staticmethod
    def _profile_to_document(
        profile: SiteProfile,
    ) -> Dict[str, Any]:
        """
        將 SiteProfile 轉換成 MongoDB Document。

        只保存最終 Site Profile。

        不保存：

            - StrategyEvaluation
            - Probe Result
            - Probe Speed
            - Content Size
            - Completeness
        """

        if profile is None:
            raise ValueError(
                "profile cannot be None."
            )

        if profile.site is None:
            raise ValueError(
                "profile.site cannot be None."
            )

        if not profile.site.base_url:
            raise ValueError(
                "profile.site.base_url cannot be empty."
            )

        created_at = (
            profile.created_at
            or datetime.now(
                timezone.utc
            )
        )

        updated_at = (
            profile.updated_at
            or created_at
        )

        return {
            "site": {
                "hostname":
                    profile.site.hostname,
                "scheme":
                    profile.site.scheme,
                "base_url":
                    profile.site.base_url,
            },
            "html": {
                "best_strategy":
                    profile.html_best_strategy,
            },
            "css": {
                "best_strategy":
                    profile.css_best_strategy,
            },
            "image": {
                "best_strategy":
                    profile.image_best_strategy,
            },
            "created_at":
                created_at,
            "updated_at":
                updated_at,
        }


__all__ = [
    "SiteProfileRepository",
]