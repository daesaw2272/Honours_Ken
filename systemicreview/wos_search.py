"""
Web of Science Search API -> CSV

Systematic Review:
Factors Associated with Domain-Specific Unmet Care Needs
Among Community-Dwelling Older Adults: A Systematic Review

Run locally. Your API key never leaves your machine.

Setup:
    pip install requests

Mac/Linux:
    export WOS_API_KEY="your_key_here"

Windows:
    setx WOS_API_KEY "your_key_here"
    # Restart terminal after running setx

Usage:
    python WOS_search.py

Notes:
- Uses Web of Science Core Collection
- TS = Topic search
- Searches title, abstract, author keywords, and Keywords Plus
"""

import os
import csv
import time
import requests


# ============================================================
# API CONFIGURATION
# ============================================================

API_KEY = os.environ.get("WOS_API_KEY", "").strip()

if not API_KEY:
    raise SystemExit(
        "ERROR: WOS_API_KEY is not set. "
        "Add your Web of Science API key as an environment variable."
    )

BASE_URL = "https://api.clarivate.com/apis/wos-starter/v1/documents"

LIMIT = 50

# Set high enough so the full search is not truncated
MAX_RESULTS = 10000

# Safe for slower/free API limits
REQUEST_DELAY = 1.05


# ============================================================
# SYSTEMATIC REVIEW SEARCH STRATEGY
# ============================================================

SEARCHES = {

    # ========================================================
    # MAIN SYSTEMATIC REVIEW SEARCH
    # ========================================================

    "wos_systematic_review_main": (

        'TS=('

        # ----------------------------------------------------
        # Concept 1: Older adults
        # ----------------------------------------------------

        '('
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

        '('

        '"unmet care need*" '
        'OR "unmet assistance need*" '
        'OR "unmet support need*" '

        'OR '

        '('
        '"unmet need*" NEAR/8 '
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
    ),


    # ========================================================
    # SUPPLEMENTARY SEARCH
    # ========================================================

    "wos_unmet_care_supplement": (

        'TS=('

        '('
        '"older adult*" '
        'OR "older person*" '
        'OR "older people" '
        'OR elderly '
        'OR ageing '
        'OR aging '
        'OR geriatric*'
        ') '

        'AND '

        '('
        '"unmet care need*" '
        'OR "unmet assistance need*" '
        'OR "unmet support need*" '
        'OR "unmet need* for assistance" '
        'OR "unmet need* for care"'
        ')'

        ')'
    ),
}


# ============================================================
# CSV OUTPUT FIELDS
# ============================================================

FIELDS = [
    "uid",
    "title",
    "authors",
    "source",
    "year",
    "doi",
    "times_cited",
    "author_keywords",
    "document_type",
    "wos_url",
    "search_source",
]

 
# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_times_cited(record):
    """
    Extract Web of Science citation count.
    """

    citations = record.get("citations", []) or []

    for citation in citations:
        if citation.get("db") == "WOS":
            return citation.get("count", "")

    if citations:
        return citations[0].get("count", "")

    return ""


def parse_record(record, search_name):
    """
    Convert one Web of Science record into a flat CSV row.
    """

    source = record.get("source", {}) or {}
    names = record.get("names", {}) or {}
    identifiers = record.get("identifiers", {}) or {}
    keywords = record.get("keywords", {}) or {}
    links = record.get("links", {}) or {}

    # --------------------------------------------------------
    # Authors
    # --------------------------------------------------------

    authors_list = []

    for author in names.get("authors", []) or []:
        name = author.get("displayName", "")

        if name:
            authors_list.append(name)

    authors = "; ".join(authors_list)

    # --------------------------------------------------------
    # Author keywords
    # --------------------------------------------------------

    author_keywords = "; ".join(
        keywords.get("authorKeywords", []) or []
    )

    # --------------------------------------------------------
    # Document type
    # --------------------------------------------------------

    document_type = "; ".join(
        record.get("types", []) or []
    )

    return {
        "uid": record.get("uid", ""),
        "title": record.get("title", ""),
        "authors": authors,
        "source": source.get("sourceTitle", ""),
        "year": source.get("publishYear", ""),
        "doi": identifiers.get("doi", ""),
        "times_cited": get_times_cited(record),
        "author_keywords": author_keywords,
        "document_type": document_type,
        "wos_url": links.get("record", ""),
        "search_source": search_name,
    }


