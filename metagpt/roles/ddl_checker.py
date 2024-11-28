from metagpt.roles import Role
from metagpt.actions import DDLCheck
from metagpt.schema import (
    Message,
)
from metagpt.logs import logger



class DDLChecker(Role):

    name: str = "lambert"
    profile: str = "DDLChecker"
    goal: str = "check DDL SQL"
    constraints: str = "Ensure accuracy and relevance of information"
    language: str = "en-us"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([DDLCheck])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo  # todo will be DDLCheck()

        msg = self.get_memories(k=1)[0]  # find the most recent messages
        code_text = await todo.run(msg.content)
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))

        return msg

