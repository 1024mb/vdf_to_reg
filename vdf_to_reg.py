import argparse
import os
import sys

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
    # Script exit codes:
    #                   2 = Language not found in supported list
    #                   3 = No registry data inside VDF file
    #                   4 = Language is in the supported list but wasn't found in the VDF file.

    args = parser.parse_args()

    supported_languages = ["arabic", "bulgarian", "schinese", "tchinese", "czech", "danish", "dutch", "english",
                           "finnish", "french", "german", "greek", "hungarian", "italian", "japanese", "koreana",
                           "norwegian", "polish", "portuguese", "brazilian", "romanian", "russian", "spanish", "latam",
                           "swedish", "thai", "turkish", "ukrainian", "vietnamese"]

    game_language = sanitize_lang(args.language.lower())

    if game_language is not None and game_language not in supported_languages:
        print("\nERROR: Specified language is not present in the supported languages list, if this is a mistake please"
              " contact the maintainer, make a PR or edit this script file to include the language.")
        sys.exit(2)
    top, reg_key_names, reg_file = create_reg(args.path, args.output)
    populate_reg(top, reg_key_names, reg_file, game_language, args.install_dir, args.no_fallback)
    sys.exit(0)


def sanitize_lang(language):
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


def create_reg(vdf_path, output):
    if output is None or output == "":
        output = os.getcwd() + os.path.sep + os.path.splitext(os.path.basename(vdf_path))[0] + ".reg"
    vdf_content = vdf.parse(open(vdf_path, "r", encoding="utf-8", errors="surrogatepass"))
    if "Registry" not in vdf_content["InstallScript"].keys():
        print("There is nothing to create a registry of, aborting...")
        sys.exit(3)
    top = vdf_content["InstallScript"]["Registry"]
    reg_key_names = list(top.keys())  # To get the registry key names/paths
    reg_file = open(output, "w", encoding="utf-8", errors="surrogatepass")
    reg_file.writelines("Windows Registry Editor Version 5.00\n\n")
    return top, reg_key_names, reg_file


def populate_reg(top, reg_key_names, reg_file, game_language, install_dir, no_fallback):
    language_present = False
    language_fallback = False
    if len(top) > 1:
        reg_separator = "\n"
    else:
        reg_separator = ""

    for x, j in enumerate(reg_key_names):
        reg_file.writelines("[" + reg_key_names[x] + "]\n")
        key_data = top[reg_key_names[x]]

        sub_keys_list = list(key_data.keys())

        for jj in sub_keys_list:
            if type(key_data[jj]) is dict:
                for i in key_data[jj]:
                    if type(key_data[jj][i]) is dict:
                        if jj == "string" or jj == "dword":  # chances are that this is for the  language, I haven't
                            # seen another use of this.
                            if i == game_language:
                                language_present = True
                                set_language(key_data, jj, i, reg_file)
                            elif no_fallback is False:
                                if game_language == "latam":
                                    if i == "spanish" and language_present is False:
                                        set_language(key_data, jj, i, reg_file)
                                        language_fallback = True
                                elif game_language == "brazilian":
                                    if i == "portuguese" and language_present is False:
                                        set_language(key_data, jj, i, reg_file)
                                        language_fallback = True
                                elif game_language == "tchinese":
                                    if i == "schinese" and language_present is False:
                                        set_language(key_data, jj, i, reg_file)
                                        language_fallback = True
                        else:
                            sub_sub_keys_list = list(key_data[jj][i])
                            sub_sub_keys_list.append(key_data[jj][i][sub_sub_keys_list[0]].
                                                     replace("%INSTALLDIR%", install_dir).replace("\\", "\\\\"))
                            reg_file.writelines("\"" + sub_sub_keys_list[0] + "\"=\"" + sub_sub_keys_list[1] + "\"\n")
                    else:
                        value_key = key_data[jj][i]
                        value_key = value_key.replace("%INSTALLDIR%", install_dir).replace("\\", "\\\\")
                        reg_file.writelines("\"" + i + "\"=\"" + value_key + "\"\n")
            else:
                value_key = key_data[jj]
                value_key = value_key.replace("%INSTALLDIR%", install_dir).replace("\\", "\\\\")
                reg_file.writelines("\"" + jj + "\"=\"" + value_key + "\"\n")

        reg_file.writelines(reg_separator)

    reg_file.close()

    if language_fallback is True:
        fallback_msg = " But a fallback has been used to set the language to the closest variation."
    else:
        fallback_msg = ""

    if language_present is False:
        print("\nINFO: The specified language wasn't found in the VDF file." + fallback_msg)
        sys.exit(4)


def set_language(key_data, jj, i, reg_file):
    lang_list = list(key_data[jj][i])
    lang_list.append(key_data[jj][i][lang_list[0]])
    if jj == "dword":
        reg_file.writelines("\"" + lang_list[0] + "\"=dword:" + lang_list[1] + "\n")
    else:
        reg_file.writelines("\"" + lang_list[0] + "\"=\"" + lang_list[1] + "\"\n")


if __name__ == "__main__":
    main()
