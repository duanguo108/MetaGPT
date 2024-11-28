#!/usr/bin/env python

from metagpt.roles.demand_analyser import DemandAnalyser
from metagpt.schema import Message

async def topic_summary(topic)-> Message | None:

    result = await DemandAnalyser().run(topic)

    return result


