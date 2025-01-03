from dash import html

from layout import styles


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
