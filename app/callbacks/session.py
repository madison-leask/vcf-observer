import uuid

from dash.dependencies import Input, Output, State

from dash_app import app
from layout import ids


@app.callback(
    Output(ids.navbar_navbar__session_id__store, 'data'),
    Output(ids.navbar_upload__compare_set__upload, 'uploadId'),
    Output(ids.navbar_upload__golden_set__upload, 'uploadId'),
    Output(ids.navbar_upload__metadata__upload, 'uploadId'),
    Output(ids.navbar_upload__regions__upload, 'uploadId'),
    Input(ids.navbar_navbar__session_id__store, 'storage_type'),
)
def set_session_id(_):
    session_id = str(uuid.uuid4())
    return (session_id,) * 5
