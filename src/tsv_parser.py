# -*- coding: utf-8 -*-
import pathlib


def parse_tsv_files(p: pathlib.Path) -> list:
    tsv_files = []

    for i in p.iterdir():
        if i.suffix == ".tsv" and i.name.split('_')[0] == 'test':
            tsv_files.append(str(i.joinpath()))

    return tsv_files


def get_tsv_files_path() -> list:
    tsv_files = []
    p = pathlib.Path().cwd().joinpath()

    tsv_files.extend(parse_tsv_files(p))

    for i in p.iterdir():
        if i.is_dir() and i.name == 'testsuites':
            tsv_files.extend(parse_tsv_files(pathlib.Path(i.cwd()).joinpath(i.name)))

    return tsv_files


if __name__ == '__main__':
    pass
