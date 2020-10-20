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
        raw_JSON = str(soup.find('script'))[35:-9]
        item_JSON = json.loads(raw_JSON,strict=False)

        self.listingName = item_JSON['name']
        self.category = item_JSON['category']
        self.description = item_JSON['description']

        #get bidding data.
        self.current_bid = float(soup.find(id="Bidding_CurrentBidValue").contents[0][1:].replace(',',''))
        reserve_text = soup.find(id="Bidding_ReserveLabel").contents[0]
        if reserve_text == "Reserve met" or reserve_text == "No reserve":
            self.reserve_met = True
        else:
            self.reserve_met = False

        #calculate the close date and time of the listing.
        self.close_datetime_str = soup.find(id="ClosingTime_ClosingTime").contents[0]
        self.close_datetime = datetime.datetime.strptime(self.close_datetime_str,'%a %d %b, %I:%M %p')
        #determine the close year
        current_datetime = datetime.datetime.now()
        if self.close_datetime.month > current_datetime.month:
            #if the close month is greater than the current month, it must have been sold last year.
            self.close_datetime_str = self.close_datetime_str + " " + str(current_datetime.year-1)
        else:
            #if the close month is less than the current month, the listing must be from this year.
            self.close_datetime_str = self.close_datetime_str + " " + str(current_datetime.year)
        self.close_datetime = datetime.datetime.strptime(self.close_datetime_str,'%a %d %b, %I:%M %p %Y')

    def __str__(self):
        return "listing id: {}\n{}\n{}\n{}\nFinal bid: ${}\nreserve met? {}\nClose datetime: {}\nSQL Tuple: {}\n{}\n".format(self.id,self.listingName, len(self.listingName)*"-", self.category, self.current_bid, self.reserve_met, self.close_datetime,self.get_sql_tuple(),self.description)

    #used for inserting listing records into the mysql listings table.
    def get_sql_tuple(self):
        return (self.id,self.search_id,self.listingName,self.category,self.description,self.current_bid,str(self.close_datetime))

#class for a current listing:
# class LiveListing:
#     def __init__(self,item_url):


# if self.is_live_listing:
#     return "{}\n{}\n{}\nBuy now: ${}\nStart price: ${}\nreserve met? {}\n{}".format(self.listingName, len(self.listingName)*"-", self.category, self.buy_now_price, self.current_bid, self.reserve_met, self.description)

# if is_live_listing:
#     self.buy_now_price = float(item_JSON['Offers'][0]['price'].replace(',',''))
