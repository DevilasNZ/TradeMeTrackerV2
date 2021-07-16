from searchterm import SearchTerm
from listing import Listing
import sys,mysql.connector,datetime,time,os

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
print("running tracker version 2.04")


#find and return all the search results stored in MySQL.
def get_search_terms(cursor):
    #get search terms from the database.
    # try:
    sql = "SELECT * FROM "+schema+".search_terms;"
    cursor.execute(sql)
    sql_result = cursor.fetchall()

    # except:
    #     sys.exit("There was an error fetching search terms from the database.")

    search_terms = []

    #load the search terms from SQL into Search term objects
    for x in sql_result:
        search_term_object = SearchTerm(x)
        search_terms.append(search_term_object)

    return search_terms

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#check every loaded search term to see if data is due for collection. If so, scrape trademe to obtain said data.
def run_tracker(search_terms,db,cursor):
    listing_sql = "INSERT INTO " + schema + ".'expired_listings' " + """('id'
    ,'search_id'
    ,'name'
    ,'category'
    ,'description'
    ,'start_datetime'
    ,'close_datetime'
    ,'start_price'
    ,'sell_price'
    ,'bid_count'
    ,'seller_name'
    ,'seller_id'
    ,'seller_unique_negative'
    ,'seller_unique_positive'
    ,'seller_feedback_count'
    ,'seller_in_trade'
    ,'seller_district'
    ,'seller_region'
    ,'has_ping'
    ,'allows_pickups'
    ,'shipping_options_count'
    ,'payment_options'
    ,'is_featured'
    ,'has_gallery'
    ,'photo_keys'
    ,'photo_count'
    ,'watchers'
    ,'view_count'
    ,'unanswered_question_count'
    ,'question_count')
    VALUES (" + "%s," * 28 + "%s)"""
    long_term_data_sql = "INSERT INTO "+schema+".`long_term_data` (`search_id`, `date`, `active_listings`, `sold_listings`, `median_sell_price`) VALUES (%s, %s, %s, %s, %s)"

    for term in search_terms:
        #firstly, check if data is due to be written to the database (it should be done weekly)
        check_due = False
        check_term_sql = "SELECT date FROM "+schema+".long_term_data WHERE search_id={} AND date >= NOW() - INTERVAL 7 DAY".format(term.id)
        try:
            cursor.execute(check_term_sql)
            check_term_sql_result = cursor.fetchall()
            if(len(check_term_sql_result) == 0): check_due = True#if no recent results show up, it must be due to check again.
        except:
            print("there was an issue with checking if data was due for an update for the search term " + term.search_name)

        if check_due:
            print("Running data collection for search id = " + str(term.id))
            term.fetch_data()

            #write the long term data.
            this_long_term_data = term.get_long_term_data()
            try:
                cursor.execute(long_term_data_sql,this_long_term_data)
                db.commit()
            except:
                print("there was an issue with writing long term data for the search term " + term.search_name)

            these_expired_listings = term.get_expired_listings()
            if(len(these_expired_listings) > 0):
                for listing in these_expired_listings:
                    if !listing.error:
                        #for each of the found listings get the sql tuple and try and insert the listing into the database. if the listing already exists it will throw an error.
                        this_listing_tuple = listing.get_sql_tuple()
                        # try:
                        cursor.execute(listing_sql,this_listing_tuple)
                        # except:
                        #     print("there was an issue with listing " + str(listing.id) + ". is it already in the database?")
                db.commit()

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#establish a connection to the MySQL db.
try:
    db = mysql.connector.connect(
      host=os.getenv('DB_HOST'),
      user=os.getenv('DB_USER'),
      password=os.getenv('DB_PASSWORD')
    )

    cursor = db.cursor()
    schema = os.getenv('DB_SCHEMA')
    print("successfully connected to the MySQL database.")
except:
    print("There was an error connecting to the Trade Me Tracker DB. Is the SQL server running?")
    sys.exit(0)

#the main process loop.
# BUG: the tracker doesnt seem to be automatically finding new searches that are added after the script is started. Is there a typo in the while loop?
while True:
    #get/refresh the search terms.
    print('Grabbing search terms from MySQL...')
    trademe_searches = get_search_terms(cursor)
    print('Done',end='\n\n')

    #run the tracker for the search terms.
    print('executing tracker for {} searches...'.format(len(trademe_searches)))
    run_tracker(trademe_searches,db,cursor)
    print('Finished running tracker on {}'.format(datetime.datetime.now()),end='\n\n')
    print('tracker will run again in 6 hours.')
    time.sleep(21600)
