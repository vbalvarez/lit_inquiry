# Introduction & Overview

In this document, we walk through an integrated pipeline that begins with extracting scholarly articles based on keywords from Google Scholar using the SERP API. With the DOIs of the articles, we download the articles' PDFs. Lastly, we scan these PDFs for specific keywords, highlight them, and record their instances.

The tools we use include the SERP API and various Python libraries for data manipulation, web scraping, and PDF processing.

The programs can also be used separately. Here's the breakdown of the function of each:
- `search.py`: takes in a set of keywords and journals (in .txt format for each) and outputs all articles on the SERP API search with these parameters
- `article_download.py`: takes in dataset of articles and DOIs (usually the output of `search.py`) and downloads them in a designated folder. For this version, this script only works with AEA articles.
- `article_analyser`: given a list of keywords and a folder of articles (usually the output of `article_download.py`), highlights the keywords in-place and returns a daframe with each instance of each word within the articles.

In order to use this repo, you first need to clone it with:

```bash
!git clone https://github.com/vbalvarez/lit_inquiry
```

Then, you'll have to change your directory, so you can run all the scripts more easily:

```bash
%cd lit_inquiry
```

# search.py

This script takes in a set of keywords and journals (in .txt format for each) and outputs all articles on the SERP API search with these parameters. Here's a detailed description of each parameter:

- -k: Path to the .txt file containing keywords (one per line). [Required]
- -a: API key for accessing the SERP API. [Required]
- -j: Path to the .txt file containing journals (one per line).
- -y: Year range for articles in format year_lo:year_hi.
- -c: Comma-separated list of citation IDs.
- -t: Test option, 1: yes, 0: no (default).

The output of this script will be a csv file `serp_articles_data.csv`.

The standard call for this script would be:

```bash
%run -i 'search.py' -k 'PATH_TO_KEYWORDS' -j 'PATH_TO_JOURNALS' -a '280d25d6d2bbc50f74ba7b2797beda29d9a6afaeb0d6ee1ac1b73b79411d8a21'
```
*Note:* Here we use the command %run -i so we can interact with the script outside the terminal and demonstrate it running. If you are calling this within the terminal, you only need the code below. And this goes for any bash code on this PDF.

```bash
!python3 search.py -k PATH_TO_KEYWORDS -j PATH_TO_JOURNALS -a 280d25d6d2bbc50f74ba7b2797beda29d9a6afaeb0d6ee1ac1b73b79411d8a21
```

Then, this is the schema for the output of the script:

| Column | Data Type | Example | Description |
| ------ | --------- | ------- | ----------- |
| Keyword | str | `"peer effects" "linear in means" ` | Keyword(s) of the article |
| Title | str | `From natural variation to optimal policy? The importance of endogenous peer group formation` | Title of the article |
| Result ID | str | `2s9lhCj7bhsJ` | Unique identifier for the search result |
| Link | str | `https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA10168` | URL to the article |
| Snippet | str | `… literature that uses peer effects estimates to … peer effects from high math ability cadets at West Point (the US Military Academy). For brevity, we do not show results for the linear in means …` | Snippet from the article |
| Authors | str | `SE Carrell, BI Sacerdote, JE West` | Author(s) of the article |
| Total Citations | float | `655.0` | Total number of citations |
| Cited By Link | str | `https://scholar.google.com/scholar?cites=1976793437900754906&as_sdt=2005&sciodt=0,5&hl=en&num=20` | Link to the "Cited By" page on Google Scholar |
| Cites ID | str | `1976793437900754906` | Google Scholar's unique identifier for citations |
| Related Pages Link | str | `https://scholar.google.com/scholar?q=related:2s9lhCj7bhsJ:scholar.google.com/&scioq=%22peer+effects%22+%22linear+in+means%22+source:%22Econometrica%22&hl=en&num=20&as_sdt=0,5&as_ylo=1800&as_yhi=2023` | Link to related articles on Google Scholar |
| Versions Total | float | `15.0` | Total number of versions of the article |
| Versions Link | str | `https://scholar.google.com/scholar?cluster=1976793437900754906&hl=en&num=20&as_sdt=0,5&as_ylo=1800&as_yhi=2023` | Link to different versions of the article on Google Scholar |
| Cluster ID | str | `1976793437900754906` | Cluster ID used by Google Scholar |
| Cached Page Link | str | `nan` | Link to the cached version of the page (if available) |
| SerpAPI Cite Link | str | `https://serpapi.com/search.json?engine=google_scholar_cite&hl=en&q=2s9lhCj7bhsJ` | Link to the SerpAPI citation page |
| SerpAPI Scholar Link (Cited By) | str | `https://serpapi.com/search.json?as_sdt=2005&cites=1976793437900754906&engine=google_scholar&hl=en&num=20` | Link to the SerpAPI "Cited By" page |
| SerpAPI Related Pages Link | str | `https://serpapi.com/search.json?as_sdt=0%2C5&as_yhi=2023&as_ylo=1800&engine=google_scholar&hl=en&num=20&q=related%3A2s9lhCj7bhsJ%3Ascholar.google.com%2F&start=0` | Link to SerpAPI's related pages |
| SerpAPI Scholar Link (Versions) | str | `https://serpapi.com/search.json?as_sdt=0%2C5&as_yhi=2023&as_ylo=1800&cluster=1976793437900754906&engine=google_scholar&hl=en&num=20` | Link to SerpAPI's versions page |
| Publisher | str | `Econometrica` | Publisher of the article |
| DOI_link | str | `abs/10.3982/ECTA10168` | Digital Object Identifier (DOI) link for the article |

---

# article_download.py

Next, this script takes in dataset of articles and DOIs (usually the output of `search.py`) and downloads them in a designated folder. For this version, this script only works with AEA articles.

Its parameters are:
- -a: The database with articles' names and DOIs. The format is assumed to be the same as the one on `search.py` output. [Required]
- -f: The folder path where the articles will be downloaded.

The output of the script is the folder with all the articles downloaded.

Then, to call it in the terminal, type:

```bash
!python3 article_download.py -a PATH_TO_DATABASE -f PATH_TO_FOLDER
```
---

# article_analyser

This script is given a list of keywords and a folder of articles (usually the output of article_download.py), and it highlights the keywords in-place and returns a daframe with each instance of each word within the articles.

Its parameters are:

- -k: Path to .txt file with keywords to be highlighted on each line. [Required]
- -a: Database of article information (usually the output of `search.py`). [Required]
- -f: Folder with all the pdf files that are to be scraped. This is usually the output of `article_download.py`. [Required]

To call it in the terminal, you'll type:

```bash
!python3 article_analyser.py -k PATH_TO_KEYWORDS -a PATH_TO_DATAFRAME -f PATH_TO_FOLDER
```

The following is the schema for this script's output:

Here is the data schema for the `key_words_freq.csv` DataFrame in a table format suitable for a Git README file:

| Column | Data Type | Example | Description |
| ------ | --------- | ------- | ----------- |
| DOIs | str | `10.1257_app.1.4.34` | DOI for the article |
| key_values | str | `LATE *U` | Word searched |
| Pages | int | `0` | Page of instance |
| Context | str | `Parent-Child Correlation in BehaviorA. Monotonicity of the s teady- state d istribution of...` | Context around the word |
| title | str | `Peer effects in the workplace: Evidence from random groupings in professional golf tournaments` | Title of the article |
| author | str | `J Guryan, K Kroft, MJ Notowidigdo` | Author(s) of the article |
