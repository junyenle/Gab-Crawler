import cssutils, time, queue, json
import atexit
from bs4 import BeautifulSoup
from splinter.browser import Browser
from splinter import exceptions
import mysql.connector
import selenium.common
import pandas as pd
from datetime import date, timedelta, datetime
from multiprocessing import Process, Array
import threading
import sys
cnx = ""
cursor = ""
metacursor = ""
metacon = ""
browser = ""
logfile = open('log.txt', 'w+')
bot = set()
nonbot = set()
#seen = set()
browser_limit = 3
browsers = []
#browser_available = Array('b', browser_limit)
browser_available = []
browser_count = []
threads = []
antidoubler = set()
output = open('posts.html', 'w+')
connection_limit = browser_limit
connections = [] # for sql connections
cursors = []
testcounter = 0
GET_EXTERNAL = False
BROWSE_LIMIT = 10
primary_count = 0
LOAD_LIMIT = int(10000 / 30)
errorlog = open('errorlog.txt', 'w+')

def cleanup():
    global browsers
    for i, browser in enumerate(browsers):
        try:
            browser.close()
            print("closed browser {}".format(i))
        except:
            print("failed to close browser {} or browser is already closed".format(i))

def initConnections():
    global connections
    global cursors
    for i in range(connection_limit):
        config = {
            'user': "root",
            'password': 'root',
            'host': 'localhost',
            'database': 'Gab',
            'raise_on_warnings': True,
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_bin'
        }
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor(buffered=True)
        connections.append(cnx)
        cursors.append(cursor)

    

# prepares browsers for post crawling
def initBrowsers():
    global browsers
    global browser_available
    for i in range(browser_limit):
        browser_available.append(True)
        browser_count.append(0)
    for i in range(browser_limit):
        try:
            crawler = Browser('firefox', headless=True)
            crawler.visit("http://gab.ai")
            crawler.driver.implicitly_wait(3)
        
            username = "renewake"
            password = "1234!@#$"
            crawler.find_by_name("username").fill(username)
            crawler.find_by_name("password").fill(password)
            crawler.find_by_text("Login")[1].click()
            browsers.append(crawler)
            print("BROWSER " + str(i) + " SET UP")
            browser_available[i] = True
        except:
            print("PROBLEM LOGGING IN... ABORTING")
            sys.exit()
    print("A TOTAL OF " + str(len(browsers)) + " BROWSERS WERE PREPARED")
    
def scrapePosts(b_index, user):
    global browser_available
    global browsers
    
    print("BROWSER IN USE: " + str(b_index) + " OF " + str(len(browser_available)))
    #print("BROWSERLEN " + str(len(browsers)))
    #browser = browsers[b_index]
    #browser = Browser('firefox')
    #browser.visit("http://gab.ai")
    #browser.driver.implicitly_wait(3)
        
    #username = "renewake"
    #password = "1234!@#$"
    #browser.find_by_name("username").fill(username)
    #browser.find_by_name("password").fill(password)
    #print(browser.find_by_text("Login")[1].click())
    
    browser = browsers[b_index]
    
    # reset if necessary
    browser_count[b_index] += 1
    try:
        if browser_count[b_index] >= BROWSE_LIMIT:
            browser.quit()
            
            crawler = Browser('firefox', headless=True)
            crawler.visit("http://gab.ai")
            crawler.driver.implicitly_wait(3)
            
            username = "renewake"
            password = "1234!@#$"
            crawler.find_by_name("username").fill(username)
            crawler.find_by_name("password").fill(password)
            crawler.find_by_text("Login")[1].click()
            browsers[b_index] = crawler
            browser_count[b_index] = 0
            print("BROWSER {} RESET".format(b_index))
    except:
        print("failed to reset browser")
        
    browser = browsers[b_index]
    
    
    browser.visit("http://gab.ai/" + user)
    browser.driver.implicitly_wait(3)
    try:
        soup = BeautifulSoup(browser.html, features="html.parser")
    except selenium.common.exceptions.TimeoutException:
        browser_available[b_index] = True
        return AttributeError
    i = 0
    count = 0
    exceptcounter = 0
    try:
        load_count = 0
        while browser.find_by_text("Load more ") and load_count <= LOAD_LIMIT:
            browser.driver.implicitly_wait(1)
            time.sleep(1)
            try:
                browser.find_by_css('.post-list__load-more').click()
                load_count += 1
                soup = BeautifulSoup(browser.html, features="html.parser")
            except Exception:
                exceptcounter += 1
                if exceptcounter == 2:
                    break
                continue
            posts = soup.findAll("post")
            if len(posts) == count:
                break
            count = len(posts)
    except selenium.common.exceptions.WebDriverException:
        browser_available[b_index] = True
        return
    soup = BeautifulSoup(browser.html, features="html.parser")
    postlist = soup.findAll("post")
    for i, post in enumerate(postlist):
        try:
            ScrapAndAddPosts(post, user, b_index)
        except Exception as e:
            error = "FAILED TO PROCESS POST {} FOR USER {}: {}".format(i,user, e)
            print(error)
            errorlog.write(error)
    browser_available[b_index] = True
    
            
