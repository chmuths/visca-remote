from os import listdir
from os.path import isfile, join, getmtime


def get_dated_files_list(directory, start='', end=''):
    if start and end:
        found_files = [f for f in listdir(directory) if isfile(join(directory, f)) &
                       (f.lower().startswith(start.lower())) & (f.lower().endswith(end.lower()))]
    elif start:
        found_files = [f for f in listdir(directory) if isfile(join(directory, f)) &
                       (f.lower().startswith(start.lower()))]
    elif end:
        found_files = [f for f in listdir(directory) if isfile(join(directory, f)) &
                       (f.lower().endswith(end.lower()))]
    else:
        found_files = [f for f in listdir(directory) if isfile(join(directory, f))]

    dated_files = []
    for file in found_files:
        mtime = getmtime(join(directory, file))
        dated_files = dated_files + [(file, mtime)]
    dated_files.sort(key=lambda tup: tup[1], reverse=True)
    return dated_files
