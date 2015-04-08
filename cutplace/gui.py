"""
A graphical user interface to set CID-FILE and DATA-FILE.
"""
# Copyright (C) 2009-2013 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import io
import os
import six
import time

try:
    if six.PY2:
        from Tkinter import *
        from tkFileDialog import askopenfilename
        from tkFileDialog import asksaveasfilename
        from tkMessageBox import showerror
        from tkMessageBox import showinfo
    else:
        from tkinter import *
        from tkinter.filedialog import askopenfilename
        from tkinter.filedialog import asksaveasfilename
        from tkinter.messagebox import showerror
        from tkinter.messagebox import showinfo
    has_tk = True
except ImportError:
    has_tk = False

from cutplace import __version__
from cutplace import errors
from cutplace import validio


def open_gui(cid_path='', data_path=''):
    assert has_tk

    root = Tk()
    root.title('cutplace %s' % __version__)
    root.geometry('600x450+650+150')
    root.minsize('600', '450')
    Gui(root, cid_path, data_path)
    root.mainloop()


class Gui:
    def __init__(self, master, cid_path, data_path):
        assert has_tk

        self.master = master
        self.processed_lines = 0
        self.cid_directory = '.'
        self.data_directory = '.'

        # cid
        self.cid_message = Message(master)
        self.cid_message.place(
            relx=0.00, rely=0.05,
            relheight=0.05, relwidth=0.1)
        self.cid_message.configure(text='CID:')
        self.cid_message.configure(width=30)

        self.cid_filename = Entry(master)
        self.cid_filename.place(relx=0.1, rely=0.05, relheight=0.05, relwidth=0.40)
        self.cid_filename.insert(0, cid_path)

        self.cid_button = Button(master, command=self.cid_open_file_dialog)
        self.cid_button.place(relx=0.52, rely=0.04, relheight=0.07, relwidth=0.10)
        self.cid_button.configure(text='Open...')

        # data
        self.data_message = Message(master)
        self.data_message.place(
            relx=0.00, rely=0.15,
            relheight=0.05, relwidth=0.1)
        self.data_message.configure(text='Data:')

        self.data_message.configure(width=30)

        self.data_filename = Entry(master)
        self.data_filename.place(relx=0.1, rely=0.15, relheight=0.05, relwidth=0.40)
        self.data_filename.insert(0, data_path)

        self.data_button = Button(master, command=self.data_open_file_dialog)
        self.data_button.place(relx=0.52, rely=0.14, relheight=0.07, relwidth=0.10)
        self.data_button.configure(text='Open...')

        # validate
        self.check_button = Button(master, command=self.validate_cid)
        self.check_button.place(relx=0.05, rely=0.24, relheight=0.07, relwidth=0.10)
        self.check_button.configure(text='Validate')

        self.status_text = StringVar()

        self.status_label = Label(master, textvariable=self.status_text)
        self.status_label.place(relx=0.18, rely=0.25, relwidth=0.5)

        # log
        self.label_frame = LabelFrame(master)
        self.label_frame.place(
            relx=0.01, rely=0.33, relheight=0.56, relwidth=0.98)
        self.label_frame.configure(text='Log')

        self.log_text = Text(self.label_frame)
        self.scrollbar = Scrollbar(self.label_frame)

        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)

        self.scrollbar.config(command=self.log_text.yview)
        self.log_text.config(yscrollcommand=self.scrollbar.set)
        self.log_text.config(state='disabled')

        # log into file
        self.choose_button = Button(master, command=self.choose_file_dialog)
        self.choose_button.place(relx=0.88, rely=0.91, relheight=0.07, relwidth=0.10)
        self.choose_button.configure(text='Save As...', state='disabled')

    def choose_file_dialog(self):
        filename = asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Txt files', '*.txt')])

        if filename:
            output = self.log_text.get(1.0, END)
            with io.open(filename, 'w', encoding='utf-8') as output_file:
                output_file.write(output)

            self.show_status_text('Log was successfully written to file.')

    def cid_open_file_dialog(self):
        filename = askopenfilename(
            initialdir=self.cid_directory,
            filetypes=[('Cid files', '*.csv;*.ods;*.xls;*.xlsx')])

        if filename:
            self.cid_directory = os.path.dirname(filename)
            self.cid_filename.delete(0, END)
            self.cid_filename.insert(0, filename)

    def data_open_file_dialog(self):
        filename = askopenfilename(
            initialdir=self.data_directory,
            filetypes=[('Data files', '*.txt;*.csv;*.ods;*.xls;*.xlsx')])

        if filename:
            self.data_directory = os.path.dirname(filename)
            self.data_filename.delete(0, END)
            self.data_filename.insert(0, filename)

    def show_status_text(self, text):
        self.status_text.set(text)

    def show_processed_lines(self):
        if self.processed_lines == 1:
            self.show_status_text('...validated %d line' % self.processed_lines)
        else:
            self.show_status_text('...validated %d lines' % self.processed_lines)

        self.master.update()

    def add_log_text(self, text):
        self.log_text.configure(state='normal')
        self.log_text.insert(END, '%s\n' % text)
        self.log_text.see(END)
        self.log_text.configure(state='disabled')

    def clear_log_text(self):
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, END)
        self.log_text.see(END)
        self.log_text.configure(state='disabled')

    def validate_cid(self):
        self.clear_log_text()
        if self.cid_filename.get() == '' or self.data_filename.get() == '':
            showerror('Error', 'CID-PATH and DATA-PATH must be specified.')
        else:
            try:
                self.show_status_text('Validation started')
                self.processed_lines = 0
                last_time = time.time()
                self.show_processed_lines()
                for row_or_error in validio.rows(self.cid_filename.get(), self.data_filename.get(), on_error='yield'):
                    self.processed_lines += 1
                    now = time.time()
                    if (now - last_time) > 3:
                        last_time = now
                        self.show_processed_lines()
                    if isinstance(row_or_error, Exception):
                        self.add_log_text(row_or_error)

                        if not isinstance(row_or_error, errors.CutplaceError):
                            raise row_or_error

                self.show_processed_lines()
                self.show_status_text('Validation finished')
            except Exception as error:
                self.show_status_text('Error occurred')
                self.add_log_text(error)

            self.choose_button.config(state='normal')
