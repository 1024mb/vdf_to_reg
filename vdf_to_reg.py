import argparse
import os
import subprocess
import sys
from io import TextIOWrapper

import vdf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", "-p", nargs="?", default="installscript.vdf",
                        help="VDF file path, by default loads the \"installscript.vdf\" file located in the current"
                             " directory.")
    parser.add_argument("--install-dir", "-id", nargs="?", default=os.getcwd(),
                        help="By default is the current directory, you can specify the game's installation"
                             " directory here.")
    parser.add_argument("--language", "-l", nargs="?", default="english",
                        help="Language to use. Specify the English name of the language, don't use the native name"
                             " or ISO codes. By default is English")
    parser.add_argument("--output", "-o", nargs="?",
                        help="Specify output file path or name. By default is the same basename as the vdf file.")
    parser.add_argument("--no-fallback", "-nf", action="store_true",
                        help="Set this for the script to not fallback to the closest variation of the language."
                             " Currently it only works for Latam, Brazilian and TChinese")
    parser.add_argument("--batch", "-b", action="store_true",
                        help="Create batch file to import registry files.")
    parser.add_argument("--auto-import", "-ai", action="store_true",
                        help="Auto import reg file after creation.")
    # Script exit codes:
    #                   2 = Language not found in supported list
    #                   3 = No registry data inside VDF file
    #                   4 = Language is in the supported list but wasn't found in the VDF file, no fallback used.
    #                   5 = Language is in the supported list but wasn't found in the VDF file, fallback used.

    args = parser.parse_args()

    supported_languages = ["arabic", "bulgarian", "schinese", "tchinese", "czech", "danish", "dutch", "english",
                           "finnish", "french", "german", "greek", "hungarian", "italian", "japanese", "koreana",
                           "norwegian", "polish", "portuguese", "brazilian", "romanian", "russian", "spanish", "latam",
                           "swedish", "thai", "turkish", "ukrainian", "vietnamese"]

    preferred_language = sanitize_lang(args.language.lower())

    if preferred_language is not None and preferred_language not in supported_languages:
        print("\nERROR: Specified language is not present in the supported languages list, if this is a mistake please"
              " contact the maintainer, make a PR or edit this script file to include the language.")
        sys.exit(2)

    top, reg_key_names, output = create_reg(args.path, args.output, args.batch)
    language_fallback, language_present = populate_reg(top, reg_key_names, preferred_language, args.install_dir,
                                                       args.no_fallback, output)
    if args.auto_import:
        print("Importing reg file to the 32-bit registry location...")  # this is for old games
        subprocess.call(["reg", "import", output, "/reg:32"])
        print("\nImporting reg file to the 64-bit registry location...")
        subprocess.call(["reg", "import", output, "/reg:64"])

    if language_fallback:
        fallback_msg = "\n      But a fallback has been used to set the language to the closest variation."
        exit_code = 5
    else:
        fallback_msg = ""
        exit_code = 4

    if not language_present:
        print("\nINFO: The specified language wasn't found in the VDF file." + fallback_msg)
        sys.exit(exit_code)

    sys.exit(0)


def create_batch(output: str) -> None:
    with open(os.path.splitext(output)[0] + ".cmd", "w", encoding="utf-8", errors="surrogatepass") as stream:
        stream.writelines("REG IMPORT \"" + output + "\" /reg:32\n"
                          + "REG IMPORT \"" + output + "\" /reg:64")


def sanitize_lang(language: str) -> str:
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
        print("There is nothing to create a registry of, aborting...")
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

    with open(output, "a", encoding="utf-8", errors="surrogatepass") as reg_file:
        for reg_key_name in reg_key_names:
            reg_file.writelines("[" + reg_key_name + "]\n")
            key_data = top[reg_key_name]

            for sub_key in key_data:
                if type(key_data[sub_key]) is dict:
                    for language in key_data[sub_key]:
                        if type(key_data[sub_key][language]) is dict:
                            # chances are that this is for the language, I haven't seen another use of this.
                            if sub_key.lower() == "string" or sub_key.lower() == "dword":
                                language_lower = language.lower()

                                if language_lower == preferred_language:
                                    language_present = True
                                    language_fallback = False
                                    set_language(key_data, sub_key, language, reg_file)
                                elif not no_fallback:
                                    if preferred_language == "latam":
                                        if language_lower == "spanish" and not language_present:
                                            set_language(key_data, sub_key, language, reg_file)
                                            language_fallback = True
                                    elif preferred_language == "brazilian":
                                        if language_lower == "portuguese" and not language_present:
                                            set_language(key_data, sub_key, language, reg_file)
                                            language_fallback = True
                                    elif preferred_language == "tchinese":
                                        if language_lower == "schinese" and not language_present:
                                            set_language(key_data, sub_key, language, reg_file)
                                            language_fallback = True
                            else:
                                sub_sub_keys_list = list(key_data[sub_key][language])
                                sub_sub_keys_list.append(key_data[sub_key][language][sub_sub_keys_list[0]].
                                                         replace("%INSTALLDIR%", install_dir).replace("\\", "\\\\"))
                                reg_file.writelines("\"" + sub_sub_keys_list[0] + "\"=\"" + sub_sub_keys_list[
                                    1] + "\"\n")
                        else:
                            value_key = key_data[sub_key][language]
                            value_key = value_key.replace("%INSTALLDIR%", install_dir).replace("\\", "\\\\")
                            reg_file.writelines("\"" + language + "\"=\"" + value_key + "\"\n")
                else:
                    value_key = key_data[sub_key]
                    value_key = value_key.replace("%INSTALLDIR%", install_dir).replace("\\", "\\\\")
                    reg_file.writelines("\"" + sub_key + "\"=\"" + value_key + "\"\n")

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


if __name__ == "__main__":
    main()
