# TradeSync Parser

A lightweight parser for cleaning trading history exports from CSV and HTML reports.

## What it does

- supports `.csv` and `.html` trade export files
- normalizes `Open Time` and `Close Time` timestamps with a configurable hour offset
- maps broker symbols to journal-friendly asset names
- removes empty rows and keeps required columns only
- exports a ready-to-import file for journal tools

## Requirements

- Python 3.10+
- pandas
- beautifulsoup4

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python project.py path/to/export.csv 2
```

Optional output filename:

```bash
python project.py path/to/export.html -o cleaned_export.html
```

## Output

- default CSV output: `ready_to_import.csv`
- default HTML output: `ready_to_import.html`

## Testing

```bash
pytest -q
```

## Notes

- The parser preserves existing `Profit` values and computes a `Total` column based on numeric profit values.
- HTML imports support both `utf-16` and `utf-8` encodings.
- Add new asset mappings in `ASSET_MAP` inside `project.py`.
