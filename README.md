Script to extract registry data from Steam's VDF files to a file.  
By default, the script falls back to the closest variation of the language, this includes:

- Spanish if Latam is not found.
- Portuguese if Brazilian is not found.
- Simplified Chinese if TChinese is not found.

You can specify:

- Input file path.
- Language.
- No fallback usage.
- Game's installation directory.
- Output file path.

Default values:

- Input: `installscript.vdf`
- Language: `English`
- Fallback: `Yes`
- Install dir: `Current path`
- Output: same base name as `input` in `current path`.

I've only tested some games so far.

Dependencies:
---------------------------------------
- [VDF](https://pypi.org/project/vdf/)

Usage:
---------------------------------------

```
usage: vdf_to_reg.py [-h] [--path [PATH]] [--install-dir [INSTALL_DIR]] [--language [LANGUAGE]] [--output [OUTPUT]] [--no-fallback]

options:
  -h, --help            show this help message and exit
  --path [PATH], -p [PATH]
                        VDF file path, by default loads the "installscript.vdf" file located in the current directory.
  --install-dir [INSTALL_DIR], -id [INSTALL_DIR]
                        By default is the current directory, you can specify the game's installation directory here.
  --language [LANGUAGE], -l [LANGUAGE]
                        Language to use. Specify the English name of the language, don't use the native name or ISO codes. By default is English
  --output [OUTPUT], -o [OUTPUT]
                        Specify output file path or name. By default is the same basename as the vdf file.
  --no-fallback, -nf    Set this for the script to not fallback to the closest variation of the language. Currently it only works for Latam, Brazilian and TChinese
```
