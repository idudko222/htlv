from dataclasses import dataclass
from typing import Optional, List

@dataclass
class MatchScore:
    team_won: str
    team_lost: str
    score_won: str
    score_lost: str
    date: Optional[str]
    time: Optional[str]
    match_format: Optional[int] = None
    match_id: Optional[int] = None
    match_url: Optional[str] = None
    event_name: Optional[str] = None

@dataclass
class MapData:
    map_name: str
    score_team1: str
    score_team2: str
    winner: str

@dataclass
class PlayerStats:
    nickname: str
    full_name: Optional[str]
    country: str
    kills: int
    deaths: int
    adr: float
    kast: float
    rating: float
    team: str
    hltv_id: int

@dataclass
class MatchDetails:
    match_link: int
    maps: List[MapData]
    players_stats: List[PlayerStats]
