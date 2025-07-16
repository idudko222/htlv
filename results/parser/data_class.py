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
