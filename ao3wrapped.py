# IMPORT STATEMENTS
# HTTP fetch and parse
from bs4 import BeautifulSoup
import requests
# data manipulation
from auxiliar import Auxiliar as aux
import pandas as pd
# interface prettify
from InquirerPy import inquirer as iq
from tqdm import tqdm
# python libraries
from time import sleep
import random

# FALSE = wrapped progress bar ENABLED
# TRUE = wrapped progress bar DISABLED
debug = False

# SUPPORT VARIABLES
# sets how the program will work:
username = ""
password = ""
year = ""
bookmarks = False
# helps to maintain the program running
is_in_date = True
is_logged_in = False
scrape = True
hist_page = 1
scrape_type = "readings"
if bookmarks:
    scrape_type = "bookmarks"
it_amount = 1000

# USER DATA FOR LATER STORAGE
# data variables
user_word_count = 0
orphaned_works = 0
title_lower_count = 0
# datas set and dict
user_ship_type = {"M/M": 0, "F/F": 0, "F/M": 0, "Gen": 0, "Multi": 0, "Other": 0, "No category": 0}
user_rating = {"General Audiences": 0, "Teen And Up Audiences": 0, "Mature": 0, "Explicit": 0, "Not Rated": 0}
user_status = {"Complete Work": 0, "Work in Progress": 0, "Unknown": 0, "Series in Progress": 0}
user_authors = {}
user_fandoms = {}
user_ships = {}
user_characters = {}
user_tags = {}
# set of sets
dict_list = [user_ship_type, user_rating, user_status, user_authors, user_fandoms, user_ships, user_characters,
             user_tags]

# USER DATAFRAME
# works.cvs where each work will be saved at
df_works = pd.DataFrame(columns=[
    "title", "authors", "last_updated", "fandoms", "ship_types", "rating",
    "work_status", "ships", "characters", "additional_tags", "word_count",
    "kudos", "hits", "user_last_visited", "user_visitations"
])
df_works = df_works.astype({
    "word_count": "int32", "kudos": "int32", "hits": "int32", "user_visitations": "int32"
})
if bookmarks:
    df_works.drop(labels="user_visitations", axis=1, inplace=True)
# user.csv where data will be counted cumulatively
df_user = pd.DataFrame(columns=[
    "filter", "content", "amount"
])


# FUNCTIONS
# gets auth token for rails
def get_token(session):
    # stores the response to the http request GET
    r = session.get("https://archiveofourown.org")
    # parses the content in bytes from r into html
    soup = BeautifulSoup(r.content, "html.parser")
    # returns the authentication token within the http
    return soup.find("meta", {"name": "csrf-token"})["content"]


# logs into ao3
def login(session, uname, upswd):
    # fetches token from http
    token = get_token(session)
    # login data
    payload = {
        "utf8": "✓",
        "authenticity_token": token,
        "user[login]": uname,
        "user[password]": upswd,
        "commit": "Log in"
    }
    # makes a login request with provided data
    p = session.post("https://archiveofourown.org/users/login", data=payload)
    # exits if status code is not OK
    if p.status_code != 200:
        exit(1)


# fetches and verifies last time
# the user has visited a work
def certify_lv(w):
    global is_in_date
    ""

    # fetches last visited time depending
    # on scrape mode chosen by the user
    if bookmarks:
        last_visited = w.find("div", {"class": "own user module group"}).find("p").text
    else:
        last_visited = w.find("div", {"class": "user module group"}).find("h4").text[15:].split("\n")[0]

    # analyzes last visited time to see if it
    # falls into the timeline requested by the user
    is_in_date = year in last_visited

    # returns the last visited time
    return last_visited


