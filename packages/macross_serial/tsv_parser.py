import pathlib


def parse_tsv_files(p: pathlib.Path) -> list:
    tsv_files = []

    for i in p.iterdir():
        if i.suffix == ".tsv" and i.name.split('_')[0] == 'test':
            tsv_files.append(str(i.joinpath()))

    return tsv_files
