import os
import sys


url_base = os.getenv('VCF_OBSERVER_URL_BASE', '/')
if url_base:
    if url_base[0] != '/':
        url_base = '/' + url_base
    if url_base[-1] != '/':
        url_base = url_base + '/'

bed_files_directory =  os.getenv('VCF_OBSERVER_BED_DIR', os.path.realpath('../BED Files'))

redis_url = os.environ.get('VCF_OBSERVER_REDIS_URL')

debug_mode = False
auto_submit = False

bundled_mode = False or getattr(sys, 'frozen', False)
