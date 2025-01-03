import os
import shutil

from data.file_readers import merge_variant_data, merge_regions

import pandas as pd
from flask_caching import Cache

import config
from dash_app import app


def clean_cache():
    pass


def delete_directory_if_exists(path):
    def directory_deleter():
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            pass
    return directory_deleter


if config.redis_url:
    CACHE_CONFIG = {
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': config.redis_url,
        'CACHE_DEFAULT_TIMEOUT': 24*60*60,
    }
else:  # Set up file system cache
    cache_directory = os.path.join(os.path.dirname(__file__), 'vcf_observer_cache')
    
    CACHE_CONFIG = {
        'CACHE_TYPE': 'FileSystemCache',
        'CACHE_DIR': cache_directory,
        'CACHE_DEFAULT_TIMEOUT': 24*60*60,
    }
    
    clean_cache = delete_directory_if_exists(cache_directory)

cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)


class SessionCache:
    def __init__(self, session_id):
        self.session_id = session_id
        self.compare_set_cache_key = session_id + '_compare_set'
        self.golden_set_cache_key = session_id + '_golden_set'
        self.metadata_cache_key = session_id + '_metadata'
        self.regions_cache_key = session_id + '_regions'

        self.filename_download_cache_key = session_id + '_filename_download'
        self.metadata_download_cache_key = session_id + '_metadata_download'
        self.raw_download_cache_key = session_id + '_raw_download'

        self.venn_figure_download_cache_key = session_id + '_venn_figure_download'
        self.venn_sites_download_cache_key = session_id + '_venn_sites_download'

        self.processed_upload_tasks_cache_key = session_id + '_processed_upload_tasks'

    def set_compare_set_as_df(self, filenames: list, file_contents: list) -> pd.DataFrame:
        data = merge_variant_data(filenames, file_contents)
        cache.set(self.compare_set_cache_key, data)
        return data

    def get_compare_set(self) -> pd.DataFrame:
        data = cache.get(self.compare_set_cache_key)
        if data is None:
            raise LookupError('The cached data has timed out.')
        return data

    def set_golden_set_as_df(self, filenames: list, file_contents: list) -> pd.DataFrame:
        data = merge_variant_data(filenames, file_contents)
        cache.set(self.golden_set_cache_key, data)
        return data

    def get_golden_set(self) -> pd.DataFrame:
        data = cache.get(self.golden_set_cache_key)
        if data is None:
            raise LookupError('The cached data has timed out.')
        return data

    def set_metadata(self, data):
        cache.set(self.metadata_cache_key, data)

    def get_metadata(self) -> pd.DataFrame:
        data = cache.get(self.metadata_cache_key)
        if data is None:
            raise LookupError('The cached data has timed out.')
        return data

    def set_regions_as_df(self, dfs) -> pd.DataFrame:
        data = (merge_regions(dfs)
                .sort_values(by=['START', 'END'])
                .reset_index(drop=True))
        cache.set(self.regions_cache_key, data)

        return data

    def get_regions(self) -> pd.DataFrame:
        data = cache.get(self.regions_cache_key)
        if data is None:
            raise LookupError('The cached data has timed out.')
        return data

    def set_filename_download(self, data: pd.DataFrame):
        cache.set(self.filename_download_cache_key, data)

    def get_filename_download(self) -> pd.DataFrame:
        data = cache.get(self.filename_download_cache_key)
        if data is None:
            raise LookupError('The cached data has timed out.')
        return data

    def set_metadata_download(self, data: pd.DataFrame):
        cache.set(self.metadata_download_cache_key, data)

    def get_metadata_download(self) -> pd.DataFrame:
        data = cache.get(self.metadata_download_cache_key)
        if data is None:
            raise LookupError('The cached data has timed out.')
        return data

    def set_raw_download(self, data: pd.DataFrame):
        cache.set(self.raw_download_cache_key, data)

    def get_raw_download(self) -> pd.DataFrame:
        data = cache.get(self.raw_download_cache_key)
        if data is None:
            raise LookupError('The cached data has timed out.')
        return data

    def set_venn_figure_download(self, figure_data: str):
        cache.set(self.venn_figure_download_cache_key, figure_data)

    def get_venn_figure_download(self) -> str:
        data = cache.get(self.venn_figure_download_cache_key)
        if data is None:
            raise LookupError('The cached data has timed out.')
        return data

    def set_venn_sites_download(self, data: pd.DataFrame):
        cache.set(self.venn_sites_download_cache_key, data)

    def get_venn_sites_download(self) -> pd.DataFrame:
        data = cache.get(self.venn_sites_download_cache_key)
        if data is None:
            raise LookupError('The cached data has timed out.')
        return data

    def set_processed_upload_tasks(self, processed_upload_tasks: list):
        cache.set(self.processed_upload_tasks_cache_key, processed_upload_tasks)

    def get_processed_upload_tasks(self) -> list:
        data = cache.get(self.processed_upload_tasks_cache_key)
        if data == None:
            data = []
        return data

    def set_data_frame(self, key_suffix: str, value: bytes):
        key = self.session_id + key_suffix
        cache.set(key, value)

    def get_data_frame(self, key_suffix) -> bytes:
        key = self.session_id + key_suffix
        return cache.get(key)

    def delete_data_frame(self, key_suffix: str):
        key = self.session_id + key_suffix
        cache.delete(key)
