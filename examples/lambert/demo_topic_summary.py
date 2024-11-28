#!/usr/bin/env python

import asyncio

from metagpt.roles.demand_analyser import DemandAnalyser
from metagpt.roles import ProductManager1 as ProductManager_Xidea
from metagpt.team import Team


'''
The enhanced query function allows users to save and reuse historical query conditions

Develop a new feature for a to-do list

'''

async def main():
    topic_id = "35879"

    company = Team()
    # company.env.context.config.project_name = "save_query"
    company.hire(
        [
            DemandAnalyser()
        ]
    )
    company.invest(investment=3.0)
    company.run_project(idea=topic_id)

    await company.run()


if __name__ == "__main__":
    asyncio.run(main())