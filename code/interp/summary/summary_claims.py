from dataclasses import dataclass, field

@dataclass
class SummaryClaims:
    parseable: bool = True
    multiline: bool = False
    echo: str = ""
    locations: list = field(default_factory=list)
    inv_added: list = field(default_factory=list)
    inv_removed: list = field(default_factory=list)
    score_deltas: list = field(default_factory=list)
    obj_states: list = field(default_factory=list)
    failures: list = field(default_factory=list)
    others: list = field(default_factory=list)
