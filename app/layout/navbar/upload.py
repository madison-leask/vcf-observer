from dash import dcc, html

from layout import ids, styles
from layout.components import button, upload_label, multi_upload, upload_result
import config


upload_tab = (
    dcc.Tab(id=ids.navbar_upload__tab__tab, label='Upload', value='tab-upload', style=styles.tab, selected_style=styles.tab_selected, children=[
        upload_label('Compare Set'),
        multi_upload(ids.navbar_upload__compare_set__upload),
        upload_result(ids.navbar_upload__compare_set_upload_result__div),

        upload_label('Golden Set'),
        multi_upload(ids.navbar_upload__golden_set__upload),
        upload_result(ids.navbar_upload__golden_set_upload_result__div),

        upload_label('Metadata'),
        multi_upload(ids.navbar_upload__metadata__upload),
        upload_result(ids.navbar_upload__metadata_upload_result__div),

        upload_label('Genomic Regions'),
        multi_upload(ids.navbar_upload__regions__upload),
        upload_result(ids.navbar_upload__regions_upload_result__div),

        html.Div('*Max size per file: 500 MB', style={'fontSize': '0.8em', 'fontStyle': 'italic', 'paddingTOp': '1em'}),

        dcc.Store(id=ids.navbar_upload__compare_set_valid__store, data='compare_set_is_invalid'),
        dcc.Store(id=ids.navbar_upload__golden_set_valid__store, data='golden_set_is_invalid'),
        dcc.Store(id=ids.navbar_upload__metadata_valid__store, data='metadata_is_invalid'),
        dcc.Store(id=ids.navbar_upload__regions_valid__store, data='regions_is_invalid'),

        button(ids.navbar_upload__go_to_analyze__button, 'Analyze >'),
    ])
)


def generate_js_to_prevent_navigation_during_uploads():
    with open('layout/navbar/antd_lock_template.js', 'r') as template_js_file:
        js_template = template_js_file.read()

    populated_template = (js_template
        .replace("''//tabBarId", f"'#{ids.navbar_navbar__tabs__tabs}';")
        .replace("''//welcomeTabButtonId", f"'#{ids.navbar_welcome__tab__tab}';")
        .replace("''//uploadTabButtonId", f"'#{ids.navbar_upload__tab__tab}';")
        .replace("''//analyzeTabButtonId", f"'#{ids.navbar_analyze_analyze__tab__tab}';")
        .replace("''//goToAnalyzeButtonId", f"'#{ids.navbar_upload__go_to_analyze__button}';")
        .replace("''//compareSetUploadId", f"'#{ids.navbar_upload__compare_set__upload}';")
        .replace("''//goldenSetUploadId", f"'#{ids.navbar_upload__golden_set__upload}';")
        .replace("''//metadataUploadId", f"'#{ids.navbar_upload__metadata__upload}';")
        .replace("''//regionsUploadId", f"'#{ids.navbar_upload__regions__upload}';")
    )

    with open('assets/antd_lock.js', 'w') as css_file:
        css_file.write(populated_template)


if not config.bundled_mode:
    generate_js_to_prevent_navigation_during_uploads()
