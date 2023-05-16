#!/bin/python

import sys
import glob

view_counts = {}
filenames = glob.glob('pageviews/*')

filters = ['File:', 'Wikipedia:', 'Help:', 'Category:', 'Portal:', 'Special:', 'Main_Page']

if len(sys.argv) > 1:
    try:
        threshold = int(sys.argv[1])
    except ValueError:
        print("Invalid threshold value. Using default value of 50.")
        threshold = 50
else:
    threshold = 50

with open('titles.txt', 'w') as out_file:
    for filename in filenames:
        print(f'Processing file: {filename}')
        with open(filename, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.split()
                page_name = parts[1]
                try:
                    view_count = int(parts[2])
                except ValueError:
                    continue
                if view_count < 1:
                    continue
                if parts[0] != "en.m":
                    continue
                if any(filter in page_name for filter in filters):
                    continue
                if page_name in view_counts:
                    view_counts[page_name] += view_count
                else:
                    view_counts[page_name] = view_count

    print('Sorting results...')
    sorted_view_counts = sorted(view_counts.items(), key=lambda x: x[1], reverse=True)

    for page_name, view_count in sorted_view_counts:
        if view_count < threshold:
            continue
        page_name = page_name.strip()
        page_name = page_name.replace("_", " ")
        out_file.write(f'{page_name}\n')

print('Done!')