# performs a select or insert query
def DBexecuter(type, statement, values, cursor, cnx):
    try:
        if type == "select":
            if values == None:
                cursor.execute(statement)
            else:
                cursor.execute(statement, values)
            fetch = cursor.fetchall()
            return fetch
        elif type == "insert":
            cursor.execute(statement, values)
            cnx.commit()
    except mysql.connector.errors.InterfaceError:
        make_connection()
        DBexecuter(type, statement, values, cursor, cnx)

# opens a link in the browser
# waiting times are added for politeness
def getHTML(site):
    global browser
    print(site)
    for i in range(5):
        try:
            browser.visit(site)
            browser.driver.implicitly_wait(3)
            break
        except selenium.common.exceptions.TimeoutException:
            continue
        except selenium.common.exceptions.WebDriverException:
            login()
    return browser

# scrapes the popular page of the Gab
def ScrapPopular():
    soup = BeautifulSoup(getHTML("https://gab.ai/popular").html, features="html.parser")
    postlist = soup.findAll("post")
    for post in postlist:
        userLink =  post.find("a", {"class": "gab__meta__author"})["href"]
        AddUser(userLink[1:])

# check if a user is already in the database
def UserInDB(username):
    select = ("SELECT * FROM Gab.User WHERE User.username = %s;")
    values = (username,)
    fetch = DBexecuter("select", select, values, cursor, cnx)
    if len(fetch) == 0:
        return False
    else:
        return True
        
# check if user seen
def UserSeen(username):
    select = ("SELECT * FROM Gab.Seen WHERE Seen.username = %s;")
    values = (username,)
    fetch = DBexecuter("select", select, values, cursor, cnx)
    if len(fetch) == 0:
        return False
    else:
        return True
        
def MakeSeen(username):
    try:
        statement = ("INSERT INTO Gab.Seen(username)VALUES('{}')".format(username))
        cursor.execute(statement)
        cnx.commit()
    except Exception as e:
        error = "FAILED to make user seen: {}".format(e)
        print(error)
        errorlog.write(error)
        
def AddBot(username):
    try:
        statement = ("INSERT INTO Meta.Bots(name)VALUES('{}')".format(username))
        metacursor.execute(statement)
        metacon.commit()
    except Exception as e:
        error = "FAILED to add bot: {}".format(e)
        print(error)
        errorlog.write(error)
        
def IsKnownBot(username):
    select = ("SELECT * FROM Meta.Bots WHERE Bots.name = %s;")
    values = (username,)
    fetch = DBexecuter("select", select, values, metacursor, metacon)
    if len(fetch) == 0:
        return False
    else:
        return True
        
    
# check whether a follow relation is already added to the DB
def LinkInDB(follower, followee):
    select = ("SELECT * FROM Gab.Follows WHERE Follows.Follower = %s and Follows.Followee = %s;")
    values = (follower, followee)
    fetch = DBexecuter("select", select, values, cursor, cnx)
    if len(fetch) == 0:
        return False
    else:
        return True

