import asyncio

from metagpt.roles.researcher import RESEARCH_PATH, Researcher
from metagpt.roles import ProductManager
from metagpt.config2 import Config
from metagpt.const import METAGPT_ROOT

from metagpt.team import Team

async def startup(idea: str):

    company = Team()
    company.hire(
        [
            ProductManager(),
            Researcher(language="en-us")
        ]
    )
    company.invest(investment=3.0)
    company.run_project(idea=idea)

    await company.run(n_round=5)


if __name__ == '__main__':
    asyncio.run(startup(idea="What are the differences between Oracle and MySQL?"))




