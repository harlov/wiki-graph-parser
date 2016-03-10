import asyncio
import sys

from wiki_api import WikiGraph

if len(sys.argv) < 2:
    sys.exit("provide input article!")

start_query = sys.argv[1]
deep = 8

if len(sys.argv) >= 3:
    deep = int(sys.argv[2])


print("start query :", start_query)


wiki_graph = WikiGraph(start_query, deep)
wiki_graph.run()