def ScrapAndAddPosts(post, link, b_index):
    # print("PROCESSING POST ON SQL CONNECTION {}".format(b_index))
    browser = browsers[b_index]
    cursor = cursors[b_index]
    cnx = connections[b_index]
    username = post.find("span", {"class": "gab__meta__author__username"}).text[1:]
    if username == link:
        try:
            # find external links
            exlinks = []
            content = post.findAll("a");
            if content != None:
                for exlink in content:
                    linkdata = exlink.get('href')
                    if linkdata != None and linkdata[:4] == 'http' and linkdata[:15] != 'https://gab.ai/':
                        exlinks.append(exlink.get('href'))
            
            
            # finding hashtags
            content = post.find("div", {"class": "gab__body"})
            hashtags = []
            if content != None:
                text = content.text
                for a in content.findAll("a", {'class': lambda x: x and 'inner-post-hashtag' in x.split()}):
                    hashtags.append(a.text[1:])
            else:
                text = ""
            
            # finding media
            media = post.findAll("div", {'class': lambda x: x and 'post-attachment-media__item' in x.split()})
            urls = []
            for m in media:
                style = cssutils.parseStyle(m['style'])['background-image']
                urls.append(style.replace('url(', '')[:-1])
            actiondiv = post.find("div", {'class': lambda x: x and 'gab__actions' in x.split()})
            actions = actiondiv.findAll("a")
            likes = actions[0].text.replace(",", "")
            comments = actions[2].text[8:].replace(",", "")
            reposts = actions[3].text[6:].replace(",", "")
            try:
                likes = int(likes) if likes != "" else 0
            except:
                likes = 0
            try:
                comments = int(comments) if comments != "" else 0
            except:
                comments = 0
            try:
                reposts = int(reposts) if reposts != "" else 0
            except:
                reposts = 0
            
            # finding meta info
            info = post.find("div", {'class': lambda x: x and 'gab__meta__info' in x.split()})
            time = info.findAll("span")[0].text
            num = 1 if time.split()[0] == 'a' or time.split()[0] == 'an' else int(time.split()[0])
            if "month" in time.split()[1]:
                num = 30 * num
            elif "year" in time.split()[1]:
                num = 365 * num
            elif "hour" in time.split()[1]:
                num = 0
            delta = timedelta(days=-num)
            post_date = date.today() + delta

            statement = (
                "INSERT INTO Gab.Post(text, user, likes, comments, reposts, date)VALUES(%s,%s,%s,%s,%s,%s)")
            values = (text, username, likes, comments, reposts, post_date)
            DBexecuter("insert", statement, values, cursor, cnx)
            post = cursor.lastrowid
            for tag in hashtags:
                statement = ("INSERT INTO Gab.Hashtag(hashtag, postId)VALUES(%s,%s)")
                values = (tag, post)
                DBexecuter("insert", statement, values, cursor, cnx)
            for url in urls:
                statement = ("INSERT INTO Gab.Media(postId, url)VALUES(%s,%s)")
                values = (post, url)
                DBexecuter("insert", statement, values, cursor, cnx)
            exlinks = list(set(exlinks))
            
            for exlink in exlinks:
                linktext = ""
                if GET_EXTERNAL:
                    browser.visit(exlink)
                    browser.driver.implicitly_wait(3)
                    try:
                        soup = BeautifulSoup(browser.html, features="html.parser")
                        textlist = soup.findAll('p')
                        for textr in textlist:
                            text = textr.text.strip()
                            if text == "" or text == None:
                                continue
                            linktext += ' ' + text
                    except selenium.common.exceptions.TimeoutException:
                        print("failed to parse link")
                        continue
                statement = ("INSERT INTO Gab.Links(postId, text, url)VALUES(%s, %s, %s)")
                values = (post, linktext.strip(), exlink)
                DBexecuter("insert", statement, values, cursor, cnx)
        except Exception as e:
            error = "EXCEPTION in scrapandaddposts: {}".format(e)
            print(error)
            errorlog.write(error)

