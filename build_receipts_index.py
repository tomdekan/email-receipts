import os
import sys
import csv
from openai import OpenAI
import re
import json
from pathlib import Path
from pdfminer.high_level import extract_text
from dotenv import load_dotenv


load_dotenv()


client = OpenAI()
if not client.api_key:
    print("Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    sys.exit(1)


def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using pdfminer.six.
    """
    try:
        text = extract_text(pdf_path)
        return text
    except Exception as e:
        print(f"Failed to extract text from {pdf_path.name}: {e}")
        return ""

def parse_receipt_with_llm(text):
    """
    Uses OpenAI's GPT to parse the receipt text and extract total amount and descriptive details.
    """
    prompt = (
        "You are an assistant that extracts specific information from receipt text.\n\n"
        "Extract the following details from the receipt text below:\n"
        "1. Total Amount: The final total amount paid.\n"
        "2. Currency: The currency of the receipt.\n"
        "3. Descriptive Details: Include merchant name and the purpose of the transaction.\n"
        "4. Transaction Date: The date of the receipt.\n\n"
        "Provide the output in the following JSON format:\n"
        "{\n"
        '  "total_amount": "amount (in currency. Note the different use of commas and decimals in european countries, e.g., 1,00 in Germany is 1.00 in the UK. Convert to the UK format)",\n'
        '  "currency": "currency 3 letter code",\n'
        '  "transaction_date": "date",\n'
        '  "descriptive_details": "details"\n'
        "}\n\n"
        "If any field is not found, set its value to null or 'N/A'.\n\n"
        "Receipt Text:\n"
        f"{text}\n"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You extract receipt information."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.2,
        )
        reply = response.choices[0].message.content.strip()
        
        json_match = re.search(r'\{.*\}', reply, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)
            total_amount = data.get("total_amount", "N/A")
            currency = data.get("currency", "N/A")
            descriptive_details = data.get("descriptive_details", "N/A")
            transaction_date = data.get("transaction_date", "N/A")
        else:
            total_amount = "N/A"
            currency = "N/A"
            descriptive_details = "N/A"
            transaction_date = "N/A"
        # Clean total_amount to ensure it's a float
        if isinstance(total_amount, str):
            total_amount_clean = ''.join(filter(lambda x: x.isdigit() or x == '.', total_amount))
            try:
                total_amount = float(total_amount_clean)
            except:
                total_amount = "N/A"
        
        return total_amount, currency, descriptive_details, transaction_date
    except Exception as e:
        print(f"LLM parsing failed: {e}")
        return "N/A", "N/A", "N/A", "N/A"

def build_receipts_index(pdf_folder, output_csv):
    """
    Processes all PDFs in the specified folder and builds an index CSV file.
    """
    pdf_dir = Path(pdf_folder)
    if not pdf_dir.exists() or not pdf_dir.is_dir():
        print(f"Error: The directory '{pdf_folder}' does not exist or is not a directory.")
        sys.exit(1)
    
    pdf_files = list(pdf_dir.glob('*.pdf'))
    if not pdf_files:
        print(f"No PDF files found in '{pdf_folder}'.")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDF files in '{pdf_folder}'. Processing...\n")
    
    # Prepare CSV
    with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['File Name', 'Total Amount ($)', 'Currency', 'Transaction Date', 'Descriptive Details']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for idx, pdf_file in enumerate(pdf_files, 1):
            print(f"Processing ({idx}/{len(pdf_files)}): {pdf_file.name}")
            text = extract_text_from_pdf(pdf_file)
            if not text:
                writer.writerow({
                    'File Name': pdf_file.name,
                    'Total Amount ($)': "N/A",
                    'Currency': "N/A",
                    'Transaction Date': "N/A",
                    'Descriptive Details': "N/A"
                })
                continue
            
            total_amount, currency, details, transaction_date = parse_receipt_with_llm(text)
            
            writer.writerow({
                'File Name': pdf_file.name,
                'Total Amount ($)': total_amount,
                'Currency': currency,
                'Transaction Date': transaction_date,
                'Descriptive Details': details
            })
    
    print(f"\nIndex file '{output_csv}' has been created successfully.")

def main():
    """
    Main function to execute the script.
    Usage: python build_receipts_index.py path/to/pdf_receipts output_index.csv
    """
    if len(sys.argv) != 3:
        print("Usage: python build_receipts_index.py path/to/pdf_receipts output_index.csv")
        sys.exit(1)
    
    pdf_receipts_dir = sys.argv[1]
    output_csv = sys.argv[2]
    
    build_receipts_index(pdf_receipts_dir, output_csv)

if __name__ == "__main__":
    main()
