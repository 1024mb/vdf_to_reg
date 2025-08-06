import argparse
import logging
import os
import subprocess
import sys
from io import TextIOWrapper

import vdf

__version__ = "0.5.0"


def main():
    parser = argparse.ArgumentParser(prog="vdf-to-reg")
    parser.add_argument("-v", "--version",
                        action="version",
                        version=f"%(prog)s v{__version__}")
    parser.add_argument("--path", "-p",
                        type=str,
                        required=False,
                        default="",
                        help="VDF file vdf_path, by default loads the \"installscript.vdf\" file located in the current"
                             " directory.")
    parser.add_argument("--install-dir", "-id",
                        type=str,
                        required=False,
                        default=os.getcwd(),
                        help="By default is the current directory, you can specify the game's installation"
                             " directory here.")
    parser.add_argument("--language", "-l",
                        type=str,
                        required=False,
                        default="english",
                        help="Language to use. Specify the English name of the language, don't use the native name"
                             " or ISO codes. By default is English")
    parser.add_argument("--output", "-o",
                        required=False,
                        help="Specify output file vdf_path or name. By default is the same basename as the vdf file.")
    parser.add_argument("--no-fallback", "-nf",
                        action="store_true",
                        help="Set this for the script to not fallback to the closest variation of the language."
                             " Currently it only works for Latam, Brazilian and TChinese")
    parser.add_argument("--batch", "-b",
                        action="store_true",
                        help="Create batch file to import registry files.")
    parser.add_argument("--auto-import", "-ai",
                        action="store_true",
                        help="Auto import reg file after creation.")
    parser.add_argument("--log-level",
                        help="Set the logging level",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        default="INFO")
    # Script exit codes:
    #                   2 = Language not found in supported list
    #                   3 = No registry data inside VDF file
    #                   4 = Language is in the supported list but wasn't found in the VDF file, no fallback used.
    #                   5 = Language is in the supported list but wasn't found in the VDF file, fallback used.

    args = parser.parse_args()

    language = args.language
    path = args.path
    batch = args.batch
    auto_import = args.auto_import
    output = args.output
    no_fallback = args.no_fallback
    install_dir = args.install_dir
    log_level = args.log_level

    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)

    if path == "":
        path = detect_vdf_file()

    start_processing(language=language,
                     vdf_path=path,
                     batch=batch,
                     auto_import=auto_import,
                     output=output,
                     no_fallback=no_fallback,
                     install_dir=install_dir)


def detect_vdf_file() -> str:
    vdf_file: str = os.path.join(os.getcwd(), "installscript.vdf")

    if not os.path.isfile(vdf_file):
        logging.warning("No installscript.vdf file found in the current directory, searching for one...")

        cur_dir_content: list[str] = os.listdir(os.getcwd())

        number_of_vdf_files: int = 0
        vdf_file: str = ""
        for file in cur_dir_content:
            if file.lower().endswith(".vdf"):
                number_of_vdf_files += 1
                vdf_file = file

        if number_of_vdf_files == 1:
            return os.path.join(os.getcwd(), vdf_file)
        else:
            logging.error("Multiple (or none) VDF files found in the current directory, aborting...")
            sys.exit(3)
    else:
        return vdf_file


def start_processing(language: str,
                     vdf_path: str,
                     output: str | None,
                     install_dir: str,
                     batch: bool,
                     auto_import: bool,
                     no_fallback: bool) -> None:
    supported_languages = ["arabic", "bulgarian", "schinese", "tchinese", "czech", "danish", "dutch", "english",
                           "finnish", "french", "german", "greek", "hungarian", "italian", "japanese", "koreana",
                           "norwegian", "polish", "portuguese", "brazilian", "romanian", "russian", "spanish", "latam",
                           "swedish", "thai", "turkish", "ukrainian", "vietnamese"]

    preferred_language = sanitize_lang(language=language)

    if preferred_language not in supported_languages:
        logging.critical("Specified language is not present in the supported languages list, "
                         "if this is a mistake please contact the maintainer, "
                         "make a PR or edit this script file to include the language.")
        sys.exit(2)

    top, reg_key_names, output = create_reg(vdf_path=vdf_path,
                                            output=output,
                                            batch=batch)
    language_fallback, language_present = populate_reg(top=top,
                                                       reg_key_names=reg_key_names,
                                                       preferred_language=preferred_language,
                                                       install_dir=install_dir,
                                                       no_fallback=no_fallback,
                                                       output=output)
    if auto_import:
        logging.info("Importing reg file to the 32-bit registry location...")  # this is for old games
        subprocess.call(["reg", "import", output, "/reg:32"])
        logging.info("Importing reg file to the 64-bit registry location...")
        subprocess.call(["reg", "import", output, "/reg:64"])

    if language_fallback:
        fallback_msg = "\n      But a fallback has been used to set the language to the closest variation."
        exit_code = 5
    else:
        fallback_msg = ""
        exit_code = 4

    if not language_present:
        logging.info("The specified language wasn't found in the VDF file." + fallback_msg)
        sys.exit(exit_code)

    sys.exit(0)


def create_batch(output: str) -> None:
    with open(os.path.splitext(output)[0] + ".cmd", "w", encoding="utf-8", errors="surrogatepass") as stream:
        stream.writelines("REG IMPORT \"" + output + "\" /reg:32\n"
                          + "REG IMPORT \"" + output + "\" /reg:64")


