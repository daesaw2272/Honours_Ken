"""
Scopus Search API -> CSV
Systematic Review:
Predictors of Domain-Specific Unmet Care Needs Among
Community-Dwelling Older Adults

Run locally. Your API key never leaves your machine.

Setup:
    pip install requests

Windows:
    setx SCOPUS_API_KEY "your_key_here"
    # Restart terminal after running setx

Mac/Linux:
    export SCOPUS_API_KEY="your_key_here"

Usage:
    python scopus_systematic_review.py
"""

import os
import csv
import time
import requests


# ============================================================
# API SETTINGS
# ============================================================
API_KEY = os.environ.get("SCOPUS_API_KEY", "").strip()

if not API_KEY:
    raise SystemExit(
        "SCOPUS_API_KEY is not set. "
        "Add your Elsevier API key as an environment variable."
    )
BASE_URL = "https://api.elsevier.com/content/search/scopus"

COUNT = 25

# Scopus API search result limit per query
MAX_RESULTS = 5000


# ============================================================
# SYSTEMATIC REVIEW SEARCH STRATEGY
# ============================================================

"""
Concept 1: Older adults

Concept 2: Unmet care / assistance needs

Concept 3: Care domains / community care

IMPORTANT:
We deliberately DO NOT require:
    - machine learning
    - prediction
    - Australia
    - specific predictors

because doing so could exclude relevant studies.
"""


SEARCHES = {

    # ========================================================
    # MAIN SYSTEMATIC REVIEW SEARCH
    # ========================================================

    "scopus_systematic_review_main": (

        '('

        # ----------------------------------------------------
        # Concept 1: Older adults
        # ----------------------------------------------------

        'TITLE-ABS-KEY('
        '"older adult*" '
        'OR "older person*" '
        'OR "older people" '
        'OR elderly '
        'OR ageing '
        'OR aging '
        'OR geriatric*'
        ') '

        'AND '

        # ----------------------------------------------------
        # Concept 2: Domain-specific unmet care needs
        # ----------------------------------------------------

        'TITLE-ABS-KEY('

        # Explicit unmet-care phrases
        '"unmet care need*" '
        'OR "unmet assistance need*" '
        'OR "unmet support need*" '

        'OR '

        # Generic unmet need must occur close to a care domain
        '('
        '"unmet need*" W/8 '
        '('
        '"activities of daily living" '
        'OR ADL '
        'OR ADLs '
        'OR "instrumental activities of daily living" '
        'OR IADL '
        'OR IADLs '
        'OR "personal care" '
        'OR "self care" '
        'OR mobility '
        'OR "household task*" '
        'OR "household activit*" '
        'OR "household chore*" '
        'OR housework '
        'OR "domestic task*" '
        'OR transport* '
        'OR "meal preparation" '
        'OR "property maintenance"'
        ')'
        ')'

        ')'

        ')'

        ' AND PUBYEAR > 2009'
    ),


    # ========================================================
    # SUPPLEMENTARY SEARCH
    # ========================================================

    "scopus_unmet_care_supplement": (

        '('

        'TITLE-ABS-KEY('
        '"older adult*" '
        'OR "older person*" '
        'OR "older people" '
        'OR elderly '
        'OR ageing '
        'OR aging '
        'OR geriatric*'
        ') '

        'AND '

        'TITLE-ABS-KEY('
        '"unmet care need*" '
        'OR "unmet assistance need*" '
        'OR "unmet support need*" '
        'OR "unmet need* for assistance" '
        'OR "unmet need* for care"'
        ')'

        ')'

        ' AND PUBYEAR > 2009'
    ),
}

# ============================================================
# OUTPUT FIELDS
# ============================================================

FIELDS = [
    "dc:title",
    "dc:creator",
    "prism:publicationName",
    "prism:coverDate",
    "prism:doi",
    "citedby-count",
    "dc:description",
    "authkeywords",
    "subtypeDescription",
    "prism:url",
]


# ============================================================
# RUN SEARCH
# ============================================================

def run_search(name, query):

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    rows = []

    start = 0

    while True:

        params = {
            "query": query,
            "start": start,
            "count": COUNT,
            "view": "STANDARD",
        }

        headers = {
            "X-ELS-APIKey": API_KEY,
            "Accept": "application/json",
        }

        try:

            response = requests.get(
                BASE_URL,
                params=params,
                headers=headers,
                timeout=30,
            )

        except requests.RequestException as error:

            print(f"Request failed: {error}")
            break


        if response.status_code != 200:

            print(
                f"Error {response.status_code}: "
                f"{response.text[:500]}"
            )

            break


        data = response.json().get(
            "search-results",
            {}
        )


        total = int(
            data.get(
                "opensearch:totalResults",
                0
            )
        )


        entries = data.get(
            "entry",
            []
        )


        if start == 0:

            print(
                f"Total Scopus results: {total}"
            )


        if not entries:
            break


        for entry in entries:

            if "error" in entry:
                continue

            row = {
                field: entry.get(field, "")
                for field in FIELDS
            }

            # Add systematic-review metadata
            row["search_source"] = name

            rows.append(row)


        start += COUNT


        print(
            f"Downloaded: "
            f"{min(start, total)} / {total}"
        )


        if start >= total:
            break


        if start >= MAX_RESULTS:

            print(
                "\nWARNING:"
                f" Search produced more than "
                f"{MAX_RESULTS} records."
            )

            print(
                "Consider splitting the search "
                "by publication year."
            )

            break


        # Avoid hammering the API
        time.sleep(0.25)


    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    output_fields = FIELDS + [
        "search_source"
    ]


    output_path = f"{name}.csv"


    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=output_fields,
        )

        writer.writeheader()

        writer.writerows(rows)


    print(
        f"\nSaved {len(rows)} records "
        f"-> {output_path}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "\nSYSTEMATIC REVIEW SCOPUS SEARCH\n"
    )

    print(
        "Review title:\n"
        "Predictors of Domain-Specific "
        "Unmet Care Needs Among "
        "Community-Dwelling Older Adults:"
        " A Systematic Review\n"
    )


    for search_name, search_query in SEARCHES.items():

        run_search(
            search_name,
            search_query
        )


    print("\nDone.")

    print(
        "\nNext steps:"
        "\n1. Combine searches"
        "\n2. Remove duplicates"
        "\n3. Title/abstract screening"
        "\n4. Full-text screening"
        "\n5. Record exclusions"
        "\n6. PRISMA flow diagram"
    )