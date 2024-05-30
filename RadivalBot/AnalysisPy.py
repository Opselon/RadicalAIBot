import MetaTrader5 as mt5
import logging
import asyncio
import feedparser
from textblob import TextBlob
from typing import List
import openai
import os
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load OpenAI API key from environment variable
openai.api_key = os.getenv('proj_O3XH0uI3Y5fM1NcrqWtXZVkM')

# Define constants for trading
SYMBOL = "XAUUSD"
LOT_SIZE = 0.1
STOP_LOSS_PIPS = 50
TAKE_PROFIT_PIPS = 100

class MT5Integration:
    def __init__(self):
        self.mt5 = mt5

    def initialize_mt5(self) -> str:
        if not self.mt5.initialize():
            logging.error("Failed to initialize MetaTrader 5")
            return "Failed to initialize MetaTrader 5"
        return "MetaTrader 5 initialized successfully"

    def login_mt5(self, login: str, password: str, server: str) -> str:
        try:
            login_int = int(login)
        except ValueError:
            logging.error(f"Invalid login credentials: {login}")
            return f"Invalid login credentials: {login}"
        
        if not self.mt5.login(login_int, password=password, server=server):
            logging.error(f"Failed to login to account #{login}, error code: {self.mt5.last_error()}")
            return f"Failed to login to account #{login}, error code: {self.mt5.last_error()}"
        return f"Logged in successfully to account #{login}"

    def get_account_info(self) -> str:
        account_info = self.mt5.account_info()
        if account_info is None:
            logging.error("Failed to get account info")
            return "Failed to get account info"
        return f"Account Info: Balance - {account_info.balance}, Equity - {account_info.equity}, Margin Free - {account_info.margin_free}"

    def shutdown_mt5(self) -> str:
        self.mt5.shutdown()
        return "MetaTrader 5 shutdown successfully"

    def get_market_info(self, symbol: str) -> str:
        if not self.mt5.symbol_select(symbol, True):
            logging.error(f"Failed to select symbol {symbol}")
            return f"Failed to select symbol {symbol}"
        
        market_info = self.mt5.symbol_info(symbol)
        if market_info is None:
            logging.error(f"Failed to get market info for {symbol}")
            return f"Failed to get market info for {symbol}"
        return f"Market Info for {symbol}: Bid - {market_info.bid}, Ask - {market_info.ask}, Last - {market_info.last}"

    def open_position(self, symbol: str, order_type: int, lot: float, price: float, sl: float, tp: float):
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 234000,
            "comment": "Python script open",
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_IOC,
        }
        result = self.mt5.order_send(request)
        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            logging.error(f"Failed to open position: {result.retcode}")
        else:
            logging.info(f"Position opened successfully: {result}")
        return result


import asyncio
import aiohttp
import feedparser
import logging

class NewsFetcher:
    @staticmethod
    async def fetch_rss_news(feed_urls: list) -> list:
        news_items = []
        async with aiohttp.ClientSession() as session:
            tasks = [NewsFetcher.fetch_news_from_url(session, url) for url in feed_urls]
            results = await asyncio.gather(*tasks)
            for result in results:
                news_items.extend(result)
        return news_items

    @staticmethod
    async def fetch_news_from_url(session, url: str) -> list:
        news_items = []
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    feed_content = await response.text()
                    feed = feedparser.parse(feed_content)
                    for entry in feed.entries:
                        title = entry.get('title', 'No title')
                        published = entry.get('published', 'No publication date')
                        author = entry.get('author', 'No author')
                        link = entry.get('link', 'No link')
                        news_item = f"{title}\n{published}"
                        news_items.append(news_item)
                else:
                    logging.error(f"Failed to fetch news from {url}: Status {response.status}")
        except Exception as e:
            logging.error(f"Failed to fetch news from {url}: {e}")
        return news_items

# Usage
async def main():
    # Fetch the RSS news from the given URLs
    urls = ["https://www.investing.com/rss/market_overview_Technical.rss",
            "https://www.investing.com/rss/news_95.rss",
            "https://www.investing.com/rss/forex_Fundamental.rss",
            "https://www.investing.com/rss/stock_Technical.rss"]
    news_items = await NewsFetcher.fetch_rss_news(urls)

    # Print the resulting list of news items
    for news_item in news_items:
        print(news_item)

asyncio.run(main())

