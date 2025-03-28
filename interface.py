from datetime import datetime
import os

from InquirerPy import inquirer as iq
from InquirerPy.base import Choice
from InquirerPy.utils import color_print
from InquirerPy.validator import EmptyInputValidator, PathValidator
from prompt_toolkit.validation import Validator, ValidationError

from exceptions import NullInput

class Interface:
    def __init__(self):
        self.__usrnm: str = None
        self.__psswrd: str = None
        self.__method: str = None
        self.__year: int = None
        self.__scrape: bool = None
        self.__file_path: str = None

    def get_username(self) -> str:
        if self.__usrnm is None:
            raise NullInput("USERNAME is NULL")
        else:
            return self.__usrnm

    def get_password(self) -> str:
        if self.__psswrd is None:
            raise NullInput("PASSWORD is NULL")
        else:
            return self.__psswrd

    def get_method(self) -> str:
        if self.__method is None:
            raise NullInput("SCRAPE METHOD is NULL")
        else:
            return self.__method

    def get_year(self) -> int:
        if self.__year is None:
            raise NullInput("YEAR is NULL")
        else:
            return self.__year

    def get_scrape(self) -> bool:
        if self.__scrape is None:
            raise NullInput("SCRAPE is NULL")
        else:
            return self.__scrape

    def get_file_path(self) -> str:
        if self.__file_path is None:
            raise NullInput("FILE_PATH is NULL")
        else:
            return self.__file_path

    def login_data(self):
        color_print([("#00d3ff", "\nPlease, log in to your ao3 account so we can access your readings data.")])
        color_print([("red", "Don't worry! None of your personal data will be kept with us.\n")])

        try:
            name = iq.text(
                message="Username: ",
                validate=EmptyInputValidator()
            ).execute()

            passwd = iq.secret(
                message="Password: ",
                validate=EmptyInputValidator()
            ).execute()

            self.__usrnm = name.strip()
            self.__psswrd = passwd.strip()

        except KeyboardInterrupt:
            Interface.__exit()

    def scrape_method(self):
        print("\n")
        try:
            self.__method = iq.select(
                message="Choose a scrape method: ",
                choices=[
                    Choice(name="History", value="readings", enabled=True),
                    Choice(name="Bookmarks", value="bookmarks")
                ]
            ).execute()

        except KeyboardInterrupt:
            Interface.__exit()

    def should_scrape(self):
        print("\n")
        try:
            self.__scrape = iq.select(
                message="Do you want to scrape your wrapped from web or a pre existing csv file? ",
                choices=[
                    Choice(name="Web", value=True, enabled=True),
                    Choice(name="Csv", value=False)
                ]
            ).execute()

        except KeyboardInterrupt:
            Interface.__exit()

    def wrap_year(self):
        print("\n")
        try:
            self.__year = iq.number(
                message="Choose your wrapped year: ",
                min_allowed=2000,
                max_allowed=datetime.now().year,
                default=datetime.now().year,
                validate=EmptyInputValidator()
            ).execute()

        except KeyboardInterrupt:
            Interface.__exit()

    def file_path(self):
        print("\n")
        dir: str = '/' if os.name == 'posix' else '\\'
        home_path = f'{os.getcwd()}{dir}results{dir}'
        try:
            self.__file_path = iq.filepath(
                message="Enter file or directory to upload:",
                default=home_path,
                validate=CsvValidator(),
                multicolumn_complete=True
            ).execute()

        except KeyboardInterrupt:
            Interface.__exit()

    @staticmethod
    def __exit():
        color_print([("purple", "Goodbye... :(")])
        exit(0)


class ExtensionValidator(Validator):
    def __init__(self, valid_extensions: list[str] = None):
        self.valid_extensions = valid_extensions or []

    def validate(self, document):
        file_extension = os.path.splitext(document.text)[1]
        if file_extension not in self.valid_extensions:
            raise ValidationError(
                message=f"Invalid file extension. Expected one of: {', '.join(self.valid_extensions)}",
                cursor_position=document.cursor_position,
            )

        return True


class CsvValidator(Validator):
    def __init__(self):
        self.path_validator = PathValidator(is_file=True, message="Input is not a valid file")
        self.valid_extensions = ExtensionValidator(['.csv'])

    def validate(self, document):
        self.path_validator.validate(document)
        self.valid_extensions.validate(document)

        return True