# parses works on one history page from an AO3 account and adds
# to works dataframe if it's from the year specified
def parse_hist_page(soup):
    global is_in_date

    ""
    if bookmarks:
        work_list = soup.select("ol.bookmark.index.group li.bookmark.blurb.group")
    else:
        work_list = soup.select("ol.reading.work.index.group li.reading.work.blurb.group")

    for w in work_list:
        try:
            if bookmarks:
                # Check if work has been deleted
                if w.find("p", {"class": "message"}) is not None:
                    if w.find("p").text == "This has been deleted, sorry!":
                        continue
                # Check if bookmark is a series
                elif w.find("div", {"class": "own user module group"}).find("ul", {"class": "actions"}).find("li", {"class": "share"}) is None:
                    continue

            # checks if work is from the selected year
            last_visited = certify_lv(w)

            # checks if the work has been deleted
            if not bookmarks:
                if w.find("h4", {"class": "viewed heading"}) is not None:
                    if "Deleted work" in w.find("h4").text:
                        continue

            # if works from this year
            if is_in_date:
                # gets tittle
                title = w.find("div", {"class": "header module"}).find("h4", {"class": "heading"}).find("a").text
                if title == title.lower():
                    global title_lower_count
                    title_lower_count += 1
                # print(f"tittle: {title}");

                # Get authors
                authors = []
                for author in w.find("div", {"class": "header module"}).find("h4", {"class": "heading"}).find_all(
                        rel="author"):
                    if author.text == "orphan_account":
                        global orphaned_works
                        orphaned_works += 1
                    else:
                        authors.append(author.text)
                        if author.text in user_authors:
                            user_authors[author.text] += 1
                        else:
                            user_authors[author.text] = 1
                # print(f"authors: {authors}");

                # Get date last updated
                updated = w.find("div", {"class": "header module"}).find("p").text
                # print(f"updated: {updated}");

                # Get fandoms
                fandoms = []
                for fandom in w.find("div", {"class": "header module"}).find("h5", "fandoms heading").find_all("a"):
                    fandoms.append(fandom.text)
                    if fandom.text in user_fandoms:
                        user_fandoms[fandom.text] += 1
                    else:
                        user_fandoms[fandom.text] = 1
                # print(f"fandoms: {fandoms}");

                # Get relationship type, rating, and work status
                req_tag_list = []
                for req_tag in w.find("div", {"class": "header module"}).find("ul").find_all("li"):
                    req_tag_list.append(req_tag.find("a").find("span", {"class": "text"}).text)
                ship_types = []
                for type in req_tag_list[2].split(", "):
                    ship_types.append(type)
                    user_ship_type[type] += 1
                rating = req_tag_list[0]
                user_rating[rating] += 1
                work_status = req_tag_list[3]
                user_status[work_status] += 1
                # print(f"ship_type: {ship_types}");
                # print(f"rating: {rating}");
                # print(f"work_status: {work_status}");

                # Get relationships
                ships = []
                for ship in w.find("ul", {"class": "tags commas"}).find_all("li", {"class": "relationships"}):
                    ships.append(ship.text)
                    if ship.text in user_ships:
                        user_ships[ship.text] += 1
                    else:
                        user_ships[ship.text] = 1
                # print(f"ships: {ships}");

                # Get characters
                characters = []
                for character in w.find("ul", {"class": "tags commas"}).find_all("li", {"class": "characters"}):
                    characters.append(character.text)
                    if character.text in user_characters:
                        user_characters[character.text] += 1
                    else:
                        user_characters[character.text] = 1
                # print(f"characters: {characters}");

                # Get freeform tags
                additional_tags = []
                for tag in w.find("ul", {"class": "tags commas"}).find_all("li", {"class": "freeforms"}):
                    additional_tags.append(tag.text)
                    if tag.text in user_tags:
                        user_tags[tag.text] += 1
                    else:
                        user_tags[tag.text] = 1
                # print(f"additional_tags: {additional_tags}");

                # Get word count
                word_count = int(w.find("dl", {"class": "stats"}).find("dd", {"class": "words"}).text.replace(",", ""))
                global user_word_count
                user_word_count += word_count
                # print(f"word_count: {word_count}");

                # Get kudos
                stats = str(w.find("dl", {"class": "stats"}).text).find("Kudos")
                kudos = 0
                if stats != -1:
                    kudos = int(
                        w.find("dl", {"class": "stats"}).find("dd", {"class": "kudos"}).find("a").text.replace(",", ""))
                # print(f"kudos: {kudos}");

                # Get hits
                hits = int(w.find("dl", {"class": "stats"}).find("dd", {"class": "hits"}).text.replace(",", ""))
                # print(f"hits: {hits}");

                # Get number of times user visited the fic
                if not bookmarks:
                    visitations = \
                        w.find("div", {"class": "user module group"}).find("h4").text[15:].split("\n")[4].split(
                            "Visited ")[
                            1].split(" ")[0]
                    if visitations == "once":
                        visitations = 1
                    else:
                        visitations = int(visitations)
                # print(f"visitations: {visitations}");

                # Add this work to the works DataFrame
                global df_works
                work = {"title": title, "authors": authors, "last_updated": updated, "fandoms": fandoms,
                        "ship_types": ship_types, "rating": rating, "work_status": work_status, "ships": ships,
                        "characters": characters, "additional_tags": additional_tags, "word_count": word_count,
                        "kudos": kudos, "hits": hits, "user_last_visited": last_visited}
                if not bookmarks:
                    work = {"title": title, "authors": authors, "last_updated": updated, "fandoms": fandoms,
                            "ship_types": ship_types, "rating": rating, "work_status": work_status, "ships": ships,
                            "characters": characters, "additional_tags": additional_tags, "word_count": word_count,
                            "kudos": kudos, "hits": hits, "user_last_visited": last_visited,
                            "user_visitations": visitations}
                df_works = pd.concat([df_works, pd.DataFrame([work])], ignore_index=True)

        except RuntimeError:
            print("Error adding work.")
            # print(w)
            pass


