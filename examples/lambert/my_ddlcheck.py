#!/usr/bin/env python

import asyncio

from metagpt.roles.ddl_checker import DDLChecker
from metagpt.config2 import Config
from metagpt.const import METAGPT_ROOT


async def main():

    gpt_synnex = Config.from_yaml_file(METAGPT_ROOT / "config/config2.yaml")
    # gpt_synnex = Config.from_yaml_file(METAGPT_ROOT / "config/config2.synnex.yaml")

    sql = """
    create table a12345678901234567890123456a12345678901234567890123456123123(
        id        int auto_increment primary key,
        name varchar(30) null,
        entry_id int
    );
    into test_table values (1, 2, 3, '192.168.1.7');
    """
    role = DDLChecker(config=gpt_synnex)

    result = await role.run(sql)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())