def sanitize_lang(language: str) -> str:
    language = language.lower()

    if "chinese" in language:
        if "traditional" in language:
            language = "tchinese"
        else:
            language = "schinese"
    if "brazil" in language:
        language = "brazilian"
    if "spanish" in language and "latin" in language:
        language = "latam"
    if "korean" in language:
        language = "koreana"

    return language


def create_reg(vdf_path: str,
               output: str | None,
               batch: bool) -> tuple[dict, list[str], str]:
    if output is None or output == "":
        output = os.getcwd() + os.path.sep + os.path.splitext(os.path.basename(vdf_path))[0] + ".reg"

    vdf_content = vdf.parse(open(vdf_path, "r", encoding="utf-8", errors="surrogatepass"))

    if "Registry" not in vdf_content["InstallScript"].keys():
        logging.critical("There is nothing to create a registry of, aborting...")
        sys.exit(3)

    top = vdf_content["InstallScript"]["Registry"]
    reg_key_names = list(top.keys())  # To get the registry key names/paths

    with open(output, "w", encoding="utf-8", errors="surrogatepass") as reg_file:
        reg_file.writelines("Windows Registry Editor Version 5.00\n\n")

    if batch:
        create_batch(output)

    return top, reg_key_names, output


def populate_reg(top: dict,
                 reg_key_names: list[str],
                 preferred_language: str,
                 install_dir: str,
                 no_fallback: bool,
                 output: str) -> tuple[bool, bool]:
    language_present = False
    language_fallback = False

    if len(top) > 1:
        reg_separator = "\n"
    else:
        reg_separator = ""

    match preferred_language:
        case "latam":
            fallback_language = "spanish"
        case "brazilian":
            fallback_language = "portuguese"
        case "tchinese":
            fallback_language = "schinese"
        case "spanish":
            fallback_language = "latam"
        case "portuguese":
            fallback_language = "brazilian"
        case "schinese":
            fallback_language = "tchinese"
        case _:
            fallback_language = None

    with open(output, "a", encoding="utf-8", errors="surrogatepass") as reg_file:
        for reg_key_name in reg_key_names:
            reg_file.writelines("[" + sanitize_key_name(key_name=reg_key_name) + "]\n")
            key_data = top[reg_key_name]

            language_found = None

            for sub_key in key_data:
                if type(key_data[sub_key]) is dict:
                    for language in key_data[sub_key]:
                        language_lower = language.lower()

                        if preferred_language == language_lower:
                            language_present = True
                            language_fallback = False
                            language_found = language
                            break

                    if not language_present:
                        if no_fallback or fallback_language is None:
                            continue

                        for language in key_data[sub_key]:
                            language_lower = language.lower()

                            if fallback_language == language_lower:
                                language_present = False
                                language_fallback = True
                                language_found = language
                                break

                    for entry in key_data[sub_key]:
                        if type(key_data[sub_key][entry]) is dict:
                            # chances are that this is for the language, I haven't seen another use of this.
                            if entry.lower() != language_found:
                                continue

                            if sub_key.lower() == "string" or sub_key.lower() == "dword":
                                set_language(key_data, sub_key, entry, reg_file)
                            else:
                                for key, value in key_data[sub_key][entry].items():
                                    reg_file.writelines("\""
                                                        + key
                                                        + "\"=\""
                                                        + value.replace("%INSTALLDIR%", install_dir).replace("\\",
                                                                                                             "\\\\")
                                                        + "\"\n")
                        else:
                            value_key = key_data[sub_key][entry]
                            if type(value_key) is dict:
                                for key, value in value_key.items():
                                    value = value.replace("%INSTALLDIR%", install_dir).replace("\\", "\\\\")
                                    if key.lower() == "(default)":
                                        reg_file.writelines("@=\"" + value + "\"\n")
                                    else:
                                        reg_file.writelines("\"" + key + "\"=\"" + value + "\"\n")

                            elif type(value_key) is str:
                                value_key = value_key.replace("%INSTALLDIR%", install_dir).replace("\\", "\\\\")
                                if entry.lower() == "(default)":
                                    reg_file.writelines("@=\"" + value_key + "\"\n")
                                else:
                                    reg_file.writelines("\"" + entry + "\"=\"" + value_key + "\"\n")
                            else:
                                raise TypeError("Unknown type, support not added for this.")
                else:
                    value_key = key_data[sub_key]
                    if type(value_key) is str:
                        value_key = value_key.replace("%INSTALLDIR%", install_dir).replace("\\", "\\\\")
                        if sub_key.lower() == "(default)":
                            reg_file.writelines("@=\"" + value_key + "\"\n")
                        else:
                            reg_file.writelines("\"" + sub_key + "\"=\"" + value_key + "\"\n")
                    else:
                        raise TypeError("Unknown type, support not added for this.")

            reg_file.writelines(reg_separator)

    return language_fallback, language_present


def set_language(key_data: dict,
                 sub_key: str,
                 language: str,
                 reg_file: TextIOWrapper) -> None:
    for key, value in key_data[sub_key][language].items():
        if sub_key.lower() == "dword":
            reg_file.writelines("\"" + key + "\"=dword:" + value + "\n")
        else:
            reg_file.writelines("\"" + key + "\"=\"" + value + "\"\n")


def sanitize_key_name(key_name: str) -> str:
    root_key, sub_key = key_name.split("\\", 1)

    if root_key.lower().endswith("_wow64_32"):
        first_child, rest = sub_key.split("\\", 1)
        return root_key[:-9] + "\\" + first_child + "\\WOW6432Node\\" + rest
    elif root_key.lower().endswith("_wow64_64"):
        return root_key[:-9] + "\\" + sub_key
    else:
        return key_name


if __name__ == "__main__":
    main()
