## Test Instructions

Due to licensing concerns, original Steam `.vdf` files are not included in this repository.

To run the full test suite:

1. Obtain the required `.vdf` files.
2. Copy them into the `tests/input_files/` directory.
3. In the terminal cd into the repo directory
4. Run `python -m pytest -v -r A`.

Test output is compared to the files in `tests/expected_output/`.

---

ACBrotherhood_Edit.vdf is the same as the original with

```
"latam"
{
    "language"		"Latam"
}
```

Added in the language section.