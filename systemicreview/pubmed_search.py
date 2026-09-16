"""
PubMed Search -> CSV

Systematic Review:
Factors Associated with Domain-Specific Unmet Care Needs
Among Community-Dwelling Older Adults: A Systematic Review

No NCBI API key is required for this script.

Setup:
    pip install requests

Usage:
    python pubmed_search.py

The script uses NCBI PubMed E-utilities:
    ESearch -> identify records
    EFetch  -> retrieve article metadata
"""

import csv
import time
import requests
import xml.etree.ElementTree as ET


# ============================================================
# CONFIGURATION
# ============================================================

ESEARCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
)

EFETCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
)

DATABASE = "pubmed"

# Number of PubMed records retrieved per request
BATCH_SIZE = 200

# Without an API key, keep requests below roughly 3/second
REQUEST_DELAY = 0.4

# Identify your script to NCBI
TOOL_NAME = "systematic_review_search"

# Put your own email here
EMAIL = "kaungkhantkyaw@student.uts.edu.au"


# ============================================================
# DATE RANGE
# ============================================================

"""
This matches the >= 2010 approach we discussed.

If you decide not to apply a publication-year restriction,
remove DATE_FILTER from the queries below.
"""

DATE_FILTER = (
    '("2010/01/01"[Date - Publication] : '
    '"2026/12/31"[Date - Publication])'
)


SEARCHES = {

    # ========================================================
    # MAIN SYSTEMATIC REVIEW SEARCH
    # ========================================================

    "pubmed_systematic_review_main": (

        # ----------------------------------------------------
        # Concept 1: Older adults
        # ----------------------------------------------------

        '('
        '"Aged"[Mesh] '
        'OR "Aged, 80 and over"[Mesh] '
        'OR "older adult*"[Title/Abstract] '
        'OR "older person*"[Title/Abstract] '
        'OR "older people"[Title/Abstract] '
        'OR elderly[Title/Abstract] '
        'OR ageing[Title/Abstract] '
        'OR aging[Title/Abstract] '
        'OR geriatric*[Title/Abstract]'
        ') '

        'AND '

        # ----------------------------------------------------
        # Concept 2: Domain-specific unmet care needs
        # ----------------------------------------------------

        '('

        # Explicit phrases
        '"unmet care need*"[Title/Abstract] '
        'OR "unmet assistance need*"[Title/Abstract] '
        'OR "unmet support need*"[Title/Abstract] '

        # ADL / IADL
        'OR "unmet need activities of daily living"[Title/Abstract:~8] '
        'OR "unmet needs activities of daily living"[Title/Abstract:~8] '
        'OR "unmet need ADL"[Title/Abstract:~8] '
        'OR "unmet needs ADL"[Title/Abstract:~8] '
        'OR "unmet need IADL"[Title/Abstract:~8] '
        'OR "unmet needs IADL"[Title/Abstract:~8] '

        # Personal care
        'OR "unmet need personal care"[Title/Abstract:~8] '
        'OR "unmet needs personal care"[Title/Abstract:~8] '
        'OR "unmet need self care"[Title/Abstract:~8] '
        'OR "unmet needs self care"[Title/Abstract:~8] '

        # Mobility
        'OR "unmet need mobility"[Title/Abstract:~8] '
        'OR "unmet needs mobility"[Title/Abstract:~8] '

        # Household / domestic activities
        'OR "unmet need household"[Title/Abstract:~8] '
        'OR "unmet needs household"[Title/Abstract:~8] '
        'OR "unmet need housework"[Title/Abstract:~8] '
        'OR "unmet needs housework"[Title/Abstract:~8] '

        # Transport
        'OR "unmet need transport"[Title/Abstract:~8] '
        'OR "unmet needs transport"[Title/Abstract:~8] '

        # Meals
        'OR "unmet need meal preparation"[Title/Abstract:~8] '
        'OR "unmet needs meal preparation"[Title/Abstract:~8] '

        # Property maintenance
        'OR "unmet need property maintenance"[Title/Abstract:~8] '
        'OR "unmet needs property maintenance"[Title/Abstract:~8]'

        ') '

        'AND '

        + DATE_FILTER
    ),


    # ========================================================
    # SUPPLEMENTARY SEARCH
    # ========================================================

    "pubmed_unmet_care_supplement": (

        '('
        '"Aged"[Mesh] '
        'OR "Aged, 80 and over"[Mesh] '
        'OR "older adult*"[Title/Abstract] '
        'OR "older person*"[Title/Abstract] '
        'OR "older people"[Title/Abstract] '
        'OR elderly[Title/Abstract] '
        'OR ageing[Title/Abstract] '
        'OR aging[Title/Abstract] '
        'OR geriatric*[Title/Abstract]'
        ') '

        'AND '

        '('
        '"unmet care need*"[Title/Abstract] '
        'OR "unmet assistance need*"[Title/Abstract] '
        'OR "unmet support need*"[Title/Abstract] '
        'OR "unmet need* for assistance"[Title/Abstract] '
        'OR "unmet need* for care"[Title/Abstract]'
        ') '

        'AND '

        + DATE_FILTER
    ),
}