# COLLECTING AND STORING DATA
# asks for ao3 login credentials
def scanner():
    # sets variables to global bc python sucks
    global username
    global password
    global bookmarks
    global year
    global scrape
    global is_logged_in

    dataframe = iq.select(
        message="Select whether you want to webscrape your data or read \\from an existing .csv file:",
        choices=[
            "Scrape from AO3 website",
            "Read from an existing .csv file",
        ],
    ).execute()

    # "parses" user input into boolean value
    scrape = True
    if ".csv" in dataframe:
        is_logged_in = True
        scrape = False

    if scrape:
        print("\nPlease, login with your AO3 account")
        username = iq.text(message="Username: ").execute()
        password = iq.secret(message="Password:").execute()

        print("\nThe Console warns you: ")
        print("None of your personal data, like username and password is being kept by us!")
        print("You must not worry, lad!\n")

        framework = iq.select(
            message="Select from where your data will be pulled:",
            choices=[
                "History",
                "Bookmarks",
            ],
        ).execute()

        # "parses" user input into boolean value
        bookmarks = False
        if framework == "bookmark":
            bookmarks = True

    print("\n")

    year = iq.number(
        message="Enter desired year: ",
        min_allowed=2008,
        max_allowed=2024,
        default=2024,
    ).execute()

    print("\n")


# collects ao3 history data
def gat_data():
    # opens a http session
    s = requests.Session()
    # tries to log in
    login(s, username, password)
    # for some reason, which i don't have enough knowledge to understand
    # yet, the session expires and for the program to work it needs to
    # log in twice, i don't know any better way to check if it's longed in,
    # other than this ugly boolean, so bear with me, please
    global is_logged_in
    is_logged_in = False

    # store the number of attempts to log in,
    # so we have a limit, and it doesn't keep
    # trying over and over again to login
    attempts = 0
    # stores how many times the progress bar has updated
    updates = 0
    # opens a progress bar so the user has
    # a sense of progress (it's all made up)
    pbar = tqdm(total=it_amount, dynamic_ncols=True, unit="works", leave=False)

    # while loop (that actually works like a do-while loop)
    # which will only work if the work-fic being fetched on
    # ao3 has been opened by the user on the selected year
    while is_in_date:
        # sets hist_page to global because python sucks
        global hist_page
        pbar.set_description("Fetching history page  %d" % hist_page)

        # checks if it has logged in, so it
        # forcefully tries to log in a second time
        if not is_logged_in:
            if attempts < 3:
                login(s, username, password)
                attempts += 1
            else:
                break

        # stores the response to the http request GET
        r = s.get(f"https://archiveofourown.org/users/{username}/{scrape_type}?page={hist_page}")
        # parses the content in bytes from r into html
        soup = BeautifulSoup(r.content, "html.parser")

        # checks login state by looking for user-specific data
        if not soup.find("a", {"href": f"/users/{username}"}):
            is_logged_in = False
            # restarts the loop if login was unsuccessful
            continue
            # this statement is only reach
        # if the login was successful
        is_logged_in = True

        # takes the html page and scrapes and stores
        # all data which will be used in the wrapped
        parse_hist_page(soup)
        # increments the hist_page, so
        # we can access the next page
        hist_page += 1
        # sleeps for 6 seconds for security purposes
        sleep(6)
        # updates progress bar in 20 works bc that's what we've
        # gotten from the html most likely (it's all made up anyway)
        pbar.update(20)
        updates += 20

    # when the while loop closes, if it was successfully logged
    # in then the progress bar needs to finish updating
    if is_logged_in:
        pbar.update(it_amount - updates)
    # regardless, the progress bar needs to be closed
    pbar.close()
    # if it failed to log in, warn the user only after
    # the progress bar closes, otherwise well have to empty
    # progress bars being printed on the console
    if not is_logged_in:
        print("\n\nFailed to login after 3 attempts.")


