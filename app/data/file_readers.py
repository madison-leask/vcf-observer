from io import BytesIO
from gzip import GzipFile
from zipfile import ZipFile
import warnings

import pandas as pd

import allel


def read_vcf_file(file: BytesIO) -> pd.DataFrame:
    fields = [
        'variants/CHROM',
        'variants/POS',
        'variants/REF',
        'variants/ALT',
        'variants/FILTER_PASS',
    ]

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        df = allel.vcf_to_dataframe(file, fields)

    if df is None:
        return pd.DataFrame()
        
    all_read_columns = df.columns.values
    unwanted_columns = [
        column for column in ['ALT_2', 'ALT_3'] if column in all_read_columns
    ]

    for column in unwanted_columns:
        df[column] = df[column].fillna('')
    df['ALT'] = df['ALT_1'].str.cat([df[column] for column in unwanted_columns])

    if (~df['FILTER_PASS']).all():
        df['FILTER_PASS'] = True

    variants = (
        df.drop(columns=unwanted_columns + ['ALT_1'])
        .drop_duplicates(['CHROM', 'POS', 'REF', 'ALT'])
    )

    # Generate key
    vals = variants[['CHROM', 'POS', 'REF', 'ALT']].values
    keys = ['-'.join([row[0], str(row[1]), row[2], row[3]]) for row in vals]
    variants['KEY'] = keys
    
    return variants


def read_vcf_files(filenames: list, file_contents: list) -> pd.DataFrame:
    sorted_filenames = sorted(filenames)
    file_content_indices = list(range(len(file_contents)))
    sorted_file_content_indices = [
        file_content_index for filename, file_content_index
        in sorted(zip(filenames, file_content_indices))
    ]
    
    dataframes = {}
    for i, filename in enumerate(sorted_filenames):
        data = file_contents[sorted_file_content_indices[i]]
        
        bytesio = BytesIO(data)

        if filename[-3:] == '.gz':
            decompressed_bytesio = GzipFile(fileobj=bytesio)
        elif filename[-4:] == '.zip':
            zipped_vcf = ZipFile(bytesio)
            decompressed_bytesio = BytesIO(zipped_vcf.read(zipped_vcf.namelist()[0]))
        else:
            decompressed_bytesio = bytesio
            
        new_vcf = read_vcf_file(decompressed_bytesio)
        
        dataframes[filename] = new_vcf

    concat_vcf_files = pd.concat(dataframes.values())

    # Normalise chromosome names
    chroms = concat_vcf_files['CHROM'].values
    normalised_chroms = [prepend_chr(chrom) for chrom in chroms]
    nonstandard_chroms = list(set(normalised_chroms).difference(standard_chroms))
    concat_vcf_files['CHROM'] = pd.Categorical(
        values=normalised_chroms,
        categories=standard_chroms + nonstandard_chroms + ['null_chr'],
    )
    
    union_of_variants = (
        concat_vcf_files.drop_duplicates('KEY')
        .sort_values(by=['CHROM', 'POS'])
        .reset_index(drop=True)
    )[['CHROM', 'POS', 'REF', 'ALT', 'KEY']]
    
    for filename, file_variants in dataframes.items():
        union_of_variants[filename] = union_of_variants['KEY'].isin(file_variants['KEY'])
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


standard_chroms = [f'chr{i}' for i in range(1, 22 + 1)]
standard_chroms += ['chrX', 'chrY', 'chrW', 'chrZ', 'chrM']


def extract_chrom(chrom_string: str) -> str:
    if chrom_string in standard_chroms:
        return chrom_string

    for valid_chrom in standard_chroms:
        if valid_chrom in chrom_string:
            return valid_chrom

    return 'null_chr'


def prepend_chr(chrom: str) -> str:
    if chrom.isdigit():
        return 'chr' + chrom
    return chrom


def read_csv_files(filenames: list, file_contents: list) -> pd.DataFrame:
    data = []
    for filename, file_content in zip(filenames, file_contents):
        data += [pd.read_csv(BytesIO(file_content), dtype=str)]
    return (
        pd.concat(data)
        .drop_duplicates('FILENAME')
        .dropna(subset=['FILENAME'])
        .reset_index(drop=True)
    )


def read_bed_files(filenames: list, file_contents: list) -> pd.DataFrame:
    data = []
    for filename, file_content in zip(filenames, file_contents):
        bytesio = BytesIO(file_content)

        if filename[-3:] == '.gz':
            decompressed_bytesio = GzipFile(fileobj=bytesio)
        elif filename[-4:] == '.zip':
            zipped_bed = ZipFile(bytesio)
            decompressed_bytesio = BytesIO(zipped_bed.read(zipped_bed.namelist()[0]))
        else:
            decompressed_bytesio = bytesio
        
        comment_indicator = None
        if decompressed_bytesio.read(1)[0] in {'#', '>'}:
            comment_indicator = file_content[0]
        decompressed_bytesio.seek(0)
        data.append(
            pd.read_csv(
                decompressed_bytesio,
                sep='\t',
                comment=comment_indicator,
                names=['CHROM', 'START', 'END'],
                dtype={'CHROM': 'str', 'START': 'int', 'END': 'int'},
                usecols=['CHROM', 'START', 'END'],
            )
        )

    df = pd.concat(data).reset_index(drop=True)
    df['CHROM'] = df['CHROM'].apply(lambda x: 'chr' + x if x.isdigit() else x)
    return df


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
