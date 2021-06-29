FROM ubuntu

#Install dependencies
RUN apt update -y && apt install -y git python3 python3-pip
RUN pip install mysql-connector-python requests beautifulsoup4 lxml

#Clone and run the code
RUN git clone https://github.com/DevilasNZ/TradeMeTrackerV2

CMD ["python3","-u","/TradeMeTrackerV2/TradeMeTrackerV2.py"]
