import asyncio
import json
import os
import random

import aiohttp
import re
from graphviz import Digraph
WORK_DIR = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('\\')[:-1])
random.seed()

class WikiApi:
    BASE_URl = 'https://en.wikipedia.org/w/api.php'
    BASE_DICT = dict(format='json', action='query', prop='revisions', rvprop='content')
    MAIN_ARTICLE_REGEXP = re.compile(r'\{\{main\|(.+?)\}\}', re.IGNORECASE)

    def __init__(self, loop, start_query, max_deep_level=8):
        self.result_graph = Digraph()
        self.loop = loop
        self.MAX_DEEP_LEVEL = max_deep_level
        with aiohttp.ClientSession(loop=self.loop) as session:
            self.loop.run_until_complete(self.get_page(session, start_query, 0))
        self.save_to_file(start_query)

    def save_to_file(self, name):
        print(self.result_graph.source)
        out_file = WORK_DIR+'/output/%s.gv' % (name, )
        self.result_graph.render(out_file, view=True)

    async def parse_main_articles(self, text, session, level, parent=None):
        subtasks = []
        matches = self.MAIN_ARTICLE_REGEXP.findall(text)
        for match in matches:
            subtasks.append(asyncio.Task(self.get_page(session, match, level+1, parent)))
        await asyncio.gather(*subtasks)

    async def get_page(self,session, query, level, parent=None):
        await asyncio.sleep(random.randint(1,5))
        if level >= self.MAX_DEEP_LEVEL:
            return
        print("start get page, %s , level %s" % (query,level ))
        request_params = self.BASE_DICT.copy()
        request_params['titles'] = query
        async with session.get(self.BASE_URl, params=request_params) as response:
            response_text = await response.text()
            response_json = json.loads(response_text)
            response.release()
            print(" page %s, level %s done" % (query, level))
            page_id = list(response_json['query']['pages'].keys())[0]
            #curr_graph_item = WikiPage(query)
            self.result_graph.node(str(page_id), query)
            if parent is not None:
                self.result_graph.edge(str(parent), str(page_id))
            await asyncio.Task(self.parse_main_articles(response_text, session, level, page_id))