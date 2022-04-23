# Invoice PDF to EDI-810 Translator
# Author: Phillip Huynh
# Date: April 2022

from typing import Any
import tkinter as tk
import tkinter.scrolledtext as st
from PIL import Image, ImageTk
from tkinter.filedialog import askdirectory
import pdfplumber
import re
import os
import datetime

# declare global variables
directory: Any = ''
edi_file_name: Any = ''
edi: Any = ''
pdf: Any = ''

current_time = datetime.datetime.now()
date_6 = current_time.strftime('%y%m%d')
date_8 = current_time.strftime('%Y%m%d')
time = current_time.strftime('%H%M%S')
segment_line_count = 0


def open_directory():
    global directory
    directory = askdirectory(parent=root, title="Choose a directory")
    if directory:
        os.chdir(directory)
        # print("directory selected ", directory)


def translate_edi():
    global directory, edi, pdf, edi_file_name

    pop = tk.Toplevel(root)
    pop.title("Job Log")
    pop.resizable(width=False, height=False)
    text_area = st.ScrolledText(pop,
                                width=110,
                                height=50,
                                font=("Calibri", 11))
    text_area.grid(column=0, pady=10, padx=10)
    text_area.configure(state='normal')

    text_area.insert(tk.INSERT, 'process invoice.pdf2edi.translator\n')
    text_area.insert(tk.INSERT, 'selected directory: ' + directory.upper() + '\n\n')
    text_area.insert(tk.INSERT, 'job started on ' + datetime.datetime.now().strftime('%B %d %Y @ %H:%M:%S') + '\n\n')
    text_area.update()

    for filename in os.listdir(directory):
        filename = filename.upper()
        if filename.endswith('.PDF'):
            # pdf = pdfplumber.open(os.path.join(directory, filename))
            pdf = pdfplumber.open(filename)
            text_area.insert(tk.INSERT, 'input file -> ' + filename + '\n')
            text_area.update()
            edi_file = filename.upper() + '.TXT'
            edi = open(edi_file, 'w')

            text_area.insert(tk.INSERT, 'output file -> ' + edi_file + '\n')
            text_area.update()

            # validate vendor and start format output file name
            text = pdf.pages[0].extract_text()

            if 'TREPCO WEST' in text.upper():
                edi_file_name = 'INVC_21771_000000_'
                write_edi_header_TREPCO()
                write_edi_body_TREPCO()

            elif 'PTL ONE' in text.upper():
                edi_file_name = 'INVC_44943_000000_'
                write_edi_header_PTL()
                write_edi_body_PTL()

            elif 'STARKMAN' in text.upper():
                edi_file_name = 'INVC_102787_000000_'
                write_edi_header_STARKMAN()
                write_edi_body_STARKMAN()

            else:
                edi_file_name = 'INVC_ERROR_000000_'
                write_edi_header_ERROR()

            write_edi_trailer()
            pdf.close()
            edi.close()

            # rename output file
            try:
                os.path = directory
                os.rename(edi_file, edi_file_name)
                text_area.insert(tk.INSERT, 'rename file ' + edi_file + ' -> ' + edi_file_name + '\n\n')
                text_area.update()
            except:
                print('rename error!')

        else:
            continue

    text_area.insert(tk.INSERT, 'job ended on ' + datetime.datetime.now().strftime('%B %d %Y @ %H:%M:%S') + '\n\n')
    text_area.update()

    # save log file
    log = open('log_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.txt', 'w+')
    log.write(text_area.get(1.0, tk.END))
    log.close()
    text_area.configure(state='disabled')
    text_area.update()