# sorts, reassigns and stores user readings info
def user_dict_list():
    # sorts all user collected data into decrescendo order
    i = 0
    for d in dict_list:
        dict_list[i] = {k: v for k, v in sorted(d.items(), key=lambda item: item[1], reverse=True)}
        i += 1

    # reassigns mixed dictionaries with sorted ones
    user_rating = dict_list[0]
    user_ship_type = dict_list[1]
    user_status = dict_list[2]
    user_authors = dict_list[3]
    user_fandoms = dict_list[4]
    user_ships = dict_list[5]
    user_characters = dict_list[6]
    user_tags = dict_list[7]

    # creates a 2d array with all the above data
    global user_info
    user_info = [["total", "word count", user_word_count],
                 ["total", "orphaned works", orphaned_works],
                 ["total", "lower titles", title_lower_count]]

    for rate in user_rating.keys():
        user_info.append(["rating", rate, user_rating[rate]])

    for rate in user_ship_type.keys():
        user_info.append(["orientation", rate, user_ship_type[rate]])

    for rate in user_status.keys():
        user_info.append(["status", rate, user_status[rate]])

    for rate in user_authors.keys():
        user_info.append(["author", rate, user_authors[rate]])

    for rate in user_fandoms.keys():
        user_info.append(["fandom", rate, user_fandoms[rate]])

    for rate in user_ships.keys():
        user_info.append(["ship", rate, user_ships[rate]])

    for rate in user_characters.keys():
        user_info.append(["char", rate, user_characters[rate]])

    for rate in user_tags.keys():
        user_info.append(["tag", rate, user_tags[rate]])

    # turns the array into a spreadsheet
    global df_user
    df_user = pd.concat([df_user, pd.DataFrame(user_info, columns=["filter", "content", "amount"])], ignore_index=True)


# PRINTING METHODS
# amount of words read this year
def print_words():
    # stores user.csv in an array, so it's easier to work with it
    totals = aux.filter_df(df_user, 'total')
    # gets user word count
    index = aux.amount_index(aux.index_of(totals, 'word count'))
    user_word_count = int(totals[index[0]][index[1]])
    # gets user orphaned works read count
    index = aux.amount_index(aux.index_of(totals, 'orphaned works'))
    orphaned_works = int(totals[index[0]][index[1]])
    # gets user lowercase title works read count
    index = aux.amount_index(aux.index_of(totals, 'lower titles'))
    title_lower_count = int(totals[index[0]][index[1]])

    print(f"You've read {len(df_works.index)} fanfics this year, totaling {user_word_count} words, "
          f"or {user_word_count / 365:.2f} words/day. There's about 70,000 words in a novel. "
          f"You could've read {user_word_count / 70000:.2f} novels this year, but you chose to read fanfic instead.")

    print(f"\nYou've also read {orphaned_works} orphaned works the year.")
    print(f"\n{title_lower_count} of those {len(df_works.index)} fics had all lower-case titles. Hipster.")

    if not bookmarks:
        # gets id of the most visited work
        work_index = aux.idmax_of(df_works, 'user_visitations')
        work_authors = aux.get_efi(df_works, 'authors', work_index)

        print(
            f"\nThe fic you've visited the most was {aux.get_efi(df_works, 'title', work_index)} by {aux.authors_prettily(work_authors)}, "
            f"with {aux.get_efi(df_works, 'user_visitations', work_index)} visitations.")

    print("\n\n\n")


# work orientation type
def print_orientation():
    orientation = aux.filter_df(df_user, 'orientation')
    top_key = orientation[0][0]
    top_val = orientation[0][1]

    print(f"You read {top_val} {top_key} fics this year.")
    aux.you_also(orientation[1:])
    print("\n\n\n")


