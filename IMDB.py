# ssh -i [AWS Private Key] [Name]@[Address] for connecting using terminal

# scp -i [AWS Private Key] -r [Folder/File to be copied] [Name]@[Address] for transferring files to cloud server using terminal

import pandas as pd
import re

import requests as r
from bs4 import BeautifulSoup
from IPython.display import HTML

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
# nltk.download(['stopwords', 'wordnet', 'punkt'])
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, WordPunctTokenizer
import string

wpt = WordPunctTokenizer()
punkt = string.punctuation
wnl = WordNetLemmatizer()

from flask import Flask, request, render_template, url_for, redirect

app = Flask(__name__)

link = 'https://www.imdb.com/india/upcoming'
link = r.get(link)
if link.status_code == 200:
    print('Successful!')
else:
    print(f'ErrorCode the link is {link.status_code}')

soup_lxml = BeautifulSoup(link.text, 'lxml')
movie_container = soup_lxml.find_all('div', class_="trending-list-rank-item")

df = pd.DataFrame(columns=['Name', 'Poster', 'Release_Date', 'Summary', 'Stars', 'Vote'])
for movie in movie_container:
    mv_link = movie.find('span', class_="trending-list-rank-item-name").find('a').get('href')
    mv_name = movie.find('span', class_="trending-list-rank-item-name").find('a').get_text()
    mv_link = BeautifulSoup(r.get(f'https://www.imdb.com{mv_link}').text, 'lxml')
    vote = float(movie.find('span', class_="trending-list-rank-item-share").get_text().strip('%'))

    date = mv_link.find('div', class_='titleBar').find('div', class_='subtext').find_all('a')[-1]
    try:
        date = re.findall(r"\d+ \w+ \d+", date.get_text())[0]
        date = pd.to_datetime(date, format="%d %B %Y").date()
    except:
        date = (re.findall(r"\d+", date.get_text())[0])

    try:
        summary = mv_link.find('div', class_='article', id="titleStoryLine").find('div', class_='inline canwrap').find(
        'span').get_text().strip()
    except:
        summary = None
    genre = [i.get_text().strip() for i in mv_link.find('div', class_='subtext').find_all('a') if 'genre' in str(i)]

    image = '<img src="' + mv_link.find('div', class_='poster').find('img').get('src') + '" width="150" >'

    try:
        cast = [row.find_all('td')[1].find('a').get_text().strip() for row in
                mv_link.find('table', class_='cast_list').find_all('tr')[1:6]]
    except:
        cast = None
    language = [i.find('a').get_text().strip() for i in
                mv_link.find('div', class_='article', id="titleDetails").find_all('div', class_='txt-block') if
                'language' in str(i)][0]

    df = df.append({'Name': mv_name, 'Poster': image, 'Release_Date': date, "Genres": genre,
                    'Summary': summary, 'Stars': cast, "Language": language, "Vote":vote},
                   ignore_index=True)

movies = pd.read_csv('movies.csv')
movies.drop(['Unnamed: 0', 'imdbId', 'rating'], 1, inplace=True)
movies.columns = ['Name', 'Genres', 'Summary', 'Poster']
movies = pd.concat([df, movies], axis=0)
movies = movies[movies.Summary.isna() != True].dropna(axis=1)

def recomMovie(selected_movie, n=5):
    cv = CountVectorizer(stop_words='english')
    cntarray = cv.fit_transform(pd.Series(str(i)+"|"+str(j) for i in df.Genres for j in df.Summary))
    selected_index = movies[movies.Name.str.contains(selected_movie)].index.values[0]
    similar_movies =  list(enumerate(cosine_similarity(cntarray)[selected_index]))
    sorted_similar_movies = sorted(similar_movies, key=lambda x:x[1],reverse=True)[1:]
    recommendations = [movies[movies.index == i[0]]["Name"].values[0] for i in sorted_similar_movies[:n]]
    return recommendations

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if request.form.get('Beginner') == 'Beginner':
            return redirect('/Beginner') # do something
        elif request.form.get('Amateur') == 'Amateur':
            return redirect('/Amateur') # do something
        elif request.form.get('Expert') == 'Expert':
            return redirect('/Expert') # do something
        elif request.form.get('Advanced') == 'Advanced':
            return redirect('/Advanced') # do something
        else:
            pass
    return render_template('Home.html')

@app.route('/Beginner')
def beginner():
    return df[['Name', 'Vote']].to_html(escape=False)

@app.route('/Amateur')
def amateur():
    return df[['Name','Poster', 'Vote']].to_html(escape=False)

@app.route('/Expert')
def expert():
    return df.to_html(escape=False)

@app.route('/Advanced', methods=['GET', 'POST'])
def advanced():
    if request.method == 'POST':
        name = request.form.get('Movies')
        recommendations = recomMovie(name)
        images = [movies[movies.Name == recom].Poster.values[0] for recom in recommendations]
        return render_template('Details.html',df=df, Name=name, images = images, recommendations=recommendations)
    else: redirect('/Advanced')
    return render_template('Advanced.html', df=df, len=len(df))

# # Uncomment if running locally
if __name__ == '__main__':
   app.run(debug=True)

# # Uncomment if running on a Cloud Server
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=8080)