def write_edi_header_TREPCO():
    global edi, pdf, date_6, date_8, time, edi_file_name
    # extract invoice header from first page of invoice
    text = pdf.pages[0].extract_text()

    invoice_re = re.compile('I_N_V_O_I_C_E')
    store_number = '0000'
    line_save = ''
    line_count = 0
    store_re = re.compile('#\d{4}')  # hash followed by 4 digit

    for line in text.split('\n'):
        line = line.upper()
        line_save = line
        if invoice_re.search(line):
            print(line.split())
            line = line.split()
            print('Invoice #{inv}, date {date}'.format(inv=line[-6], date=line[-5]))
            inv_number = line[-6]
            ediline = 'ISA*00*          *00*          *ZZ*LANDRYS_IT     *ZZ*LANDRYS        *{date}*{time}*U*00401*123456789*0*P*>~\n'.format(date=date_6, time=time)
            edi.write(ediline)
            ediline = 'GS*IN*LANDRYS_IT*LANDRYS*{date}*{time}*123456789*X*4010~\n'.format(date=date_8, time=time)
            edi.write(ediline)
            # Segment begin
            edi.write('ST*810*123456789~\n')

            inv_date = datetime.datetime.strptime(line[-5], "%m/%d/%y").strftime("%Y%m%d")
            inv_nbr = line[-6]
            ediline = 'BIG*{date}*{inv}**000000***DI~\n'.format(date=inv_date, inv=inv_nbr)
            edi.write(ediline)

            edi.write('CUR*BY*USD~\n')
            edi.write('PER*SR*TIM TALBOT GN RETAIL~\n')
            edi.write('N1*VN*TREPCO WEST / SNACK MAN*92*21771~\n')
            edi.write('N2*LAS VEGAS CC~\n')
            edi.write('N3*3930 CIVIC CENTER DR*NORTH LAS VEGAS NV 89030~\n')
            edi.write('N4*North Las Vegas*Ne*89030-7541*US~\n')

            # assign edi file name
            edi_file_name = edi_file_name + inv_number + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M') + '.DAT'


        # find store number
        if store_re.search(line_save):
            # if store found, remove prefix hash #
            store_number = re.sub(r'#', '', store_re.search(line_save).group())
            ediline = 'N1*ST*{addr}*00*{store}~\n'.format(addr=line_save, store=store_number)   # need to update/import store #
            edi.write(ediline)

            edi.write('N3*STORE-ADDRESS~\n')
            edi.write('N4*CITY*STATE*ZIPCODE*US~\n')
            edi.write('N1*RE*TREPCO WEST / SNACK MAN*92*21771~\n')
            edi.write('N2*LAS VEGAS CC~\n')
            edi.write('N3*3930 CIVIC CENTER DR*NORTH LAS VEGAS NV 89030 0~\n')
            edi.write('N4*North Las Vegas*Ne*89030-7541*US~\n')
            edi.write('ITD*03*****{date}******30 DAYS~\n'.format(date=date_8))

            break


def write_edi_body_TREPCO():
    global edi, pdf
    pages = pdf.pages
    item_count = 0

    for page in pdf.pages:
        text = page.extract_text()
        upc_re = re.compile(r'^\d{12}')

        for line in text.split('\n'):
            line = line.upper()
            if upc_re.match(line):
                line = line.split()
                if line[2] != '0':  # ignore zero order qty detail line
                    item_count += 1
                    # print('UPC:' + line[0] + ' QTY:' + line[2] + ' COST: ' + line[-2])

                    # build item description
                    item_desc = ''
                    for i in range(7, len(line) - 5):
                        item_desc += line[i] + ' '

                    # build IT1 segment
                    ediline = 'IT1*' + str(item_count) + '*' + line[2] + '*' + line[3] + '*' + line[-2] + '**UP*' + \
                              line[0] + '*IN**VN*' + line[1] + '~\n'
                    edi.write(ediline)

                    # build PID segment
                    ediline = 'PID*F*8***' + line[4] + ' ' + line[5] + ' ' + line[6] + ' ' + item_desc.strip() + '~\n'
                    edi.write(ediline)

def write_edi_header_PTL():
    global edi, pdf, date_6, date_8, time, edi_file_name
    # extract invoice header from first page of invoice
    text = pdf.pages[0].extract_text()
    invoice_re = re.compile('^INVOICE ')
    # store_re = re.compile('ESS.+\d{4}')
    store_1 = re.compile('ESS.+\d{4}')  # search for ESS before store number
    store_2 = re.compile('#\d{4}')      # search for hash sign before store number

    for line in text.split('\n'):
        line = line.upper()
        line_save = line
        if invoice_re.search(line):
            print(line.split())
            line = line.split()
            inv_number = line[2]

            ediline = 'ISA*00*          *00*          *ZZ*LANDRYS_IT     *ZZ*LANDRYS        *{date}*{time}*U*00401*123456789*0*P*>~\n'.format(date=date_6, time=time)
            edi.write(ediline)
            ediline = 'GS*IN*LANDRYS_IT*LANDRYS*{date}*{time}*123456789*X*4010~\n'.format(date=date_8, time=time)
            edi.write(ediline)
            # Segment begin
            edi.write('ST*810*123456789~\n')

            ediline = 'BIG*{date}*{inv}**000000***DI~\n'.format(date=date_8, inv=inv_number)
            edi.write(ediline)

            edi.write('CUR*BY*USD~\n')
            edi.write('N1*VN*PTL ONE*92*44943~\n')
            edi.write('N4*Pompano Beach*FL*33069*US~\n')

            # assign edi file name
            edi_file_name = edi_file_name + inv_number + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M') + '.DAT'

        # find store number by search for 4-digit pattern
        # if found, use the last set since the first may be
        # part of the account number
        if store_1.search(line_save) or store_2.search(line_save):
            store_number = re.findall('\d{4}', line_save)[-1]
            edi.write('N1*ST*{addr}*92*{store}~\n'.format(addr=line_save, store=store_number))   # need to update/import store #
            edi.write('N4*CITY*STATE*ZIPCODE*US~\n')
            edi.write('N1*RE*PTL ONE~\n')
            edi.write('N4*Pompano Beach*FL*33069*US~\n')
            edi.write('ITD*03*****{date}******30 DAYS~\n'.format(date=date_8))

            break