# insert a specific user to the DB, there are other attributes that should be captured here
def AddUser(link):
    page = getHTML("https://gab.ai/" + link)
    time.sleep(1)
    try:
        soup = BeautifulSoup(page.html, features="html.parser")
    except selenium.common.exceptions.TimeoutException:
        return AttributeError
    try:
        name = str(soup.find("span", {"class": "profile__name__username"}).previousSibling)
    except AttributeError:
        name = ""
    if soup.find("h1"):
        if soup.find("h1").text == "403 Forbidden":
            return AttributeError

    if not UserInDB(link):
        statement = (
            "INSERT INTO Gab.User(bio, followers, followings, username, name)VALUES(%s,%s,%s,%s,%s)")
        try:
            bio = soup.find("div", {'class': lambda x: x and 'profile__bio' in x.split()}).text
        except AttributeError:
            bio = ""
        try:
            followers = soup.find("a", {"href" : page.url[14:] + "/followers"}).text
            #followers = soup.findAll("a", {"class" : "profile__bar__nav"})[0].text
            followers = int(followers[:-9].replace(",", ""))
            followings = soup.find("a", {"href": page.url[14:] + "/following"}).text
            #followings = soup.findAll("a", {"class" : "profile__bar__nav"})[1].text
            followings = int(followings[:-9].replace(",", ""))
        except AttributeError:
            return AttributeError
        values = (bio, followers, followings, link, name)
        DBexecuter("insert", statement, values, cursor, cnx)

# check if user is known to be a bot
# if unknown, checks and updates
# also adds nonbot users to database
def IsBot(user, follower, link):
    print("\nCHECKING IF {} IS A BOT".format(user))
    global bot
    global nonbot
    global browsers
    global browser_available
    global antidoubler
    global browser
    global primary_count
    
    if IsKnownBot(user):
        print("USER {} IS A BOT".format(user))
        return True
    elif user in nonbot or UserInDB(user):
        statement = ("INSERT INTO Gab.Follows(Follower, Followee)VALUES(%s,%s)")
        values = (user,link) if follower else (link, user)
        if not LinkInDB(values[0], values[1]):
            DBexecuter("insert", statement, values, cursor, cnx)
        return False
    else:
        print("DOING FIRST TIME PROCESSING FOR {}".format(user))
        
        # check if we need to reset browser
        primary_count += 1
        if primary_count >= BROWSE_LIMIT:
            browser.quit()
            
            crawler = Browser('firefox', headless=True)
            crawler.visit("http://gab.ai")
            crawler.driver.implicitly_wait(3)
            
            username = "renewake"
            password = "1234!@#$"
            crawler.find_by_name("username").fill(username)
            crawler.find_by_name("password").fill(password)
            crawler.find_by_text("Login")[1].click()
            browser = crawler
            primary_count = 0
            print("PRIMARY BROWSER RESET")
        
        # check if user is bot or not
        page = getHTML("https://gab.ai/" + user)
        soup = BeautifulSoup(page.html, features="html.parser")
        isBot = False
        try:
            # find bio
            bio = soup.find('div', {'class':'profile__bio'})
            # bio message
            bioMessage = bio.find("div").text
            # find metadata
            profileBar = soup.find('div', {'class':'profile__bar'})
            meta = profileBar.findAll('a')
            # number of posts
            numposts = int(meta[1].text.split()[0].replace(',', ''))
            # number of followers
            numfollowers = int(meta[2].text.split()[0].replace(',', ''))
            # number of following
            numfollowing = int(meta[3].text.split()[0].replace(',', ''))
            # perform bot check logic
            if numposts == 0:
                isBot = True
            elif float(numfollowers)/numposts > 100:
                isBot = True
            elif numfollowing != 0 and float(numfollowing)/numposts > 100:
                isBot = True
            elif bioMessage[0] == '"' or bioMessage[0] == "'":
                isBot = True
            elif len(bioMessage.split()) >= 3:
                bioList = bioMessage.split()
                if bioList[-2][0] == '-' or bioList[-3] == '-':
                    isBot = True
        except:
            print("ERROR PARSING USER")
            isBot = True
        # update bot / nonbot
        if isBot:     
            print("USER {} IS A BOT".format(user))
            AddBot(user)
            #bot.add(user)
        else:
            nonbot.add(user)
    
    # if not bot, parse it here and now instead of reloading it
    # if is bot, push name into meta db
    if isBot:
        try:
            print("Adding {} to meta bot DB".format(user))
            statement = """insert into bots (name) values("{}")""".format(user)
            metacursor.execute(statement)
            metacon.commit()
        except:
            print("Failed to add {} to meta bot DB".format(user))
    else: # that is, not isBot
        print("ADDING NEW USER {} TO DATABASE AND SCRAPING POSTS".format(user))
        if not UserInDB(user) and not user in antidoubler:
            try:
                antidoubler.add(user)
                AddUser(user)
                print("GETTING POSTS FOR USER " + user)
                #print("JUST CHECKING... LEN BROWSERS is {}".format(len(browsers)))
                # grab posts here
                # check for an available browser
                while True:
                    found = False
                    for i in range(browser_limit):
                        #print("A - iteration " + str(i))
                        if browser_available[i] == True:
                            found = True
                            #print("B - browser available")
                            browser_available[i] = False
                            #print("C - set browser to unavailable")
                            #p = Process(target=scrapePosts, args=(i, user))
                            p = threading.Thread(target=scrapePosts, args=(i, user))
                            #print("D - process set")
                            threads.append(p)
                            #print("E - appended thread to threads list")
                            p.start()
                            #print("F - started thread")
                            print(user + " IS BEING CRAWLED ON BROWSER " + str(i))
                            break
                    if found:
                        print("DUPLICATE REQUEST IGNORED")
                        break
                    time.sleep(1)
                
            except:
                print("ENCOUNTERED EXCEPTION DOWNLOADING POSTS")
                return isBot
        if UserInDB(user):
            statement = ("INSERT INTO Gab.Follows(Follower, Followee)VALUES(%s,%s)")
            values = (user,link) if follower else (link, user)
            if not LinkInDB(values[0], values[1]):
                DBexecuter("insert", statement, values, cursor, cnx)
    return isBot
        
        
