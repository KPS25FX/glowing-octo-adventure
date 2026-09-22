# glowing-octo-adventure

# Overview : What I built
The SEC is the US market regulator. It requires company insiders (officers, directors and major shareholders) to report their trades on a Form 4, which it publishes through its EDGAR filing system. Over a chosen time window, this project retrieves every Form 4, cleans it into a small data model, and finds companies where several independent insiders bought shares on the open market within a few weeks of each other. This is a screening tool designed to suggest companies of interest to a trader , reducing the search space of possible investment opportunities

# Who its for 
I guess ... people who trade ? 

# Things I take for granted
In the form 4 there are fields : these fields tell us more about what exactly the nature of the submisison is - we want to examine forms that meet the following criteria : 
- code P -> this means the insider purchased shares on the open market (as opposed to receiving them as part of a compensation package, or some other reason)

# How I used AI 
- Generally speaking , I had claude code instruct me on the idea behind the project - I did not know what data set to use but I like trading related things and most of all I like maths 
- Then I gave claude a list of the general themes and ideas ive picked up on since doing my degree that make code good , and does not make me want to rip my eyes out looking at it : that list is below - I gave it to claude just so I don't forget to code in a certain way once i become focussed on each feature and thing
- Claude also told me the syntax for libaries i have no used before like XML Etree
- Claude also gave me URL's to the EDGAR filing system and the Form 4 filings, which I then used to scrape the data I needed