def write_edi_body_PTL():
    global edi, pdf
    pages = pdf.pages
    item_count = 0

    for page in pdf.pages:
        text = page.extract_text()
        upc_re = re.compile(r'\d{12}.*\$|\d{14}.*\$')  # 12 or 14 -digit UPC followed by any chars and a $

        for line in text.split('\n'):
            line = line.upper()
            if upc_re.search(line):
                line = line.split()
                print(line)
                if line[2] != '0':  # ignore zero order qty detail line
                    item_count += 1
                    # print('UPC:' + line[0] + ' QTY:' + line[2] + ' COST: ' + line[-2])

                    # build item description
                    item_desc = ''
                    for i in range(1, len(line) - 4):
                        item_desc += line[i] + ' '
                    print("item_desc:", item_desc)

                    # build IT1 segment
                    qty = line[-3] + '.00'  # qty is a floating-point number
                    cost = re.sub('[$]', '', line[-2])  # remove leading $
                    vpn = line[0]
                    upc = line[-4]

                    ediline = 'IT1*' + str(item_count) + '*' + qty + '*EA*' + cost + '**UP*' + \
                              upc + '*IN**VN*' + vpn + '~\n'
                    edi.write(ediline)

                    # build PID segment
                    ediline = 'PID*F*8***' + item_desc.strip() + '~\n'
                    edi.write(ediline)


def write_edi_header_STARKMAN():
    pass


def write_edi_body_STARKMAN():
    pass


def write_edi_header_ERROR():
    edi.write('*** ERROR - INVALID VENDOR or NO VENDOR DETECTED ***')


def write_edi_trailer():
    global edi, pdf
    # Service, Promotion, Allowance (misc charges)
    edi.write('SAC*C*{misc-charge-1}~\n')

    # Total Monetary Value Summary (invoice total)
    edi.write('TDS*{invoice-total}~\n')

    # Inv Shipment Summary (total quantity)
    edi.write('ISS*{qty-total}~\n')

    # Trans Set Trailer (segment counts between beginning ST and ending SE)
    edi.write('SE*{line-count}*123456789~\n')
    edi.write('GE*1*123456789~\n')
    edi.write('IEA*1*123456789~\n')


# main-loop start
root = tk.Tk()
root.title("PDF>EDI Translator")
root.resizable(width=False, height=False)

# favicon
img_icon = Image.open('img/invoice.png')
img_icon = ImageTk.PhotoImage(img_icon)
root.iconphoto(False, img_icon)

canvas = tk.Canvas(root, width=476, heigh=200, borderwidth=0, bg='white')
canvas.grid(columnspan=3, rowspan=5)

# logo
logo = Image.open('img/landrys_pdf2edi_logo.png')
logo = ImageTk.PhotoImage(logo)
logo_label = tk.Label(image=logo, borderwidth=0)
logo_label.image = logo
logo_label.grid(columnspan=3, row=0,)

# arrow
img_arrow = Image.open('img/right-arrow.png')
img_arrow = img_arrow.resize((50, 50), resample=Image.LANCZOS)
img_arrow = ImageTk.PhotoImage(img_arrow)
arrow_label = tk.Label(image=img_arrow, borderwidth=0)
arrow_label.image = img_arrow
arrow_label.grid(columnspan=2, row=2)

img_PDF = Image.open('img/folder_pdf.png')
img_PDF = img_PDF.resize((60, 60), resample=Image.LANCZOS)
img_PDF = ImageTk.PhotoImage(img_PDF)

img_EDI = Image.open('img/folder_edi.png')
img_EDI = img_EDI.resize((60, 60), resample=Image.LANCZOS)
img_EDI = ImageTk.PhotoImage(img_EDI)

img_OFF = Image.open('img/power.png')
img_OFF = img_OFF.resize((30, 30), resample=Image.LANCZOS)
img_OFF = ImageTk.PhotoImage(img_OFF)

# instructions
instructions = tk.Label(root, text = "Click PDF to select folder, then click on EDI to translate", borderwidth=0, bg='white', font=("Raleway", 10))
instructions.grid(columnspan=3, column=0, row=1)


# PDF button
pdf_text = tk.StringVar()
pdf_btn = tk.Button(root, image=img_PDF, command=lambda: open_directory(), borderwidth=0, padx=15, pady=15)
pdf_text.set("PDF")
pdf_btn.grid(column=0, row=2)

# EDI button
edi_text = tk.StringVar()
edi_btn = tk.Button(root, image=img_EDI, command=lambda: translate_edi(), borderwidth=0, padx=15, pady=15)
edi_text.set("EDI")
edi_btn.grid(column=1, row=2)

# OFF button
off_text = tk.StringVar()
off_btn = tk.Button(root, image=img_OFF, command=root.quit, bg='white', borderwidth=0, padx=15, pady=15)
off_text.set("QUIT")
off_btn.grid(column=2, row=2)

root.mainloop()