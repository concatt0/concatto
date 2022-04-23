import re
import pdfplumber
from tabula import read_pdf
import pandas

# line = 'GOLDEN NUG LNDY#9871 SOUTH-CHIPS GOLDEN NUGGET HOTEL & CASINO'
# print(re.search(r'LNDY#', line))

# pdf = pdfplumber.open(r'c:\data\test\TREPECO INVOICE_1126857.PDF')
# text = pdf.pages[0].extract_text()
# print(text)

dfs = read_pdf(r'c:\data\test\INVC_44943_03242022_374544_032520221721.PDF', pages='all')

# print(dfs)

for df in dfs:
    for row in df.iterrows():
        try:
            print(row[1].at['Description'])
        except KeyError:
            pass

# for df in dfs:
#     for row in df.iterrows():
#         print(row[1].at['Description'])
