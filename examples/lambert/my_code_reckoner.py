import asyncio


from metagpt.roles import (
    Architect,
    Engineer,
    ProductManager,
    ProjectManager,
    QaEngineer,
)
from metagpt.team import Team

async def startup(idea: str):
    company = Team()
    company.hire(
        [
            ProductManager(),
            Architect(),
            ProjectManager(),
            Engineer(),
            QaEngineer()
        ]
    )
    company.invest(investment=3.0)
    company.run_project(idea=idea)

    await company.run(n_round=5)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    asyncio.run(startup(idea="""
   write +&- Reckoner by java
    """))




# See PyCharm help at https://www.jetbrains.com/help/pycharm/