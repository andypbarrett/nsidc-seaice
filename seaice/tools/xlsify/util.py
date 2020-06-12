import os

import seaice.nasateam as nt


def add_documentation_sheet(writer, doc_file):
    workbook = writer.book

    worksheet = workbook.add_worksheet(name='Documentation')
    textfile = open(doc_file)

    # Write the first description worksheet.
    row = col = 0
    for line in textfile:
        worksheet.write(row, col, line.rstrip('\n'))
        row += 1

    textfile.close()

    workbook.close()

    return writer


def documentation_file(output_filename):
    """Given the filename of a spreadsheet, return path of doc file."""
    filename = os.path.basename(output_filename)
    txt_file = '{}.txt'.format(filename)

    return os.path.join(os.path.dirname(__file__), os.pardir, 'configs', 'documentation', txt_file)


def regional_sheet_name(df_column_name):
    """Takes a column name (string) found in the regional dataframe returned from
    seaicetimeseries, and returns a name that can be used for a sheet in a
    regional xlsx file. Example: "bering_area_km2" => "Bering-Area-km^2"

    """

    sheet_name = df_column_name.title().replace('_', '-').replace('-Km2', '-km^2')

    # these regions are special cases; would probably be best to update
    # nasateam.regional_masks.py, but that would be a higher risk change
    if 'Centralarctic' in sheet_name:
        sheet_name = sheet_name.replace('Centralarctic', 'Central-Arctic')

    elif 'Eastsiberian' in sheet_name:
        sheet_name = sheet_name.replace('Eastsiberian', 'East-Siberian')

    elif 'Stlawrence' in sheet_name:
        sheet_name = sheet_name.replace('Stlawrence', 'St-Lawrence')

    # "Canadian-Archipelago-Extent-km^2" is 32 characters, too long to be the
    # name of an Excel sheet, so we drop the first dash here
    elif 'Canadianarchipelago' in sheet_name:
        sheet_name = sheet_name.replace('Canadianarchipelago', 'CanadianArchipelago')

    elif 'Bellingshausen Amundsen' in sheet_name:
        sheet_name = sheet_name.replace('Bellingshausen Amundsen', 'Bell-Amundsen')

    return sheet_name


def regional_mask_cfg_from_column_name(column_name):
    """Look up regional mask config based on column name.

    Requires that no regional mask names start with another regional mask name,
    e.g. "region" and "region_s".
    """
    for mask_cfg in nt.DEFAULT_REGIONAL_MASKS:
        prefix = mask_cfg['name'] + '_'
        if column_name.startswith(prefix):
            return mask_cfg, prefix

    msg = 'No regional mask config found for column: {}'.format(column_name)
    raise RuntimeError(msg)
