"""Regenerate daily.p with subset data.

Only include 1987 and January-June of 2013.

WARNING: This script must be run from this directory. The config file uses
relative paths.
"""
import os

import pandas as pd

share_dir = '/share/apps/seaice'
this_dir = os.path.dirname(os.path.realpath(__file__))

# The "live" input file
input_fp = os.path.join(share_dir, 'datastore', 'daily.p')
# The test file we're replacing
original_fp = os.path.join(this_dir, 'daily.p')
# The replacement
output_fp = original_fp + '.new'


def generate_new_stats():
    """Build new datastore from live data."""
    inp_df = pd.read_pickle(input_fp)
    july_2013_df = inp_df.loc['2013-07-01':'2013-07-31']
    july_2013_south_df = july_2013_df.loc[
        july_2013_df.index.get_level_values('hemisphere') == 'S'
    ]
    output_df = pd.concat([
        inp_df.loc['1987-12-01':'1987-12-31'],
        inp_df.loc['2013-01-01':'2013-01-31'],
        inp_df.loc['2013-05-01':'2013-06-30'],
        july_2013_south_df
    ])

    output_df.to_pickle(output_fp)


def test_new_stats():
    """Print information about the new stats dataframe."""
    original_df = pd.read_pickle(original_fp)
    output_df = pd.read_pickle(output_fp)
    try:
        pd.testing.assert_frame_equal(original_df, output_df)
    except Exception as e:
        print('Differences between dataframes:')
        print(e)

    original_df_f = original_df.drop('filename', axis='columns')
    output_df_f = output_df.filter(items=list(original_df_f.columns),
                                   axis='columns')

    try:
        pd.testing.assert_frame_equal(original_df_f, output_df_f)
    except Exception as e:
        print('Differences between dataframes (original columns only, '
              "excluding 'filename' column):")
        print(e)


if __name__ == '__main__':
    generate_new_stats()
    test_new_stats()