# find all followers and followings of a specific user
# there is a problem with this function, the list of followers and followings
# is not always loaded completely.
def AddNeighbors(link, follower):
    try:
        # at this point we know this is not a bot
        print("loading page...")
        if follower:
            page = getHTML("https://gab.ai/" + link + "/followers")
        else:
            page = getHTML("https://gab.ai/" + link + "/following")
        print("page loaded!")
        i = 1
        usersperload = 30
        targetcount = 0
        # how many should we have?
        soup = BeautifulSoup(page.html, features="html.parser")
        profileBar = soup.find('div', {'class':'profile__bar'})
        meta = profileBar.findAll('a')
        # number of followers
        numfollowers = int(meta[2].text.split()[0].replace(',', ''))
        # number of following
        numfollowing = int(meta[3].text.split()[0].replace(',', ''))
        if follower:
            targetcount = numfollowing
        else:
            targetcount = numfollowers
            
        print(targetcount)
        #TODO: REMOVE
        #targetcount = min(5, targetcount)
        try:
            load_count = 0
            while page.find_by_text("Load more") and load_count <= LOAD_LIMIT:
                if targetcount < usersperload:
                    break
                page.driver.implicitly_wait(1)
                time.sleep(1)
                page.find_by_css('.user-list__load').click()
                load_count += 1
                i += 1
                usersloaded = i * usersperload
                print("loaded {}/{}...".format(usersloaded, targetcount))
                if usersloaded >= targetcount:
                    break
        except selenium.common.exceptions.WebDriverException:
            pass

        soup = BeautifulSoup(page.html, features="html.parser")
        users = soup.findAll("a", {"class": "user-list__item__name__username"})
        print(len(users))
        nonbotusers = []
        for user in users:
            try:
                f_link = user.text[1:]
                # these are the users we are checking
                if IsBot(f_link, follower, link):
                    continue
                nonbotusers.append(user)
                print("added user {} to network".format(f_link))
            except Exception as e:
                error = "error in addneighbors user loop: {}".format(e)
                print(error)
                errorlog.write(error)
                continue
        return nonbotusers
    except:
        print("fatal error in addneighbors")
        return []

