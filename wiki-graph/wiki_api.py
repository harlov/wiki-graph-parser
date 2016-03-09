import aiohttp
import re


class WikiApi:
    BASE_URl = 'https://en.wikipedia.org/w/api.php'
    BASE_DICT = dict(format='json', action='query', prop='revisions', rvprop='content')
    MAIN_ARTICLE_REGEXP = re.compile(r'\{\{main\|(.+?)\}\}')

    def __init__(self, loop, start_query):
        self.result_list = []
        self.loop = loop
        with aiohttp.ClientSession(loop=self.loop) as session:
            self.loop.run_until_complete(self.get_page(session, start_query))
        print(self.result_list)

    async def parse_main_articles(self, text, session):
        matches = self.MAIN_ARTICLE_REGEXP.findall(text)
        for match in matches:
            await self.get_page(session, match)
            self.result_list.append(match)

    async def get_page(self, session, start_query):
        request_params = self.BASE_DICT.copy()
        request_params['titles'] = start_query
        async with session.get(self.BASE_URl, params=request_params) as response:
            await self.parse_main_articles(await response.text(), session)