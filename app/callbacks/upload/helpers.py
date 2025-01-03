import uuid

from data.cache import SessionCache


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

                file_content = session_cache.get_data_frame(cache_key)
                file_contents.append(file_content)

                session_cache.delete_data_frame(cache_key)

    session_cache.set_processed_upload_tasks(previous_tasks)

    return filenames, file_contents


def handle_upload(request, file_processing_function) -> dict:
    session_id = request.values.get('uploadId')
    session_cache = SessionCache(session_id)

    filename = request.files['file'].filename
    file_content = request.files['file'].read()

    data_frame = file_processing_function(filename, file_content)

    cache_key = str(uuid.uuid4())
    session_cache.set_data_frame(cache_key, data_frame)

    return {'cacheKey': cache_key}
