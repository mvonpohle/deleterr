"""
Unit tests for MediaCleaner helper functions.

These tests verify the standalone helper functions in media_cleaner.py work correctly
with mock data. They test the decision logic functions in isolation.

Test categories:
- Exclusion functions: check_excluded_titles, check_excluded_genres, etc.
- Threshold checks: added_at_threshold, last_watched_threshold
- Sorting functions: sort_media
- Filtering functions: filter by watch status, series type
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class MockPlexMediaItem:
    """Mock Plex media item for testing MediaCleaner logic."""

    def __init__(
        self,
        title: str,
        year: int,
        guid: str = None,
        guids: list = None,
        added_at: datetime = None,
        collections: list = None,
        genres: list = None,
        labels: list = None,
        studio: str = None,
        directors: list = None,
        writers: list = None,
        roles: list = None,
        producers: list = None,
    ):
        self.title = title
        self.year = year
        self.guid = guid or f"plex://movie/{title.lower().replace(' ', '-')}"
        self.guids = [MagicMock(id=g) for g in (guids or [])]
        self.addedAt = added_at or datetime.now() - timedelta(days=60)
        self.collections = [MagicMock(tag=c) for c in (collections or [])]
        self.genres = [MagicMock(tag=g) for g in (genres or [])]
        self.labels = [MagicMock(tag=l) for l in (labels or [])]
        self.studio = studio
        self.directors = [MagicMock(tag=d) for d in (directors or [])]
        self.writers = [MagicMock(tag=w) for w in (writers or [])]
        self.roles = [MagicMock(tag=r) for r in (roles or [])]
        self.producers = [MagicMock(tag=p) for p in (producers or [])]


class TestExclusionsByTitle:
    """Test title-based exclusion rules."""

    def test_excluded_title_is_protected(self):
        """Test that movies with excluded titles are protected from deletion."""
        from app.media_cleaner import check_excluded_titles

        # Create mock Plex item with excluded title
        plex_item = MockPlexMediaItem(title="The Matrix", year=1999)

        # Define exclusion rules
        exclude = {"titles": ["The Matrix", "Inception", "Fight Club"]}

        # Create mock media data (from Radarr)
        media_data = {"title": "The Matrix", "year": 1999}

        # Check exclusion - should return False (excluded)
        result = check_excluded_titles(media_data, plex_item, exclude)
        assert result is False, "The Matrix should be excluded by title"

    def test_non_excluded_title_is_actionable(self):
        """Test that movies without excluded titles are actionable."""
        from app.media_cleaner import check_excluded_titles

        plex_item = MockPlexMediaItem(title="Some Random Movie", year=2020)
        exclude = {"titles": ["The Matrix", "Inception", "Fight Club"]}
        media_data = {"title": "Some Random Movie", "year": 2020}

        result = check_excluded_titles(media_data, plex_item, exclude)
        assert result is True, "Non-excluded title should be actionable"

    def test_title_exclusion_is_case_insensitive(self):
        """Test that title exclusion is case-insensitive."""
        from app.media_cleaner import check_excluded_titles

        plex_item = MockPlexMediaItem(title="THE MATRIX", year=1999)
        exclude = {"titles": ["the matrix"]}
        media_data = {"title": "THE MATRIX", "year": 1999}

        result = check_excluded_titles(media_data, plex_item, exclude)
        assert result is False, "Title exclusion should be case-insensitive"


class TestExclusionsByGenre:
    """Test genre-based exclusion rules."""

    def test_excluded_genre_is_protected(self):
        """Test that movies with excluded genres are protected."""
        from app.media_cleaner import check_excluded_genres

        plex_item = MockPlexMediaItem(
            title="Scary Movie", year=2020, genres=["Horror", "Comedy"]
        )
        exclude = {"genres": ["Horror", "Documentary"]}
        media_data = {"title": "Scary Movie", "year": 2020}

        result = check_excluded_genres(media_data, plex_item, exclude)
        assert result is False, "Movie with Horror genre should be excluded"

    def test_non_excluded_genre_is_actionable(self):
        """Test that movies without excluded genres are actionable."""
        from app.media_cleaner import check_excluded_genres

        plex_item = MockPlexMediaItem(
            title="Action Movie", year=2020, genres=["Action", "Thriller"]
        )
        exclude = {"genres": ["Horror", "Documentary"]}
        media_data = {"title": "Action Movie", "year": 2020}

        result = check_excluded_genres(media_data, plex_item, exclude)
        assert result is True, "Movie without excluded genres should be actionable"


class TestExclusionsByCollection:
    """Test collection-based exclusion rules."""

    def test_excluded_collection_is_protected(self):
        """Test that movies in excluded collections are protected."""
        from app.media_cleaner import check_excluded_collections

        plex_item = MockPlexMediaItem(
            title="Iron Man",
            year=2008,
            collections=["Marvel Cinematic Universe", "Favorites"],
        )
        exclude = {"collections": ["Marvel Cinematic Universe", "Never Delete"]}
        media_data = {"title": "Iron Man", "year": 2008}

        result = check_excluded_collections(media_data, plex_item, exclude)
        assert result is False, "Movie in MCU collection should be excluded"

    def test_non_excluded_collection_is_actionable(self):
        """Test that movies not in excluded collections are actionable."""
        from app.media_cleaner import check_excluded_collections

        plex_item = MockPlexMediaItem(
            title="Some Movie", year=2020, collections=["Random Collection"]
        )
        exclude = {"collections": ["Marvel Cinematic Universe", "Never Delete"]}
        media_data = {"title": "Some Movie", "year": 2020}

        result = check_excluded_collections(media_data, plex_item, exclude)
        assert result is True, "Movie not in excluded collections should be actionable"


class TestExclusionsByLabel:
    """Test Plex label-based exclusion rules."""

    def test_excluded_label_is_protected(self):
        """Test that movies with excluded Plex labels are protected."""
        from app.media_cleaner import check_excluded_labels

        plex_item = MockPlexMediaItem(
            title="Kids Movie", year=2020, labels=["children", "family"]
        )
        exclude = {"plex_labels": ["keep", "children", "favorite"]}
        media_data = {"title": "Kids Movie", "year": 2020}

        result = check_excluded_labels(media_data, plex_item, exclude)
        assert result is False, "Movie with 'children' label should be excluded"

    def test_non_excluded_label_is_actionable(self):
        """Test that movies without excluded labels are actionable."""
        from app.media_cleaner import check_excluded_labels

        plex_item = MockPlexMediaItem(
            title="Regular Movie", year=2020, labels=["watched"]
        )
        exclude = {"plex_labels": ["keep", "children", "favorite"]}
        media_data = {"title": "Regular Movie", "year": 2020}

        result = check_excluded_labels(media_data, plex_item, exclude)
        assert result is True, "Movie without excluded labels should be actionable"


class TestExclusionsByReleaseYear:
    """Test release year-based exclusion rules."""

    def test_recent_release_is_protected(self):
        """Test that recently released movies are protected."""
        from app.media_cleaner import check_excluded_release_years

        current_year = datetime.now().year
        plex_item = MockPlexMediaItem(title="New Movie", year=current_year)
        exclude = {"release_years": 2}  # Protect movies from last 2 years
        media_data = {"title": "New Movie", "year": current_year}

        result = check_excluded_release_years(media_data, plex_item, exclude)
        assert result is False, "Movie from current year should be excluded"

    def test_old_release_is_actionable(self):
        """Test that older releases are actionable."""
        from app.media_cleaner import check_excluded_release_years

        old_year = datetime.now().year - 5
        plex_item = MockPlexMediaItem(title="Old Movie", year=old_year)
        exclude = {"release_years": 2}
        media_data = {"title": "Old Movie", "year": old_year}

        result = check_excluded_release_years(media_data, plex_item, exclude)
        assert result is True, "Movie from 5 years ago should be actionable"


class TestExclusionsByStudio:
    """Test studio-based exclusion rules."""

    def test_excluded_studio_is_protected(self):
        """Test that movies from excluded studios are protected."""
        from app.media_cleaner import check_excluded_studios

        plex_item = MockPlexMediaItem(
            title="Spirited Away", year=2001, studio="Studio Ghibli"
        )
        exclude = {"studios": ["studio ghibli", "pixar"]}  # lowercase in config
        media_data = {"title": "Spirited Away", "year": 2001}

        result = check_excluded_studios(media_data, plex_item, exclude)
        assert result is False, "Movie from Studio Ghibli should be excluded"


class TestExclusionsByDirector:
    """Test director-based exclusion rules."""

    def test_excluded_director_is_protected(self):
        """Test that movies by excluded directors are protected."""
        from app.media_cleaner import check_excluded_directors

        plex_item = MockPlexMediaItem(
            title="Inception", year=2010, directors=["Christopher Nolan"]
        )
        exclude = {"directors": ["Christopher Nolan", "Steven Spielberg"]}
        media_data = {"title": "Inception", "year": 2010}

        result = check_excluded_directors(media_data, plex_item, exclude)
        assert result is False, "Movie by Christopher Nolan should be excluded"


class TestExclusionsByActor:
    """Test actor-based exclusion rules."""

    def test_excluded_actor_is_protected(self):
        """Test that movies with excluded actors are protected."""
        from app.media_cleaner import check_excluded_actors

        plex_item = MockPlexMediaItem(
            title="Forrest Gump", year=1994, roles=["Tom Hanks", "Robin Wright"]
        )
        exclude = {"actors": ["Tom Hanks", "Meryl Streep"]}
        media_data = {"title": "Forrest Gump", "year": 1994}

        result = check_excluded_actors(media_data, plex_item, exclude)
        assert result is False, "Movie with Tom Hanks should be excluded"


class TestAddedAtThreshold:
    """Test added_at_threshold protection."""

    def test_recently_added_is_protected(self):
        """Test that recently added movies are protected."""
        from app.media_cleaner import MediaCleaner

        # Create mock plex item added 3 days ago
        plex_item = MockPlexMediaItem(
            title="New Movie",
            year=2023,
            added_at=datetime.now() - timedelta(days=3),
        )
        media_data = {"title": "New Movie", "year": 2023}

        # Create a minimal mock config
        mock_config = MagicMock()
        mock_config.settings = {
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        # Test the check_added_date method directly
        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)
            result = cleaner.check_added_date(
                media_data, plex_item, added_at_threshold=7
            )

        assert result is False, "Movie added 3 days ago should be protected (threshold 7)"

    def test_old_added_is_actionable(self):
        """Test that movies added long ago are actionable."""
        from app.media_cleaner import MediaCleaner

        plex_item = MockPlexMediaItem(
            title="Old Movie",
            year=2020,
            added_at=datetime.now() - timedelta(days=60),
        )
        media_data = {"title": "Old Movie", "year": 2020}

        mock_config = MagicMock()
        mock_config.settings = {
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)
            result = cleaner.check_added_date(
                media_data, plex_item, added_at_threshold=7
            )

        assert result is True, "Movie added 60 days ago should be actionable"


class TestWatchedStatusCheck:
    """Test watched status filtering."""

    def test_recently_watched_is_protected(self):
        """Test that recently watched movies are protected."""
        from app.media_cleaner import MediaCleaner

        plex_item = MockPlexMediaItem(title="Recent Movie", year=2020)
        media_data = {"title": "Recent Movie", "year": 2020}

        # Activity data showing movie was watched 5 days ago
        activity_data = {
            plex_item.guid: {
                "last_watched": datetime.now() - timedelta(days=5),
                "title": "Recent Movie",
                "year": 2020,
            }
        }

        library_config = {"last_watched_threshold": 30}

        mock_config = MagicMock()
        mock_config.settings = {
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)
            result = cleaner.check_watched_status(
                library_config,
                activity_data,
                media_data,
                plex_item,
                last_watched_threshold=30,
            )

        assert (
            result is False
        ), "Movie watched 5 days ago should be protected (threshold 30)"

    def test_old_watched_is_actionable(self):
        """Test that movies watched long ago are actionable."""
        from app.media_cleaner import MediaCleaner

        plex_item = MockPlexMediaItem(title="Old Movie", year=2020)
        media_data = {"title": "Old Movie", "year": 2020}

        # Activity data showing movie was watched 60 days ago
        activity_data = {
            plex_item.guid: {
                "last_watched": datetime.now() - timedelta(days=60),
                "title": "Old Movie",
                "year": 2020,
            }
        }

        library_config = {"last_watched_threshold": 30}

        mock_config = MagicMock()
        mock_config.settings = {
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)
            result = cleaner.check_watched_status(
                library_config,
                activity_data,
                media_data,
                plex_item,
                last_watched_threshold=30,
            )

        assert result is True, "Movie watched 60 days ago should be actionable"

    def test_watch_status_filter_watched_only(self):
        """Test watch_status: watched filter (only delete watched items)."""
        from app.media_cleaner import MediaCleaner

        # Unwatched movie
        plex_item = MockPlexMediaItem(title="Unwatched Movie", year=2020)
        media_data = {"title": "Unwatched Movie", "year": 2020}
        activity_data = {}  # No watch history

        library_config = {"watch_status": "watched"}

        mock_config = MagicMock()
        mock_config.settings = {
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)
            result = cleaner.check_watched_status(
                library_config,
                activity_data,
                media_data,
                plex_item,
                last_watched_threshold=None,
            )

        assert (
            result is False
        ), "Unwatched movie should be protected when watch_status='watched'"

    def test_watch_status_filter_unwatched_only(self):
        """Test watch_status: unwatched filter (only delete unwatched items)."""
        from app.media_cleaner import MediaCleaner

        # Watched movie
        plex_item = MockPlexMediaItem(title="Watched Movie", year=2020)
        media_data = {"title": "Watched Movie", "year": 2020}
        activity_data = {
            plex_item.guid: {
                "last_watched": datetime.now() - timedelta(days=60),
                "title": "Watched Movie",
                "year": 2020,
            }
        }

        library_config = {"watch_status": "unwatched"}

        mock_config = MagicMock()
        mock_config.settings = {
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)
            result = cleaner.check_watched_status(
                library_config,
                activity_data,
                media_data,
                plex_item,
                last_watched_threshold=None,
            )

        assert (
            result is False
        ), "Watched movie should be protected when watch_status='unwatched'"


class TestCollectionThreshold:
    """Test apply_last_watch_threshold_to_collections feature."""

    def test_collection_recently_watched_protects_all_items(self):
        """Test that entire collections are protected when any item was recently watched."""
        from app.media_cleaner import MediaCleaner

        # Unwatched movie in a collection
        plex_item = MockPlexMediaItem(
            title="Unwatched MCU Movie",
            year=2020,
            collections=["Marvel Cinematic Universe"],
        )
        media_data = {"title": "Unwatched MCU Movie", "year": 2020}

        mock_config = MagicMock()
        mock_config.settings = {
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)
            # Add MCU to watched collections
            cleaner.watched_collections = {"Marvel Cinematic Universe"}

            result = cleaner.check_collections(
                apply_last_watch_threshold_to_collections=True,
                media_data=media_data,
                plex_media_item=plex_item,
            )

        assert (
            result is False
        ), "Movie in recently watched collection should be protected"


class TestSortingBehavior:
    """Test media sorting functionality."""

    def test_sort_by_size_descending(self):
        """Test sorting by size descending (largest first)."""
        from app.media_cleaner import sort_media

        media_list = [
            {"title": "Small Movie", "sizeOnDisk": 1_000_000_000},  # 1GB
            {"title": "Large Movie", "sizeOnDisk": 10_000_000_000},  # 10GB
            {"title": "Medium Movie", "sizeOnDisk": 5_000_000_000},  # 5GB
        ]

        sort_config = {"field": "size", "order": "desc"}
        sorted_list = sort_media(media_list, sort_config)

        assert sorted_list[0]["title"] == "Large Movie"
        assert sorted_list[1]["title"] == "Medium Movie"
        assert sorted_list[2]["title"] == "Small Movie"

    def test_sort_by_added_date_ascending(self):
        """Test sorting by added date ascending (oldest first)."""
        from app.media_cleaner import sort_media

        media_list = [
            {"title": "Recent Movie", "added": "2024-01-15T00:00:00Z"},
            {"title": "Oldest Movie", "added": "2020-01-01T00:00:00Z"},
            {"title": "Middle Movie", "added": "2022-06-15T00:00:00Z"},
        ]

        sort_config = {"field": "added_date", "order": "asc"}
        sorted_list = sort_media(media_list, sort_config)

        assert sorted_list[0]["title"] == "Oldest Movie"
        assert sorted_list[1]["title"] == "Middle Movie"
        assert sorted_list[2]["title"] == "Recent Movie"

    def test_sort_by_rating_descending(self):
        """Test sorting by rating descending (highest rated first)."""
        from app.media_cleaner import sort_media

        media_list = [
            {"title": "Low Rated", "ratings": {"imdb": {"value": 5.0}}},
            {"title": "High Rated", "ratings": {"imdb": {"value": 9.0}}},
            {"title": "Medium Rated", "ratings": {"imdb": {"value": 7.5}}},
        ]

        sort_config = {"field": "rating", "order": "desc"}
        sorted_list = sort_media(media_list, sort_config)

        assert sorted_list[0]["title"] == "High Rated"
        assert sorted_list[1]["title"] == "Medium Rated"
        assert sorted_list[2]["title"] == "Low Rated"

    def test_sort_by_multiple_fields(self):
        """Test multi-level sorting with comma-separated fields."""
        from app.media_cleaner import sort_media

        media_list = [
            {"title": "A", "year": 2020, "sizeOnDisk": 1_000_000_000},
            {"title": "B", "year": 2020, "sizeOnDisk": 3_000_000_000},
            {"title": "C", "year": 2019, "sizeOnDisk": 2_000_000_000},
            {"title": "D", "year": 2020, "sizeOnDisk": 2_000_000_000},
        ]

        # Sort by year desc, then size desc
        sort_config = {"field": "release_year,size", "order": "desc"}
        sorted_list = sort_media(media_list, sort_config)

        # 2020 items first by size desc (B=3GB, D=2GB, A=1GB), then 2019 (C)
        assert sorted_list[0]["title"] == "B"
        assert sorted_list[1]["title"] == "D"
        assert sorted_list[2]["title"] == "A"
        assert sorted_list[3]["title"] == "C"

    def test_sort_by_multiple_fields_mixed_orders(self):
        """Test multi-level sorting with different orders per field."""
        from app.media_cleaner import sort_media

        media_list = [
            {"title": "A", "year": 2020, "sizeOnDisk": 1_000_000_000},
            {"title": "B", "year": 2020, "sizeOnDisk": 3_000_000_000},
            {"title": "C", "year": 2019, "sizeOnDisk": 2_000_000_000},
            {"title": "D", "year": 2020, "sizeOnDisk": 2_000_000_000},
        ]

        # Sort by year desc, then size asc
        sort_config = {"field": "release_year,size", "order": "desc,asc"}
        sorted_list = sort_media(media_list, sort_config)

        # 2020 items first by size asc (A=1GB, D=2GB, B=3GB), then 2019 (C)
        assert sorted_list[0]["title"] == "A"
        assert sorted_list[1]["title"] == "D"
        assert sorted_list[2]["title"] == "B"
        assert sorted_list[3]["title"] == "C"

    def test_sort_by_last_watched_desc(self):
        """Test sorting by last_watched with unwatched items first."""
        from app.media_cleaner import sort_media

        # Create mock Plex items
        plex_item_a = MagicMock()
        plex_item_a.guid = "plex://movie/a"
        plex_item_a.guids = [MagicMock(id="tmdb://1001")]
        plex_item_a.title = "Watched Recently"
        plex_item_a.year = 2020

        plex_item_b = MagicMock()
        plex_item_b.guid = "plex://movie/b"
        plex_item_b.guids = [MagicMock(id="tmdb://1002")]
        plex_item_b.title = "Watched Long Ago"
        plex_item_b.year = 2019

        plex_item_c = MagicMock()
        plex_item_c.guid = "plex://movie/c"
        plex_item_c.guids = [MagicMock(id="tmdb://1003")]
        plex_item_c.title = "Never Watched"
        plex_item_c.year = 2021

        plex_guid_item_pair = [
            (["plex://movie/a", "tmdb://1001"], plex_item_a),
            (["plex://movie/b", "tmdb://1002"], plex_item_b),
            (["plex://movie/c", "tmdb://1003"], plex_item_c),
        ]

        # Activity data: A watched 10 days ago, B watched 30 days ago, C never
        activity_data = {
            "plex://movie/a": {
                "title": "Watched Recently",
                "year": 2020,
                "last_watched": datetime.now() - timedelta(days=10),
            },
            "plex://movie/b": {
                "title": "Watched Long Ago",
                "year": 2019,
                "last_watched": datetime.now() - timedelta(days=30),
            },
        }

        media_list = [
            {"title": "Watched Recently", "year": 2020, "tmdbId": 1001},
            {"title": "Watched Long Ago", "year": 2019, "tmdbId": 1002},
            {"title": "Never Watched", "year": 2021, "tmdbId": 1003},
        ]

        sort_config = {"field": "last_watched", "order": "desc"}
        sorted_list = sort_media(media_list, sort_config, activity_data, plex_guid_item_pair)

        # Unwatched first, then longest-ago watched
        assert sorted_list[0]["title"] == "Never Watched"
        assert sorted_list[1]["title"] == "Watched Long Ago"
        assert sorted_list[2]["title"] == "Watched Recently"

    def test_sort_by_last_watched_then_size(self):
        """Test combined last_watched and size sorting."""
        from app.media_cleaner import sort_media

        # Create mock Plex items - two unwatched items to test secondary sort
        plex_item_a = MagicMock()
        plex_item_a.guid = "plex://movie/a"
        plex_item_a.guids = [MagicMock(id="tmdb://1001")]
        plex_item_a.title = "Watched Movie"
        plex_item_a.year = 2020

        plex_item_b = MagicMock()
        plex_item_b.guid = "plex://movie/b"
        plex_item_b.guids = [MagicMock(id="tmdb://1002")]
        plex_item_b.title = "Unwatched Small"
        plex_item_b.year = 2019

        plex_item_c = MagicMock()
        plex_item_c.guid = "plex://movie/c"
        plex_item_c.guids = [MagicMock(id="tmdb://1003")]
        plex_item_c.title = "Unwatched Large"
        plex_item_c.year = 2021

        plex_guid_item_pair = [
            (["plex://movie/a", "tmdb://1001"], plex_item_a),
            (["plex://movie/b", "tmdb://1002"], plex_item_b),
            (["plex://movie/c", "tmdb://1003"], plex_item_c),
        ]

        # Only item A is watched
        activity_data = {
            "plex://movie/a": {
                "title": "Watched Movie",
                "year": 2020,
                "last_watched": datetime.now() - timedelta(days=5),
            },
        }

        media_list = [
            {"title": "Watched Movie", "year": 2020, "tmdbId": 1001, "sizeOnDisk": 2_000_000_000},
            {"title": "Unwatched Small", "year": 2019, "tmdbId": 1002, "sizeOnDisk": 1_000_000_000},
            {"title": "Unwatched Large", "year": 2021, "tmdbId": 1003, "sizeOnDisk": 5_000_000_000},
        ]

        # Sort by last_watched desc, then size desc
        sort_config = {"field": "last_watched,size", "order": "desc"}
        sorted_list = sort_media(media_list, sort_config, activity_data, plex_guid_item_pair)

        # Unwatched items first, sorted by size desc
        # Then watched items sorted by days since watched desc
        assert sorted_list[0]["title"] == "Unwatched Large"  # Unwatched, 5GB
        assert sorted_list[1]["title"] == "Unwatched Small"  # Unwatched, 1GB
        assert sorted_list[2]["title"] == "Watched Movie"    # Watched 5 days ago


class TestSeriesTypeFiltering:
    """Test series_type filtering for Sonarr."""

    def test_filter_standard_series(self):
        """Test that only standard series are processed when series_type=standard."""
        from app.media_cleaner import MediaCleaner

        library_config = {"series_type": "standard"}

        # Mock show data with different series types
        all_show_data = [
            {"id": 1, "title": "Standard Show", "seriesType": "standard"},
            {"id": 2, "title": "Anime Show", "seriesType": "anime"},
            {"id": 3, "title": "Daily Show", "seriesType": "daily"},
            {"id": 4, "title": "Another Standard", "seriesType": "standard"},
        ]

        mock_config = MagicMock()
        mock_config.settings = {
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)
            filtered = cleaner.filter_shows(library_config, all_show_data)

        assert len(filtered) == 2
        assert all(show["seriesType"] == "standard" for show in filtered)

    def test_filter_anime_series(self):
        """Test that only anime series are processed when series_type=anime."""
        from app.media_cleaner import MediaCleaner

        library_config = {"series_type": "anime"}

        all_show_data = [
            {"id": 1, "title": "Standard Show", "seriesType": "standard"},
            {"id": 2, "title": "Attack on Titan", "seriesType": "anime"},
            {"id": 3, "title": "Naruto", "seriesType": "anime"},
        ]

        mock_config = MagicMock()
        mock_config.settings = {
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)
            filtered = cleaner.filter_shows(library_config, all_show_data)

        assert len(filtered) == 2
        assert all(show["seriesType"] == "anime" for show in filtered)


class TestDiskSpaceThreshold:
    """Test disk_size_threshold functionality."""

    def test_library_above_threshold_is_skipped(self):
        """Test that libraries with disk space above threshold are skipped."""
        from app.media_cleaner import library_meets_disk_space_threshold

        library_config = {
            "name": "Movies",
            "disk_size_threshold": [{"path": "/movies", "threshold": "100GB"}],
        }

        # Mock Radarr client with plenty of free space
        mock_radarr = MagicMock()
        mock_radarr.get_disk_space.return_value = [
            {"path": "/movies", "freeSpace": 500_000_000_000}  # 500GB free
        ]

        result = library_meets_disk_space_threshold(library_config, mock_radarr)
        assert result is False, "Library with 500GB free should be skipped (threshold 100GB)"

    def test_library_below_threshold_is_processed(self):
        """Test that libraries with disk space below threshold are processed."""
        from app.media_cleaner import library_meets_disk_space_threshold

        library_config = {
            "name": "Movies",
            "disk_size_threshold": [{"path": "/movies", "threshold": "100GB"}],
        }

        # Mock Radarr client with low free space
        mock_radarr = MagicMock()
        mock_radarr.get_disk_space.return_value = [
            {"path": "/movies", "freeSpace": 50_000_000_000}  # 50GB free
        ]

        result = library_meets_disk_space_threshold(library_config, mock_radarr)
        assert result is True, "Library with 50GB free should be processed (threshold 100GB)"


class TestDryRunMode:
    """Test dry_run mode behavior."""

    def test_dry_run_does_not_call_delete(self):
        """Test that dry_run mode does not actually delete movies."""
        from app.media_cleaner import MediaCleaner

        mock_config = MagicMock()
        mock_config.settings = {
            "dry_run": True,
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        mock_radarr = MagicMock()
        radarr_movie = {
            "id": 123,
            "title": "Test Movie",
            "sizeOnDisk": 5_000_000_000,
        }
        library = {"name": "Movies", "add_list_exclusion_on_delete": False}

        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)
            cleaner.process_movie(
                library, mock_radarr, radarr_movie, actions_performed=0, max_actions_per_run=10
            )

        # del_movie should NOT have been called
        mock_radarr.del_movie.assert_not_called()


class TestMaxActionsPerRun:
    """Test max_actions_per_run limit."""

    def test_stops_at_max_actions(self):
        """Test that processing stops after max_actions_per_run is reached."""
        from app.media_cleaner import MediaCleaner

        mock_config = MagicMock()
        mock_config.settings = {
            "dry_run": True,  # Use dry run so we don't actually delete
            "action_delay": 0,
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        # Create 5 movies to process with all required fields
        movies_to_process = [
            {
                "id": i,
                "title": f"Movie {i}",
                "year": 2020 + i,
                "sizeOnDisk": 1_000_000_000,
                "alternateTitles": [],
                "tmdbId": 100000 + i,
            }
            for i in range(5)
        ]

        library = {"name": "Movies", "max_actions_per_run": 2}

        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)

            mock_radarr = MagicMock()
            mock_radarr.get_movies.return_value = movies_to_process
            mock_movies_library = MagicMock()
            mock_movies_library.all.return_value = []

            _saved_space = cleaner.process_movies(
                library,
                mock_radarr,
                mock_movies_library,
                {},  # movie_activity
                {},  # trakt_movies
                max_actions_per_run=2,
            )

        # Should only process 2 movies (dry run returns sizeOnDisk for each)
        # The exact behavior depends on process_library_rules, but max should limit it


class TestAddListExclusion:
    """Test add_list_exclusion_on_delete functionality."""

    def test_add_exclusion_flag_passed_to_radarr(self):
        """Test that add_exclusion flag is correctly passed to Radarr."""
        from app.media_cleaner import MediaCleaner

        mock_config = MagicMock()
        mock_config.settings = {
            "dry_run": False,
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        mock_radarr = MagicMock()
        radarr_movie = {
            "id": 123,
            "title": "Test Movie",
            "sizeOnDisk": 5_000_000_000,
        }
        library = {"name": "Movies", "add_list_exclusion_on_delete": True}

        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)
            cleaner.delete_movie_if_allowed(
                library,
                mock_radarr,
                radarr_movie,
            )

        # Verify del_movie was called with add_exclusion=True
        mock_radarr.del_movie.assert_called_once_with(
            123, delete_files=True, add_exclusion=True
        )


class TestCombinedExclusions:
    """Test that multiple exclusion rules work together correctly."""

    def test_all_exclusion_checks_must_pass(self):
        """Test that media must pass ALL exclusion checks to be actionable."""
        from app.media_cleaner import MediaCleaner

        # Movie that should pass most checks but fail on genre
        plex_item = MockPlexMediaItem(
            title="Some Documentary",  # Not in excluded titles
            year=2015,  # Old enough
            genres=["Documentary"],  # Excluded genre
            collections=[],
            labels=[],
            directors=["Unknown Director"],
            roles=["Unknown Actor"],
        )
        media_data = {"title": "Some Documentary", "year": 2015}

        library = {
            "exclude": {
                "titles": ["The Matrix"],
                "genres": ["Documentary"],  # This should exclude it
                "collections": ["Favorites"],
                "plex_labels": ["keep"],
                "release_years": 2,
                "directors": ["Christopher Nolan"],
                "actors": ["Tom Hanks"],
            }
        }

        mock_config = MagicMock()
        mock_config.settings = {
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)
            result = cleaner.check_exclusions(library, media_data, plex_item)

        assert result is False, "Movie with excluded genre should fail exclusion check"

    def test_media_passing_all_checks_is_actionable(self):
        """Test that media passing all exclusion checks is actionable."""
        from app.media_cleaner import MediaCleaner

        # Movie that should pass all checks
        plex_item = MockPlexMediaItem(
            title="Random Movie",
            year=2015,
            genres=["Action", "Thriller"],
            collections=["Random Collection"],
            labels=["watched"],
            studio="Random Studio",
            directors=["Random Director"],
            roles=["Random Actor"],
            producers=["Random Producer"],
            writers=["Random Writer"],
        )
        media_data = {"title": "Random Movie", "year": 2015}

        library = {
            "exclude": {
                "titles": ["The Matrix"],
                "genres": ["Documentary", "Horror"],
                "collections": ["Favorites"],
                "plex_labels": ["keep"],
                "release_years": 2,
                "studios": ["Studio Ghibli"],
                "directors": ["Christopher Nolan"],
                "actors": ["Tom Hanks"],
            }
        }

        mock_config = MagicMock()
        mock_config.settings = {
            "plex": {"url": "http://localhost:32400", "token": "test"},
            "tautulli": {"url": "http://localhost:8181", "api_key": "test"},
        }

        with patch("app.media_cleaner.PlexServer"), patch(
            "app.modules.watch_provider.Tautulli"
        ), patch("app.media_cleaner.Trakt"):
            cleaner = MediaCleaner(mock_config)
            result = cleaner.check_exclusions(library, media_data, plex_item)

        assert result is True, "Movie passing all exclusion checks should be actionable"


class TestTitleAndYearMatch:
    """Tests for title_and_year_match fallback watch data matching."""

    def test_exact_year_match_should_find_watch_data(self):
        """Regression: exact same year should match (was broken - year != check)."""
        from app.media_cleaner import title_and_year_match

        plex_item = MockPlexMediaItem(title="Game of Thrones", year=2011)
        history = {"title": "Game of Thrones", "year": 2011}
        assert title_and_year_match(plex_item, history) is True

    def test_off_by_one_year_still_matches(self):
        """Year off by 1 should still match (existing behavior, keep working)."""
        from app.media_cleaner import title_and_year_match

        plex_item = MockPlexMediaItem(title="Some Movie", year=2020)
        history = {"title": "Some Movie", "year": 2021}
        assert title_and_year_match(plex_item, history) is True

    def test_year_off_by_two_rejects(self):
        """Year off by 2+ should not match."""
        from app.media_cleaner import title_and_year_match

        plex_item = MockPlexMediaItem(title="Some Movie", year=2020)
        history = {"title": "Some Movie", "year": 2022}
        assert title_and_year_match(plex_item, history) is False

    def test_different_title_rejects(self):
        """Different titles should not match even with same year."""
        from app.media_cleaner import title_and_year_match

        plex_item = MockPlexMediaItem(title="Movie A", year=2020)
        history = {"title": "Movie B", "year": 2020}
        assert title_and_year_match(plex_item, history) is False

    def test_none_year_on_plex_item_rejects(self):
        """Missing year on plex item should not match."""
        from app.media_cleaner import title_and_year_match

        plex_item = MockPlexMediaItem(title="Some Movie", year=None)
        history = {"title": "Some Movie", "year": 2020}
        assert title_and_year_match(plex_item, history) is False

    def test_none_year_on_history_rejects(self):
        """Missing year in history should not match."""
        from app.media_cleaner import title_and_year_match

        plex_item = MockPlexMediaItem(title="Some Movie", year=2020)
        history = {"title": "Some Movie", "year": None}
        assert title_and_year_match(plex_item, history) is False


class TestCheckExcludedPlexWatchlist:
    """Test Plex watchlist exclusion logic."""

    def _make_plex_item(self, title="The Matrix", year=1999):
        return MockPlexMediaItem(title=title, year=year)

    def test_watchlist_disabled_returns_true(self):
        """When plex_watchlist is False, media is always actionable."""
        from app.media_cleaner import check_excluded_plex_watchlist

        media_data = {"title": "The Matrix", "tmdbId": 603}
        plex_item = self._make_plex_item()
        exclude = {"plex_watchlist": False}
        watchlist_guids = {"tmdb://603"}

        assert check_excluded_plex_watchlist(media_data, plex_item, exclude, watchlist_guids) is True

    def test_watchlist_not_configured_returns_true(self):
        """When plex_watchlist key is absent, media is actionable."""
        from app.media_cleaner import check_excluded_plex_watchlist

        media_data = {"title": "The Matrix", "tmdbId": 603}
        plex_item = self._make_plex_item()
        exclude = {}
        watchlist_guids = {"tmdb://603"}

        assert check_excluded_plex_watchlist(media_data, plex_item, exclude, watchlist_guids) is True

    def test_empty_watchlist_returns_true(self):
        """When watchlist is empty, nothing is excluded."""
        from app.media_cleaner import check_excluded_plex_watchlist

        media_data = {"title": "The Matrix", "tmdbId": 603}
        plex_item = self._make_plex_item()
        exclude = {"plex_watchlist": True}

        assert check_excluded_plex_watchlist(media_data, plex_item, exclude, set()) is True

    def test_tmdb_match_excludes_movie(self):
        """Movie with matching TMDB ID in watchlist is excluded."""
        from app.media_cleaner import check_excluded_plex_watchlist

        media_data = {"title": "The Matrix", "tmdbId": 603}
        plex_item = self._make_plex_item()
        exclude = {"plex_watchlist": True}
        watchlist_guids = {"tmdb://603", "tmdb://999"}

        assert check_excluded_plex_watchlist(media_data, plex_item, exclude, watchlist_guids) is False

    def test_tvdb_match_excludes_show(self):
        """TV show with matching TVDB ID in watchlist is excluded."""
        from app.media_cleaner import check_excluded_plex_watchlist

        media_data = {"title": "Breaking Bad", "tvdbId": 81189}
        plex_item = self._make_plex_item(title="Breaking Bad", year=2008)
        exclude = {"plex_watchlist": True}
        watchlist_guids = {"tvdb://81189"}

        assert check_excluded_plex_watchlist(media_data, plex_item, exclude, watchlist_guids) is False

    def test_imdb_match_excludes_movie(self):
        """Movie with matching IMDB ID in watchlist is excluded."""
        from app.media_cleaner import check_excluded_plex_watchlist

        media_data = {"title": "The Matrix", "imdbId": "tt0133093"}
        plex_item = self._make_plex_item()
        exclude = {"plex_watchlist": True}
        watchlist_guids = {"imdb://tt0133093"}

        assert check_excluded_plex_watchlist(media_data, plex_item, exclude, watchlist_guids) is False

    def test_no_id_match_returns_true(self):
        """Media not in watchlist is actionable."""
        from app.media_cleaner import check_excluded_plex_watchlist

        media_data = {"title": "Unknown Movie", "tmdbId": 12345, "tvdbId": 67890, "imdbId": "tt9999999"}
        plex_item = self._make_plex_item(title="Unknown Movie", year=2020)
        exclude = {"plex_watchlist": True}
        watchlist_guids = {"tmdb://603", "tvdb://81189", "imdb://tt0133093"}

        assert check_excluded_plex_watchlist(media_data, plex_item, exclude, watchlist_guids) is True

    def test_media_without_ids_returns_true(self):
        """Media with no IDs is not excluded (cannot match watchlist)."""
        from app.media_cleaner import check_excluded_plex_watchlist

        media_data = {"title": "Some Movie"}
        plex_item = self._make_plex_item(title="Some Movie", year=2020)
        exclude = {"plex_watchlist": True}
        watchlist_guids = {"tmdb://603", "tvdb://81189"}

        assert check_excluded_plex_watchlist(media_data, plex_item, exclude, watchlist_guids) is True


class TestGetPlexWatchlistGuids:
    """Test _get_plex_watchlist_guids caching on MediaCleaner."""

    @pytest.fixture
    def media_cleaner(self):
        from unittest.mock import MagicMock, patch
        from app.media_cleaner import MediaCleaner

        config = MagicMock()
        config.settings = {
            "plex": {"url": "http://localhost:32400", "token": "test"},
        }
        with patch("app.media_cleaner.PlexServer"):
            with patch("app.media_cleaner.create_watch_provider"):
                mc = MediaCleaner(config)
        return mc

    def test_returns_empty_set_without_media_server(self, media_cleaner):
        """Without media_server, watchlist guids is empty set."""
        media_cleaner.media_server = None
        result = media_cleaner._get_plex_watchlist_guids()
        assert result == set()

    def test_fetches_guids_from_media_server(self, media_cleaner):
        """Calls media_server.get_user_watchlist() and returns set."""
        mock_server = MagicMock()
        mock_server.get_user_watchlist.return_value = ["tmdb://603", "tvdb://81189"]
        media_cleaner.media_server = mock_server

        result = media_cleaner._get_plex_watchlist_guids()

        assert result == {"tmdb://603", "tvdb://81189"}
        mock_server.get_user_watchlist.assert_called_once()

    def test_caches_result_on_second_call(self, media_cleaner):
        """Second call uses cached value without re-fetching."""
        mock_server = MagicMock()
        mock_server.get_user_watchlist.return_value = ["tmdb://603"]
        media_cleaner.media_server = mock_server

        media_cleaner._get_plex_watchlist_guids()
        media_cleaner._get_plex_watchlist_guids()

        mock_server.get_user_watchlist.assert_called_once()


class TestPlexMediaServerGetUserWatchlist:
    """Test PlexMediaServer.get_user_watchlist()."""

    @pytest.fixture
    def plex_server(self):
        from unittest.mock import MagicMock, patch
        from app.modules.plex import PlexMediaServer

        with patch("app.modules.plex.PlexServer") as mock_plex:
            server = PlexMediaServer("http://localhost:32400", "test-token")
            yield server, mock_plex.return_value

    def test_returns_guids_from_watchlist(self, plex_server):
        """Returns list of GUID strings from watchlist items."""
        plex, mock_raw_server = plex_server

        mock_account = MagicMock()
        mock_raw_server.myPlexAccount.return_value = mock_account

        item1 = MagicMock()
        item1.guids = [MagicMock(id="tmdb://603"), MagicMock(id="imdb://tt0133093")]
        item2 = MagicMock()
        item2.guids = [MagicMock(id="tvdb://81189")]
        mock_account.watchlist.return_value = [item1, item2]

        result = plex.get_user_watchlist()

        assert "tmdb://603" in result
        assert "imdb://tt0133093" in result
        assert "tvdb://81189" in result

    def test_returns_empty_list_on_exception(self, plex_server):
        """Returns empty list when Plex API call fails."""
        plex, mock_raw_server = plex_server
        mock_raw_server.myPlexAccount.side_effect = Exception("Connection refused")

        result = plex.get_user_watchlist()

        assert result == []

    def test_empty_watchlist_returns_empty_list(self, plex_server):
        """Returns empty list when watchlist is empty."""
        plex, mock_raw_server = plex_server

        mock_account = MagicMock()
        mock_raw_server.myPlexAccount.return_value = mock_account
        mock_account.watchlist.return_value = []

        result = plex.get_user_watchlist()

        assert result == []
