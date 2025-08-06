import os
import shutil

import pytest

from vdf_to_reg import start_processing

INPUT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "input_files")
EXPECTED_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "expected_output")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tmp_output")

MAIN_INSTALL_DIR = r"C:\Games"
MAIN_LANGUAGE = "latam"


def setup_function():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def teardown_function():
    shutil.rmtree(OUTPUT_DIR)


@pytest.mark.parametrize("input_file,expected_file", [
    ("ACBrotherhood.vdf", "ACBrotherhood.reg"),
    ("ACBrotherhood_Edit.vdf", "ACBrotherhood_Edit.reg"),
    ("AlphaProtocol.vdf", "AlphaProtocol.reg"),
    ("DeadIsland.vdf", "DeadIsland.reg"),
    ("DeadRising2.vdf", "DeadRising2.reg"),
    ("Fallout4.vdf", "Fallout4.reg"),
    ("SniperNZA.vdf", "SniperNZA.reg"),
    ("TheCuartel.vdf", "TheCuartel.reg"),
    ("Watch_Dogs.vdf", "Watch_Dogs.reg"),
    ("AWayOut.vdf", "AWayOut.reg"),
    ("ItTakesTwo.vdf", "ItTakesTwo.reg"),
])
def test_parser_output(input_file,
                       expected_file):
    input_path = os.path.join(INPUT_DIR, input_file)
    expected_path = os.path.join(EXPECTED_DIR, expected_file)
    output_path = os.path.join(OUTPUT_DIR, expected_file)

    try:
        start_processing(language=MAIN_LANGUAGE,
                         vdf_path=input_path,
                         output=output_path,
                         install_dir=os.path.join(MAIN_INSTALL_DIR, os.path.splitext(input_file)[0]),
                         auto_import=False,
                         no_fallback=False,
                         batch=False)
    except SystemExit as e:
        assert e.code in [0, 2, 4, 5]

    with open(output_path) as f1, open(expected_path) as f2:
        output_content = f1.read()
        expected_content = f2.read()
        assert output_content == expected_content