# Gets the list of users whose followers are not still crawled and sorts them by the number of their
# followers according to their information. Then uses a queue to crawl the users and their followers.
# Followers are added to the queue and crawled later in the process
def MakeNetwork():
    global bot
    global nonbot
    #global seen
    global primary_count
    global browser
    
    # cheat a little... cut the bot checking wait...
    global metacursor
    global metacon
    config = {
        'user': "root",
        'password': 'root',
        'host': 'localhost',
        'database': 'Meta',
        'raise_on_warnings': True,
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_bin'
    }
    metacon = mysql.connector.connect(**config)
    metacursor = metacon.cursor(buffered=True)
    readBots = "Select name from bots"
    botusers = DBexecuter("select", readBots, None, metacursor, metacon)
    for b in botusers:
        botuser = b[0].decode("utf-8")
        #seen.add(botuser)
        MakeSeen(botuser)
        AddBot(botuser)
        #bot.add(botuser)
        print("Added to botlist from DB: {}".format(botuser))
    
    
    #readUsers = "Select User.username from User left join Follows on User.username = Follows.followee where Follows.Follower is null order by User.followers desc"
    readUsers = "Select username from User"
    #readUsers = "Select `User`.`username` From User Order By User.Followers DESC"
    #readUsers = "Select A.Followee, (`User`.`followers` - A.counts) as Dif from (select Followee, count(*) as counts from Follows Group by Follows.Followee) as A join User on User.username = A.Followee order by Dif DESC"
    users = DBexecuter("select", readUsers, None, cursor, cnx)
    q = queue.Queue()
    for u in users:
        user = u[0].decode("utf-8")
        #seen.add(user)
        MakeSeen(user)
        nonbot.add(user)
        q.put(user)
        print("Added to network from DB: {}".format(user))
    global testcounter
    
    while not q.empty():
        # ensure we haven't gone over browse limit
        primary_count += 1
        if primary_count >= BROWSE_LIMIT:
            try:
                    browser.quit()
                    
                    crawler = Browser('firefox', headless=True)
                    crawler.visit("http://gab.ai")
                    crawler.driver.implicitly_wait(3)
                    
                    username = "renewake"
                    password = "1234!@#$"
                    crawler.find_by_name("username").fill(username)
                    crawler.find_by_name("password").fill(password)
                    crawler.find_by_text("Login")[1].click()
                    browser = crawler
                    primary_count = 0
                    print("PRIMARY BROWSER RESET")
            except:
                print("failed to reset primary browser")
        
        user = q.get() # known not to be bot
        testcounter += 1
        print("\nSCRAPING " + user)
        print("grabbing followings")
        followings = AddNeighbors(user, False) # NOTE: THIS FILTERS BOTS ON ITS OWN
        print("grabbing followers")
        followers = AddNeighbors(user, True)
        print("found {} following".format(len(followings)))
        print("found {} followers".format(len(followers)))


        for f_raw in (followings + followers):
            try:
                f = f_raw.text[1:]
                if not UserSeen(f): # if user not yet seen .. IF SLOW, WE CAN MAKE THIS IF NOT USERINDB
                    print("\nappending user {} to the queue...".format(f))
                    q.put(f)
                    MakeSeen(f)
                print("there are now {} members in the queue".format(len(q)))
            except:
                print("error adding user to queue")
                continue
                
    
# loads all posts in a user's page and scrapes the posts
def ScrapUser(link):
    # page = getHTML("https://gab.ai/" + link)
    i = 0
    count = 0
    try:
        load_count = 0
        while (page.find_by_text("Load more") and i < 10) and load_count <= LOAD_LIMIT:
            page.driver.implicitly_wait(1)
            time.sleep(1)
            try:
                page.find_by_css('.post-list__load-more').click()
                load_count += 1
                soup = BeautifulSoup(page.html, features="html.parser")
            except Exception:
                continue
            users = soup.findAll("post")
            if len(users) == count:
                i += 1
            count = len(users)
    except selenium.common.exceptions.WebDriverException:
        return
    soup = BeautifulSoup(page.html, features="html.parser")
    postlist = soup.findAll("post")
    for post in postlist:
        ScrapAndAddPosts(post, link, b_index)

def make_connection():
    config = {
        'user': "root",
        'password': 'root',
        'host': 'localhost',
        'database': 'Gab',
        'raise_on_warnings': True,
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_bin'
    }
    global cnx
    global cursor
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor(buffered=True)

