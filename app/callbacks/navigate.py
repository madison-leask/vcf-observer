from dash.dependencies import Input, Output, State

from dash_app import app
from layout import ids


app.clientside_callback(
    """
    function updateAnalysis(selected_tab) {
        let venn_hidden = true;
        let clustergram_hidden = true;
        let prerec_hidden = true;
        let summary_hidden = true;

        if (selected_tab === 'venn') {
            venn_hidden = false;
        }

        if (selected_tab === 'clustergram') {
            clustergram_hidden = false;
        }

        if (selected_tab === 'prerec') {
            prerec_hidden = false;
        }

        if (selected_tab === 'summary') {
            summary_hidden = false;
        }

        return [
            venn_hidden, venn_hidden,
            clustergram_hidden, clustergram_hidden,
            prerec_hidden, prerec_hidden,
            summary_hidden, summary_hidden
        ];
    }
    """,
    (Output(ids.navbar_analyze_venn__options__div, 'hidden'),
     Output(ids.display_analyze__venn_display__div, 'hidden')),

    (Output(ids.navbar_analyze_clustergram__options__div, 'hidden'),
     Output(ids.display_analyze__clustergram_display__div, 'hidden')),

    (Output(ids.navbar_analyze_prerec__options__div, 'hidden'),
     Output(ids.display_analyze__prerec_display__div, 'hidden')),

    (Output(ids.navbar_analyze_summary__options__div, 'hidden'),
     Output(ids.display_analyze__summary_display__div, 'hidden')),

    Input(ids.navbar_analyze_analyze__analysis_type__radio_items, 'value'),
)


app.clientside_callback(
    """
    function updateDisplay(selectedTab){
        let displayWelcomeHidden = true;
        let displayUploadedHidden = true;
        let displayResultsHidden = true;

        if (selectedTab === 'tab-welcome'){
            displayWelcomeHidden = false;
        }

        if (selectedTab === 'tab-upload'){
            displayUploadedHidden = false;
        }

        if (selectedTab === 'tab-analyze'){
            displayResultsHidden = false;
        }

        return [
            displayWelcomeHidden,
            displayUploadedHidden,
            displayResultsHidden,
        ];
    }
    """,
    Output(ids.display_welcome__display__div, 'hidden'),
    Output(ids.display_upload__display__div, 'hidden'),
    Output(ids.display_analyze__display__div, 'hidden'),
    Input(ids.navbar_navbar__tabs__tabs, 'value'),
    prevent_initial_call=True,
)


app.clientside_callback(
    """
    function buttonNavigation(upload, analyze, firstVisit) {
        let selectedTab;
        if (firstVisit === null) {
            selectedTab = 'tab-welcome';
        } else {
            selectedTab = 'tab-upload';
        }
        
        if (upload) {
            selectedTab = 'tab-upload';
        }
        
        if (analyze) {
            selectedTab = 'tab-analyze';
        }
        
        return [
            selectedTab,
            0, 0,
            'not_first_visit',
        ]
    }
    """,
    Output(ids.navbar_navbar__tabs__tabs, 'value'),

    Output(ids.navbar_upload__go_to_upload__button, 'n_clicks'),
    Output(ids.navbar_upload__go_to_analyze__button, 'n_clicks'),

    Output(ids.navbar_navbar__first_visit_for_tabs__store, 'data'),

    Input(ids.navbar_upload__go_to_upload__button, 'n_clicks'),
    Input(ids.navbar_upload__go_to_analyze__button, 'n_clicks'),

    State(ids.navbar_navbar__first_visit_for_tabs__store, 'data'),
)


app.clientside_callback(
    """
    function buttonGuideText(_1, _2, _3, _4, _5, _6, firstVisit) {
        let goToUploadText;
        let goToAnalyzeText;
        let submitText;
        if (firstVisit === null) {
            goToUploadText = 'Upload your VCFs >';
            goToAnalyzeText = 'Select analysis options >';
            submitText = 'Submit your analysis';
        } else {
            goToUploadText = 'Upload >';
            goToAnalyzeText = 'Analyze >';
            submitText = 'Submit';
        }
        
        return [
            goToUploadText,
            goToAnalyzeText,
            ...Array(6).fill(submitText),
            'not_first_visit'
        ]
    }
    """,
    Output(ids.navbar_upload__go_to_upload__button, 'children'),
    Output(ids.navbar_upload__go_to_analyze__button, 'children'),

    (Output(ids.navbar_analyze_venn__submit__button, 'children'),
    Output(ids.navbar_analyze_clustergram__submit__button, 'children'),
    Output(ids.navbar_analyze_prerec__submit__button, 'children'),
    Output(ids.navbar_analyze_summary__filename_submit__button, 'children'),
    Output(ids.navbar_analyze_summary__metadata_submit__button, 'children'),
    Output(ids.navbar_analyze_summary__raw_submit__button, 'children')),

    Output(ids.navbar_navbar__first_visit_for_buttons__store, 'data'),

    Input(ids.navbar_analyze_venn__submit__button, 'n_clicks'),
    Input(ids.navbar_analyze_clustergram__submit__button, 'n_clicks'),
    Input(ids.navbar_analyze_prerec__submit__button, 'n_clicks'),
    Input(ids.navbar_analyze_summary__filename_submit__button, 'n_clicks'),
    Input(ids.navbar_analyze_summary__metadata_submit__button, 'n_clicks'),
    Input(ids.navbar_analyze_summary__raw_submit__button, 'n_clicks'),

    State(ids.navbar_navbar__first_visit_for_buttons__store, 'data'),
)


app.clientside_callback(
    """
    function updateSummaryType(summaryType) {
        var filenameHidden = true;
        var metadataHidden = true;
        var rawHidden = true;

        if (summaryType === 'filename') {
            filenameHidden = false;
        }

        if (summaryType === 'metadata') {
            metadataHidden = false;
        }

        if (summaryType === 'raw') {
            rawHidden = false;
        }

        return [
            filenameHidden, filenameHidden,
            metadataHidden, metadataHidden,
            rawHidden, rawHidden
        ];
    }
    """,
    Output(ids.navbar_analyze_summary__filename_options__div, 'hidden'),
    Output(ids.display_analyze__filename_summary_display__div, 'hidden'),
    Output(ids.navbar_analyze_summary__metadata_options__div, 'hidden'),
    Output(ids.display_analyze__metadata_summary_display__div, 'hidden'),
    Output(ids.navbar_analyze_summary__raw_options__div, 'hidden'),
    Output(ids.display_analyze__raw_summary_display__div, 'hidden'),

    Input(ids.navbar_analyze_summary__type__radio_items, 'value'),
)


app.clientside_callback(
    """
    function updateFontSizeSelectorVisibility(visualizationType) {
        let fontSizeSelectorHidden = true;
        
        if (visualizationType === 'graph') {
            fontSizeSelectorHidden = false;
        }
        
        return fontSizeSelectorHidden;
    }
    """,
    Output(ids.navbar_analyze_summary__font_size__div, 'hidden'),
    Input(ids.navbar_analyze_summary__filename_visualization__div, 'value'),
)