# work ratings
def print_ratings():
    rating = aux.filter_df(df_user, 'rating')
    top_key = rating[0][0]
    top_val = rating[0][1]

    print(f"You read {top_val} {top_key} fics this year.")
    aux.you_also(rating[1:])
    print("\n\n\n")


# user status
def print_status():
    status = aux.filter_df(df_user, 'status')
    top_key = status[0][0]
    top_val = status[0][1]
    print(f"You read {top_val} {top_key} and {status[1][1]} {status[1][0]} fics this year.")
    print("\n\n\n")


# prints authors
def print_authors():
    authors = aux.filter_df(df_user, 'author')
    top_key = authors[0][0]
    top_val = authors[0][1]

    print(f"You read {len(authors)} different authors this year.")

    print(
        f"\nYour most read author this year was {top_key}, with {top_val} fics. You should tell them you're such a big fan, like right now. They deserve to know.")
    print("Seriously. I'll wait. Leave (another) comment on a fic of theirs.")

    print("\nYou also read:")
    aux.you_also(authors[1:6])
    print("\n\n\n")


# print fandoms
def print_fandoms():
    fandoms = aux.filter_df(df_user, 'fandom')
    top_key = fandoms[0][0]
    top_val = fandoms[0][1]

    print("You read fics for %d different fandoms this year." % len(fandoms))
    print(f"\nYour most read fandom was {top_key}, with {top_val} fics this year." % ())

    aux.you_also(fandoms[1:6])
    print("\n\n\n")


# print ships
def print_ships():
    ships = aux.filter_df(df_user, 'ship')
    top_key = ships[0][0]
    top_val = ships[0][1]

    print(f"You read fics with {len(ships)} different ships this year.")
    print(f"\nAre you not tired of reading about {top_key}? You read {top_val} fics of them this year.")

    aux.you_also(ships[1:6])
    print("\n\n\n")


# print characters
def print_characters():
    chars = aux.filter_df(df_user, 'char')
    top_key = chars[0][0]
    top_val = chars[0][1]

    print(f"You read about {len(chars)} different characters this year.")
    print(f"\nWhat a {top_key} stan. You read {top_val} fics of them this year.")

    aux.you_also(chars[1:6])
    print("\n\n\n")


# print tags
def print_tags():
    tags = aux.filter_df(df_user, 'tag')
    top_key = tags[0][0]
    top_val = tags[0][1]

    print(
        f"You read fics with {len(tags)} different tags this year, averaging {len(tags) / len(df_works):.2f} tags/work.")
    print(
        f"\nYou absolutely love {top_key}, but you already knew that. You read {top_val} fics with that tag this year.")

    aux.you_also(tags[1:6])
    print("\n\n\n")


# print word stats
def print_word_stats():
    work_index = aux.idmax_of(df_works, 'word_count')
    work_authors = aux.authors_prettily(aux.get_efi(df_works, 'authors', work_index))
    work_name = aux.get_efi(df_works, 'title', work_index)
    print(
        f"Highest word count: {work_name} by {work_authors} with {int(aux.get_efi(df_works, 'word_count', work_index))} words.")

    work_index = aux.idmin_of(df_works, 'word_count')
    work_authors = aux.authors_prettily(aux.get_efi(df_works, 'authors', work_index))
    work_name = aux.get_efi(df_works, 'title', work_index)
    print(
        f"\nLowest word count: {work_name} by {work_authors} with {int(aux.get_efi(df_works, 'word_count', work_index))} words.")

    print(f"\nAverage word count: {aux.mean_of(df_works, 'word_count'):.2f}.")
    print("\n\n\n")


# print hit  stats
def print_hits_stats():
    work_index = aux.idmax_of(df_works, 'hits')
    work_authors = aux.authors_prettily(aux.get_efi(df_works, 'authors', work_index))
    work_name = aux.get_efi(df_works, 'title', work_index)
    print(f"Most hits:  {work_name} by {work_authors} with {int(aux.get_efi(df_works, 'hits', work_index))} hits.")

    work_index = aux.idmin_of(df_works, 'hits')
    work_authors = aux.authors_prettily(aux.get_efi(df_works, 'authors', work_index))
    work_name = aux.get_efi(df_works, 'title', work_index)
    print(f"\nLeast hits: {work_name} by {work_authors} with {int(aux.get_efi(df_works, 'hits', work_index))} hits.")

    print(f"\nAverage hits: {aux.mean_of(df_works, 'hits'):.2f}.")
    print("\n\n\n")


