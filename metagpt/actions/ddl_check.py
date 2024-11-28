from metagpt.actions import Action

from typing import Optional, Union

class DDLCheck(Action):
    PROMPT_TEMPLATE: str = """
        请检查下面的sql语句，并根据sql语句的规范性打分0-100分
        检查基本规则：mysql标准 ，比重占比50%
        检查特殊规则：比重占比50%
        1、必须包含entry_id,这些字段
        2、It is not allowed hard code IP in SQL
         
        check sql as follow：
        {sql}
       """

    name: str = "DDL check"

    async def _aask(self, prompt: str, system_msgs: Optional[list[str]] = None) -> str:
        """Append default prefix"""
        return await self.llm.aask(prompt, system_msgs,stream = False)

    async def run(self, sql: str):
        prompt = self.PROMPT_TEMPLATE.format(sql=sql)
        rsp = await self._aask(prompt)
        return rsp

