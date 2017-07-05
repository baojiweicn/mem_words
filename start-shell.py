#!/usr/bin/env python
# encoding: utf-8
import os, sys
sys.setrecursionlimit(99999)
sys.path.append(os.path.dirname(__file__))

from common.db import BaseConnection
import asyncio
from config import DB_CONFIG

def main():
    loop = asyncio.get_event_loop()
    db = None
    async def before_start(loop,DB_CONFIG):
        db = await BaseConnection(loop=loop).init(DB_CONFIG=DB_CONFIG)
        return db

    db = loop.run_until_complete(before_start(loop,DB_CONFIG))
    local_vars = locals()
    local_vars['db'] = db
    local_vars['loop'] = loop

    def fetch(sql):
        async def run(sql):
            async with db as cur:
                res = await cur.fetch(sql)
                return res
        res = loop.run_until_complete(run(sql))
        return res

    local_vars['fetch'] = fetch
    try:
        from IPython.frontend.terminal.embed import InteractiveShellEmbed
        ipshell = InteractiveShellEmbed()
        ipshell()
    except ImportError:
        import code
        pyshell = code.InteractiveConsole(locals=local_vars)
        pyshell.interact()

if __name__ == "__main__":
    main()

