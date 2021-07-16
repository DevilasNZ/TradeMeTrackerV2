import requests,bs4,json,datetime
from lxml import html

#class for expired listing:
class Listing:

    def __init__(self,item_url,search_id):
        print("scanning " + item_url)

        self.id = int(item_url[-24:-14])
        self.search_id = search_id

        #get the raw html JSON data.
        res = requests.get(item_url)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text,features="html.parser")

        #in newer versions of the site, the JSON data has been moved to the bottom of the page source.
        raw_JSON = str(soup.find('script', {'id':"frend-state"}))[49:-9]
        raw_JSON = raw_JSON.replace('&q;','\"')
        item_JSON = json.loads(raw_JSON,strict=False)
        item_JSON = item_JSON['NGRX_STATE']['listing']['cachedDetails']['entities'][str(self.id)]['item']

        #general listing data
        self.listingName = item_JSON['title']
        self.category = item_JSON['categoryPath']
        self.description = item_JSON['body']

        #date related data
        start_datetime_str = item_JSON['startDate'][9:-5]
        self.start_datetime = datetime.datetime.strptime(start_datetime_str,'%Y-%m-%dT%H:%M:%S')
        close_datetime_str = item_JSON['endDate'][9:-5]
        self.close_datetime = datetime.datetime.strptime(close_datetime_str,'%Y-%m-%dT%H:%M:%S')

        #bidding data.
        self.start_price = item_JSON['startPrice']
        self.sell_price = item_JSON['maxBidAmount']
        if 'isReserveMet' in item_JSON:
            self.reserve_met = item_JSON['isReserveMet']
        else:
            self.reserve_met = False
        self.bid_count = item_JSON['bidCount']

        #seller data
        self.seller_name = item_JSON['member']['nickname']
        self.seller_id = item_JSON['member']['memberId']
        self.seller_unique_negative = item_JSON['member']['uniqueNegative']
        self.seller_unique_positive = item_JSON['member']['uniquePositive']
        self.seller_feedback_count = item_JSON['member']['feedbackCount']
        if 'isInTrade' in item_JSON['member']:
            self.seller_in_trade = item_JSON['member']['isInTrade']
        else:
            self.seller_in_trade = False
        self.seller_district = item_JSON['suburb']
        self.seller_region = item_JSON['region']

        #payment data
        if 'hasPing' in item_JSON:
            self.has_ping = item_JSON['hasPing']
        else:
            self.has_ping = False
        self.allows_pickups = bool(item_JSON['allowsPickups'])
        self.shipping_options = len(item_JSON['shippingOptions'])
        self.payment_options = item_JSON['paymentOptions']

        #marketing data
        if 'isFeatured' in item_JSON:
            self.is_featured = item_JSON['isFeatured']
        else:
            self.is_featured = False
        if 'hasGallery' in item_JSON:
            self.has_gallery = item_JSON['hasGallery']
        else:
            self.has_gallery = False
        photos = item_JSON['photos']
        self.photo_keys = []
        for p in photos:
            self.photo_keys.append(p['key'])
        self.photo_count = len(self.photo_keys)

        #bidder interaction data
        self.watchers = item_JSON['bidderAndWatchers']
        self.view_count = item_JSON['viewCount']
        if 'unansweredQuestionCount' in item_JSON:
            self.unanswered_question_count = item_JSON['unansweredQuestionCount']
            self.question_count = item_JSON['questions']['totalCount']
        else:
            #no questions have been asked.
            self.unanswered_question_count = 0
            self.question_count = 0

    def __str__(self):
        return "listing id: {}\n{}\n{}\n{}\nFinal bid: ${}\nreserve met? {}\nClose datetime: {}\nSQL Tuple: {}\n{}\n".format(self.id,self.listingName, len(self.listingName)*"-", self.category, self.current_bid, self.reserve_met, self.close_datetime,self.get_sql_tuple(),self.description)

    #used for inserting listing records into the mysql listings table.
    def get_sql_tuple(self):
        return (self.id
        ,self.search_id
        ,self.listingName
        ,self.category
        ,self.description
        ,self.start_datetime
        ,self.close_datetime
        ,self.start_price
        ,self.sell_price
        ,self.bid_count
        ,self.seller_name
        ,self.seller_id
        ,self.seller_unique_negative
        ,self.seller_unique_positive
        ,self.seller_feedback_count
        ,self.seller_in_trade
        ,self.seller_district
        ,self.seller_region
        ,self.has_ping
        ,self.allows_pickups
        ,self.shipping_options_count
        ,self.payment_options
        ,self.is_featured
        ,self.has_gallery
        ,self.photo_keys
        ,self.photo_count
        ,self.watchers
        ,self.view_count
        ,self.unanswered_question_count
        ,self.question_count)
