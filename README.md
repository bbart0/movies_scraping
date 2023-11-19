This is a project on scraping data about movies.

# Sources
The data was scraped from [The Numbers](https://www.the-numbers.com/box-office-records/worldwide/all-movies/cumulative/released-in-2022) (consisting of years 2016-2022) and [Wikipedia](https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)) (countries GDP)\
The given dataset only concerns a fraction of the film industry as the scraping was based on tabular data in the form of rankings (from about 200 to 500 biggest films per year).

# Contents
Film count: 1661\
A simple dataset consisting of movies which includes information about the movie's:
- title
- income (only concerns tickets sold in theaters) [$]
- budget [$]
- rating (MPAA)
- genre
- language
- countries of production
- the GDP of the countries (in case of multiple countries, they are summed) [$]

In the case for Chinese movies a default "G" rating was applied due to the censorship laws that regulate films\
If a budget wasn't given, the missing value was initiated as 0\
There are fields with no values!