class MarketAnalyzer:
    def __init__(self, mt5_integration: MT5Integration):
        self.mt5_integration = mt5_integration

    async def analyze_market(self, symbols: List[str]) -> str:
        tasks = [self.get_market_info_async(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        return "\n".join(results)

    async def get_market_info_async(self, symbol: str) -> str:
        return await asyncio.to_thread(self.mt5_integration.get_market_info, symbol)

class OpenAIAnalyzer:
    @staticmethod
    async def get_analysis(market_data: str, news_data: List[str]) -> str:
        try:
            response = await asyncio.to_thread(openai.Completion.create,
                                               engine="text-davinci-003",
                                               prompt=f"Analyze the following market data and news for potential trading strategies:\n\nMarket Data:\n{market_data}\n\nNews:\n{news_data}",
                                               max_tokens=500)
            return response.choices[0].text.strip()
        except Exception as e:
            logging.error(f"Failed to get analysis from OpenAI: {e}")
            return "Failed to get analysis from OpenAI"

class SentimentAnalyzer:
    @staticmethod
    async def analyze_sentiment(news_data: List[str]) -> float:
        tasks = [SentimentAnalyzer.analyze_sentiment_async(news) for news in news_data]
        sentiments = await asyncio.gather(*tasks)
        return sum(sentiments) / len(sentiments) if sentiments else 0

    @staticmethod
    async def analyze_sentiment_async(news: str) -> float:
        analysis = await asyncio.to_thread(TextBlob, news)
        return analysis.sentiment.polarity

class TradingBot:
    def __init__(self, mt5_integration: MT5Integration, news_fetcher: NewsFetcher, market_analyzer: MarketAnalyzer, openai_analyzer: OpenAIAnalyzer, sentiment_analyzer: SentimentAnalyzer):
        self.mt5_integration = mt5_integration
        self.news_fetcher = news_fetcher
        self.market_analyzer = market_analyzer
        self.openai_analyzer = openai_analyzer
        self.sentiment_analyzer = sentiment_analyzer

    async def run(self):
        # Fetch news
        feed_urls = [
            "https://www.investing.com/rss/market_overview_Technical.rss",
            "https://www.investing.com/rss/news_95.rss",
            "https://www.investing.com/rss/forex_Fundamental.rss",
            "https://www.investing.com/rss/stock_Technical.rss"
        ]
        news_data = await self.news_fetcher.fetch_rss_news(feed_urls)
        logging.info(f"Fetched {len(news_data)} news items.")

        # Analyze sentiment
        sentiment_score = await self.sentiment_analyzer.analyze_sentiment(news_data)
        logging.info(f"Sentiment Score: {sentiment_score}")

        # Get market data
        symbols = ["XAUUSD", "USDJPY", "EURUSD"]
        market_data = await self.market_analyzer.analyze_market(symbols)
        logging.info(f"Market Data:\n{market_data}")

        # Get OpenAI analysis
        ai_analysis = await self.openai_analyzer.get_analysis(market_data, news_data)
        logging.info(f"AI Analysis:\n{ai_analysis}")

        # Trading decision based on sentiment and AI analysis
        if sentiment_score > 0:
            order_type = self.mt5_integration.mt5.ORDER_TYPE_BUY
        else:
            order_type = self.mt5_integration.mt5.ORDER_TYPE_SELL

        # Get current price for XAUUSD
        market_info = self.mt5_integration.mt5.symbol_info_tick(SYMBOL)
        if not market_info:
            logging.error(f"Failed to get market info for {SYMBOL}")
            return

        price = market_info.ask if order_type == self.mt5_integration.mt5.ORDER_TYPE_BUY else market_info.bid
        sl = price - STOP_LOSS_PIPS * self.mt5_integration.mt5.symbol_info(SYMBOL).point
        tp = price + TAKE_PROFIT_PIPS * self.mt5_integration.mt5.symbol_info(SYMBOL).point

        # Open position
        result = self.mt5_integration.open_position(SYMBOL, order_type, LOT_SIZE, price, sl, tp)
        logging.info(f"Trade result: {result}")

# Initialize the components
mt5_integration = MT5Integration()
news_fetcher = NewsFetcher()
market_analyzer = MarketAnalyzer(mt5_integration)
openai_analyzer = OpenAIAnalyzer()
sentiment_analyzer = SentimentAnalyzer()
trading_bot = TradingBot(mt5_integration, news_fetcher, market_analyzer, openai_analyzer, sentiment_analyzer)

# Run the bot
asyncio.run(trading_bot.run())
