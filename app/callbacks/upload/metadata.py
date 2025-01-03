import pandas as pd

import dash
from dash.dependencies import Input, Output, State
from flask import request

from callbacks.upload.components import csv_upload_result, upload_summary_card
from callbacks.upload.helpers import get_files, handle_upload
from dash_app import app
from data.cache import SessionCache
from data import file_readers
from data.file_readers import get_filenames_from_variant_df, merge_metadata
from data.retrieval import get_uploaded_data
from layout import ids
import config


@app.server.route(config.url_base + ids.navbar_upload__metadata__upload, methods=['POST'])
def metadata_upload():
    return handle_upload(request, file_readers.read_csv_file)


@app.callback(
    Output(ids.navbar_upload__metadata_upload_result__div, 'children'),
    Output(ids.display_upload__metadata_summary_card__div, 'children'),

    Output(ids.navbar_upload__metadata_valid__store, 'data'),

    Input(ids.navbar_upload__metadata__upload, 'listUploadTaskRecord'),

    Input(ids.navbar_upload__compare_set_valid__store, 'data'),

    Input(ids.navbar_navbar__session_id__store, 'data'),

    State(ids.navbar_upload__metadata_valid__store, 'data'),
)
def on_metadata_upload(upload_tasks, compare_set_valid, session_id, current_metadata_valid):
    metadata_filenames, metadata_contents = get_files(session_id, upload_tasks)

    metadata_not_updated = metadata_filenames == []

    (compare_set,), _, _ = get_uploaded_data(session_id, compare_set_valid=compare_set_valid)

    if compare_set is None:
        compare_set_filenames = []
    else:
        compare_set_filenames = get_filenames_from_variant_df(compare_set)

    missing_filenames = []
    metadata = None
    new_metadata_valid = 'metadata_is_invalid'
    exception = None

    if metadata_not_updated and current_metadata_valid == 'metadata_is_valid':
        (metadata,), _, _ = get_uploaded_data(session_id, metadata_valid=current_metadata_valid)
        missing_filenames = missing_metadata(metadata, compare_set_filenames)

        if missing_filenames:
            result = dash.no_update
            summary_card = generate_metadata_summary_card(metadata, missing_filenames, exception)
        else:
            new_metadata_valid = 'metadata_is_valid'

            metadata = metadata[metadata['FILENAME'].isin(compare_set_filenames)]
            SessionCache(session_id).set_metadata(metadata)

            result = dash.no_update
            summary_card = dash.no_update

    elif metadata_filenames:
        try:
            metadata = merge_metadata(metadata_contents)
            relevant_data = metadata[metadata['FILENAME'].isin(compare_set_filenames)]

            SessionCache(session_id).set_metadata(relevant_data)
            missing_filenames = missing_metadata(metadata, compare_set_filenames)

            if not missing_filenames:
                new_metadata_valid = 'metadata_is_valid'
        except Exception as e:
            exception = e

        result = csv_upload_result(metadata_filenames, exception)
        summary_card = generate_metadata_summary_card(metadata, missing_filenames, exception)
    else:
        result = csv_upload_result(metadata_filenames, exception)
        summary_card = generate_metadata_summary_card(metadata, missing_filenames, exception)

    return result, summary_card, new_metadata_valid


@app.callback(
    (Output(ids.navbar_analyze_venn__grouping_columns__dropdown, 'options'),
     Output(ids.navbar_analyze_venn__grouping_columns__dropdown, 'value')),
    (Output(ids.navbar_analyze_clustergram__grouping_columns__dropdown, 'options'),
     Output(ids.navbar_analyze_clustergram__grouping_columns__dropdown, 'value')),
    (Output(ids.navbar_analyze_prerec__grouping_columns__dropdown, 'options'),
     Output(ids.navbar_analyze_prerec__grouping_columns__dropdown, 'value')),
    (Output(ids.navbar_analyze_summary__metadata_grouping_columns__dropdown, 'options'),
     Output(ids.navbar_analyze_summary__metadata_grouping_columns__dropdown, 'value')),

    Input(ids.navbar_upload__compare_set_valid__store, 'data'),
    Input(ids.navbar_upload__metadata_valid__store, 'data'),

    Input(ids.navbar_navbar__session_id__store, 'data'),
)
def on_complete_metadata_upload(compare_set_valid, metadata_valid, session_id):
    group_selection = []
    group_selection_value = []

    (
        (_, metadata),
        _,
        _
    ) = get_uploaded_data(session_id, compare_set_valid=compare_set_valid, metadata_valid=metadata_valid)

    if metadata is not None:
        group_selection = metadata.columns.values
        if len(group_selection) > 0:
            group_selection_value = [group_selection[0]]

    return (group_selection, group_selection_value) * 4


def generate_metadata_summary_card(metadata: pd.DataFrame, files_not_in_metadata: list, e: Exception = None):
    if e:
        return upload_summary_card('Metadata', 'An exception occurred:', [f'{e}'])

    if type(metadata) == pd.DataFrame:
        if files_not_in_metadata:
            status = 'Metadata missing for files below:'
            filenames = files_not_in_metadata
        else:
            status = 'Loaded following columns:'
            filenames = metadata.columns.values.tolist()
    else:
        status = 'Not uploaded.'
        filenames = [
            '> Required to dynamically group VCFs.',
            '> Must contain a column titled "FILENAME".',
            '> Must contain a row for each VCF in the compare set.',
        ]

    return upload_summary_card('Metadata', status, filenames, aggregate_after=4)


def missing_metadata(metadata: pd.DataFrame, filenames_to_look_for: list):
    missing_filenames = []
    for filename in filenames_to_look_for:
        if filename not in metadata['FILENAME'].values:
            missing_filenames.append(filename)
    return missing_filenames