# print kudos stats
def print_kudos_stats():
    work_index = aux.idmax_of(df_works, 'kudos')
    work_authors = aux.authors_prettily(aux.get_efi(df_works, 'authors', work_index))
    work_name = aux.get_efi(df_works, 'title', work_index)
    print(f"Most kudos:  {work_name} by {work_authors} with {int(aux.get_efi(df_works, 'kudos', work_index))} kudos.")

    work_index = aux.idmin_of(df_works, 'kudos')
    work_authors = aux.authors_prettily(aux.get_efi(df_works, 'authors', work_index))
    work_name = aux.get_efi(df_works, 'title', work_index)
    print(f"\nLeast kudos: {work_name} by {work_authors} with {int(aux.get_efi(df_works, 'kudos', work_index))} kudos.")

    print(f"\nAverage kudos: {aux.mean_of(df_works, 'kudos'):.2f}.")
    print("\n\n\n")


# print full wrapped
def print_wrapped():
    file_name = "works" + year
    global df_works
    df_works = pd.read_csv(f"./results/{file_name}.csv")
    file_name = "user" + year
    global df_user
    df_user = pd.read_csv(f"./results/{file_name}.csv")

    if not scrape:
        print(f"\nReading from the files results/works{year}.csv and results/user{year}.csv\n")

    global debug
    # funny progress bar to make the user wait at least 40s before
    # receiving their wrapped, so they realize how hard it is to code it
    if not debug:
        processes = ["     Works", "     Words",
                     "   Ratings", "   Authors",
                     "   Fandoms", "     Ships",
                     "Characters", "      Tags",
                     "      Hits", "     Kudos"]

        pbar = tqdm(total=len(df_works.index) * 10, unit="works", dynamic_ncols=True, leave=False)
        for process in processes:
            pbar.set_description("Processing %s" % process)
            sleep(random.uniform(1.5, 4))
            pbar.update(len(df_works.index))
        pbar.close()

    # PRINT USER STATS
    # about the works:
    print_words()
    print_orientation()
    print_ratings()
    print_status()
    print_authors()

    # ships and tags:
    print_fandoms()
    print_ships()
    print_characters()
    print_tags()

    # some of the stats:
    print_word_stats()
    print_hits_stats()
    print_kudos_stats()


def main():
    # welcome message
    print("\nWelcome to the AO3 Year End Wrapped!")
    print("To start with, we need to collect some of your data.")
    print("For the application to work, please enter the following correctly:\n")

    # gets input from the user which helps the program decides how it will work:
    # 1. if they'll read a .cvs document already created or if they'll scrape online
    # 2. if the scrape will happen through the users history or bookmarks
    # 3. the year which the user wants the works to be scraped from
    scanner()
    # accesses ao3 history/bookmarks and fetches user data
    if scrape:
        gat_data()

    # stores the data collected into two csvs files
    # then prints the stats pretty to the user to read
    if is_logged_in:
        if scrape:
            # saves works related data
            file_name = "works" + year
            df_works.to_csv(f"./results/{file_name}.csv")

            # sorts and reassigns user dictionary lists
            user_dict_list()
            # saves user related data
            file_name = "user" + year
            df_user.to_csv(f"./results/{file_name}.csv")

            # warns the user files have been created and
            # that they can access it if they want to
            print("\n+1 : works.cvs")
            print("+1 : user.cvs")
            print("Two .csv files were created!")
            print("\nYou can browse through your directories and open them with\n"
                  "a spreadsheet reader like Microsoft Excel or Google Sheets.\n\n\n")

        try:
            print_wrapped()
        except FileNotFoundError:
            print(f"It seems like there are no .csv files from the year of {year}.")
            print("You may want to try scraping AO3's website for the program to work.")


if __name__ == '__main__':
    try:
        print("\n\nYou can press 'Ctrl + C' to interrupt the program at any time.")
        main()
    except KeyboardInterrupt:
        print("\n\nKeyboardInterrupt detected. Exiting gracefully...\n\n")
