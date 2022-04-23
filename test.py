import re
import datetime
import pdfplumber

pdf = pdfplumber.open(r'C:/data/test/PTL Invoice_375501.pdf')

print(pdf.pages[0].extract_text())