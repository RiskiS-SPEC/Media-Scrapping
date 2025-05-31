from flask import Flask, render_template, request, send_file
from bs4 import BeautifulSoup
import requests
import datetime
from textblob import TextBlob
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

# --- Sentiment analysis ---
def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0:
        return "Positif"
    elif polarity < 0:
        return "Negatif"
    else:
        return "Netral"

# --- Scraping functions ---
def scrape_kompas(keyword):
    url = f"https://www.kompas.com/search/?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all("div", class_="article__list__title")

    results = []
    for article in articles[:10]:
        a_tag = article.find("a")
        if a_tag:
            title = a_tag.get_text(strip=True)
            link = a_tag["href"]
            results.append({"judul": title, "url": link})
    return results

def scrape_detik(keyword):
    url = f"https://www.detik.com/search/searchall?query={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all("h3", class_="media__title")

    results = []
    for article in articles[:10]:
        a_tag = article.find("a")
        if a_tag:
            title = a_tag.get_text(strip=True)
            link = a_tag["href"]
            results.append({"judul": title, "url": link})
    return results

def scrape_liputan6(keyword):
    url = f"https://www.liputan6.com/search?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all("div", class_="articles--iridescent-list")

    results = []
    for article in articles[:10]:
        a_tag = article.find("a")
        title_tag = article.find("h4")
        if a_tag and title_tag:
            title = title_tag.get_text(strip=True)
            link = a_tag["href"]
            results.append({"judul": title, "url": link})
    return results

# --- Visualization ---
def generate_trend_chart(results, keyword):
    media_names = list(results.keys())
    counts = [len(results[media]) for media in media_names]

    plt.bar(media_names, counts, color='skyblue')
    plt.title(f'Jumlah Artikel per Media untuk: "{keyword}"')
    plt.xlabel('Media')
    plt.ylabel('Jumlah Artikel')
    filename = f'static/trend_{keyword}.png'
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return filename

# --- Save to CSV ---
def save_to_csv(data, keyword, tanggal):
    df = pd.DataFrame(data)
    filename = f"{keyword}_{tanggal}.csv"
    filepath = f"static/{filename}"
    df.to_csv(filepath, index=False)
    return filepath

# --- Main route ---
@app.route("/", methods=["GET", "POST"])
def index():
    results = {"kompas": [], "detik": [], "liputan6": []}
    keyword = ""
    tanggal = ""
    sentiment_data = []
    chart_path = ""
    csv_path = ""

    if request.method == "POST":
        keyword = request.form.get("keyword")
        tanggal = request.form.get("tanggal")

        # Scrape dari masing-masing media
        results["kompas"] = scrape_kompas(keyword)
        results["detik"] = scrape_detik(keyword)
        results["liputan6"] = scrape_liputan6(keyword)

        # Analisis sentimen
        for media, articles in results.items():
            for article in articles:
                judul = article["judul"] if isinstance(article, dict) else article
                sentiment = analyze_sentiment(judul)
                sentiment_data.append({
                    "media": media,
                    "judul": judul,
                    "sentimen": sentiment,
                    "tanggal_input": tanggal
                })

        # Visualisasi dan simpan CSV
        chart_path = generate_trend_chart(results, keyword)
        csv_path = save_to_csv(sentiment_data, keyword, tanggal)

    return render_template("index.html",
                        keyword=keyword,
                        tanggal=tanggal,
                        results=results,
                        chart_path=chart_path,
                        csv_path=csv_path,
                        sentiment_data=sentiment_data)

# --- Endpoint untuk download CSV ---
@app.route("/download_csv/<path:filename>")
def download_csv(filename):
    return send_file(os.path.join("static", filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
