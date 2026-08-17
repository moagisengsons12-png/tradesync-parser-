import pandas as pd
from pathlib import Path

def test_clean_timestamp_no_offset():
    from project import clean_timestamp

    date, time = clean_timestamp("2026.07.16 14:15:41", 0)
    assert date == "2026-07-16"
    assert time == "14:15:41"


def test_clean_timestamp_with_offset():
    from project import clean_timestamp

    date, time = clean_timestamp("2026.07.16 14:15:41", 2)
    assert date == "2026-07-16"
    assert time == "16:15:41"


def test_clean_timestamp_rollover():
    from project import clean_timestamp

    date, time = clean_timestamp("2026.07.16 23:30:00", 2)
    assert date == "2026-07-17"
    assert time == "01:30:00"


def test_clean_timestamp_negative_offset():
    from project import clean_timestamp

    date, time = clean_timestamp("2026.07.16 01:30:00", -3)
    assert date == "2026-07-15"
    assert time == "22:30:00"


def test_validate_row_data_mapped():
    from project import validate_row_data

    assert validate_row_data([None, "US100"]) == "NAS100"
    assert validate_row_data([None, "US500"]) == "SPX500USD"


def test_validate_row_data_unmapped():
    from project import validate_row_data

    assert validate_row_data([None, "EURUSD"]) == "EURUSD"
    assert validate_row_data([None, "GBPUSD"]) == "GBPUSD"


def test_clean_dataframe_adds_columns_and_total():
    from project import clean_dataframe

    df = pd.DataFrame(
        {
            "Symbol": ["US100", "EURUSD"],
            "Open Time": ["2026.07.16 22:00:00", "2026.07.16 23:30:00"],
            "Close Time": ["2026.07.16 22:30:00", "2026.07.16 23:45:00"],
            "Profit": ["100", "-20"],
        }
    )

    cleaned = clean_dataframe(df, 2)

    assert cleaned.loc[0, "Asset"] == "NAS100"
    assert cleaned.loc[1, "Date"] == "2026-07-17"
    assert cleaned.loc[1, "Time"] == "01:30:00"
    assert cleaned.loc[0, "Close Time"] == "00:30:00"
    assert cleaned["Total"].tolist() == [80.0, 80.0]


def test_load_html_extracts_table_rows(tmp_path):
    from project import load_html

    sample_html = (
        "<html><body><table>"
        "<tr>"
        "<td>2026.07.16 14:00:00</td>"
        "<td>US100</td>"
        "<td>Buy</td>"
        "<td>1</td>"
        "<td>100</td>"
        "<td>0</td>"
        "<td>0</td>"
        "<td>2026.07.16 14:15:00</td>"
        "<td>101</td>"
        "<td>0</td>"
        "<td>0</td>"
        "<td>10</td>"
        "<td>Test</td>"
        "<td>10</td>"
        "</tr>"
        "</table></body></html>"
    )
    html_file = tmp_path / "sample.html"
    html_file.write_text(sample_html, encoding="utf-8")

    df = load_html(html_file)

    assert len(df) == 1
    assert df.loc[0, "Symbol"] == "US100"
    assert df.loc[0, "Open Time"] == "2026.07.16 14:00:00"
