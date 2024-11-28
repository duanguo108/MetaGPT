from metagpt.actions import Action
import requests
from metagpt.logs import logger
from typing import Optional

SUMMARIZE_PROMPT_5W1H: str =\
    """### Reference Information
{topic}


### Requirements
Please provide a summary first, and then refine the requirements according to 1,2,3... enumerate,using the information provided above. The output must meet the following requirements:

- be formatted with Markdown syntax following APA style guidelines.
- According to the Reference Information, judge whether it is suitable to use the thinking mode of "5W1H". If it is suitable, please add the thinking result of "5W1H" to the end of the output as extended information
"""

SUMMARIZE_PROMPT: str =\
    """### Reference Information
{topic}


### Requirements
Please provide a summary first, and then refine the requirements according to 1,2,3... enumerate,using the information provided above. The output must meet the following requirements:

- be formatted with Markdown syntax following APA style guidelines.
"""

class  Topic_Summary(Action):

    async def _aask(self, prompt: str, system_msgs: Optional[list[str]] = None) -> str:
        """Append default prefix"""
        return await self.llm.aask(prompt, system_msgs, stream=True)

    async def run(self, msg: str):
        # topic = Topic_MG().get_topic(msg[0].content)
        prompt = SUMMARIZE_PROMPT.format(topic=msg[0].content)
        rsp = await self._aask(prompt)
        return rsp

class Topic_MG():
    def get_topic(self,topic_id:str):
        res = requests.get(url=f"https://prmtask-uat.synnex.org:443/xidea/service/api/topic/{topic_id}",
                            headers={"apiKey": "lTcXIQFwMzbnmgqsa2xry2qi8dBzVgmFcK==",
                                     "x-email": "lambert.duan@tdsynnex.com"})

        if res.status_code >= 400 or res.json()["status"] >= 400:
            logger.error(f"Xidea reply with code {res.status_code},error msg:{res.text}")
            raise Exception(f"Xidea reply with code {res.status_code},error msg:{res.text}")

        return res.json()["data"]["topic"]["description"]


#         mock_topic = {
#             '24923': """
#         QGen Design tool and QR deploy process enhancement.
# The root reason is that our qgen design tool uat env is same as prod version. And our designer updated this qgen screen sql on uat env on January mistook, and QC could test it on uat normally, but uat data can’t sync to prod directly, on prod still as old version.
# And this qgen screen need do data maintain operations , QC can’t do post test on prod, only user with operation on prod.
# This time the new sql has been updated on prod already by QR-4787.
# We plan to do some enhancements to avoid this situation happen again:
# We will update our qgen design tool front client style , add flag or background color to distinguish UAT and Prod env.
# For QGen request deploy process, we will add validation when QC approve, compare the sha1 values between last prod version and current plan deploy version , if the sha1 value no change, will give alert message, QC will confirm with owner and designer why there isn’t any update between two version .
# (If with some special reason have to redeploy , need add comments on QGen request )
#         """,
#             '5724': """
#         Allow user to build user defined query condition(could be multiple options per page/per user) so that it could be re-used easily by user. User can name it as needed. We should keep the most recent 20 query history so that user can save any of them as permanent options for future used. Add a drop-down list besides the query button to display the query options, and once a query condition saved by user, it should be on the top of query history with bold font.
#         """,
#             '12': """
#             New feature about developing a to-do task feature.
#         """}
#
#         return mock_topic[topic_id]

    def update_topic(self):
        pass