def GetPosts():
    #readUsers = "Select User.username from User"
    readUsers = "Select Follows.Followee, Count(*) as counts From Follows Group By Follows.Followee Order by count(*) DESC "
    users = DBexecuter("select", readUsers, None, cursor, cnx)

    readUsers = "Select Distinct user from Post"
    existing_users = DBexecuter("select", readUsers, None, cursor, cnx)
    existing_users = [str(x[0]) for x in existing_users]

    begin = False
    for u in users:
        if begin:
            if str(u[0]) not in existing_users:
                ScrapUser(u[0].decode("utf-8"))
        if u[0].decode("utf-8") == "Deutschland77":
            begin = True

# Find potential hate posts using a dictionary
def exportHatePosts():
    getposts = "select postId, date, text from Post"
    posts = DBexecuter("select", getposts, None, cursor, cnx)
    hate = []
    with open("mydictionary.txt", "r") as dic:
        for l in dic.readlines():
            hate.append(l.replace("\n", ""))
    count = 0
    with open("gab.json", "w") as gab:
        for post in posts:
            for i in hate:
                if i in post[2].lower():
                    if "..." in post[2] and "http" not in post[2]:
                        continue
                    else:
                        sent = cleanPost(post[2])
                        entity = {}
                        tags = []
                        for tag in sent.split():
                            if tag[0] == "#":
                                tags.append(tag)
                        entity["tid"] = str(post[0])
                        entity["timestamp"] = int(
                            time.mktime(time.strptime(str(post[1]), '%Y-%m-%d')))
                        entity["text"] = sent
                        entity["full_text"] = sent
                        entity["retweet"] = False
                        entity["entities"] = tags
                        json.dump(entity, gab)
                        gab.write("\n")
                        break
    print(count)


def cleanPost(post):
    sent1 = " ".join(
        w.decode("utf-8").replace("#", " #").replace("@", " @").replace("http", " http").replace("&amp;", "&").replace("...", "... ") for w in
        post.split()).lstrip()
    sent = ''.join([i if ord(i) < 128 else '' for i in sent1])
    sent = sent.replace('\"', "")
    return sent

# Export all the posts into a pandas dataframe
def exportAll():
    getposts = "select postId, text, user from Post"
    posts = DBexecuter("select", getposts, None, cursor, cnx)

    index = [u[0] for u in posts]

    text = [cleanPost(u[1]) for u in posts]

    user = [u[2].decode("utf-8") for u in posts]

    data = {"index": index, "text": text, "user": user}
    df = pd.DataFrame(data)
    df.to_pickle("gab_all.pkl")

def main():
    
    try:
        
        logfile.write("START: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
        print("Making DB Connections")
        make_connection()
        initConnections()
        print("Logging in to Gab.ai")
        login()
        logfile.write("BROWSER SET UP: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
        print("Setting up crawler browsers")
        initBrowsers()
        print("{} crawler browsers were set up".format(len(browsers)))
        logfile.write("CRAWLER BROWSERS SET UP: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
        
        # starts scraping from Milo Yiannopoulos!
        print("Creating Network")
        AddUser("Pamela")
        MakeNetwork()
        logfile.write("NETWORK CREATED: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
        #print("Getting Posts")
        #GetPosts()
        #logfile.write("POSTS COLLECTED: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
        #print("Exporting Data")
        #exportAll()
        for thread in threads:
            thread.join()
      
        logfile.write("DONE: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
        print("DONE: {} USERS CRAWLED".format(testcounter))
    except Exception as e:
        errorlog.write(e)
        print(e)
    finally:
        errorlog.close()
        browser.quit()
        for b in browsers:
            b.quit()
    

def login():
    global browser

    # insert your own path-to-driver here
    #executable_path = {'executable_path': 'C:/Users/Jun/Documents/gab/chromedriver.exe'}
    #browser = Browser('chrome', **executable_path)
    browser = Browser('firefox', headless=True)
    browser = getHTML("https://gab.ai/")
	

    # It's an account I have already created
    username = "renewake"
    password = "1234!@#$"
    browser.find_by_name("username").fill(username)
    browser.find_by_name("password").fill(password)
    print(browser.find_by_text("Login")[1].click())

if __name__ == "__main__":
    main()