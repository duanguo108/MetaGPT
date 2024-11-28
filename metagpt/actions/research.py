#!/usr/bin/env python

from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional, Union

from pydantic import TypeAdapter, model_validator

from metagpt.actions import Action
from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.tools.search_engine import SearchEngine
from metagpt.tools.web_browser_engine import WebBrowserEngine
from metagpt.utils.common import OutputParser
from metagpt.utils.text import generate_prompt_chunk, reduce_message_length

LANG_PROMPT = "Please respond in {language}."

RESEARCH_BASE_SYSTEM = """You are an AI critical thinker research assistant. Your sole purpose is to write well \
written, critically acclaimed, objective and structured reports on the given text."""

RESEARCH_TOPIC_SYSTEM = "You are an AI researcher assistant, and your research topic is:\n#TOPIC#\n{topic}"

SEARCH_TOPIC_PROMPT = """Please provide up to 2 necessary keywords related to your research topic for Google search. \
Your response must be in JSON format, for example: ["keyword1", "keyword2"]."""

SUMMARIZE_SEARCH_PROMPT = """### Requirements
1. The keywords related to your research topic and the search results are shown in the "Search Result Information" section.
2. Provide up to {decomposition_nums} queries related to your research topic base on the search results.
3. Please respond in the following JSON format: ["query1", "query2", "query3", ...].

### Search Result Information
{search_results}
"""

COLLECT_AND_RANKURLS_PROMPT = """### Topic
{topic}
### Query
{query}

### The online search results
{results}

### Requirements
Please remove irrelevant search results that are not related to the query or topic. Then, sort the remaining search results \
based on the link credibility. If two results have equal credibility, prioritize them based on the relevance. Provide the
ranked results' indices in JSON format, like [0, 1, 3, 4, ...], without including other words.
"""

WEB_BROWSE_AND_SUMMARIZE_PROMPT = """### Requirements
1. Utilize the text in the "Reference Information" section to respond to the question "{query}".
2. If the question cannot be directly answered using the text, but the text is related to the research topic, please provide \
a comprehensive summary of the text.
3. If the text is entirely unrelated to the research topic, please reply with a simple text "Not relevant."
4. Include all relevant factual information, numbers, statistics, etc., if available.

### Reference Information
{content}
"""


CONDUCT_RESEARCH_PROMPT = """### Reference Information
{content}

### Requirements
Please provide a detailed research report in response to the following topic: "{topic}", using the information provided \
above. The report must meet the following requirements:

- Focus on directly addressing the chosen topic.
- Ensure a well-structured and in-depth presentation, incorporating relevant facts and figures where available.
- Present data and findings in an intuitive manner, utilizing feature comparative tables, if applicable.
- The report should have a minimum word count of 2,000 and be formatted with Markdown syntax following APA style guidelines.
- Include all source URLs in APA format at the end of the report.
"""