# ============================================================
# RUN SEARCH
# ============================================================

def run_search(name, query):

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    rows = []
    page = 1

    headers = {
        "X-ApiKey": API_KEY,
        "Accept": "application/json",
    }

    while True:

        params = {
            "db": "WOS",
            "q": query,
            "limit": LIMIT,
            "page": page,
        }

        try:
            response = requests.get(
                BASE_URL,
                params=params,
                headers=headers,
                timeout=60,
            )

        except requests.RequestException as error:
            print(f"Request failed: {error}")
            break

        # ----------------------------------------------------
        # Rate limiting
        # ----------------------------------------------------

        if response.status_code == 429:

            retry_after = int(
                response.headers.get("Retry-After", 5)
            )

            print(
                f"Rate limited. Waiting "
                f"{retry_after} seconds..."
            )

            time.sleep(retry_after)
            continue

        # ----------------------------------------------------
        # Other API errors
        # ----------------------------------------------------

        if response.status_code != 200:

            print(
                f"Error {response.status_code}: "
                f"{response.text[:500]}"
            )

            break

        # ----------------------------------------------------
        # Parse response
        # ----------------------------------------------------

        data = response.json()

        metadata = data.get("metadata", {})
        hits = data.get("hits", [])

        total = int(
            metadata.get("total", 0)
        )

        # ----------------------------------------------------
        # First page
        # ----------------------------------------------------

        if page == 1:

            print(
                f"Total Web of Science results: {total}"
            )

            if total > MAX_RESULTS:

                print(
                    f"WARNING: Search returned more than "
                    f"{MAX_RESULTS} results."
                )

                print(
                    f"Only the first {MAX_RESULTS} "
                    f"records will be downloaded."
                )

        # ----------------------------------------------------
        # Stop if nothing returned
        # ----------------------------------------------------

        if not hits:
            break

        # ----------------------------------------------------
        # Parse records
        # ----------------------------------------------------

        for record in hits:

            rows.append(
                parse_record(
                    record,
                    name
                )
            )

            if len(rows) >= MAX_RESULTS:
                break

        print(
            f"Downloaded: "
            f"{len(rows)} / "
            f"{min(total, MAX_RESULTS)}"
        )

        # ----------------------------------------------------
        # Stop conditions
        # ----------------------------------------------------

        if len(rows) >= MAX_RESULTS:
            break

        if len(rows) >= total:
            break

        if len(hits) < LIMIT:
            break

        # ----------------------------------------------------
        # Next page
        # ----------------------------------------------------

        page += 1

        time.sleep(
            REQUEST_DELAY
        )

    # ========================================================
    # WRITE CSV
    # ========================================================

    output_path = f"{name}.csv"

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS,
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
        "\nWEB OF SCIENCE SYSTEMATIC REVIEW SEARCH\n"
    )

    print(
        "Review title:\n"
        "Factors Associated with Domain-Specific "
        "Unmet Care Needs Among Community-Dwelling "
        "Older Adults: A Systematic Review\n"
    )

    print(
        "Search structure:\n"
        "Older adults\n"
        "AND\n"
        "Unmet care / assistance needs\n"
        "AND\n"
        "Care / assistance domains\n"
    )

    for search_name, search_query in SEARCHES.items():

        run_search(
            search_name,
            search_query
        )

    print(
        "\nDone."
    )

    print(
        "\nNext steps:"
        "\n1. Combine Web of Science searches"
        "\n2. Combine with Scopus results"
        "\n3. Remove duplicates"
        "\n4. Title/abstract screening"
        "\n5. Full-text screening"
        "\n6. Record exclusion reasons"
        "\n7. Create PRISMA flow diagram"
    )