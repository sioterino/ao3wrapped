from typing import Any

from interface import Interface


def user_data(i: Interface):
    i.should_scrape()
    if i.get_scrape():
        i.login_data()
        i.wrap_year()
        i.scrape_method()
    else:
        i.file_path()


def main():
    i: Interface = Interface()
    user_data(i)


if __name__ == "__main__":
    main()
