import requests
import pandas as pd
import argparse
import os

def parse_arg():
    parser = argparse.ArgumentParser(description="Get scholar data for keywords and journals from .txt files.")
    parser.add_argument("-k", "--keyword_filepath", help="Path to the .txt file containing keywords (one per line).")
    parser.add_argument("-j", "--journal_filepath", default=None, help="Path to the .txt file containing journals (one per line).")
    parser.add_argument("-a", "--api_key", help="API key for accessing the SERP API.")
    parser.add_argument("-y", "--year", default="1800:2023", help="Year range for articles in format year_lo:year_hi.")
    parser.add_argument("-c", "--cites", default="", help="Comma-separated list of citation IDs.")
    parser.add_argument("-t", "--test", default=0, type=int, help="Run in test mode to limit to two pages.")
    return parser.parse_args()


def load_from_file(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"The file {filepath} does not exist.")
    
    with open(filepath, 'r') as file:
        items = [line.strip() for line in file.readlines()]
    return items


def get_scholar_data_for_keyword(keyword, api_key, year_lo, year_hi, cites=None, test_mode=False, yes_to_all=False):
    url = "https://serpapi.com/search"
    all_results = []
    start = 0
    page_count = 0  # Counter to keep track of the number of pages fetched
    
    while True:
        params = {
            "q": keyword,
            "engine": "google_scholar",
            "api_key": api_key,
            "start": start,
            "num": 20,  # Number of results per page
            "as_ylo": year_lo,
            "as_yhi": year_hi
        }
        
        if cites:
            params["cites"] = cites
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('organic_results', [])
        
        if not results:
            break
        
        if not test_mode and page_count == 0 and not yes_to_all:
            total_results = data.get('search_information', {}).get('total_results', 0)
            print(f"\nTotal results found: {total_results}")
            user_input = input("Do you want to continue? (Yes/No/Yes to All): ")
            if user_input.lower() == 'yes to all':
                yes_to_all = True
            elif user_input.lower() != 'yes':
                break
        
        for result in results:
            entry = {
                "Keyword": keyword,
                "Title": result.get('title'),
                "Result ID": result.get('result_id'),
                "Link": result.get('link'),
                "Snippet": result.get('snippet'),
                "Authors": result.get('publication_info', {}).get('summary'),
                "Total Citations": result.get('inline_links', {}).get('cited_by', {}).get('total', "NA"),
                "Cited By Link": result.get('inline_links', {}).get('cited_by', {}).get('link'),
                "Cites ID": result.get('inline_links', {}).get('cited_by', {}).get('cites_id'),
                "Related Pages Link": result.get('inline_links', {}).get('related_pages_link'),
                "Versions Total": result.get('inline_links', {}).get('versions', {}).get('total', "NA"),
                "Versions Link": result.get('inline_links', {}).get('versions', {}).get('link'),
                "Cluster ID": result.get('inline_links', {}).get('versions', {}).get('cluster_id'),
                "Cached Page Link": result.get('inline_links', {}).get('cached_page_link'),
                "SerpAPI Cite Link": result.get('inline_links', {}).get('serpapi_cite_link'),
                "SerpAPI Scholar Link (Cited By)": result.get('inline_links', {}).get('cited_by', {}).get('serpapi_scholar_link'),
                "SerpAPI Related Pages Link": result.get('inline_links', {}).get('serpapi_related_pages_link'),
                "SerpAPI Scholar Link (Versions)": result.get('inline_links', {}).get('versions', {}).get('serpapi_scholar_link')
            }
            all_results.append(entry)
        
        start += 20  # Increment by the number of results per page
        page_count += 1  # Increment the page counter
        
        if test_mode and page_count >= 2:  # Limit to 2 pages in test mode
            break

    return all_results, yes_to_all


def clean_df(d):
    # Add publisher column
    publishers = []

    for x in d['Keyword']:
        publishers.append(x.split('source:')[1].replace("\"", ""))

    d['Publisher'] = publishers

    # Remove publisher info
    d['Keyword'] = d['Keyword'].apply(lambda x: x.split('source:')[0])

    # Clean author string
    d['Authors'] = d['Authors'].apply(lambda x: x.split(' -')[0])

    df.fillna("NA", inplace=True)


def main():
    args = parse_arg()
    keywords = load_from_file(args.keyword_filepath)
    journals = load_from_file(args.journal_filepath) if args.journal_filepath else [None]
    
    year_range = args.year.split(":")
    year_lo = year_range[0] if year_range[0] else "1800"
    year_hi = year_range[1] if len(year_range) > 1 and year_range[1] else "2023"
    
    cites_list = args.cites.split(",") if args.cites else []
    
    test_mode = bool(int(args.test))
    
    total_keywords = len(keywords)
    keywords_with_results = 0
    keywords_without_results = 0
    total_articles = 0
    
    all_data = []
    ye_to_all = False
    
    for keyword in keywords:
        print(f"Searching for {keyword}...")
        total_results_for_keyword = 0
        
        for journal in journals:
            query = f"{keyword} source:\"{journal}\"" if journal else keyword
            print(f"\nLooking in journal {journal}", end="")
            
            for cites in cites_list:
                results, yes_to_all = get_scholar_data_for_keyword(query, args.api_key, year_lo, year_hi, cites, test_mode, yes_to_all)
                total_results_for_keyword += len(results)
                all_data.extend(results)
            
            if not cites_list:
                results, yes_to_all = get_scholar_data_for_keyword(query, args.api_key, year_lo, year_hi, test_mode=test_mode, yes_to_all=yes_to_all)
                total_results_for_keyword += len(results)
                all_data.extend(results)
        
        if total_results_for_keyword > 0:
            print(f"\nFound in total {total_results_for_keyword} results for {keyword} ✅")
            keywords_with_results += 1
            total_articles += total_results_for_keyword
        else:
            print(f" No results found for {keyword} ❌")
            keywords_without_results += 1
    
    df = pd.DataFrame(all_data)

    # Clean and export df
    clean_df(df)    
    df.to_csv('serp_articles_data.csv', index=False)
    
    print("\n--- Summary ---")
    print(f"Number of keywords searched: {total_keywords}")
    print(f"Number of keywords with no result: {keywords_without_results}")
    print(f"Number of keywords with result: {keywords_with_results}")
    print(f"Number of articles found: {total_articles}")

if __name__ == "__main__":
    main()

df = pd.read_csv('/Users/viniciusalvarez/serp_articles_data.csv')
