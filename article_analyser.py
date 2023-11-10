import os
import argparse
import re
import nltk.data
import pandas as pd
from glob import glob
from PyPDF2 import PdfReader
from fuzzywuzzy import fuzz
from fitz import open as fitz_open

class PDFHighlighter:
    # Initial setup
    def __init__(self, pdf_folder, data_path, keywords_path):
        self.tokenizer = nltk.data.load('tokenizers/punkt/english.pickle') # Tokenizer for context
        self.keywords = self.load_keywords(keywords_path) # Load keywords
        self.filenames = glob(os.path.join(pdf_folder, "*.pdf")) # Get filenames
        df = pd.read_csv(data_path) # Load database
        self.df_ref = df[pd.notna(df['DOI_link'])]
        self.df_ref['DOIs'] = df['DOI_link'].astype(str).apply(lambda x: x.replace('/', '_'))
        #self.df_ref['DOI_short'] = self.df_ref['DOI_link'].apply(lambda x: x[8:])

    # Loads keywords given the txt file
    def load_keywords(self, path):
        with open(path, 'r') as file:
            return [line.strip() for line in file]

    # Creates regex pattern given the symbol in the txt file
    def create_pattern(self, word):
        # Citation handling
        if word[-2:] == '*C':
            authors, year = re.match(r'^(.*?)(\(\d{4}\)|\d{4})$', \
            word.split(' / ')[0]).groups()

            authors = [re.escape(author.strip()) for author in authors.split(',')]

            title = word[:-3].split(' / ')[1].replace(" ", "\s*")

            pattern = re.compile(fr'\(?\b(?:{"|".join(authors)})(?:, \
                *\b(?:{"|".join(authors)}))*\s*[,-]?\s*{year}\)?|{title}',\
                re.IGNORECASE | re.MULTILINE)
          
        # Upper case handling
        elif word[-2:] == '*U':
            pattern = re.compile(r'\s*'.join(word[0:-3]) \
                + r'(s|es|ies)?\b', re.MULTILINE)
        
        # Regular keywords, handling only plural
        else:
            pattern = re.compile(r'\s*'.join(word) + r'(s|es|ies)?\b',\
                re.IGNORECASE | re.MULTILINE)
            
        return pattern

    # Highlights keywords and outputs recorded info about instances
    def highlighter(self, doc):

        # Lists to record final data
        DOIs = []
        instance_pages = []
        key_values = []
        context = []

        # Open the PDF file and highlight word
        with open(doc, 'rb') as pdf_file:
            # Create a PDF reader object
            reader = PdfReader(pdf_file)

            # Create a PyMuPDF Document object
            pdf_document = fitz_open(doc)

            # Loops over pages to search for words
            for page_num in range(len(reader.pages)):

                page = reader.pages[page_num]

                # Get the text of the current page of the PDF file
                page_text = page.extract_text()

                for word in self.keywords:

                    # Current lists to record data
                    curr_DOIs = []
                    curr_instance_pages = []
                    curr_key_values = []
                    curr_context = []

                    # Create pattern to be searched
                    pattern = self.create_pattern(word)
                    
                    matches = pattern.finditer(page_text)

                    def process_doc_name(doc):
                            # Check if 'doc' is a path and extract the file name
                            if '/' in doc or '\\' in doc:
                                file_name = os.path.basename(doc)
                                return file_name
                            else:
                                return doc

                    # Loop through all matches and add a highlight to each one
                    for match in matches:
                        # Add instance page to list
                        curr_instance_pages.append(page_num + 1)

                        # Add instance of DOI
                        curr_DOIs.append(process_doc_name(doc).replace(".pdf", ""))

                        # Add word to list
                        curr_key_values.append(word)

                        start_pos = match.start()
                        end_pos = match.end()
                        match_word = match.group()

                        # Add context (100 characters in diameter)
                        larger_context = page_text[start_pos-200:end_pos+200]
                        sentences = self.tokenizer.tokenize(larger_context)

                        # Use flag to control loop
                        sentence_added = False
                        for sentence in sentences:
                            if match_word in sentence and not sentence_added:
                                curr_context.append(sentence)
                                sentence_added = True
                                break

                        # Check for errors
                        if len(curr_DOIs) != len(curr_context):
                            curr_context.append('Context not accessible')

                        # Get the current page of the PDF file as a PyMuPDF Page object
                        pdf_page = pdf_document[page_num]

                        # Get the bounds of the match on the current page
                        word_rects = pdf_page.search_for(match_word)

                        # Create a PyMuPDF highlight object
                        pdf_page.add_highlight_annot(word_rects)

                    # Udpate outbound info
                    context = context + curr_context
                    DOIs = DOIs + curr_DOIs
                    instance_pages = instance_pages + curr_instance_pages
                    key_values = key_values + curr_key_values

            # Save the changes to the PDF file
            pdf_document.saveIncr()

        # If no instances found for a word, set default
        for word in self.keywords:
            if word not in key_values:
                # Page is NA
                instance_pages.append(0)

                # Add DOI
                DOIs.append(process_doc_name(doc).replace(".pdf", ""))

                # Add word
                key_values.append(word)       

                # Add context
                context.append("NA")  


        # Returns DOIs, instances, and words
        return [DOIs, instance_pages, key_values, context]
    
    # Formats record info given from highlighter function
    def format_record(self, pdf):
        record = self.highlighter(pdf)

        DOIs = record[0]
        pages = record[1]
        key_values = record[2]
        context = record[3]

        return pd.DataFrame({'DOIs': DOIs, 'key_values' : key_values,\
                'Pages' : pages, 'Context' : context})

    # Loops format_record on all the PDF files a outputs final dataframe
    def final_df(self):
        total_files = len(self.filenames)
        print(f"Scraping 1/{total_files}: {self.filenames[0].split('/')[-1]} ...", end=' ')
        df = self.format_record(self.filenames[0])
        print("done!")

        for id, pdf in enumerate(self.filenames[1:]):
            print(f"Scraping {id + 2}/{total_files}: {pdf.split('/')[-1]} ...", end=' ')
            d = self.format_record(pdf)
            print("done!")
            df = df.append(d, ignore_index=True)

        df.Context = df.Context.str.replace("\n", "")
        return self.add_metadata(df)


    # Adds additional information to the dataframe
    def add_metadata(self, df):
        # Create metadata columns
        df['title'] = df['DOIs'].map(self.df_ref.groupby('DOIs')['Title'].first())
        # df['DOIs'] = df['title'].map(self.df_ref.groupby('Title')['DOIs'].first())
        df['author'] = df['title'].map(self.df_ref.groupby('Title')['Authors'].first())
        # df['year_pub'] = df['title'].map(self.df_ref.groupby('Title')['year_pub'].first())
        # df['month_pub'] = df['title'].map(self.df_ref.groupby('Title')['month_pub'].first())

        return df

# Command call for directory and files
def parse_args():
    parser = argparse.ArgumentParser(description='PDF Highlighter')
    parser.add_argument('-k', '--keywords', type=str, default='./keywords.txt',
                        help='Path to keywords file')
    parser.add_argument('-a', '--articledb', type=str, default='./all_articles.dta',
                        help='Path to articles database')
    parser.add_argument('-f', '--pdf_folder', type=str, default='./all_pdfs',
                        help='Path to pdfs folder (default: current directory)')
    return parser.parse_args()

# Usage
def main():
    args = parse_args()

    pdf_highlighter = PDFHighlighter(args.pdf_folder, args.articledb, args.keywords)

    df = pdf_highlighter.final_df()
    df.to_csv('key_words_freq.csv', index=False)

if __name__ == "__main__":
    main()
