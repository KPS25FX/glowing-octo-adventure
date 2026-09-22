# glowing-octo-adventure

# Overview : What I built
The SEC is the US market regulator. It requires company insiders (officers, directors and major shareholders) to report their trades on a Form 4, which it publishes through its EDGAR filing system. Over a chosen time window, this project retrieves every Form 4, cleans it into a small data model, and finds companies where several independent insiders bought shares on the open market within a few weeks of each other. This is a screening tool designed to suggest companies of interest to a trader , reducing the search space of possible investment opportunities

# Who its for 
I guess ... people who trade ? 

# Things I take for granted
In the form 4 there are fields : these fields tell us more about what exactly the nature of the submisison is - we want to examine forms that meet the following criteria : 
- code P -> this means the insider purchased shares on the open market (as opposed to receiving them as part of a compensation package, or some other reason)