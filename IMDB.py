import pandas as pd
import re

import requests as r
from bs4 import BeautifulSoup
from IPython.display import HTML
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
    print
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

    summary = mv_link.find('div', class_='article', id="titleStoryLine").find('div', class_='inline canwrap').find(
        'span').get_text().strip()
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
        return render_template('Details.html',df=df, Name=name)
    else: redirect('/Advanced')
    return render_template('Advanced.html', df=df, len=len(df))

if __name__ == '__main__':
    app.run(debug=True)