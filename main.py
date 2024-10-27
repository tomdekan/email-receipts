import os
import email
import sys
from fpdf import FPDF

from email import policy
from datetime import datetime
from pathlib import Path
import re
import html
import unicodedata

class EmailConverter:
    def __init__(self, input_dir, output_dir):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.index = []
        # Initialize the font here
        self.font_family = 'DejaVu'
        self.font_path = './fonts/DejaVuSans.ttf'

    def clean_filename(self, text):
        """Create safe filename from text."""
        if not text:
            return "no_subject"
        # Normalize Unicode characters
        text = unicodedata.normalize('NFKD', str(text))
        # Remove invalid chars and limit length
        clean = re.sub(r'[^\w\s-]', '', text)
        return clean.strip().replace(' ', '_')[:50]

    def format_date(self, date_str):
        """Format email date string."""
        try:
            if date_str:
                date = email.utils.parsedate_to_datetime(date_str)
                return date.strftime("%Y-%m-%d_%H-%M")
        except:
            pass
        return datetime.now().strftime("%Y-%m-%d_%H-%M")

    def sanitize_text(self, text):
        """Sanitize text for PDF output."""
        if text is None:
            return ""
        # Convert to string if not already
        text = str(text)
        # Decode HTML entities
        text = html.unescape(text)
        # Normalize Unicode characters
        text = unicodedata.normalize('NFKD', text)
        # Replace problematic characters
        text = text.replace('\u2019', "'")  # Smart quotes
        text = text.replace('\u2018', "'")
        text = text.replace('\u201c', '"')
        text = text.replace('\u201d', '"')
        text = text.replace('\u2013', '-')  # En dash
        text = text.replace('\u2014', '--')  # Em dash
        text = text.replace('\u20ac', 'EUR')  # Euro symbol
        return text

    def create_pdf(self):
        """Initialize a new PDF with Unicode support."""
        pdf = FPDF()
        pdf.add_font(self.font_family, '', self.font_path, uni=True)
        pdf.set_font(self.font_family, size=12)
        return pdf

    def create_index(self):
        """Create index PDF of all converted emails."""
        pdf = self.create_pdf()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font(self.font_family, size=16)
        
        pdf.cell(0, 10, 'Email Archive Index', ln=True, align='C')
        pdf.ln(10)

        # Sort by 
        self.index.sort(key=lambda x: x[2] or '')

        pdf.set_font(self.font_family, size=12)
        for idx, (filename, subject, date, sender) in enumerate(self.index, 1):
            pdf.cell(0, 10, f'{idx}. Date: {self.sanitize_text(date or "Unknown")}', ln=True)
            pdf.cell(0, 10, f'From: {self.sanitize_text(sender or "Unknown")}', ln=True)
            pdf.cell(0, 10, f'Subject: {self.sanitize_text(subject or "No Subject")}', ln=True)
            pdf.cell(0, 10, f'File: {filename}', ln=True)
            pdf.ln(5)
        pdf.output(str(self.output_dir / 'index.pdf'))

    def convert_email(self, eml_path):
        """Convert single EML file to PDF."""
        try:
            # Read email
            with open(eml_path, 'rb') as f:
                msg = email.message_from_bytes(f.read(), policy=policy.default)

            # Create filename
            date_str = self.format_date(msg['date'])
            subject = msg['subject'] or 'No Subject'
            filename = f"{date_str}_{self.clean_filename(subject)}.pdf"

            # Create PDF
            pdf = self.create_pdf()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            
            # Header
            pdf.set_font(self.font_family, size=14)
            pdf.cell(0, 10, 'Email Details', ln=True, align='C')
            pdf.ln(5)

            # Metadata
            pdf.set_font(self.font_family, size=12)
            metadata = [
                ('Subject', self.sanitize_text(msg['subject'])),
                ('From', self.sanitize_text(msg['from'])),
                ('To', self.sanitize_text(msg['to'])),
                ('Date', self.sanitize_text(msg['date'])),
            ]
            
            for label, value in metadata:
                if value:
                    pdf.cell(0, 10, f'{label}: {value}', ln=True)
            pdf.ln(10)

            # Body
            pdf.set_font(self.font_family, size=12)
            body_part = msg.get_body(preferencelist=('plain', 'html'))
            if body_part:
                content = body_part.get_content()
                # Simple HTML stripping if needed
                if body_part.get_content_type() == 'text/html':
                    content = content.replace('<br>', '\n').replace('<br/>', '\n')
                    content = re.sub('<[^<]+?>', '', content)
                content = self.sanitize_text(content)
                pdf.multi_cell(0, 10, content)

            # List attachments
            attachments = []
            for part in msg.iter_attachments():
                if part.get_filename():
                    attachments.append(self.sanitize_text(part.get_filename()))

            if attachments:
                pdf.ln(10)
                pdf.set_font(self.font_family, size=12)
                pdf.cell(0, 10, 'Attachments:', ln=True)
                for attachment in attachments:
                    pdf.cell(0, 10, f'- {attachment}', ln=True)

            # Save PDF
            output_path = self.output_dir / filename
            pdf.output(str(output_path))

            # Add to index
            self.index.append((
                filename,
                msg['subject'],
                msg['date'],
                msg['from']
            ))

            return True

        except Exception as e:
            print(f"Error converting {eml_path.name}: {str(e)}")
            return False

    def process_directory(self):
        """Process all EML files in directory."""
        eml_files = list(self.input_dir.glob('*.eml'))
        print(f"Found {len(eml_files)} EML files")

        successful = 0
        for eml_file in eml_files:
            if self.convert_email(eml_file):
                successful += 1
            print(f"Progress: {successful}/{len(eml_files)}", end='\r')

        print(f"\nSuccessfully converted {successful} out of {len(eml_files)} files")

        if successful > 0:
            self.create_index()
            print(f"Created index at {self.output_dir / 'index.pdf'}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py input_directory output_directory")
        sys.exit(1)

    converter = EmailConverter(sys.argv[1], sys.argv[2])
    converter.process_directory()

if __name__ == "__main__":
    main()
