"""
site_profile_service.py

AutoSearch V7

R2 Site Profile Service

用途：

    提供 Site Profile 對外使用的主要入口。

輸入：

    任意 URL

流程：

    1. 建立 Site Identity
    2. 取得 base_url
    3. 查詢 MongoDB Site Profile
    4. 如果存在，直接回傳
    5. 如果不存在，建立新的 Site Profile
    6. 保存到 MongoDB
    7. 回傳 Site Profile

Site Profile Identity：

    site.base_url

例如：

    https://www.digitimes.com.tw/news/123
    https://www.digitimes.com.tw/research/456

都會轉換成：

    https://www.digitimes.com.tw/

因此會共用同一個 Site Profile。

Architecture：

    URL
        |
        v
    SiteProfileService
        |
        +--> SiteProfileRepository
        |
        +--> create_site_profile()
        |
        v
    SiteProfile
"""

from __future__ import annotations

from typing import Any, Dict

from crawler.retrieval.site_profile import (
    SiteProfile,
    build_site_identity,
    create_site_profile,
)

from crawler.retrieval.site_profile_repository import (
    SiteProfileRepository,
)


class SiteProfileService:
    """
    Site Profile Service。
    """

    def __init__(
        self,
        repository: SiteProfileRepository | None = None,
    ) -> None:
        self.repository = (
            repository
            or SiteProfileRepository()
        )

    def get_or_create(
        self,
        url: str,
    ) -> SiteProfile:
        """
        取得 Site Profile。

        如果 MongoDB 已經存在相同來源網站的
        Site Profile，直接回傳既有 Profile。

        如果不存在，建立新的 Site Profile，
        保存到 MongoDB 後回傳。

        Parameters
        ----------
        url:
            要查詢的 URL。

        Returns
        -------
        SiteProfile
            既有或新建立的 Site Profile。
        """

        if not url:
            raise ValueError(
                "url cannot be empty."
            )

        site = build_site_identity(
            url
        )

        document = (
            self.repository.find_by_base_url(
                site.base_url
            )
        )

        if document is not None:
            return self._document_to_profile(
                document
            )

        profile = create_site_profile(
            url
        )

        self.repository.save(
            profile
        )

        return profile

    @staticmethod
    def _document_to_profile(
        document: Dict[str, Any],
    ) -> SiteProfile:
        """
        將 MongoDB Document 還原成 SiteProfile。
        """

        site_data = document.get(
            "site",
            {}
        )

        html_data = document.get(
            "html",
            {}
        )

        css_data = document.get(
            "css",
            {}
        )

        image_data = document.get(
            "image",
            {}
        )

        site = build_site_identity(
            site_data.get(
                "base_url",
                ""
            )
        )

        return SiteProfile(
            site=site,
            html_best_strategy=(
                html_data.get(
                    "best_strategy"
                )
            ),
            css_best_strategy=(
                css_data.get(
                    "best_strategy"
                )
            ),
            image_best_strategy=(
                image_data.get(
                    "best_strategy"
                )
            ),
            created_at=document.get(
                "created_at"
            ),
            updated_at=document.get(
                "updated_at"
            ),
        )


__all__ = [
    "SiteProfileService",
]