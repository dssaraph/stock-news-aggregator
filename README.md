# stock-news-aggregator
Business and markets news from major publications scraped and parsed into JSON.

Highlights:
1. Uses feather filesystem to store news
2. More than 1-day old news available for analysis
3. JSON API output with front-end to refresh data

Instructions:
1. Clone this git repo to your machine.
2. Install requirements using `pip install -r requirements.txt`
3. Run the flask code using `python api.py`
4. Navigate to [localhost](http://localhost/) on your default browser to see the interface.

NOTE: This program uses Zerodha's Pulse news aggregator to scrape news.
