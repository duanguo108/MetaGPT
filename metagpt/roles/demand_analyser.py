from metagpt.roles import Role
from metagpt.actions import Topic_Summary,UserRequirement

from pydantic import BaseModel


class Report(BaseModel):
    topic: str
    links: dict[str, list[str]] = None
    summaries: list[tuple[str, str]] = None
    content: str = ""

class DemandAnalyser(Role):

    name: str = "Xidea-bot"
    profile: str = "Demand Analyser"
    goal: str = "demand analysis and demand summary"
    constraints: str = "Ensure accuracy and relevance of information"
    language: str = "en-us"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([Topic_Summary])
        # self._watch([UserRequirement])