class CollectLinks(Action):
    """Action class to collect links from a search engine."""

    name: str = "CollectLinks"
    i_context: Optional[str] = None
    desc: str = "Collect links from a search engine."
    search_func: Optional[Any] = None
    search_engine: Optional[SearchEngine] = None
    rank_func: Optional[Callable[[list[str]], None]] = None

    @model_validator(mode="after")
    def validate_engine_and_run_func(self):
        if self.search_engine is None:
            self.search_engine = SearchEngine.from_search_config(self.config.search, proxy=self.config.proxy)
        return self

    async def run(
        self,
        topic: str,
        decomposition_nums: int = 4,
        url_per_query: int = 4,
        system_text: str | None = None,
    ) -> dict[str, list[str]]:
        """Run the action to collect links.

        Args:
            topic: The research topic.
            decomposition_nums: The number of search questions to generate.
            url_per_query: The number of URLs to collect per search question.
            system_text: The system text.

        Returns:
            A dictionary containing the search questions as keys and the collected URLs as values.
        """
        system_text = system_text if system_text else RESEARCH_TOPIC_SYSTEM.format(topic=topic)
        keywords = await self._aask(SEARCH_TOPIC_PROMPT, [system_text])
        try:
            keywords = OutputParser.extract_struct(keywords, list)
            keywords = TypeAdapter(list[str]).validate_python(keywords)
        except Exception as e:
            logger.exception(f"fail to get keywords related to the research topic '{topic}' for {e}")
            keywords = [topic]
        results = await asyncio.gather(*(self.search_engine.run(i, as_string=False) for i in keywords))

        def gen_msg():
            while True:
                search_results = "\n".join(
                    f"#### Keyword: {i}\n Search Result: {j}\n" for (i, j) in zip(keywords, results)
                )
                prompt = SUMMARIZE_SEARCH_PROMPT.format(
                    decomposition_nums=decomposition_nums, search_results=search_results
                )
                yield prompt
                remove = max(results, key=len)
                remove.pop()
                if len(remove) == 0:
                    break

        model_name = config.llm.model
        prompt = reduce_message_length(gen_msg(), model_name, system_text, config.llm.max_token)
        logger.debug(prompt)
        # Lambert：大模型拆分问题
        '''
        ### Requirements
        1. The keywords related to your research topic and the search results are shown in the "Search Result Information" section.
        2. Provide up to 1 queries related to your research topic base on the search results.
        3. Please respond in the following JSON format: ["query1", "query2", "query3", ...].
        
        ### Search Result Information
        #### Keyword: MySQL
         Search Result: [{'title': 'MySQL', 'link': 'https://www.mysql.com/', 'snippet': 'MySQL Cluster enables users to meet the database challenges of next generation web, cloud, and communications services with uncompromising scalability, uptime ...'}, {'title': 'MySQL', 'link': 'https://en.wikipedia.org/wiki/MySQL', 'snippet': 'MySQL is free and open-source software under the terms of the GNU General Public License, and is also available under a variety of proprietary licenses. MySQL ...'}, {'title': 'MySQL Tutorial', 'link': 'https://www.w3schools.com/MySQL/default.asp', 'snippet': 'MySQL is a widely used relational database management system (RDBMS). MySQL is free and open-source. MySQL is ideal for both small and large applications.'}, {'title': 'MySQL', 'link': 'https://github.com/mysql', 'snippet': "MySQL Server, the world's most popular open source database, and MySQL Cluster, a real-time, open source transactional database."}]
        
        #### Keyword: Oracle
         Search Result: [{'title': 'Oracle | Cloud Applications and Cloud Platform', 'link': 'https://www.oracle.com/', 'snippet': 'Oracle offers a comprehensive and fully integrated stack of cloud applications and cloud platform services.'}, {'title': 'Oracle Corporation', 'link': 'https://en.wikipedia.org/wiki/Oracle_Corporation', 'snippet': 'Oracle Corporation is an American multinational computer technology company headquartered in Austin, Texas. In 2020, Oracle was the third-largest software ...'}, {'title': 'Oracle Definition & Meaning', 'link': 'https://www.merriam-webster.com/dictionary/oracle', 'snippet': 'The meaning of ORACLE is a person (such as a priestess of ancient Greece) through whom a deity is believed to speak. How to use oracle in a sentence.'}, {'title': 'Oracle', 'link': 'https://en.wikipedia.org/wiki/Oracle', 'snippet': 'An oracle is a person or thing considered to provide insight, wise counsel or prophetic predictions, most notably including precognition of the future, ...'}]
        '''
        queries = await self._aask(prompt, [system_text])
        try:
            queries = OutputParser.extract_struct(queries, list)
            queries = TypeAdapter(list[str]).validate_python(queries)
        except Exception as e:
            logger.exception(f"fail to break down the research question due to {e}")
            queries = keywords
        ret = {}
        for query in queries:
            ret[query] = await self._search_and_rank_urls(topic, query, url_per_query)
        return ret

    async def _search_and_rank_urls(self, topic: str, query: str, num_results: int = 4) -> list[str]:
        """Search and rank URLs based on a query.

        Args:
            topic: The research topic.
            query: The search query.
            num_results: The number of URLs to collect.

        Returns:
            A list of ranked URLs.
        """
        max_results = max(num_results * 2, 6)
        # results = await self.search_engine.run(query, max_results=max_results, as_string=False)
        # mock call search API
        results = [{'title': 'Oracle vs. MySQL: Compare Syntax, Features & More', 'link': 'https://www.integrate.io/blog/oracle-vs-mysql/', 'snippet': 'The main difference between MySQL and SQL lies in their nature and usage. MySQL is an open-source database system, while SQL is a language used ...'}, {'title': '2 Oracle and MySQL Compared', 'link': 'https://docs.oracle.com/cd/E12151_01/doc.150/e12155/oracle_mysql_compared.htm', 'snippet': 'MySQL differs from Oracle in the way it handles default value for a column that does not allow NULL value. In MySQL, for a column that does not allow NULL value ...'}, {'title': 'Difference between MySQL and Oracle', 'link': 'https://www.javatpoint.com/mysql-vs-oracle', 'snippet': 'MySQL and Oracle are the two famous relational databases that are used in small and big companies. Although Oracle Corporation supports both databases, ...'}, {'title': 'Difference between Oracle and MySQL', 'link': 'https://www.geeksforgeeks.org/difference-between-oracle-and-mysql/', 'snippet': 'Difference between Oracle and MySQL · 1. It is developed By Oracle in 1980. · 2. It is commercial. · 3. Server operating systems for Oracle is ...'}, {'title': 'Differences between MySQL and Oracle databases [closed]', 'link': 'https://stackoverflow.com/questions/40356107/differences-between-mysql-and-oracle-databases', 'snippet': "In general, Oracle is much more powerful and is a deeper RDBMS, which allows you to write any complex system. That's why it is used in banking, ..."}]
        _results = "\n".join(f"{i}: {j}" for i, j in zip(range(max_results), results))
        prompt = COLLECT_AND_RANKURLS_PROMPT.format(topic=topic, query=query, results=_results)
        logger.debug(prompt)
        '''
        ### Topic
        The difference between mysql and oracle
        ### Query
        What is MySQL and how does it differ from Oracle?
        
        ### The online search results
        0: {'title': 'Oracle vs. MySQL: Compare Syntax, Features & More', 'link': 'https://www.integrate.io/blog/oracle-vs-mysql/', 'snippet': 'The main difference between MySQL and SQL lies in their nature and usage. MySQL is an open-source database system, while SQL is a language used ...'}
        1: {'title': '2 Oracle and MySQL Compared', 'link': 'https://docs.oracle.com/cd/E12151_01/doc.150/e12155/oracle_mysql_compared.htm', 'snippet': 'MySQL differs from Oracle in the way it handles default value for a column that does not allow NULL value. In MySQL, for a column that does not allow NULL value ...'}
        2: {'title': 'Difference between MySQL and Oracle', 'link': 'https://www.javatpoint.com/mysql-vs-oracle', 'snippet': 'MySQL and Oracle are the two famous relational databases that are used in small and big companies. Although Oracle Corporation supports both databases, ...'}
        3: {'title': 'Difference between Oracle and MySQL', 'link': 'https://www.geeksforgeeks.org/difference-between-oracle-and-mysql/', 'snippet': 'Difference between Oracle and MySQL · 1. It is developed By Oracle in 1980. · 2. It is commercial. · 3. Server operating systems for Oracle is ...'}
        4: {'title': 'Differences between MySQL and Oracle databases [closed]', 'link': 'https://stackoverflow.com/questions/40356107/differences-between-mysql-and-oracle-databases', 'snippet': "In general, Oracle is much more powerful and is a deeper RDBMS, which allows you to write any complex system. That's why it is used in banking, ..."}
        
        ### Requirements
        Please remove irrelevant search results that are not related to the query or topic. Then, sort the remaining search results based on the link credibility. If two results have equal credibility, prioritize them based on the relevance. Provide the
        ranked results' indices in JSON format, like [0, 1, 3, 4, ...], without including other words.

        '''
        indices = await self._aask(prompt)
        try:
            indices = OutputParser.extract_struct(indices, list)
            assert all(isinstance(i, int) for i in indices)
        except Exception as e:
            logger.exception(f"fail to rank results for {e}")
            indices = list(range(max_results))
        indices = [0];
        results = [results[i] for i in indices]
        if self.rank_func:
            results = self.rank_func(results)
        return [i["link"] for i in results[:num_results]]


