#this code goes through current tradeMe listings for a search and determines whether they are a bargain according to the seach parameters set.
## NOTE: for now these deals should be output to the console, but in future there should be a notification system.

from searchterm import SearchTerm
from listing import Listing
import sys,mysql.connector,datetime,time,os

#set the database details depending on the working environment
if(os.environ['DEV_ENV'] == "production"):
    print("=====running tracker in production environment====")
    database_name = '`TradeMe_Tracker`'
    database_user = 'tmt'
else:
    print("====running tracker in development environment====")
    database_name = '`TradeMe_Tracker_dev`'
    database_user = 'tmt_dev'

#grab the password from the password file.
password_file = open("dbPassword.txt","r")
db_password = password_file.readline()
password_file.close()

#establish a connection to the MySQL db.
try:
    tmt_db = mysql.connector.connect(
      host="192.168.1.176",
      user=database_user,
      password=db_password
    )

    tmt_cursor = tmt_db.cursor()
    print("successfully connected to the MySQL database.")

except:
    sys.exit("There was an error connecting to the Trade Me Tracker DB. Is the SQL server running?")

#retrieve the list of searches
