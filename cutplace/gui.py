"""
Methods to create sql statements from existing fields.
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
import six

if six.PY3:
    from tkinter import *
    from tkinter.filedialog import askopenfilename
    from tkinter.filedialog import asksaveasfilename
    from tkinter import messagebox
else:
    from Tkinter import *
    from Tkinter.filedialog import *
    import tkMessageBox

from cutplace import errors
from cutplace import validio


def open_gui():
    root = Tk()
    root.title('cutplace')
    root.geometry('600x450+650+150')
    root.minsize('600', '450')
    Gui(root)
    root.mainloop()


class Gui:
    def __init__(self, master):
        # cid
        self.cid_message = Message(master)
        self.cid_message.place(
            relx=0.00, rely=0.05,
            relheight=0.05, relwidth=0.1)
        self.cid_message.configure(text='Cid:')
        self.cid_message.configure(width=30)

        self.cid_filename = Entry(master)
        self.cid_filename.place(relx=0.1, rely=0.05, relheight=0.05, relwidth=0.40)

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

        self.data_button = Button(master, command=self.data_open_file_dialog)
        self.data_button.place(relx=0.52, rely=0.14, relheight=0.07, relwidth=0.10)
        self.data_button.configure(text='Open...')

        # validate
        self.check_button = Button(master, command=self.validate_cid)
        self.check_button.place(relx=0.05, rely=0.24, relheight=0.07, relwidth=0.10)
        self.check_button.configure(text='Validate')

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
            filetypes=[('Txt files', '*.txt')])

        if filename:
            if '.' not in filename:
                filename = filename + '.txt'
            output = self.log_text.get(1.0, END)
            with io.open(filename, 'w', encoding='utf-8') as output_file:
                output_file.write(output)

            title = 'Info'
            message = 'Log was successfully written to file.'
            if six.PY3:
                messagebox.showinfo(title, message)
            else:
                tkMessageBox.showinfo(title, message)

    def cid_open_file_dialog(self):
        filename = askopenfilename(
            filetypes=[('Cid files', '*.csv;*.ods;*.xls;*.xlsx')])

        if filename:
            self.cid_filename.delete(0, END)
            self.cid_filename.insert(0, filename)

    def data_open_file_dialog(self):
        filename = askopenfilename(
            filetypes=[('Data files', '*.txt;*.csv;*.ods;*.xls;*.xlsx')])

        if filename:
            self.data_filename.delete(0, END)
            self.data_filename.insert(0, filename)

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

            title = 'Error'
            message = 'Please choose a CID-FILE and a DATA-FILE.'
            if six.PY3:
                messagebox.showerror(title, message)
            else:
                tkMessageBox.showerror(title, message)
        else:
            try:
                for row_or_error in validio.rows(self.cid_filename.get(), self.data_filename.get(), on_error='yield'):
                    if isinstance(row_or_error, Exception):
                        self.add_log_text(row_or_error)

                        if not isinstance(row_or_error, errors.CutplaceError):
                            raise row_or_error

                title = 'Info'
                message = 'Validation finished'
                if six.PY3:
                    messagebox.showerror(title, message)
                else:
                    tkMessageBox.showerror(title, message)
            except FileNotFoundError as error:
                self.add_log_text(error)

            self.choose_button.config(state='normal')
