# Receipts to CSV

## Problem:
1. I needed to file taxes. I had many email receipts (around 330) in `.eml` format. I needed to convert them to `.pdf` format before sending them to my accountant as a link to a cloud folder.

2. Give that the PDF receipts follow a non-standard format, I wanted to extract the data from the receipts to a spreadsheet in a standard format. I would also send this standardised data to my accountant. This includes the currency of the receipt, the transaction date, the purpose of the transaction, and the total amount. This would allow me to check that my accountant had managed to include all the receipts.

So, that's what this repo does.

This repo contains scripts to:
### Convert .eml to .pdf
1. Convert .eml files to .pdf files -> `convert_eml_to_pdf.py`
You'll just need to state the path to your folder containing your .eml files. The script will convert each .eml file to a .pdf file in the same folder.

![Example of .eml to .pdf conversion](./example_converted_pdf.jpg) (I redacted personal details from the screenshot)

### Extract data from .pdf to .csv (plus enriched data)
2. Parse any .pdf files to extract receipt data using an LLM (currently GPT4o Mini) to a .csv file. You can then import this straight into an Excel spreadsheet or Google Sheet. -> `build_receipts_index.py`
You'll just need to state the path to your folder containing your .pdf files. The script will parse each .pdf file and save the data to a .csv file in the same folder, including the currency of the receipt, the transaction date, the purpose of the transaction, and the total amount.

Example csv output:
```csv
File Name,Total Amount ($),Currency,Transaction Date,Descriptive Details
Receipt-2566-5568.pdf,47.42,USD,2050-06-01,"Render - Servers, PostgresDB, Redis usage for May 2050"
Receipt-2952-5288.pdf,9.52,EUR,2050-03-03,Twitter International ULC - Twitter Blue subscription
email_receipt_2050-04-02_05-49_Your_receipt_from_Render_2916-0813.pdf,61.52,USD,2050-04-02,Render - Payment for services
Invoice-F4276E5C-0009.pdf,9.52,EUR,2050-10-03,Twitter International ULC - X Premium subscription
...
```

## To run

To run the scripts:
1. Set up a Python environment 
2. Install the dependencies: `pip install -r requirements.txt`
3. Renamed the `.example.env` file to `.env` and paste your OpenAI API key as an environment variable `OPENAI_API_KEY`. 
4. Run one of the scripts from the command line: `python build_receipts_index.py`. Each script has its own usage, which is printed when you run the script. 
