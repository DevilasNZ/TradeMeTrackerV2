import requests,bs4,statistics,datetime
from listing import Listing

#the searchterm class is used to manage searches on trade me

class SearchTerm:

    #parse one line of data from the search term dataset. This is translated to data points saved in the class.
    #syntax:
    #[search-term],[category],[condition(new/used)],[deal-detection-enabled(true/false)],[bagain-price-factor(as a % of median price, integer)],[max excluded terms],[excluded-terms],... (unlimited number of excluded terms on the end of the line.)
    def __init__(self,raw_search_term_data):

        self.id = raw_search_term_data[0]
        self.search_name = raw_search_term_data[1]#the user entered name of the search.
        self.search_term = raw_search_term_data[2]
        self.category = raw_search_term_data[3]
        self.condition = raw_search_term_data[4]
        self.deal_detection_enabled = bool(raw_search_term_data[5])
        self.bargain_price_factor = raw_search_term_data[6]
        self.max_excluded_terms = raw_search_term_data[7]#how many excluded terms are allowed in a listing before disregarding it.
        if len(raw_search_term_data) > 7:
            self.excluded_terms = raw_search_term_data[8].split(',')
        else:
            self.excluded_terms = []

        self.fetched_data = False
        self.expired_listings = []#temporary storage for the latest collection of expired listings
        self.long_term_data = ()#tuple of data to be written to MySQL

    def __str__(self):
        return "{}\n{}\n{}\nDeal detection enabled? {}\nBargain price factor: {}%\nExcluded search terms: {}\n".format(self.search_term, self.category, self.condition, self.deal_detection_enabled, self.bargain_price_factor, self.excluded_terms)

    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #fetch all the needed data from Trade Me.
    def fetch_data(self):
        self.clear_data()

        still_searching = True
        search_page = 1
        while still_searching:
            link_text_expired_listings = "https://www.trademe.co.nz/Browse/SearchResults.aspx?sort_order=bids_asc&from=advanced&advanced=true&searchstring=" + self.search_term + "&current=0&cid=0&rptpath=all&searchregion=100&page=" + str(search_page)

            try:
                #make the request and soup
                exp_res = requests.get(link_text_expired_listings)
                exp_res.raise_for_status()
                expired_search_result_soup = bs4.BeautifulSoup(exp_res.text,features="html.parser")
            except requests.exceptions.HTTPError as err:
                still_searching = False
                print("an HTTP error occured fetching expired listings under the search " + self.search_term)

            #go through all the listings on this page, checking to see if they have bids
            raw_listings_this_page = expired_search_result_soup.find_all("li",class_="listingCard")
            for listing in raw_listings_this_page:
                if "Current bid" in listing.text: #the current bid section in the html indicates if bid/s have been placed on the item.
                    #get the link and make a listing object.
                    listing_link = listing.find('a',href=True)['href']
                    #if the listing link is for property or motors, prevent it being made into a listing object
                    if "/property/" in listing_link or "/motors/" in listing_link or "/farming-forestry/" in listing_link:
                        print("found a bad item, link: "+listing_link)
                    else:
                        this_listing = Listing("https://www.trademe.co.nz" + listing_link, self.id)
                        self.expired_listings.append(this_listing)
                else:
                    #stop searching if the script hits listings without bids on the page.
                    still_searching = False

            #stop searching if there are no more listings.
            listing_count_text_parts = expired_search_result_soup.find('p',class_="listing-count-holder").text.split(" ")
            if listing_count_text_parts[0] == listing_count_text_parts[-1]:
                still_searching = False

            search_page += 1

        #---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #clean the listings that were found

        #clean out all the listings that:
        ## are not from the same category as the search term.
        i = 0
        while i < len(self.expired_listings):
            if self.category.lower() in self.expired_listings[i].category.lower():
                i += 1
            else:
                del self.expired_listings[i]

        ## contain too many excluded terms TODO: this doesnt appear to be working properly, it's not important for now, but it will help refine results.
        while i < len(self.expired_listings):
            excluded_word_count = len([ele for ele in self.excluded_terms if(ele in self.expired_listings[i].description.lower())]) + len([ele for ele in self.excluded_terms if(ele in self.expired_listings[i].listingName.lower())])

            if excluded_word_count > self.max_excluded_terms:
                print("listing ID {} contained too many excluded terms. The listing will not be recorded.".format(self.expired_listings[i].id))
                del self.expired_listings[i]
            else:
                i+=1

        print("finished finding expired listings for the search term '{}', returned {} results".format(self.search_term,len(self.expired_listings)))

        #---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #fetch all the long term data.
        expired_listing_count = len(self.expired_listings)

        #find how many current listings there are.
        link_text = "https://www.trademe.co.nz/Browse/SearchResults.aspx?searchString=" + self.search_term + "&type=Search&searchType=all&user_region=100&user_district=0&generalSearch_keypresses=5&generalSearch_suggested=0&generalSearch_suggestedCategory="

        #make the request and soup
        res = requests.get(link_text)
        res.raise_for_status()
        search_result_soup = bs4.BeautifulSoup(res.text,features="html.parser")

        #get the number of results returned.
        resultCount = search_result_soup.select("#totalCount")
        current_listing_count = int(resultCount[0].getText())

        #get the median sale price of sold listings.
        sold_listings_prices = []
        for listing in self.expired_listings:
            sold_listings_prices.append(listing.current_bid)

        median_sell_price = statistics.median(sold_listings_prices) if len(self.expired_listings) > 0 else None

        #finally, make the long term data tuple so that these statistics can be recorded in MySQL.
        #format: (search_id, date, active_listings, sold_listings, median_sell_price)
        date = str(datetime.datetime.now())
        self.long_term_data = (self.id, date, current_listing_count, expired_listing_count, median_sell_price)


        self.fetched_data = True

    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #Getters for the fetched data.
    def get_expired_listings(self):
        if self.fetched_data:
            return self.expired_listings
        else:
            self.fetch_data()
            return self.get_expired_listings()#this may cause recursive issues if there is a problem with the fetch code.

    def get_long_term_data(self):
        if self.fetched_data:
            return self.long_term_data
        else:
            self.fetch_data()
            return self.get_long_term_data()#this may cause recursive issues if there is a problem with the fetch code.

    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #CLear out all the data. should help with memory use. To be used after the data is written to the database.
    def clear_data(self):
        self.fetched_data = False
        self.expired_listings = []
        self.long_term_data = ()
