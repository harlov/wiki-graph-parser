import asyncio
import json
import os

import aiohttp
import re
from graphviz import Digraph
WORK_DIR = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]


class WikiGraph:
    def __init__(self, start_query, max_deep_level=8):
        self.start_query = start_query
        self.result_graph = Digraph()
        self.result_repeat_cache = list()
        self.loop = asyncio.get_event_loop()
        self.wiki_api = WikiApi(self.loop)
        self.MAX_DEEP_LEVEL = max_deep_level
        print(WORK_DIR)

    def run(self):
        self.loop.run_until_complete(self.process_node(self.start_query, 0))
        self.save_to_file()

    async def process_node(self, name, level, parent=None):
        print("start get page, %s , level %s" % (name,level ))
        page_data = await self.wiki_api.get_page(name)
        print(" page %s, level %s done" % (name, level))

        self.result_graph.node(page_data[0], name)
        if parent is not None and not (parent, page_data[0]) in self.result_repeat_cache:
            self.result_graph.edge(parent, page_data[0])
            self.result_repeat_cache.append((parent, page_data[0]))

        if level >= self.MAX_DEEP_LEVEL:
            return

        sub_tasks = list()
        for sub_node in self.wiki_api.get_main_articles(page_data):
            print(sub_node)
            sub_tasks.append(asyncio.Task(self.process_node(sub_node, level+1, page_data[0])))
        await asyncio.gather(*sub_tasks)

    def save_to_file(self):
        out_file = WORK_DIR+'/output/%s_deep_%s.gv' % (self.start_query, self.MAX_DEEP_LEVEL )
        self.result_graph.render(out_file, view=True)


class WikiApi:
    """ Class for async getting and parsing wiki pages """
    BASE_URl = 'https://en.wikipedia.org/w/api.php'
    BASE_DICT = dict(format='json', action='query', prop='revisions', rvprop='content')
    MAIN_ARTICLE_REGEXP = re.compile(r'\{\{main\|(.+?)\}\}', re.IGNORECASE)

    def __init__(self, loop):
        self.session = aiohttp.ClientSession(loop=loop)

    def __del__(self):
        self.session.close()

    async def get_page(self, query):
        request_done = False
        while not request_done:
            response_json, response_status = await self.get_page_low(query)
            if response_status == 200:
                global request_done
                request_done = True
                page = response_json['query']['pages'].popitem()
                return page

    async def get_page_low(self, query):
        request_params = self.BASE_DICT.copy()
        request_params['titles'] = query

        async with self.session.get(self.BASE_URl, params=request_params) as response:
            return await response.json(), response.status

    def get_main_articles(self, page):
        """
        :param page: JSON object of wiki page
        :return: list of main titles lins on page
        """
        if not 'revisions' in page[1]:
            return list()

        page_text = page[1]['revisions'][0]['*']
        return self.MAIN_ARTICLE_REGEXP.findall(page_text)