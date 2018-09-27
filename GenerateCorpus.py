import mysql.connector
import json

#define
USER = 0
DATE = 1
ID = 2
TEXT = 3

# set up file
ofile = open("corpus.json", "w+")

# connect to server
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

# get list of users
userlist = []
readUsers = "Select user, sum(1) as sumposts from post group by user order by sumposts desc limit 800"
cursor.execute(readUsers)
for user in cursor.fetchall():
    userlist.append(user[0].decode("utf-8"))
    
# get 8000 posts
posts = []
for i, user in enumerate(userlist):
    print("USER {}".format(i+1))
    getPosts = "Select user, date, postId, text from post where user = '{}' order by date desc limit 10".format(user)
    cursor.execute(getPosts)
    for post in cursor.fetchall():
        user = post[USER].decode("utf-8")
        date = post[DATE].decode("utf-8")
        postid = post[ID]
        text = post[TEXT].decode("utf-8").replace("\n", " ").replace('"', "'").strip()
        posts.append(tuple([user, date, postid, text]))
 
# sort by date descending
posts.sort(key=lambda tup: int(tup[DATE].replace("-", "")), reverse=True)

# write to file
lines = 0
for post in posts:
    if post[TEXT] == "":
        continue
    lines += 1
    datadict = { "user" : post[USER], "date" : post[DATE], "postid" : post[ID], "text" : post[TEXT]}
    ofile.write(json.dumps(datadict))
    ofile.write("\n")
    
print("Succesfully wrote {} lines".format(lines))