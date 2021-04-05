"""
Crawler implementation
"""
import requests
import random
from time import sleep
import shutil
import re
import os
import json
import datetime
from bs4 import BeautifulSoup
from article import Article
from constants import CRAWLER_CONFIG_PATH, ASSETS_PATH

headers = {
         'user-agent':
     'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 '
     '(KHTML, like Gecko) Chrome/88.0.4324.152 YaBrowser/21.2.2.102 Yowser/2.5 Safari/537.36'}
class IncorrectURLError(Exception):
    """
    Custom error
    """

class NumberOfArticlesOutOfRangeError(Exception):
    """
    Custom error
    """


class IncorrectNumberOfArticlesError(Exception):
    """
    Custom error
    """

class UnknownConfigError(Exception):
    """
    Most general error
    """


class Crawler:
    """
    Crawler implementation
    """

    def __init__(self, seed_urls: list, max_articles: int, max_articles_per_seed:int):
        self.seed_urls = seed_urls
        self.max_articles = max_articles
        self.max_articles_per_seed = max_articles_per_seed
        self.urls = []

    @staticmethod
    def _extract_url(article_bs):
        return article_bs.find('a').attrs['href']

    def find_articles(self):
        """
        Finds articles
        """
        for seed_url in self.seed_urls:
            try:
                response = requests.get(seed_url, headers=headers)
                sleep(random.randint(3, 6))
                response.encoding = 'utf-8'
                if not response:
                    raise IncorrectURLError

            except IncorrectURLError:
                continue

            soup_page = BeautifulSoup(response.content, features='lxml')
            all_urls_soup = soup_page.find_all('li', class_="node_read_more first")
            for one_of_urls in all_urls_soup[:self.max_articles_per_seed]:
                if len(self.urls) < self.max_articles:
                    self.urls.append("http://tomsk-novosti.ru/" + self._extract_url(one_of_urls))

            if len(self.urls) == self.max_articles:
                return self.urls

        return self.urls

    def get_search_urls(self):
        """
        Returns seed_urls param
        """
        pass


class ArticleParser:
    """
    ArticleParser implementation
    """
    def __init__(self, full_url: str, article_id: int):
        self.full_url = full_url
        self.article_id = article_id
        self.article = Article(full_url, article_id)

    @staticmethod
    def clean_text(text):
        return '\n'.join(re.findall(r'[А-я]+.+\.[ \t]*', text))

    def _fill_article_with_text(self, article_soup):
        article_preview = article_soup.find('div', {'class': 'one-news-preview-text'}).text + '\n'
        article_content = article_soup.find('div', {'class': 'js-mediator-article'}).text
        self.article.text = article_preview + self.clean_text(article_content)

    def _fill_article_with_meta_information(self, article_soup):
        title = article_soup.find('h4')
        self.article.title = title.text
        self.article.date = self.unify_date_format(article_soup.find('em').text)
        self.article.author = 'NOT FOUND'

    @staticmethod
    def unify_date_format(date_str):
        """
        Unifies date format
        """
        return datetime.datetime.strptime(date_str, '%d.%m.%Y')

    def parse(self):
        """
        Parses each article
        """
        response = requests.get(self.full_url, headers=headers)
        article_bs = BeautifulSoup(response.content, features='lxml')
        self._fill_article_with_text(article_bs)
        self._fill_article_with_meta_information(article_bs)
        return self.article


def prepare_environment(base_path):
    """
    Creates ASSETS_PATH folder if not created and removes existing folder
    """
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
    os.makedirs(base_path)


def validate_config(crawler_path):
    """
    Validates given config
    """
    with open(crawler_path, 'r', encoding='utf-8') as file:
        config = json.load(file)
    if not isinstance(config, dict) or not "base_urls" in config \
            or not "total_articles_to_find_and_parse" in config:
        raise UnknownConfigError
    if not isinstance(config["base_urls"], list) or not all(isinstance(url, str) for url in config["base_urls"]):
        raise IncorrectURLError
    if not isinstance(config["total_articles_to_find_and_parse"], int):
        raise IncorrectNumberOfArticlesError
    if config["total_articles_to_find_and_parse"] > 100:
        raise NumberOfArticlesOutOfRangeError
    return config.values()


if __name__ == '__main__':
    # YOUR CODE HERE
    urls, max_num_articles, max_per_seed = validate_config(CRAWLER_CONFIG_PATH)
    crawler_current = Crawler(seed_urls=urls, max_articles=max_num_articles, max_articles_per_seed=max_per_seed)
    crawler_current.find_articles()

    prepare_environment(ASSETS_PATH)
    for ind, article_url in enumerate(crawler_current.urls):
        parser = ArticleParser(full_url=article_url, article_id=ind + 1)
        parser.parse()
        parser.article.save_raw()
