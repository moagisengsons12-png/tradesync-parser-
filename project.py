from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import re
import sys
from typing import Iterable

import pandas as pd
from bs4 import BeautifulSoup

ASSET_MAP = {
    "US100": "NAS100",
    "US500": "SPX500USD",
}

HTML_COLUMNS = [
    "Open Time",
    "Symbol",
    "Type",
    "Volume",
    "Open Price",
    "Stop Loss",
    "Take Profit",
    "Close Time",
    "Close Price",
    "Commission",
    "Swap",
    "Profit",
    "Comment",
    "Total",
]

EXPORT_COLUMNS = [
    "Time",
    "Date",
    "Asset",
    "Type",
    "Side",
    "Volume",
    "Open Price",
    "Close Price",
    "Stop Loss",
    "Take Profit",
    "Close Time",
    "Commission",
    "Swap",
    "Profit",
    "Comment",
    "Total",
]

TIMESTAMP_PATTERN = re.compile(r"^(?P<date>\d{4}[.-]\d{2}[.-]\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2})$")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean CSV or HTML trade history files and export a journal-ready file."
    )
    parser.add_argument("input_file", help="Path to the CSV or HTML trade export file.")
    parser.add_argument(
        "hour_offset",
        type=int,
        help="Timezone offset to apply to all timestamps (e.g. 2 or -5).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output filename. Defaults to ready_to_import.csv/html.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    input_path = Path(args.input_file)
    output_path = Path(args.output) if args.output else default_output_path(input_path)

    if not input_path.exists():
        print(f"Error: File does not exist: {input_path}", file=sys.stderr)
        return 1

    try:
        if input_path.suffix.lower() == ".csv":
            df = load_csv(input_path)
        elif input_path.suffix.lower() == ".html":
            df = load_html(input_path)
        else:
            print(
                f"Error: Unsupported file format: {input_path.suffix}", file=sys.stderr
            )
            return 1

        if df.empty:
            print("No trading rows were found in the input file.")
            print(generate_report(0, 0))
            return 0

        cleaned_df = clean_dataframe(df, args.hour_offset)
        save_output(cleaned_df, output_path)
        print(generate_report(len(cleaned_df), 0))
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def load_csv(file_path: Path) -> pd.DataFrame:
    df = pd.read_csv(file_path, dtype=str, skip_blank_lines=True)
    df.columns = df.columns.str.strip()
    return df


def load_html(file_path: Path) -> pd.DataFrame:
    html_text = None
    for encoding in ("utf-16", "utf-8", "latin-1"):
        try:
            html_text = file_path.read_text(encoding=encoding)
            break
        except UnicodeError:
            continue

    if html_text is None:
        raise ValueError("Unable to decode HTML file with utf-16, utf-8 or latin-1.")

    soup = BeautifulSoup(html_text, "html.parser")
    table = soup.find("table")
    if table is None:
        raise ValueError("Could not find a table in the HTML file.")

    parsed_rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        row_data = [cell.get_text().strip() for cell in cells]
        if len(row_data) >= len(HTML_COLUMNS) and re.match(r"^\d{4}", row_data[0]):
            parsed_rows.append(row_data[: len(HTML_COLUMNS)])

    if not parsed_rows:
        return pd.DataFrame(columns=HTML_COLUMNS)

    return pd.DataFrame(parsed_rows, columns=HTML_COLUMNS)


def clean_dataframe(df: pd.DataFrame, hour_offset: int) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()

    if "Symbol" not in df.columns or "Open Time" not in df.columns:
        raise ValueError("Input data must include Symbol and Open Time columns.")

    df = df.dropna(subset=["Symbol", "Open Time"]).reset_index(drop=True)
    df["Symbol"] = df["Symbol"].astype(str).str.strip()
    df["Open Time"] = df["Open Time"].astype(str).str.strip()

    df["Asset"] = df["Symbol"].apply(map_asset)

    cleaned_open = df["Open Time"].apply(lambda value: clean_timestamp(value, hour_offset))
    df["Date"] = cleaned_open.apply(lambda pair: pair[0])
    df["Time"] = cleaned_open.apply(lambda pair: pair[1])

    if "Close Time" in df.columns:
        df["Close Time"] = df["Close Time"].astype(str).str.strip()
        df["Close Time"] = df["Close Time"].replace({"nan": ""})
        df["Close Time"] = df["Close Time"].apply(
            lambda value: apply_close_time(value, hour_offset)
        )

    total_value = calculate_total(df)
    df["Total"] = total_value

    return df


def clean_timestamp(raw_string: str, hour_offset: int) -> tuple[str, str]:
    if raw_string is None:
        raise ValueError("Timestamp is empty.")

    value = str(raw_string).strip()
    match = TIMESTAMP_PATTERN.match(value)
    if not match:
        raise ValueError(f"Invalid timestamp format: {value!r}")

    normalized_date = match.group("date").replace(".", "-")
    normalized_time = match.group("time")
    dt = datetime.strptime(f"{normalized_date} {normalized_time}", "%Y-%m-%d %H:%M:%S")
    dt += timedelta(hours=hour_offset)

    return dt.date().isoformat(), dt.time().isoformat(timespec="seconds")


def apply_close_time(raw_string: str, hour_offset: int) -> str:
    if not raw_string:
        return ""
    try:
        return clean_timestamp(raw_string, hour_offset)[1]
    except ValueError:
        return raw_string


def map_asset(symbol: str) -> str:
    return ASSET_MAP.get(symbol, symbol)


def validate_row_data(row):
    if isinstance(row, (list, tuple)):
        raw_asset = row[1] if len(row) > 1 else row[0] if row else ""
    else:
        raw_asset = str(row)

    return ASSET_MAP.get(raw_asset, raw_asset)


def calculate_total(df: pd.DataFrame) -> float:
    if "Profit" not in df.columns:
        return 0.0

    profit_series = pd.to_numeric(
        df["Profit"].astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    ).fillna(0.0)
    return float(profit_series.sum())


def default_output_path(input_path: Path) -> Path:
    return input_path.with_name(
        "ready_to_import.html" if input_path.suffix.lower() == ".html" else "ready_to_import.csv"
    )


def save_output(df: pd.DataFrame, output_path: Path) -> None:
    export_cols = [col for col in EXPORT_COLUMNS if col in df.columns]
    export_df = df[export_cols]

    if output_path.suffix.lower() == ".html":
        export_df.to_html(output_path, index=False)
    else:
        export_df.to_csv(output_path, index=False)
    print(f"[+] Success: Cleaned data exported to '{output_path.name}'!")


def generate_report(total_rows: int, error_count: int) -> str:
    if error_count == 0 and total_rows > 0:
        status_msg = "STATUS: 100% Clean File. Ready to be uploaded!🚀"
    elif error_count > 0:
        status_msg = f"STATUS: Completed with {error_count} errors. Check Files.⚠️"
    else:
        status_msg = "STATUS: No Trading rows were processed.🛑"

    return (
        "\n"
        "=========================================\n"
        "        TRADE JOURNAL IMPORT REPORT      \n"
        "=========================================\n"
        f"  [+] Total Rows Processed : {total_rows}\n"
        f"  [!] Errors Encountered   : {error_count}\n"
        "=========================================\n"
        f"{status_msg}\n"
        "=========================================\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
