from bs4 import BeautifulSoup
import requests
import csv
import json
import re
import pandas as pd

URL_SITE_BASE = 'https://www.the-numbers.com'
URLS = ['https://www.the-numbers.com/box-office-records/worldwide/all-movies/cumulative/released-in-2022',
        'https://www.the-numbers.com/box-office-records/worldwide/all-movies/cumulative/released-in-2021',
        'https://www.the-numbers.com/box-office-records/worldwide/all-movies/cumulative/released-in-2020',
        'https://www.the-numbers.com/box-office-records/worldwide/all-movies/cumulative/released-in-2019',
       'https://www.the-numbers.com/box-office-records/worldwide/all-movies/cumulative/released-in-2018',
       'https://www.the-numbers.com/box-office-records/worldwide/all-movies/cumulative/released-in-2017',
       'https://www.the-numbers.com/box-office-records/worldwide/all-movies/cumulative/released-in-2016']

#variables which indicate how many pages of box office data does each link contain
TWO_PAGES='101'
THREE_PAGES=TWO_PAGES+':201'
FOUR_PAGES=THREE_PAGES+':301'

NUM_OF_PAGES_PER_URL = [TWO_PAGES, TWO_PAGES,TWO_PAGES, THREE_PAGES, FOUR_PAGES, FOUR_PAGES, FOUR_PAGES]

#normalizing the countries names - reason: different names on different sites
COUNTRY_NAME_CORR = [('Republic of Korea','South Korea'), ('Russian Federation','Russia'), 
                                 ('Islamic Republic of Iran', 'Iran'), ('Bolivarian Republic of Venezuela', 'Venezuela'),
                                  ('The Former Yugoslav Republic of Macedonia','North Macedonia'), 
                                   ('German Democratic Republic','Germany'), ('Occupied Palestinian Territory','Palestine'),
                                    ("Democratic People's Republic of Korea", 'North Korea'), ('Republic of Kosovo', 'Kosovo'),
                                     ('Viet Nam','Vietnam'),
                                     ('Libyan Arab Jamahiriya','Libya'), ('Brunei Darussalam', 'Brunei'), ('Lao People’s Democratic Republic', 'Laos')]



#extracts the wikipedia table containing information about each country's gdp in 2022 
# (or 2021 or 2020 in case of missing data such as in the case of North Korea)
# getting the gdp data of countries
GDPS = 'https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)'

response = requests.get(GDPS)
soup = BeautifulSoup(response.content, "html.parser")
table = soup.find("table", class_="wikitable")

# lists for storing the data
countries = []
gdps = []



# values multiplier due to the format of the extracted table (in USD millions)
VALUES_MULTIPLIER = 1000000

rows = table.find_all("tr")[2:]  

#processing all rows in the table excluding the "world" row
for row in rows[1:]:
    cells = row.find_all("td")
    country = cells[0].text.strip()
    if('—' in cells[2]):
        try:
            gdp=float(cells[3].text.strip().replace(",", ""))
        except:
            gdp = float(cells[4].text.strip().replace(",", ""))
    else:
        gdp = float(cells[2].text.strip().replace(",", "")) 
    gdp = gdp*VALUES_MULTIPLIER
    countries.append(country)
    gdps.append(gdp)

countries.append("Northen Ireland")
gdps.append(38910000000)

countries.append('Isle of Man')
gdps.append(6680000000)
data = {"Country": countries, "GDP": gdps}
country_data = pd.DataFrame(data)
country_data['GDP'] = pd.to_numeric(country_data['GDP'])


#function for scraping a given url from the base site
def scrape(url):
    source = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0'}).text
    soup = BeautifulSoup(source, 'html.parser')

    #get the table that holds the relevant data; denoted by tbody in html
    table = soup.find('tbody')
    
    #get all rows contained in the table; denoted by 'tr'
    rows = table.find_all('tr')
    film_list = []

    for movie in rows:
       dict_film = process_row(movie)
       film_list.append(dict_film)


    columns = ['Title','Overall_income','Budget','Rating','Genre','Languages','Countries','Countries_GDP']

    with open('.\movie_data.csv', 'a', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        for film in film_list:
            if film:
                writer.writerow(film)




#function that processes a row in the ranking by accessing more information of a given movie 
#by requesting the page dedicated to the movie (as extracted from the hrefs in the html)
def process_row(row):
    countries_gdp=0
    genre=''
    rating=''
    budget = 0
    countries=[]
    languages=[]

    #example data_list: ['1', 'Avatar: The Way of Water', '$2,320,247,738', '$684,073,224', '$1,636,174,514', '29.48%']
    data_list: str = row.text.strip('\n').split('\n')
    income: int = int(data_list[2][1:].replace(',',''))

    # getting more specific information about the movie by accessing its summary entry
    link_data = row.find('a', href=True)
    film_link = URL_SITE_BASE + link_data['href']
    
    #broken link fixes - these do not work in browsers either
    if data_list[1] == 'The Northman':
        film_link = 'https://www.the-numbers.com/movie/Northman-The-(2022)#tab=summary'
        countries = ['Unites States']

    film_req = requests.get(film_link, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0'}).text
    film_soup = BeautifulSoup(film_req, 'lxml')

    title = film_soup.find('h1').text[:-7]
    print(title)
    movie_details_header = film_soup.find('h2', string='Movie Details')
   
    try:
        general_info = movie_details_header.find_next('table')
        
        #table containg the financial information of the film
        finance_tab = film_soup.find('h2', string='Metrics').find_next('table').find_next('table')

        if finance_tab:
            budget_row=finance_tab.find('td', string=re.compile(r'Production.*?Budget:'))
            if budget_row:
                budget = int(budget_row.find_next('td').text.split(' ')[0][1:].replace(',',''))
    except AttributeError:
        title=data_list[1]
        general_info = film_soup
    finally:
        
        lang_row = general_info.find('td', string = "Languages:")
        if lang_row:
            languages = lang_row.find_next('td').text.split(', ')
        
        genre_row = general_info.find('td', string = "Genre:")
        if genre_row:
            genre = genre_row.find_next('td').text
    
            

        country_row = general_info.find('td', string = "Production Countries:")
        if country_row:
            
            countries = country_row.find_next('td').text.split(', ')

            for name, corr in COUNTRY_NAME_CORR:
                if name in countries:
                    countries[countries.index(name)] = corr
            
            # shortening the name of Taiwan
            # (due to the splitting recognzing Province of China as a separate country)
            # dont worry Taiwan is included in the dataset
            if 'Province of China' in countries:
                countries.remove('Province of China')
            if countries != [''] and countries:
                for country in countries:
                    countries_gdp += country_data.loc[country_data['Country'] == country, 'GDP'].item()

        rating_row = general_info.find('td',string =re.compile('MPAA'))
        if rating_row:
            rating = rating_row.find_next('td').text.split(' ')[0]
            if rating=='G(Rating':
                rating='G'
        else:
            if 'China' in countries:
                rating='G'
    

    return {'Title': title,
            'Overall_income': income,
            'Budget': budget,
            'Rating': rating,
            'Genre': genre,
            'Languages': languages,
            'Countries': countries,
            'Countries_GDP': countries_gdp
            }


def scrape_everything():

    columns = ['Title','Overall_income','Budget','Rating','Genre','Languages','Countries','Countries_GDP']
    with open('.\movie_data.csv', 'a', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()

    for ind,url in enumerate(URLS):
        scrape(url)
        for link_extend in NUM_OF_PAGES_PER_URL[ind].split(':'):
            print(url+link_extend)
            scrape(url + '/' + link_extend)

if __name__ == '__main__':
    scrape_everything()