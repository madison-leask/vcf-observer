import uuid

import dash
import pandas as pd

from dash import html
from dash.dependencies import Input, Output, State

from dash_app import app
from data.cache import SessionCache
from data.retrieval import get_uploaded_data
from data.file_readers import read_csv_files, get_filenames_from_variant_df
from layout import ids, styles
import config

from flask import request


@app.server.route(config.url_base + 'upload/', methods=['POST'])
def upload():
    session_id = request.values.get('uploadId')
    session_cache = SessionCache(session_id)

    file_content = request.files['file'].read()

    cache_key = str(uuid.uuid4())
    
    session_cache.set_byte_string_cache(cache_key, file_content)
    
    return {'cacheKey': cache_key}


def get_files(session_id, upload_tasks) -> tuple:
    session_cache = SessionCache(session_id)

    previous_tasks = session_cache.get_processed_upload_tasks()

    filenames = []
    file_contents = []
    if upload_tasks:
        for task in upload_tasks:
            task_id = task['uid']
            if (task_id not in previous_tasks and
                    task['taskStatus'] == 'success'):
                previous_tasks.append(task_id)
                
                filename = task['fileName']
                cache_key = task['uploadResponse']['cacheKey']

                filenames.append(filename)

                file_content = session_cache.get_byte_string_cache(cache_key)
                file_contents.append(file_content)

                session_cache.delete_byte_string_cache(cache_key)

    session_cache.set_processed_upload_tasks(previous_tasks)

    return filenames, file_contents


@app.callback(
    Output(ids.navbar_upload__compare_set_upload_result__div, 'children'),
    Output(ids.display_upload__compare_set_summary_card__div, 'children'),
    Output(ids.navbar_upload__compare_set_valid__store, 'data'),
    
    Input(ids.navbar_upload__compare_set__upload, 'listUploadTaskRecord'),
    
    Input(ids.navbar_navbar__session_id__store, 'data'),
)
def on_compare_set_upload(upload_tasks, session_id):
    filenames, contents = get_files(session_id, upload_tasks)

    compare_set = None
    compare_set_valid = 'compare_set_is_invalid'
    exception = None
    if filenames:
        try:
            compare_set = SessionCache(session_id).set_compare_set_as_df(filenames, contents)
            compare_set_valid = 'compare_set_is_valid'
            
        except Exception as e:
            exception = e

    result = vcf_upload_result(filenames, exception)
    summary_card = generate_compare_set_summary_card(compare_set, exception)

    return result, summary_card, compare_set_valid


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
            metadata = read_csv_files(metadata_filenames, metadata_contents)
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
            regions = SessionCache(session_id).set_regions_as_df(filenames, contents)
            regions_valid = 'regions_is_valid'
        except Exception as e:
            exception = e

    result = bed_upload_result(filenames, exception)
    summary_card = generate_regions_summary_card(regions, filenames, exception)

    return result, summary_card, regions_valid


def upload_summary_card(title, status, body_items, counts_list=None, aggregate_after=5):
    body_items = filename_lister(body_items, aggregate_after=aggregate_after)

    if counts_list:
        counts_list = count_lister(counts_list, aggregate_after=aggregate_after)
    else:
        counts_list = [None] * len(body_items)

    return (
        html.Div(style=styles.upload_summary_card, children=[
            html.Div([
                html.H4(title, style={'display': 'inline-block'}),
                html.Div(status, style={'display': 'inline-block', 'paddingLeft': '1em'})
            ]),
            html.P(style={'paddingLeft': '1em', 'marginBottom': '0px', 'whiteSpace': 'pre-line'}, children=[
                html.Pre(html.Table(html.Tbody(
                    [
                        html.Tr([
                            html.Td(count, style={'textAlign': 'right', 'paddingRight': '1em'}) if count else None,
                            html.Td(body_item)
                        ])
                        for count, body_item in zip(counts_list, body_items)
                    ]
                )))
            ])
        ])
    )


def vcf_upload_result(filenames: list, e: Exception = None):
    if e:
        message = 'Errors encountered when processing files.'
    else:
        message = f'{len(filenames)} VCFs have been loaded.'

        if len(filenames) == 0:
            message = 'No VCFs have been loaded.'

        if len(filenames) == 1:
            message = '1 VCF has been loaded.'

    return message


def csv_upload_result(filenames: list, e: Exception = None):
    if e:
        message = 'Errors encountered when processing files.'
    else:
        message = f'{len(filenames)} CSVs have been loaded.'

        if len(filenames) == 0:
            message = 'No CSVs have been loaded.'

        if len(filenames) == 1:
            message = '1 CSV has been loaded.'

    return message


def bed_upload_result(filenames: list, e: Exception = None):
    if e:
        message = 'Errors encountered when processing files.'
    else:
        message = f'{len(filenames)} BEDs have been loaded.'

        if len(filenames) == 0:
            message = 'No BEDs have been loaded.'

        if len(filenames) == 1:
            message = '1 BED has been loaded.'

    return message


def generate_compare_set_summary_card(compare_set: pd.DataFrame, e: Exception = None):
    if e:
        return upload_summary_card('Compare Set', 'An exception occurred:', [f'{e}'])

    if compare_set is None:
        status = 'Not uploaded.'
        filenames = ['> Required for analysis.']
        counts = []
    else:
        filenames = get_filenames_from_variant_df(compare_set)
        
        variant_counts = {}
        for filename in filenames:
            variant_counts[filename] = compare_set[filename].astype(int).sum()
        
        sorted_variant_counts = dict(sorted(
            variant_counts.items(),
            key=lambda pair: pair[1],
            reverse=True
        ))

        filenames = list(sorted_variant_counts.keys())
        counts = list(sorted_variant_counts.values())

        status = [html.Pre(sum(counts), style={'display': 'inline'}), ' variants loaded.']

    return upload_summary_card('Compare Set', status, filenames, counts, aggregate_after=11)


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


def generate_regions_summary_card(regions: pd.DataFrame, bed_filenames: list, e: Exception = None):
    if e:
        return upload_summary_card('Genomic Regions', 'An exception occurred:', [f'{e}'])

    if not bed_filenames:
        status = 'Not uploaded.'
        filenames = ['> Custom regions for filtering.']
    else:
        status = [html.Pre(len(regions), style={'display': 'inline'}), ' regions loaded.']
        filenames = bed_filenames

    return upload_summary_card('Genomic Regions', status, filenames, aggregate_after=3)


def filename_lister(filenames: list, aggregate_after: int) -> list:
    if len(filenames) > aggregate_after + 1:
        filenames[aggregate_after] = f'... and {len(filenames) - aggregate_after} more'
        filenames = filenames[:aggregate_after + 1]

    return filenames


def count_lister(counts: list, aggregate_after=11) -> list:
    if len(counts) > aggregate_after + 1:
        counts[aggregate_after] = sum(counts[aggregate_after:])
        counts = counts[:aggregate_after + 1]

    return list(map(str, counts))


def missing_metadata(metadata: pd.DataFrame, filenames_to_look_for: list):
    missing_filenames = []
    for filename in filenames_to_look_for:
        if filename not in metadata['FILENAME'].values:
            missing_filenames.append(filename)
    return missing_filenames
