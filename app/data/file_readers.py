import io
from gzip import GzipFile, BadGzipFile
from zipfile import ZipFile, BadZipFile
import warnings

import pandas as pd

import allel


def read_vcf_file(filename: str, data: bytes) -> pd.DataFrame:
    bytesio = get_decompressed_bytesio(data)
    
    fields = [
        'variants/CHROM',
        'variants/POS',
        'variants/REF',
        'variants/ALT',
        'variants/FILTER_PASS',
    ]

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        df = allel.vcf_to_dataframe(bytesio, fields)

    if df is None:
        return pd.DataFrame()
    
    df['ALT'] = df['ALT_1']
    
    df_alt_2 = df[df['ALT_2'].notna()]
    df_alt_2['ALT'] = df_alt_2['ALT_2']
    
    df_alt_3 = df[df['ALT_3'].notna()]
    df_alt_3['ALT'] = df_alt_3['ALT_3']

    df = pd.concat([df, df_alt_2, df_alt_3])

    if (~df['FILTER_PASS']).all():
        df['FILTER_PASS'] = True

    variants = (
        df.drop(columns=['ALT_1', 'ALT_2', 'ALT_3'])
        .drop_duplicates(['CHROM', 'POS', 'REF', 'ALT'])
        .reset_index(drop=True)
    )

    # Normalise chromosome names
    normalised_chroms = variants['CHROM'].apply(prepend_chr)
    nonstandard_chroms = list(set(normalised_chroms).difference(standard_chroms))
    variants['CHROM'] = pd.Categorical(
        values=normalised_chroms,
        categories=standard_chroms + nonstandard_chroms,
    )

    # Generate key
    vals = variants[['CHROM', 'POS', 'REF', 'ALT']].values
    keys = ['-'.join([row[0], str(row[1]), row[2], row[3]]) for row in vals]
    variants['KEY'] = keys
    
    return variants


def merge_variant_data(filenames: list, file_contents: list) -> pd.DataFrame:
    sorted_filenames = sorted(filenames)
    file_content_indices = list(range(len(file_contents)))
    sorted_file_content_indices = [
        file_content_index for filename, file_content_index
        in sorted(zip(filenames, file_content_indices))
    ]
    
    dataframes = {}
    for i, filename in enumerate(sorted_filenames):
        data = file_contents[sorted_file_content_indices[i]]
        
        dataframes[filename] = data

    concat_vcf_files = pd.concat(dataframes.values())
    
    union_of_variants = (
        concat_vcf_files.drop_duplicates('KEY')
        .sort_values(by=['CHROM', 'POS'])
        .reset_index(drop=True)
    )[['CHROM', 'POS', 'REF', 'ALT', 'KEY']]
    
    for filename, file_variants in dataframes.items():
        file_variants_set = set(file_variants['KEY'])
        union_of_variants[filename] = union_of_variants['KEY'].isin(file_variants_set)
        union_of_variants[filename+'/PASS'] = (
            union_of_variants
            .merge(file_variants, on='KEY', how='left')['FILTER_PASS']
            .fillna(False)
        )
    
    return union_of_variants


def get_filenames_from_variant_df(variant_df: pd.DataFrame) -> list:
    filenames = []
    for column_name in variant_df.columns:
        if (column_name not in {'CHROM', 'POS', 'REF', 'ALT', 'KEY'} and
            not column_name.endswith('/PASS')):
            filenames.append(column_name)
    return filenames


def get_filenames_from_regions_df(variant_df: pd.DataFrame) -> list:
    filenames = []
    for column_name in variant_df.columns:
        if (column_name not in {'CHROM', 'START', 'END'}):
            filenames.append(column_name)
    return filenames


standard_chroms = [f'chr{i}' for i in range(1, 22 + 1)]
standard_chroms += ['chrX', 'chrY', 'chrW', 'chrZ', 'chrM']


def prepend_chr(chrom: str) -> str:
    if chrom.isdigit():
        return 'chr' + chrom
    return chrom


def read_csv_file(filename: list, data: list) -> pd.DataFrame:
    bytesio = get_decompressed_bytesio(data)
    return (
        pd.read_csv(bytesio, dtype=str)
        .dropna(subset=['FILENAME'])
        .drop_duplicates('FILENAME')
        .fillna('_NULL_')
    )


def merge_metadata(dfs: list) -> pd.DataFrame:
    return (
        pd.concat(dfs)
        .drop_duplicates('FILENAME')
        .reset_index(drop=True)
    )


def read_bed_file(filename: list, data: bytes) -> pd.DataFrame:
    bytesio = get_decompressed_bytesio(data)
    
    first_char = bytesio.read(1).decode()
    bytesio.seek(0)
    
    comment_indicator = None
    if first_char in {'#', '>'}:
        comment_indicator = first_char
    
    df = pd.read_csv(
        bytesio,
        sep='\t',
        comment=comment_indicator,
        names=['CHROM', 'START', 'END'],
        dtype={'CHROM': 'str', 'START': 'int', 'END': 'int'},
        usecols=['CHROM', 'START', 'END'],
    )
    
    df['CHROM'] = df['CHROM'].apply(prepend_chr)
    df[filename] = True
    return df


def merge_regions(dfs: list) -> pd.DataFrame:
    return (
        pd.concat(dfs)
        .reset_index(drop=True)
        .fillna(False)
    )


def read_local_bed_files(filenames: list) -> pd.DataFrame:
    data = []
    for filename in filenames:
        data += [
            pd.read_csv(
                filename,
                sep='\t',
                comment='#',
                names=['CHROM', 'START', 'END'],
                dtype={'CHROM': 'str', 'START': 'int', 'END': 'int'},
                usecols=['CHROM', 'START', 'END'],
            )
        ]

    df = pd.concat(data).reset_index(drop=True)
    df['CHROM'] = df['CHROM'].apply(lambda x: 'chr' + x if x.isdigit() else x)
    return df


def get_decompressed_bytesio(data: bytes) -> io.BufferedIOBase:
    bytesio = io.BytesIO(data)
    
    try:
        decompressed_bytesio = GzipFile(fileobj=bytesio)
        decompressed_bytesio.read(1)
        decompressed_bytesio.seek(0)
        return decompressed_bytesio
    except BadGzipFile:
        bytesio.seek(0)
    
    try:
        zipped_vcf = ZipFile(bytesio)
        decompressed_bytesio = io.BytesIO(zipped_vcf.read(zipped_vcf.namelist()[0]))
        return decompressed_bytesio
    except BadZipFile:
        bytesio.seek(0)
    
    return bytesio