class WebBrowseAndSummarize(Action):
    """Action class to explore the web and provide summaries of articles and webpages."""

    name: str = "WebBrowseAndSummarize"
    i_context: Optional[str] = None
    desc: str = "Explore the web and provide summaries of articles and webpages."
    browse_func: Union[Callable[[list[str]], None], None] = None
    web_browser_engine: Optional[WebBrowserEngine] = None

    @model_validator(mode="after")
    def validate_engine_and_run_func(self):
        if self.web_browser_engine is None:
            self.web_browser_engine = WebBrowserEngine.from_browser_config(
                self.config.browser,
                browse_func=self.browse_func,
                proxy=self.config.proxy,
            )
        return self

    async def run(
        self,
        url: str,
        *urls: str,
        query: str,
        system_text: str = RESEARCH_BASE_SYSTEM,
    ) -> dict[str, str]:
        """Run the action to browse the web and provide summaries.

        Args:
            url: The main URL to browse.
            urls: Additional URLs to browse.
            query: The research question.
            system_text: The system text.

        Returns:
            A dictionary containing the URLs as keys and their summaries as values.
        """
        contents = await self.web_browser_engine.run(url, *urls)
        if not urls:
            contents = [contents]

        summaries = {}
        prompt_template = WEB_BROWSE_AND_SUMMARIZE_PROMPT.format(query=query, content="{}")
        for u, content in zip([url, *urls], contents):
            content = content.inner_text
            # content = "Difference between MySQL and Oracle";
            chunk_summaries = []
            for prompt in generate_prompt_chunk(content, prompt_template, self.llm.model, system_text, 4096):
                logger.debug(prompt)
                summary = await self._aask(prompt, [system_text])
                if summary == "Not relevant.":
                    continue
                chunk_summaries.append(summary)

            # prompt = """### Requirements
            #             1. Utilize the text in the "Reference Information" section to respond to the question "{query}".
            #             2. If the question cannot be directly answered using the text, but the text is related to the research topic, please provide \
            #             a comprehensive summary of the text.
            #             3. If the text is entirely unrelated to the research topic, please reply with a simple text "Not relevant."
            #             4. Include all relevant factual information, numbers, statistics, etc., if available.
            #
            #             ### Reference Information
            #             Difference between MySQL and Oracle
            #             """
            # summary = await self._aask(prompt, [system_text])
            # chunk_summaries.append(summary)

            if not chunk_summaries:
                summaries[u] = None
                continue

            if len(chunk_summaries) == 1:
                summaries[u] = chunk_summaries[0]
                continue

            content = "\n".join(chunk_summaries)
            prompt = WEB_BROWSE_AND_SUMMARIZE_PROMPT.format(query=query, content=content)
            summary = await self._aask(prompt, [system_text])
            summaries[u] = summary
        return summaries


class ConductResearch(Action):
    """Action class to conduct research and generate a research report."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(
        self,
        topic: str,
        content: str,
        system_text: str = RESEARCH_BASE_SYSTEM,
    ) -> str:
        """Run the action to conduct research and generate a research report.

        Args:
            topic: The research topic.
            content: The content for research.
            system_text: The system text.

        Returns:
            The generated research report.
        """
        prompt = CONDUCT_RESEARCH_PROMPT.format(topic=topic, content=content)
        logger.debug(prompt)
        self.llm.auto_max_tokens = True
        return await self._aask(prompt, [system_text])


def get_research_system_text(topic: str, language: str):
    """Get the system text for conducting research.

    Args:
        topic: The research topic.
        language: The language for the system text.

    Returns:
        The system text for conducting research.
    """
    return " ".join((RESEARCH_TOPIC_SYSTEM.format(topic=topic), LANG_PROMPT.format(language=language)))