# ============================================================
# OUTPUT FIELDS
# ============================================================

FIELDS = [
    "pmid",
    "title",
    "authors",
    "journal",
    "year",
    "doi",
    "abstract",
    "keywords",
    "publication_types",
    "pubmed_url",
    "search_source",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_text(element):
    """
    Extract all text from an XML element,
    including nested formatting tags.
    """

    if element is None:
        return ""

    return "".join(
        element.itertext()
    ).strip()


def get_publication_year(article):

    journal_issue = article.find(
        ".//JournalIssue/PubDate"
    )

    if journal_issue is not None:

        year = journal_issue.findtext("Year")

        if year:
            return year

        medline_date = journal_issue.findtext(
            "MedlineDate"
        )

        if medline_date:
            return medline_date[:4]

    article_date = article.find(
        ".//ArticleDate"
    )

    if article_date is not None:

        year = article_date.findtext("Year")

        if year:
            return year

    return ""


def parse_article(pubmed_article, search_name):
    """
    Convert a PubMed XML article into a flat CSV row.
    """

    medline = pubmed_article.find(
        "MedlineCitation"
    )

    article = medline.find(
        "Article"
    )

    # --------------------------------------------------------
    # PMID
    # --------------------------------------------------------

    pmid = medline.findtext(
        "PMID",
        default=""
    )


    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    title = get_text(
        article.find("ArticleTitle")
    )


    # --------------------------------------------------------
    # Authors
    # --------------------------------------------------------

    authors_list = []

    for author in article.findall(
        ".//AuthorList/Author"
    ):

        collective_name = author.findtext(
            "CollectiveName"
        )

        if collective_name:
            authors_list.append(
                collective_name
            )
            continue

        last_name = author.findtext(
            "LastName",
            default=""
        )

        fore_name = author.findtext(
            "ForeName",
            default=""
        )

        full_name = (
            f"{last_name} {fore_name}"
        ).strip()

        if full_name:
            authors_list.append(
                full_name
            )

    authors = "; ".join(
        authors_list
    )


    # --------------------------------------------------------
    # Journal
    # --------------------------------------------------------

    journal = article.findtext(
        ".//Journal/Title",
        default=""
    )


    # --------------------------------------------------------
    # Publication year
    # --------------------------------------------------------

    year = get_publication_year(
        article
    )


    # --------------------------------------------------------
    # DOI
    # --------------------------------------------------------

    doi = ""

    for article_id in pubmed_article.findall(
        ".//PubmedData/ArticleIdList/ArticleId"
    ):

        if article_id.attrib.get(
            "IdType"
        ) == "doi":

            doi = (
                article_id.text or ""
            ).strip()

            break


    # --------------------------------------------------------
    # Abstract
    # --------------------------------------------------------

    abstract_parts = []

    for abstract_text in article.findall(
        ".//Abstract/AbstractText"
    ):

        text = get_text(
            abstract_text
        )

        label = abstract_text.attrib.get(
            "Label",
            ""
        )

        if label and text:
            abstract_parts.append(
                f"{label}: {text}"
            )

        elif text:
            abstract_parts.append(
                text
            )

    abstract = " ".join(
        abstract_parts
    )


    # --------------------------------------------------------
    # Keywords
    # --------------------------------------------------------

    keyword_list = []

    for keyword in medline.findall(
        ".//KeywordList/Keyword"
    ):

        text = get_text(
            keyword
        )

        if text:
            keyword_list.append(
                text
            )

    keywords = "; ".join(
        keyword_list
    )


    # --------------------------------------------------------
    # Publication types
    # --------------------------------------------------------

    publication_types_list = []

    for publication_type in article.findall(
        ".//PublicationTypeList/PublicationType"
    ):

        text = get_text(
            publication_type
        )

        if text:
            publication_types_list.append(
                text
            )

    publication_types = "; ".join(
        publication_types_list
    )


    # --------------------------------------------------------
    # PubMed URL
    # --------------------------------------------------------

    pubmed_url = ""

    if pmid:
        pubmed_url = (
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        )


    return {

        "pmid": pmid,

        "title": title,

        "authors": authors,

        "journal": journal,

        "year": year,

        "doi": doi,

        "abstract": abstract,

        "keywords": keywords,

        "publication_types":
            publication_types,

        "pubmed_url":
            pubmed_url,

        "search_source":
            search_name,
    }


# ============================================================
# ESEARCH
# ============================================================

def start_search(query):

    params = {

        "db": DATABASE,

        "term": query,

        "retmode": "json",

        "retmax": 0,

        "usehistory": "y",

        "tool": TOOL_NAME,

        "email": EMAIL,
    }

    response = requests.get(
        ESEARCH_URL,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    results = data.get(
        "esearchresult",
        {}
    )

    count = int(
        results.get(
            "count",
            0
        )
    )

    webenv = results.get(
        "webenv"
    )

    query_key = results.get(
        "querykey"
    )

    return (
        count,
        webenv,
        query_key,
    )


# ============================================================
# EFETCH
# ============================================================

def fetch_batch(
    webenv,
    query_key,
    start,
    batch_size
):

    params = {

        "db": DATABASE,

        "query_key": query_key,

        "WebEnv": webenv,

        "retstart": start,

        "retmax": batch_size,

        "retmode": "xml",

        "tool": TOOL_NAME,

        "email": EMAIL,
    }

    response = requests.get(
        EFETCH_URL,
        params=params,
        timeout=120,
    )

    response.raise_for_status()

    return ET.fromstring(
        response.content
    )


# ============================================================
# RUN ONE SEARCH
# ============================================================

def run_search(
    search_name,
    search_query
):

    print(
        "\n" + "=" * 70
    )

    print(
        search_name
    )

    print(
        "=" * 70
    )


    # --------------------------------------------------------
    # Run ESearch
    # --------------------------------------------------------

    try:

        (
            total,
            webenv,
            query_key,
        ) = start_search(
            search_query
        )

    except requests.RequestException as error:

        print(
            f"Search failed: {error}"
        )

        return


    print(
        f"Total PubMed results: {total}"
    )


    if total == 0:

        print(
            "No records found."
        )

        return


    rows = []


    # --------------------------------------------------------
    # Retrieve results in batches
    # --------------------------------------------------------

    for start in range(
        0,
        total,
        BATCH_SIZE
    ):

        try:

            root = fetch_batch(

                webenv,

                query_key,

                start,

                BATCH_SIZE
            )

        except requests.RequestException as error:

            print(
                f"Fetch failed at "
                f"record {start}: {error}"
            )

            break


        articles = root.findall(
            ".//PubmedArticle"
        )


        for article in articles:

            rows.append(
                parse_article(
                    article,
                    search_name
                )
            )


        print(
            f"Downloaded: "
            f"{len(rows)} / {total}"
        )


        time.sleep(
            REQUEST_DELAY
        )


    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    output_path = (
        f"{search_name}.csv"
    )


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

        writer.writerows(
            rows
        )


    print(
        f"\nSaved {len(rows)} records "
        f"-> {output_path}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "\nPUBMED SYSTEMATIC REVIEW SEARCH\n"
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


    for (
        search_name,
        search_query
    ) in SEARCHES.items():

        run_search(
            search_name,
            search_query
        )


    print(
        "\nDone."
    )

    print(
        "\nExpected output:"
        "\n1. pubmed_systematic_review_main.csv"
        "\n2. pubmed_domain_specific_supplement.csv"
    )

    print(
        "\nAfter PubMed:"
        "\n1. Combine Scopus files"
        "\n2. Combine Web of Science files"
        "\n3. Combine PubMed files"
        "\n4. Merge all databases"
        "\n5. Remove duplicates"
        "\n6. Begin title/abstract screening"
    )