import contextlib
from typing import Any, Dict, List, Optional, Union

from .enums import Platform, PlaylistKey
from .tier_estimates import TierEstimates

RANKS = (
    "Unranked",
    "Bronze I",
    "Bronze II",
    "Bronze III",
    "Silver I",
    "Silver II",
    "Silver III",
    "Gold I",
    "Gold II",
    "Gold III",
    "Platinum I",
    "Platinum II",
    "Platinum III",
    "Diamond I",
    "Diamond II",
    "Diamond III",
    "Champion I",
    "Champion II",
    "Champion III",
    "Grand Champion",
)
DIVISIONS = ("I", "II", "III", "IV")

__all__ = ("Playlist", "SeasonRewards", "Player")


class Playlist:
    """Playlist()
    Represents Rocket League playlist stats data.

    .. container:: operations

        ``str(x)``
            Returns playlist's rank string, e.g. "Champion I Div III"

    Attributes
    ----------
    key: `PlaylistKey` or `int`
        Playlist's key. Might be `int`, if that key
        is not within the ones recognised by the enumerator.
    tier: int
        Tier on this playlist.
    division: int
        Division on this playlist.
    mu: float
        Mu on this playlist.
    skill: int
        Skill rating on this playlist.
    sigma: float
        Sigma on this playlist.
    win_streak: int
        Win streak on this playlist.
    matches_played: int
        Amount of matches played on this playlist.
    tier_max: int
        Maximum tier that can be achieved on this playlist.
    breakdown: dict
        Playlist tier breakdown.
    tier_estimates: `TierEstimates`
        Tier estimates for this playlist.

    """

    __slots__ = (
        "key",
        "tier",
        "division",
        "mu",
        "skill",
        "sigma",
        "win_streak",
        "matches_played",
        "tier_max",
        "breakdown",
        "tier_estimates",
    )

    def __init__(
        self,
        *,
        breakdown: Optional[Dict[int, Dict[int, List[Union[float, int]]]]] = None,
        playlist_key: Union[PlaylistKey, int],
        data: Dict[str, Any],
    ):
        self.key = playlist_key
        self.tier: int = data.get("tier", 0)
        self.division: int = data.get("division", 0)
        self.mu: float = data.get("mu", 25)
        self.skill: int = data.get("skill", self.mu * 20 + 100)
        self.sigma: float = data.get("sigma", 8.333)
        self.win_streak: int = data.get("win_streak", 0)
        self.matches_played: int = data.get("matches_played", 0)
        self.tier_max: int = data.get("tier_max", 19)
        self.breakdown = breakdown if breakdown is not None else {}
        self.tier_estimates = TierEstimates(self)

    def __str__(self) -> str:
        try:
            if self.tier in {0, self.tier_max}:
                return RANKS[self.tier]
            return f"{RANKS[self.tier]} Div {DIVISIONS[self.division]}"
        except IndexError:
            return "Unknown"


class SeasonRewards:
    """SeasonRewards()
    Represents season rewards informations.

    Attributes
    ----------
    level: int
        Player's season reward level.
    wins: int
        Player's season reward wins.
    reward_ready: bool
        Tells if player can advance in season rewards.

    """

    __slots__ = ("level", "wins", "reward_ready")

    def __init__(self, *, highest_tier: int = 0, data: Dict[str, Any]) -> None:
        self.level: int = data.get("level", 0)
        if self.level is None:
            self.level = 0
        self.wins: int = data.get("wins", 0)
        if self.wins is None:
            self.wins = 0
        self.reward_ready: bool
        if self.level == 0 or self.level * 3 < highest_tier:
            self.reward_ready = True
        else:
            self.reward_ready = False


class Player:
    """Player()
    Represents Rocket League Player

    Attributes
    ----------
    platform: `Platform`
        Player's platform.
    user_name: str
        Player's username (display name)
    player_id: str
        Player's user ID, same as `user_name` except for Steam players.
    playlists: dict
        Dictionary mapping `PlaylistKey` with `Playlist`.
    tier_breakdown: dict
        Tier breakdown.
    highest_tier: int
        Highest tier of the player.
    season_rewards: `SeasonRewards`
        Season rewards info.

    """

    __slots__ = (
        "platform",
        "user_name",
        "player_id",
        "playlists",
        "tier_breakdown",
        "highest_tier",
        "season_rewards",
    )

    def __init__(
        self,
        *,
        tier_breakdown: Optional[
            Dict[int, Dict[int, Dict[int, List[Union[float, int]]]]]
        ] = None,
        platform: Platform,
        data: Dict[str, Any],
    ) -> None:
        self.platform = platform
        self.user_name: str = data.get("user_name", "")
        self.player_id: str = data.get("user_id", self.user_name)
        self.playlists: Dict[Union[PlaylistKey, int], Playlist] = {}
        player_skills = data.get("player_skills", [])
        self.tier_breakdown = tier_breakdown if tier_breakdown is not None else {}
        self._prepare_playlists(player_skills)
        self.highest_tier = max(
            (playlist.tier for playlist in self.playlists.values()), default=0
        )
        season_rewards = data.get("season_rewards", {})
        self.season_rewards = SeasonRewards(
            highest_tier=self.highest_tier, data=season_rewards
        )

    def get_playlist(self, playlist_key: PlaylistKey) -> Optional[Playlist]:
        """
        Get playlist for the player.

        Parameters
        ----------
        playlist_key: PlaylistKey
            `PlaylistKey` for playlist to get.

        Returns
        -------
        `Playlist`, optional
            Playlist object for provided playlist key.

        """
        return self.playlists.get(playlist_key)

    def add_playlist(self, playlist: Dict[str, Any]) -> None:
        playlist_key = playlist.pop("playlist")
        breakdown = self.tier_breakdown.get(playlist_key, {})
        with contextlib.suppress(ValueError):
            playlist_key = PlaylistKey(playlist_key)

        self.playlists[playlist_key] = Playlist(
            breakdown=breakdown, playlist_key=playlist_key, data=playlist
        )

    def _prepare_playlists(self, player_skills: List[Dict[str, Any]]) -> None:
        for playlist in player_skills:
            self.add_playlist(playlist)
