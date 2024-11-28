import unittest
import asyncio
import requests
from metagpt.actions import Action
from metagpt.logs import  logger
from pathlib import Path


REQUIREMENT_TEMPLATE: str =\
    """### Reference Information
{content}


### Requirements
Please provide a summary first, and then refine the requirements according to 1,2,3... enumerate,using the information provided above. The output must meet the following requirements:

- be formatted with Markdown syntax following APA style guidelines.
- According to the Reference Information, judge whether it is suitable to use the thinking mode of "5W1H". If it is suitable, please add the thinking result of "5W1H" to the end of the output as extended information
"""

REQUIREMENT_CHECK_TEMPLATE: str = \
    """### Reference Information
{content}
 
### format example
### 5W1H Check Result:
- Who: ...
- What: ...
- Where: ...
- When: ...
- Why: ...
- How: ...
 
 
### Requirements
Please extract the above information according to the 5W1H rule as 5W1H Check Result. If there is any missing part, please directly say that it is missing, and give a friendly and concise prompt at the end for the user to supplement the explanation.The output must meet the following requirements:
- be formatted with Markdown syntax following APA style guidelines.
- Format: output wrapped like format example, nothing else.
"""

# REQUIREMENT_CHECK_TEMPLATE_JSON: str = \
#     """### Reference Information
# {content}
#
# ### format example
# {
#     "Who":"...",
#     "What":"...",
#     "Where":"...",
#     "When":"...",
#     "Why":"...",
#     "How":"..."
# }
#
#
# ### Requirements
# Please extract the above information according to the 5W1H rule as 5W1H Check Result. If there is any missing part, please directly say that it is missing, and give a friendly and concise prompt at the end for the user to supplement the explanation.The output must meet the following requirements:
# - be formatted with JSON.
# - Format: output wrapped like format example, nothing else.
# """

class MyTest(unittest.TestCase):

    def test_ask(self):

        def append_to_file(filename, content):
            with open(filename, 'a', encoding='utf-8') as file:
                file.write(content + '\n\n')

        file_name = "Requirement AI Check Result-Test.md"
        file_path = Path(file_name)
        if file_path.exists():
            file_path.unlink()

        res = BackLog().get_backlogs_by_jql()
        descriptions = [(issue.get("key"), issue.get("fields").get("description")) for issue in res.get("issues")]
        for description in descriptions:
            content = description[1]
            llm = TestLLM()
            check_result = asyncio.run(llm.run(content))
            append_to_file(file_name,f"\n### {description[0]}")
            append_to_file(file_name,f"Original Requirements: \n\n{str(content)}")
            append_to_file(file_name,check_result)
            append_to_file(file_name,"---")




class TestLLM(Action):

    async def run(self, content: str) -> str:
        prompt = REQUIREMENT_CHECK_TEMPLATE.format(content=content)
        print(f"prompt:\n{prompt}")
        result = await self._aask(prompt)
        print('start:\n\n',result)
        return result

class BackLog():

    jira_url: str = "https://testjira.synnex.com"

    # def get_backlog(self,issue_keys:list):
    #     fields = "description"
    #     headers = {
    #         'Authorization': 'Basic aWhtczpzeW5uZXg=',
    #     }
    #     for issue in issue_keys:
    #         url = f"{BackLog.jira_url}/rest/api/2/issue/{issue}?fields={fields}"
    #         res = requests.request("GET", url, headers=headers)


    def get_backlogs_by_jql(self) -> list:

        jql = '''project = "LTDUSCIS" AND  summary !~ "*test*" AND created  > "2024-01-01" ORDER BY created  DESC'''
        maxResults = 1
        fields = "description"
        url = f"{BackLog.jira_url}/rest/api/2/search?jql={jql}&fields={fields}&maxResults={maxResults}"
        res = requests.request("GET", url, headers={'Authorization': 'Basic aWhtczpzeW5uZXg=',})
        if res.status_code >= 400:
            raise RuntimeError(f"Jira reply with code {res.status_code},error msg:{res.text}")

        return res.json()


    async def create_backlog(self, m: dict):
        description = '\n'.join(m["User Stories"])
        summary = m["Original Requirements"]
        backlog = {"fields": {
            "project": {
                "id": "10000"
            },
            "summary": summary,
            "issuetype": {
                "id": "10003"
            },
            "priority": {
                "id": "5"
            },
            "customfield_13000": {
                "name": "erik.liu@tdsynnex.com"
            },
            "customfield_13003": {
                "name": "erik.liu@tdsynnex.com"
            },
            "assignee": {
                "name": "lambert.duan@tdsynnex.com"
            },
            "customfield_12102": {
                "id": "11801",
                "child": {
                    "id": "12604"
                }
            },
            "customfield_14900": {
                "id": "15927"
            },
            "customfield_13607": {
                "id": "14142"
            },
            "description": description
        }}
        res = requests.post(
            f"{BackLog.jira_url}/rest/api/2/issue",
            json=backlog,
            headers={"Authorization": "Basic aWhtczpzeW5uZXg="},
            timeout=6000,
        )
        logger.info(f"Jira resp: {res.json()}")
        if res.status_code >= 400:
            logger.error(f"Jira reply with code {res.status_code},error msg:{res.text}")
        return res.json()
