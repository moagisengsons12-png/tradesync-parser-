# TradeSync Parser
    #### Video Demo:  <URL HERE>
    #### Description:
    I built a data parser to clean trading history files exported from broker and prop firm platforms like MT4, MT5, and
    MatchTrader. The problem with these platforms is that they often export incredibly messy data—like using the wrong server
    timezone or using asset names that don't match up with popular trading journals like FXReplay or TradeZella. Because of this
    mismatched data, the journal platforms fail their validation checks when you try to upload the file. When that happens,
    you’re forced to add every single trade manually. It’s boring, irritating, and a complete waste of time. On days when I took
    multiple trades, the sheer hassle made me lazy, and I’d just give up on tracking my journal altogether. I created this Data
    Parser to solve this exact problem. Real-world data is messy, and I wanted a simple, automated way to clean my files so I
    could track my trading progress with ease.

    The data parser relies on three core functions. The first function addresses the frustrating timezone mismatch issue. When I
    export a report, the trade times never match my local timezone. If I don't adjust for this, the journal platform completely
    rejects the file during validation. Checking chart times constantly to figure out if a platform uses a 1-hour or 2-hour
    offset is incredibly stressful, especially since getting it wrong means going back to hated manual entry. To fix this, I
    built the clean_timestamp function. It takes the raw timestamp string from the file and splits it into a list containing the
    date and time separately. For the date portion, the function uses a regular expression (regex) to substitute the dots (.)
    with standardized dashes (-).

    Next, the function extracts the time string from that split list. It splits the time by colons so it can isolate just the
    hour piece, since there's no reason to alter the minutes or seconds. It then applies the math for the timezone shift by
    adding the user-defined hour offset typed into the terminal. To handle trades that cross over the midnight boundary, I used
    the modulo operator (% 24). This restricts the results to a strict 24-hour cycle by finding the remainder after dividing by
    24, allowing the time to roll over correctly instead of going past 24. Finally, the function ensures the hours are formatted
    with leading zeros to maintain two digits, and then returns the newly cleaned date and time.

    The second function handles asset mapping by checking the file rows for the symbol column. I added this because broker asset
    names rarely match the exact naming conventions required by online trading journals. If they don't match, the journal's
    metrics and analytics pages won't display that trade data correctly, completely ruining my ability to see the full picture of
    my performance and find areas to improve. To solve this cleanly, I built a dictionary right inside the function. Using a
    dictionary makes it incredibly easy to add new trading assets down the line without having to hardcode endless .replace()
    statements every single time. The function takes the raw asset symbol from the file, checks it against the dictionary using
    the .get() method, replaces it with the journal-friendly version if found, or simply returns the raw asset as a fallback
    before outputting the final clean_asset.

    The final function is responsible for generating a terminal report that summarizes the total rows processed and any errors
    encountered. It provides crucial feedback by showing a clear status message—whether the file is completely ready for upload,
    if there were formatting errors, or if no rows were processed at all. This status check acts as a final safeguard, giving me
    complete confidence that the data is flawless before the parser executes its last job: creating and saving the newly cleaned
    export file so I never have to deal with an unvetted upload again.

    The main function serves as the central hub of the application, coordinating command-line parsing, file validation, data
    extraction, and final exporting. It leverages multiple tools, including pandas, BeautifulSoup, regular expressions, and
    structural try-except blocks to build a secure pipeline. When executed, main first inspects the command-line arguments to
    verify that both a filename and an hour offset are supplied. It extracts these arguments from the terminal, converting the
    hour offset into an integer. A try-except block wraps this conversion to immediately catch errors if an invalid number is
    provided, while terminal print statements confirm that the correct file and offset values are loaded.

    Inside main, conditional if/elif/else blocks split the execution path depending on whether the input file ends with .csv or .
    html. Instead of relying on slow, manual loops to iterate through rows, I specifically utilized pandas for vectorized data
    cleaning across both file types. This approach allows pandas to target entire columns instantly by name, completely removing
    the need to manually track down indices. For HTML files, the script integrates BeautifulSoup to open the file, read the table
    structure, and strip out clean text. It then uses a regular expression to verify that a row data cell begins with four
    digits, confirming it represents a valid timestamp entry.
    Next, the script maps the data to a column array structured around standard MetaTrader layouts, ensuring wide compatibility
    with various trading brokers. The dataframe calls our specialized cleaning functions across entire columns at once, updating
    asset symbols and calculating the new timestamp offsets simultaneously. This entire parsing operation runs inside a protected
    try block, backed by error handling that catches missing files, layout parsing anomalies, or unsupported file formats before
    generating a final summary report and exporting a beautifully cleaned spreadsheet.

    The final segment of the program handles exporting the exact columns required by popular trade tracking journals. I
    implemented a protective guardrail that checks for column existence dynamically, ensuring missing fields in different file
    types won't cause the script to crash. The processed data is then saved directly to ready_to_import.csv or ready_to_import.
    html. It wraps up by running the reporting function to output the final status message, leaving me with a perfectly formatted 
    file ready for seamless upload, saving hours of tedious administrative work.
