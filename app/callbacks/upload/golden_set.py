import pandas as pd

from dash import html
from dash.dependencies import Input, Output
from flask import request

from dash_app import app
from data.cache import SessionCache
from data import file_readers
from data.file_readers import get_filenames_from_variant_df
from layout import ids
import config
from callbacks.upload.components import upload_summary_card, vcf_upload_result
from callbacks.upload.helpers import get_files, handle_upload


@app.server.route(config.url_base + ids.navbar_upload__golden_set__upload, methods=['POST'])
def golden_set_upload():
    return handle_upload(request, file_readers.read_vcf_file)


@app.callback(
    Output(ids.navbar_upload__golden_set_upload_result__div, 'children'),
    Output(ids.display_upload__golden_set_summary_card__div, 'children'),
    Output(ids.navbar_upload__golden_set_valid__store, 'data'),

    Input(ids.navbar_upload__golden_set__upload, 'listUploadTaskRecord'),

    Input(ids.navbar_navbar__session_id__store, 'data'),
)
def on_golden_set_upload(upload_tasks, session_id):
    filenames, contents = get_files(session_id, upload_tasks)

    golden_set = None
    golden_set_valid = 'golden_set_is_invalid'
    exception = None
    if filenames:
        try:
            golden_set = SessionCache(session_id).set_golden_set_as_df(filenames, contents)
            golden_set_valid = 'golden_set_is_valid'
        except Exception as e:
            exception = e

    result = vcf_upload_result(filenames, exception)
    summary_card = generate_golden_set_summary_card(golden_set, exception)

    return result, summary_card, golden_set_valid


def generate_golden_set_summary_card(golden_set: pd.DataFrame, e: Exception = None):
    if e:
        return upload_summary_card('Golden Set', 'An exception occurred:', [f'{e}'])

    if golden_set is None:
        status = 'Not uploaded.'
        filenames = [
            '> Required for benchmarking.',
            '> Precision and recall are calculated based on exact matches of variants.',
        ]
        counts = []
    else:
        filenames = get_filenames_from_variant_df(golden_set)

        variant_counts = {}
        for filename in filenames:
            variant_counts[filename] = golden_set[filename].astype(int).sum()

        sorted_variant_counts = dict(sorted(
            variant_counts.items(),
            key=lambda pair: pair[1],
            reverse=True
        ))

        filenames = list(sorted_variant_counts.keys())
        counts = list(sorted_variant_counts.values())

        status = [html.Pre(sum(counts), style={'display': 'inline'}), ' variants loaded.']

    return upload_summary_card('Golden Set', status, filenames, counts, aggregate_after=3)
