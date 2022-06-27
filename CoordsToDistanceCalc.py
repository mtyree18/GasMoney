from haversine import haversine, Unit
import csv
import json
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import dropbox


csv_filename = "recent_trip.csv"
json_filename = "points.json"
DROPBOX_ACCESS_TOKEN = "sl.BKQysbk1dZQ6G1FCORVOQ4oEIbB5Co" \
                       "nQyfuDjf1FPUjxp5-MnaoJYLHr8e7AVv-Eh" \
                       "B5xSyP18e7ojHz4SKnrICXNYTHel2Lk96IY4Wv" \
                       "2neDdp842vC5ktKi5gqVBpWhjluMyTqMerCq5"


# connect to dropbox
def dropbox_connect():
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    return dbx


# a function to retrieve the most recent csv file
def dropbox_get_recent_csv():
    # calling the connect to dropbox function
    dbx = dropbox_connect()
    recent = 0
    # creating a for loop that loops through my dropbox files not in a folder
    # (which is where they're stored by default when you upload the file). Because
    # the files are automatically named with the date and time at the end of them,
    # I check for the most recent date (largest number) and return the name of that file
    for file in dbx.files_list_folder("").entries:
        if int(file.name[7:21]) > recent:
            recent = int(file.name[7:21])
            recent_file_name = file.name
    return recent_file_name


# this function makes a new empty csv, and fills it with the content it downloads from
# the dropbox file. That is the csv we use in the rest of the code to find total distance
def dropbox_download_file():
    dbx = dropbox_connect()
    with open("recent_trip.csv", 'wb') as f:
        metadata, res = dbx.files_download(path=f"/{dropbox_get_recent_csv()}")
        f.write(res.content)


# This deletes the first line of the csv which when downloaded from the app
# is an unnecessary one that messes up the program
def delete_unnecessary(csv_path):
    with open(csv_path, 'r+') as dl:
        lines = dl.readlines()
        if "#" in lines[0]:
            dl.seek(0)
            dl.truncate()
            dl.writelines(lines[1:])


# this converts the csv to json, which I did so that I could access lat and lon from a dictionary
def convert_json(csv_path, json_path):
    # establishing empty dictionary
    data = {}
    n = 0
    with open(csv_path, encoding='utf-8-sig') as csvf:
        # creating a reader object to parse through csv file
        csvreader = csv.DictReader(csvf)
        # a for loop to go through each row of reader object
        for row in csvreader:
            # I wanted to make my own numbered keys for each row, so I used an increasing int to appoint them
            key = n
            # appointing a row to each consecutive dictionary item (with key n)
            data[key] = row
            n += 1
    # dumps the dictionary into the json file
    with open(json_path, 'w') as jsonf:
        jsonf.write(json.dumps(data, indent=4))


# formula to calculate distance based on the points in the json file
def distance_calc(json_path):
    distance = 0
    with open(json_path, "r") as p:
        # looking back on this I didn't have to convert it to json because what I'm
        # doing here is just putting the dictionary into json format and then taking
        # it back out of json format to put in a new dictionary
        dictionary = json.loads(p.read())
        # a for loop to iterate through the entire dictionary minus one
        for n in range(0, len(dictionary) - 1):
            # gathering the latitude and longitudes to construct points.
            # Because the values in this dictionary were actually another dictionary
            # I had to input two keys. One for which point in time I'm looking for and
            # one for getting lat/lon
            lat1 = float(dictionary[f"{n}"][" Latitude (deg)"])
            lat2 = float(dictionary[f"{n+1}"][" Latitude (deg)"])
            lon1 = float(dictionary[f"{n}"][" Longitude (deg)"])
            lon2 = float(dictionary[f"{n+1}"][" Longitude (deg)"])
            point1 = (lat1, lon1)
            point2 = (lat2, lon2)
            # running my points through a very useful haversine function from the
            # haversine module to get the distance from point to point
            d = haversine(point1, point2, unit=Unit.MILES)
            # those distances are added up (because of course the
            # dictionary is just a ton of different points)
            # and this function returns the total distance of all the points in the csv
            distance += d
    return distance


# this function takes distance and converts it to gas cost based on current prices in VA
def distance_to_cost(distance):
    # miles per gallon of my car in the city
    mpg = 23
    # requesting the gas prices web page. headers is used to trick the website into
    # thinking I'm a normal user requesting this page
    req = Request("https://gasprices.aaa.com/?state=VA", headers={'User-Agent': 'Mozilla/5.0'})
    # reads the data from the webpage I just requested
    webpage = urlopen(req).read()
    # created a beautiful soup object that parses the webpage and gets all the data from it.
    # This data is what you would see if you did inspect element.
    soup = BeautifulSoup(webpage, "html.parser")
    # this line finds the gas price by navigating to the numb class and extracting its value
    gas_price = soup.find('p', class_='numb').text
    # this formats the string into an actual number
    formatted_gas_price = float(gas_price[8:])
    # simple formula to get the amount it cost you to go the distance that was retrieved
    # from the earlier function
    cost = (distance/mpg) * formatted_gas_price
    return cost


dropbox_connect()
dropbox_get_recent_csv()
dropbox_download_file()
# deletes the unnecessary line at the beginning of the csv file that is automatically generated
# by the obd2 reader
delete_unnecessary(csv_filename)
# calling the convert to json function
convert_json(csv_filename, json_filename)
# calling the distance calc function to convert the points to a total distance
distance_calc(json_filename)
# printing what distance to cost returns in a rounded string form. The parameter for it
# is the distance calc function because that returns distance.
print("$" + str(round(distance_to_cost(distance_calc(json_filename)), 2)))

# my next step in this project is to make a website with a link you click, and it downloads
# the most recent trip file from the obd2 app and runs it in this program and gives you the cost.
# What would be cool is to eventually have a good-looking website that has many functions
# related to this idea. Possibly even a gauge you can put in your car that ticks up the amount the
# current trip is costing you in real time.
