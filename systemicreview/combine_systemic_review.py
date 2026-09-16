import os
import re
import pandas as pd


# ============================================================
# FILES
# ============================================================

FILES = [
    ("scopus_systematic_review_main.csv", "Scopus"),
    ("scopus_unmet_care_supplement.csv", "Scopus"),

    ("wos_systematic_review_main.csv", "Web of Science"),
    ("wos_unmet_care_supplement.csv", "Web of Science"),

    ("pubmed_systematic_review_main.csv", "PubMed"),
    ("pubmed_unmet_care_supplement.csv", "PubMed"),
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_column(df, column_name):
    """
    Return a column if it exists, otherwise return blanks.
    """

    if column_name in df.columns:
        return df[column_name].fillna("").astype(str)

    return pd.Series(
        [""] * len(df),
        index=df.index
    )


def normalise_doi(doi):
    """
    Convert DOI into a consistent format.

    Examples:
    https://doi.org/10.1234/abc -> 10.1234/abc
    DOI:10.1234/abc            -> 10.1234/abc
    """

    if pd.isna(doi):
        return ""

    doi = str(doi).strip().lower()

    doi = doi.replace(
        "https://doi.org/",
        ""
    )

    doi = doi.replace(
        "http://doi.org/",
        ""
    )

    doi = doi.replace(
        "http://dx.doi.org/",
        ""
    )

    doi = re.sub(
        r"^doi:\s*",
        "",
        doi
    )

    return doi.strip()


def normalise_title(title):
    """
    Normalise titles for duplicate detection.
    """

    if pd.isna(title):
        return ""

    title = str(title).lower()

    # Remove punctuation
    title = re.sub(
        r"[^\w\s]",
        " ",
        title
    )

    # Collapse repeated whitespace
    title = re.sub(
        r"\s+",
        " ",
        title
    )

    return title.strip()


def combine_unique(values):
    """
    Combine unique non-empty values from duplicate records.
    """

    cleaned = []

    for value in values:

        if pd.isna(value):
            continue

        value = str(value).strip()

        if not value:
            continue

        if value not in cleaned:
            cleaned.append(value)

    return "; ".join(cleaned)


# ============================================================
# STANDARDISE EACH DATABASE
# ============================================================

def standardise_scopus(df, filename):

    output = pd.DataFrame()

    output["title"] = safe_column(
        df,
        "dc:title"
    )

    output["authors"] = safe_column(
        df,
        "dc:creator"
    )

    output["journal"] = safe_column(
        df,
        "prism:publicationName"
    )

    output["year"] = safe_column(
        df,
        "prism:coverDate"
    ).str[:4]

    output["doi"] = safe_column(
        df,
        "prism:doi"
    )

    output["abstract"] = safe_column(
        df,
        "dc:description"
    )

    output["keywords"] = safe_column(
        df,
        "authkeywords"
    )

    output["document_type"] = safe_column(
        df,
        "subtypeDescription"
    )

    output["url"] = safe_column(
        df,
        "prism:url"
    )

    output["times_cited"] = safe_column(
        df,
        "citedby-count"
    )

    output["pmid"] = ""
    output["wos_uid"] = ""

    output["database"] = "Scopus"
    output["search_file"] = filename

    if "search_source" in df.columns:
        output["search_source"] = safe_column(
            df,
            "search_source"
        )
    else:
        output["search_source"] = filename.replace(
            ".csv",
            ""
        )

    return output


def standardise_wos(df, filename):

    output = pd.DataFrame()

    output["title"] = safe_column(
        df,
        "title"
    )

    output["authors"] = safe_column(
        df,
        "authors"
    )

    output["journal"] = safe_column(
        df,
        "source"
    )

    output["year"] = safe_column(
        df,
        "year"
    )

    output["doi"] = safe_column(
        df,
        "doi"
    )

    output["abstract"] = ""
    
    output["keywords"] = safe_column(
        df,
        "author_keywords"
    )

    output["document_type"] = safe_column(
        df,
        "document_type"
    )

    output["url"] = safe_column(
        df,
        "wos_url"
    )

    output["times_cited"] = safe_column(
        df,
        "times_cited"
    )

    output["pmid"] = ""

    output["wos_uid"] = safe_column(
        df,
        "uid"
    )

    output["database"] = "Web of Science"
    output["search_file"] = filename

    if "search_source" in df.columns:
        output["search_source"] = safe_column(
            df,
            "search_source"
        )
    else:
        output["search_source"] = filename.replace(
            ".csv",
            ""
        )

    return output


def standardise_pubmed(df, filename):

    output = pd.DataFrame()

    output["title"] = safe_column(
        df,
        "title"
    )

    output["authors"] = safe_column(
        df,
        "authors"
    )

    output["journal"] = safe_column(
        df,
        "journal"
    )

    output["year"] = safe_column(
        df,
        "year"
    )

    output["doi"] = safe_column(
        df,
        "doi"
    )

    output["abstract"] = safe_column(
        df,
        "abstract"
    )

    output["keywords"] = safe_column(
        df,
        "keywords"
    )

    output["document_type"] = safe_column(
        df,
        "publication_types"
    )

    output["url"] = safe_column(
        df,
        "pubmed_url"
    )

    output["times_cited"] = ""

    output["pmid"] = safe_column(
        df,
        "pmid"
    )

    output["wos_uid"] = ""

    output["database"] = "PubMed"
    output["search_file"] = filename

    if "search_source" in df.columns:
        output["search_source"] = safe_column(
            df,
            "search_source"
        )
    else:
        output["search_source"] = filename.replace(
            ".csv",
            ""
        )

    return output


# ============================================================
# LOAD FILES
# ============================================================

all_dataframes = []

print("\nSYSTEMATIC REVIEW DATABASE MERGE\n")

for filename, database in FILES:

    if not os.path.exists(filename):

        print(
            f"WARNING: File not found -> {filename}"
        )

        continue

    print(
        f"Loading {filename}..."
    )

    df = pd.read_csv(
        filename,
        dtype=str,
        encoding="utf-8-sig"
    )

    print(
        f"  {len(df)} records"
    )

    if database == "Scopus":

        standardised = standardise_scopus(
            df,
            filename
        )

    elif database == "Web of Science":

        standardised = standardise_wos(
            df,
            filename
        )

    elif database == "PubMed":

        standardised = standardise_pubmed(
            df,
            filename
        )

    else:
        continue

    all_dataframes.append(
        standardised
    )


# ============================================================
# COMBINE
# ============================================================

if not all_dataframes:

    raise SystemExit(
        "ERROR: No CSV files were found."
    )


combined = pd.concat(
    all_dataframes,
    ignore_index=True
)


print(
    f"\nTotal records before deduplication: "
    f"{len(combined)}"
)


# ============================================================
# SAVE RAW COMBINED DATA
# ============================================================

combined.to_csv(
    "systematic_review_combined_raw.csv",
    index=False,
    encoding="utf-8-sig"
)

print(
    "Saved raw combined file -> "
    "systematic_review_combined_raw.csv"
)


# ============================================================
# NORMALISE DOI AND TITLE
# ============================================================

combined["doi_normalised"] = (
    combined["doi"]
    .apply(normalise_doi)
)

combined["title_normalised"] = (
    combined["title"]
    .apply(normalise_title)
)


# ============================================================
# CREATE DUPLICATE KEY
# ============================================================

def create_duplicate_key(row):

    # DOI is strongest identifier
    if row["doi_normalised"]:

        return (
            "DOI:"
            + row["doi_normalised"]
        )

    # Fall back to normalised title
    if row["title_normalised"]:

        return (
            "TITLE:"
            + row["title_normalised"]
        )

    # No DOI/title -> preserve separately
    return (
        "UNMATCHED:"
        + str(row.name)
    )


combined["duplicate_key"] = (
    combined.apply(
        create_duplicate_key,
        axis=1
    )
)


# ============================================================
# COLLAPSE DUPLICATES
# ============================================================

deduplicated_rows = []


for duplicate_key, group in combined.groupby(
    "duplicate_key",
    sort=False
):

    # Choose the first record as the base
    row = group.iloc[0].copy()


    # --------------------------------------------------------
    # Preserve provenance
    # --------------------------------------------------------

    row["database"] = combine_unique(
        group["database"]
    )

    row["search_source"] = combine_unique(
        group["search_source"]
    )

    row["search_file"] = combine_unique(
        group["search_file"]
    )


    # --------------------------------------------------------
    # Preserve identifiers
    # --------------------------------------------------------

    row["pmid"] = combine_unique(
        group["pmid"]
    )

    row["wos_uid"] = combine_unique(
        group["wos_uid"]
    )


    # --------------------------------------------------------
    # Choose best available metadata
    # --------------------------------------------------------

    for column in [
        "title",
        "authors",
        "journal",
        "year",
        "doi",
        "abstract",
        "keywords",
        "document_type",
        "url",
        "times_cited",
    ]:

        values = [
            str(v).strip()
            for v in group[column]
            if pd.notna(v)
            and str(v).strip()
        ]

        if values:

            # For abstract choose longest version
            if column == "abstract":

                row[column] = max(
                    values,
                    key=len
                )

            else:

                row[column] = values[0]


    row["number_of_duplicate_records"] = len(
        group
    )

    deduplicated_rows.append(
        row
    )


deduplicated = pd.DataFrame(
    deduplicated_rows
)


# ============================================================
# CLEAN OUTPUT
# ============================================================

deduplicated = deduplicated.reset_index(
    drop=True
)


# Create systematic-review ID
deduplicated.insert(
    0,
    "review_id",
    [
        f"SR{number:05d}"
        for number in range(
            1,
            len(deduplicated) + 1
        )
    ]
)


# ============================================================
# SCREENING COLUMNS
# ============================================================

deduplicated[
    "title_abstract_decision"
] = ""

deduplicated[
    "title_abstract_exclusion_reason"
] = ""

deduplicated[
    "full_text_decision"
] = ""

deduplicated[
    "full_text_exclusion_reason"
] = ""

deduplicated[
    "notes"
] = ""


# ============================================================
# SAVE DEDUPLICATED CSV
# ============================================================

deduplicated.to_csv(
    "systematic_review_deduplicated.csv",
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# SAVE EXCEL SCREENING WORKBOOK
# ============================================================

try:

    deduplicated.to_excel(
        "systematic_review_screening.xlsx",
        index=False
    )

    excel_created = True

except ImportError:

    excel_created = False


# ============================================================
# SUMMARY
# ============================================================

raw_count = len(combined)

unique_count = len(deduplicated)

duplicates_removed = (
    raw_count - unique_count
)


print("\n" + "=" * 60)

print("MERGE COMPLETE")

print("=" * 60)

print(
    f"Records identified:       {raw_count}"
)

print(
    f"Duplicate records removed: {duplicates_removed}"
)

print(
    f"Unique records remaining:  {unique_count}"
)


print(
    "\nCreated:"
)

print(
    "1. systematic_review_combined_raw.csv"
)

print(
    "2. systematic_review_deduplicated.csv"
)

if excel_created:

    print(
        "3. systematic_review_screening.xlsx"
    )

else:

    print(
        "\nExcel file was not created."
    )

    print(
        "Install openpyxl:"
    )

    print(
        "pip install openpyxl"
    )