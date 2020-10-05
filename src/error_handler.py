import os
import sys

# handle wrong file formats and file existings
def handle_wrong_arguments(known_file,unknown_file):
    known_filename, known_file_extension = os.path.splitext(known_file)
    unknown_filename, unknown_file_extension = os.path.splitext(unknown_file)
    if not os.path.isfile(known_file):
        print('The path specified file for known_stations does not exist')
        sys.exit()
    if not os.path.isfile(unknown_file):
        print('The path specified file for unknown_stations does not exist')
        sys.exit()
    if not (known_file_extension=='.csv' or known_file_extension=='.json'):
        print('The path specified known_station file should be in json or csv formats')
        sys.exit()
    if not (unknown_file_extension=='.csv' or unknown_file_extension=='.json'):
        print('The path specified unknown_station file should be in json or csv formats')
        sys.exit()
        
# check required attributes of input files
def check_requirements(header,is_random):
    if 'ID' not in header:
        print('You should have ID attribute in your file!')
        sys.exit()
    elif 'Latitude' not in header:
        print('You should have Latitude attribute in your file!')
        sys.exit()
    elif 'Longitude' not in header:
        print('You should have Latitude attribute in your file!')
        sys.exit()
    if not is_random:
        if 'Time' not in header:
            print('You should have Time attribute in your file!')
            sys.exit()
        elif 'CH4' not in header:
            print('You should have CH4 attribute in your file!')
            sys.exit()