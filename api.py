from datetime import datetime
from flask import Flask, render_template
from flask import jsonify
import requests, json
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)

def aggregate_news(URL):
	
	headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36"}
	page = requests.get(URL, headers=headers)
	soup = BeautifulSoup(page.content, 'html.parser')
	news = soup.find_all("li", {"class":"box item"})
	
	news_id = []
	headings = []
	descriptions = []
	news_url = []
	time_published = []
	publisher = []
	image_url = []
	
	for i in news:
		news_id.append(int(i["id"].replace("item-","")))
		headings.append(i.find("h2").get_text().strip())
		descriptions.append(i.find("div", {"class":"desc"}).get_text().strip())
		news_url.append(i.a["href"].strip())
		time_published.append(i.span["title"])
		publisher.append(i.find("span", {"class":"feed"}).get_text().strip().replace("— ",""))
		img_link = i.find("div",{"class":"desc"}).img
		if img_link is not None:
			image_url.append(i.find("div",{"class":"desc"}).img["data-src"])
		else:
			image_url.append(None)
	news_agg = pd.DataFrame(columns=["news_id","time_published","publisher","title","description","news_url","image_url"])
	
	news_agg["news_id"] = news_id
	news_agg["time_published"] = time_published
	news_agg["publisher"] = publisher
	news_agg["title"] = headings
	news_agg["description"] = descriptions
	news_agg["news_url"] = news_url
	news_agg["image_url"] = image_url
	
	news_agg["time_published"] = pd.to_datetime(news_agg["time_published"])
	
	news_id_sim = []
	headings_sim = []
	news_url_sim = []
	time_published_sim = []
	publisher_sim = []
	
	for i in news:
		similar = i.find("ul",{"class":"similar"})
		try:
			for sim_news in similar:
				if sim_news is not None:
					news_id_sim.append(int(i["id"].replace("item-","")))
					headings_sim.append(sim_news.a.get_text().strip())
					news_url_sim.append(sim_news.a["href"].strip())
					time_published_sim.append(sim_news.find("span",class_="date")["title"])
					publisher_sim.append(sim_news.find("span",class_="feed").get_text().replace("— ",""))
		except TypeError:
			pass
		
	similar_agg = pd.DataFrame(columns=["sim_id","news_id","time_published_sim","publisher_sim","title_sim","news_url_sim"])
	
	similar_agg["sim_id"] = similar_agg.index
	similar_agg["news_id"] = news_id_sim
	similar_agg["time_published_sim"] = time_published_sim
	similar_agg["publisher_sim"] = publisher_sim
	similar_agg["title_sim"] = headings_sim
	similar_agg["news_url_sim"] = news_url_sim
	
	similar_agg["time_published_sim"] = pd.to_datetime(similar_agg["time_published_sim"])
	
	news_agg.to_feather(r"news_agg.feather")
	similar_agg.to_feather(r"similar_agg.feather")
	
def sync_news(URL):
	
	aggregate_news(URL)
	
	news_agg_old = pd.read_feather("news_all.feather")
	similar_agg_old = pd.read_feather("similar_all.feather")
	
	news_agg = pd.read_feather("news_agg.feather")
	similar_agg = pd.read_feather("similar_agg.feather")
	
	news_all = pd.concat([news_agg,news_agg_old]).drop_duplicates().reset_index(drop=True)
	similar_all = pd.concat([similar_agg,similar_agg_old]).drop_duplicates().reset_index(drop=True)
	
	similar_all["sim_id"] = similar_all.index
	
	merged_news = pd.merge(news_all,similar_all, on="news_id", how="left")
	
	news_all.to_feather(r"news_all.feather")                   # All news at any point of time
	similar_all.to_feather(r"similar_all.feather")             # All similar-news at any point of time
	merged_news.to_feather(r"merged_news.feather")             # Merged news at any point of time
	
	news_json = news_all.to_json(orient='records')
	similar_json = similar_all.to_json(orient='records')
	
	with open("news.json", "w") as outfile:
		outfile.write(json.dumps(json.loads(news_json), indent=4, sort_keys=False))
	
	with open("similar.json", "w") as outfile:
		outfile.write(json.dumps(json.loads(similar_json), indent=4, sort_keys=False))

URL = "https://pulse.zerodha.com"

@app.route('/')
def home():
	return render_template("home.html")

@app.route('/refresh')
def refresh():
	sync_news(URL)
	news_agg = pd.read_feather("news_all.feather")
	similar_agg = pd.read_feather("similar_all.feather")
	print("News database refreshed at {}. Total news: {}. Similar news: {}".format((datetime.now().strftime("%I:%M:%S %p")),len(news_agg),len(similar_agg)))
	return "News database refreshed at {}. Total news: {}. Similar news: {}".format((datetime.now().strftime("%I:%M:%S %p")),len(news_agg),len(similar_agg))

@app.route('/news-api', methods=['GET'])
def news_api():
	with open("news.json") as file:
		news_json = json.load(file)
	return jsonify(news_json), 400
	
@app.route('/similar-api', methods=['GET'])
def similar_api():
	with open("similar.json") as file:
		similar_json = json.load(file)
	return jsonify(similar_json), 400

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80, debug=True)