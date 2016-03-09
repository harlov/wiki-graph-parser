import asyncio
import sys

from wiki_api import WikiApi

if len(sys.argv) < 2:
    sys.exit("provide input article!")

start_query = sys.argv[1]
print("let's parse start from :", start_query)

loop = asyncio.get_event_loop()
WikiApi(loop, start_query)
