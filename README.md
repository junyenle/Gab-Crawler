

# Gab Crawler Written by Jun Yen Leung

DESCRIPTION: 

Crawls Gab network. Pushes to a database.
Scrapes posts, users, follower/followees, metadata, etc. You can basically recreate a representation of the Gab network.

WHAT IS GAB?

Gab.ai is an "alt-right racist social network", in the words of the person who asked for this crawler. From this you can infer what type of research the data will be used for.

INSTRUCTIONS:

    run Gab.sql
    run Meta.sql
    change the SQL_CONFIG variable at the top of Scraper.py to match your database configuration
    run with "python3 GabCrawl.py" or similar command

SO WHAT ARE ALL THESE WEIRD OTHER FILES?

    botlist.txt keeps track of known bots over multiple runs so we don't waste time crawling them again
        if you don't see botlist.txt it's because either the crawler hasn't been run, or the runner never committed the botlist so everyone can benefit
    GenerateCorpus.py was used to generate corpus.json, which is what the annotaters are labelling
    errorlog.txt should be self explanatory

NOTES: 
   
   The code has not been cleaned up. It works, but it's hard as hell to read. Will be updated once I have time to refactor.  
   You can run multiples of this crawler so long as they all have access to the same database. You might get a little bit of duplication but no biggie. Be sure to change the crawl's starting point (it should be a user).
   
