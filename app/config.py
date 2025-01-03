import os
import sys


def resolve_path_relative_to_project(path):
    expanded_path = os.path.expanduser(path)
    
    if os.path.isabs(expanded_path):
        return expanded_path
    else:
        project_directory = os.path.dirname(os.path.dirname(__file__))
        return os.path.realpath(os.path.join(project_directory, expanded_path))


url_base = os.getenv('VCF_OBSERVER_URL_BASE', '/')
if url_base:
    if url_base[0] != '/':
        url_base = '/' + url_base
    if url_base[-1] != '/':
        url_base = url_base + '/'


bed_files_directory =  resolve_path_relative_to_project(os.getenv('VCF_OBSERVER_BED_DIR', 'BED Files'))

redis_url = os.environ.get('VCF_OBSERVER_REDIS_URL')

debug_mode = False
auto_submit = False

bundled_mode = False or getattr(sys, 'frozen', False)
