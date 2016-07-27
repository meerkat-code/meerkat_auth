"""

Helper file to manage translations for the Meerkat Authentication module.

We have two types of translations, general and implementation specific

The general translations are extracted from the python, jijna2 and js files. 

The implementation specific text that needs to be translated is stored in a csv file. 

"""
 
from csv import DictReader
import argparse
import os
import shutil
import datetime
from babel.messages.pofile import read_po, write_po
from babel.messages.catalog import Catalog, Message
from babel._compat import BytesIO

parser = argparse.ArgumentParser()
parser.add_argument("action", 
                    choices=["update-po", "initialise", "compile" ],
                    help="Choose action" )
parser.add_argument("-l", type=str,
                    help="Two letter langauge code")

if __name__ == "__main__":

    args = parser.parse_args()
    lang_dir = "meerkat_auth"

    if args.action == "update-po":
        os.system("pybabel extract -F babel.cfg -o {}/messages.pot .".format(lang_dir) )
        os.system("pybabel update -i {}/messages.pot -d {}/translations".format(lang_dir, lang_dir) )
        os.system("rm {}/messages.pot".format(lang_dir))
    elif args.action == "initialise":
        if args.l and len(args.l) == 2:
            os.system("pybabel extract -F babel.cfg -o {}/messages.pot .".format(lang_dir) )
            os.system("pybabel init -i {}/messages.pot -d {}/translations -l {}".format(
                lang_dir, lang_dir,args.l
            ))
            os.system("pybabel update -i {}/messages.pot -d {}/translations".format(lang_dir, lang_dir) )
            os.system("rm {}/messages.pot".format(lang_dir))
        else:
            print("Need to specify a two letter language code")
    elif args.action == "compile":
        os.system("pybabel compile -d {}/translations".format(lang_dir))
        


