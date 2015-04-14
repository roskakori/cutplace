"""
A graphical user interface to specify a CID and data file and validate them.
"""
# Copyright (C) 2009-2015 Thomas Aglassinger
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
    if six.PY3:
        from tkinter import *
        from tkinter.filedialog import Open
        from tkinter.filedialog import SaveAs
        from tkinter.messagebox import showerror
    else:
        from Tkinter import *
        from tkFileDialog import Open
        from tkFileDialog import SaveAs
        from tkMessageBox import showerror
    has_tk = True
except ImportError:
    has_tk = False

from cutplace import errors
from cutplace import interface
from cutplace import validio
from cutplace import __version__

_PADDING = 4

_CID_ROW = 0
_DATA_ROW = 1
_VALIDATE_BUTTON_ROW = 2
_VALIDATION_RESULT_ROW = 3
_SAVE_ROW = 4


class CutplaceFrame(Frame):
    """
    Tk frame to validate a CID and data file.
    """
    def __init__(self, master, cid_path=None, data_path=None, config=dict(), **keywords):
        """
        Set up a frame with widgets to validate ``id_path`` and ``data_path``.

        :param master: Tk master or root in which the frame should show up
        :param cid_path: optional preset for :guilabel:`CID` widget
        :type: str or None
        :param data_path: optional preset for :guilabel:`Data` widget
        :type: str or None
        :param config: Tik configuration
        :param keywords: Tk keywords
        """
        assert has_tk
        if six.PY2:
            # In Python 2, Frame is an old style class.
            Frame.__init__(self, master, config, **keywords)
        else:
            super().__init__(master, config, **keywords)

        # Define basic layout.
        self.grid(padx=_PADDING, pady=_PADDING)
        # self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(_VALIDATION_RESULT_ROW, weight=1)

        # Choose CID.
        self._cid_label = Label(self, text='CID:')
        self._cid_label.grid(row=_CID_ROW, column=0, sticky=E)
        self._cid_path_entry = Entry(self, width=55)
        self._cid_path_entry.grid(row=_CID_ROW, column=1, sticky=E + W)
        self._choose_cid_button = Button(self, command=self.choose_cid, text='Choose...')
        self._choose_cid_button.grid(row=_CID_ROW, column=2)
        self.cid_path = cid_path

        # Choose data.
        self._data_label = Label(self, text='Data:')
        self._data_label.grid(row=_DATA_ROW, column=0, sticky=E)
        self._data_path_entry = Entry(self, width=55)
        self._data_path_entry.grid(row=_DATA_ROW, column=1, sticky=E + W)
        self._choose_data_button = Button(self, command=self.choose_data, text='Choose...')
        self._choose_data_button.grid(row=_DATA_ROW, column=2)
        self.data_path = data_path

        # Validate.
        self._validate_button = Button(self, command=self.validate, text='Validate')
        self._validate_button.grid(row=_VALIDATE_BUTTON_ROW, column=0, padx=_PADDING, pady=_PADDING)

        # Validation status text.
        self._validation_status_text = StringVar()
        validation_status_label = Label(self, textvariable=self._validation_status_text)
        validation_status_label.grid(row=_VALIDATE_BUTTON_ROW, column=1)

        # Validation result.
        validation_result_frame = LabelFrame(self, text='Validation result')
        validation_result_frame.grid(row=_VALIDATION_RESULT_ROW, columnspan=3, sticky=E + N + S + W)
        validation_result_frame.grid_columnconfigure(0, weight=1)
        validation_result_frame.grid_rowconfigure(0, weight=1)
        self._validation_result_text = Text(validation_result_frame)
        self._validation_result_text.grid(column=0, row=0, sticky=E + N + S)
        _validation_result_scrollbar = Scrollbar(validation_result_frame)
        _validation_result_scrollbar.grid(column=1, row=0, sticky=N + S + W)
        _validation_result_scrollbar.config(command=self._validation_result_text.yview)
        self._validation_result_text.config(yscrollcommand=_validation_result_scrollbar.set)

        # "Save validation result as" button.
        self._save_log_button = Button(self, command=self.save_log_as, text='Save validation result as...')
        self._save_log_button.grid(row=_SAVE_ROW, column=1, columnspan=2, sticky=E + S)

        # Set up file dialogs.
        self._choose_cid_dialog = Open(
            initialfile=self.cid_path,
            title='Choose CID',
        )
        self._choose_data_dialog = Open(
            initialfile=self.data_path,
            title='Choose data',
        )
        self._save_log_as_dialog = SaveAs(
            defaultextension='.log',
            initialfile='cutplace.log',
            title='Save validation result',
        )

        self._enable_usable_widgets()

    def _enable_usable_widgets(self):
        def set_state(widget_to_set_state_for, possibly_empty_text):
            if (possibly_empty_text is not None) and (possibly_empty_text.rstrip() != ''):
                state = 'normal'
            else:
                state = 'disabled'
            widget_to_set_state_for.config(state=state)

        set_state(self._validate_button, self.cid_path)
        set_state(self._validation_result_text, self.validation_result)
        set_state(self._save_log_button, self.validation_result)

    def choose_cid(self):
        """
        Open a dialog to set the CID path.
        """
        cid_path = self._choose_cid_dialog.show()
        if cid_path != '':
            self.cid_path = cid_path
            self._enable_usable_widgets()

    def choose_data(self):
        """
        Open a dialog to set the data path.
        """
        data_path = self._choose_data_dialog.show()
        if data_path != '':
            self.data_path = data_path
            self._enable_usable_widgets()

    def save_log_as(self):
        """
        Open a dialog to set specify where the validation results should be
        stored and write to this file.
        """
        validation_result_path = self._save_log_as_dialog.show()
        if validation_result_path != '':
            try:
                with io.open(validation_result_path, 'w', encoding='utf-8') as validation_result_file:
                    validation_result_file.write(self._validation_result_text.get(1.0, END))
            except Exception as error:
                showerror('Cutplace error', 'Cannot save validation results:\n%s' % error)

    def clear_validation_result_text(self):
        """
        Clear the text area containing the validation results.
        """
        self._validation_result_text.configure(state='normal')
        self._validation_result_text.delete(1.0, END)
        self._validation_result_text.see(END)
        self._validation_result_text.configure(state='disabled')

    def _cid_path(self):
        return self._cid_path_entry.get()

    def _set_cid_path(self, value):
        self._cid_path_entry.delete(0, END)
        if value is not None:
            self._cid_path_entry.insert(0, value)

    cid_path = property(_cid_path, _set_cid_path, None, 'Path of the CID to use for validation')

    def _data_path(self):
        return self._data_path_entry.get()

    def _set_data_path(self, value):
        self._data_path_entry.delete(0, END)
        if value is not None:
            self._data_path_entry.insert(0, value)

    data_path = property(_data_path, _set_data_path, None, 'Path of the data to validate')

    @property
    def validation_result(self):
        return self._validation_result_text.get(0.0, END)

    def validate(self):
        """
        Validate the CID and (if specified) data file and update the
        :py:attr:`validation_result`. Show any errors unrelated to data in a
        dialog.
        """
        assert self.cid_path != ''

        def add_log_line(line):
            self._validation_result_text.config(state=NORMAL)
            try:
                self._validation_result_text.insert(END, line + '\n')
                self._validation_result_text.see(END)
            finally:
                self._validation_result_text.config(state=DISABLED)

        def add_log_error_line(line):
            add_log_line('ERROR: %s' % line)

        def show_status_line(line):
            self._validation_status_text.set(line)
            self.master.update()

        assert self.cid_path != ''

        cid_name = os.path.basename(self.cid_path)
        self.clear_validation_result_text()
        add_log_line('%s: validating' % cid_name)
        self._enable_usable_widgets()
        cid = None
        try:
            cid = interface.Cid(self.cid_path)
            add_log_line('%s: ok' % cid_name)
        except errors.InterfaceError as error:
            add_log_error_line(error)
        except Exception as error:
            add_log_error_line('cannot read CID: %s' % error)

        if (cid is not None) and (self.data_path != ''):
            try:
                data_name = os.path.basename(self.data_path)
                add_log_line('%s: validating' % data_name)
                validator = validio.Reader(cid, self.data_path, on_error='yield')
                show_status_line('Validation started')
                last_update_time = time.time()
                for row_or_error in validator.rows():
                    now = time.time()
                    if (now - last_update_time) >= 3:
                        last_update_time = now
                        show_status_line(
                            '%d rows validated' % (validator.accepted_rows_count + validator.rejected_rows_count))
                    if isinstance(row_or_error, errors.CutplaceError):
                        add_log_error_line(row_or_error)
                show_status_line(
                    '%d rows validated - finished' % (validator.accepted_rows_count + validator.rejected_rows_count))
                add_log_line(
                    '%s: %d rows accepted, %d rows rejected'
                    % (data_name, validator.accepted_rows_count, validator.rejected_rows_count))
            except Exception as error:
                add_log_error_line('cannot validate data: %s' % error)


def open_gui(cid_path=None, data_path=None):
    """
    Open a new window with a user interface to validate a CID and data file.

    :param cid_path: optional preset for :guilabel:`CID` widget
    :type: str or None
    :param data_path: optional preset for :guilabel:`Data` widget
    :type: str or None
    """
    assert has_tk

    root = Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    # TODO: Make GUI scale on resized window.
    root.resizable(width=False, height=False)
    root.title('Cutplace v' + __version__)
    CutplaceFrame(root, cid_path, data_path)
    root.mainloop()
