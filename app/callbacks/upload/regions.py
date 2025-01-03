import pandas as pd

from dash import html
from dash.dependencies import Input, Output
from flask import request

from callbacks.upload.components import bed_upload_result, upload_summary_card
from callbacks.upload.helpers import get_files
from callbacks.upload.helpers import handle_upload
from data import file_readers
from dash_app import app
from data.cache import SessionCache
from layout import ids
import config


@app.server.route(config.url_base + ids.navbar_upload__regions__upload, methods=['POST'])
def regions_upload():
    return handle_upload(request, file_readers.read_bed_file)


@app.callback(
    Output(ids.navbar_upload__regions_upload_result__div, 'children'),
    Output(ids.display_upload__regions_summary_card__div, 'children'),
    Output(ids.navbar_upload__regions_valid__store, 'data'),

    Input(ids.navbar_upload__regions__upload, 'listUploadTaskRecord'),

    Input(ids.navbar_navbar__session_id__store, 'data'),
)
def on_regions_upload(upload_tasks, session_id):
    filenames, contents = get_files(session_id, upload_tasks)

    regions = None
    regions_valid = 'regions_is_invalid'
    exception = None
    if filenames:
        try:
            regions = SessionCache(session_id).set_regions_as_df(contents)
            regions_valid = 'regions_is_valid'
        except Exception as e:
            exception = e

    result = bed_upload_result(filenames, exception)
    summary_card = generate_regions_summary_card(regions, filenames, exception)

    return result, summary_card, regions_valid


def generate_regions_summary_card(regions: pd.DataFrame, bed_filenames: list, e: Exception = None):
    if e:
        return upload_summary_card('Genomic Regions', 'An exception occurred:', [f'{e}'])

    if not bed_filenames:
        status = 'Not uploaded.'
        filenames = [
            '> Custom regions for filtering.',
            '> Each file is applied sequentially.',
        ]
        counts = []
    else:
        status = [html.Pre(len(regions), style={'display': 'inline'}), ' regions loaded.']
        filenames = bed_filenames
        
        counts = []
        for filename in filenames:
            count = regions[filename].astype(int).sum()
            counts.append(count)

    return upload_summary_card('Genomic Regions', status, filenames, counts, aggregate_after=3)
