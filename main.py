import os
import requests
import pdfplumber
import re
from bs4 import BeautifulSoup
from tqdm import tqdm

# URL to scrape
url = "https://www.woah.org/en/disease/avian-influenza/"

# Directory for PDFs
directory = "reports"

# Directory for MD files
markdown_directory = "md"

def should_combine(line1, line2):
    return not re.search(r'[.?!;:\-–—]$', line1.strip())

def clean_extracted_text(text):
    lines = text.split('\n')
    cleaned_lines = []

    for i, line in enumerate(lines):
        if i > 0 and should_combine(lines[i - 1], line):
            cleaned_lines[-1] += ' ' + line.strip()
        else:
            cleaned_lines.append(line.strip())

    return '\n\n'.join(cleaned_lines)

def pdf_to_markdown(pdf_path, markdown_path):
    with pdfplumber.open(pdf_path) as pdf:
        extracted_text = ""
        for page in tqdm(pdf.pages, desc="Extracting text from pages"):
            extracted_text += page.extract_text()

        cleaned_text = clean_extracted_text(extracted_text)

        with open(markdown_path, 'w', encoding='utf-8') as markdown_file:
            markdown_file.write(cleaned_text)

response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Find "Global Situation" span
global_situation = soup.find('span', {'class': 'wp-block-getwid-tabs__title'}, string='Global Situation')

# Find "Situation Reports" section
situation_reports_section = global_situation.find_next('div', {'class': 'wp-block-getwid-tabs__tab-content'})

# Create directories if they don't exist
os.makedirs(directory, exist_ok=True)
os.makedirs(markdown_directory, exist_ok=True)

for link in situation_reports_section.find_all('a', {'class': 'cards__file-link'}):
    pdf_url = link.get('href')

    # The name of the PDF will be the same as in the URL
    pdf_name = pdf_url.split('/')[-1]

    # Check if PDF already exists in the directory
    if not os.path.isfile(os.path.join(directory, pdf_name)):
        # Download the PDF
        pdf_response = requests.get(pdf_url)

        # Save the PDF
        pdf_path = os.path.join(directory, pdf_name)
        with open(pdf_path, 'wb') as f:
            f.write(pdf_response.content)

        print(f"Downloaded {pdf_name}")

        # Convert the PDF to Markdown
        markdown_name = pdf_name.replace('.pdf', '.md')
        markdown_path = os.path.join(markdown_directory, markdown_name)
        pdf_to_markdown(pdf_path, markdown_path)
    else:
        print(f"{pdf_name} already exists in the directory")
