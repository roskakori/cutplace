"""
A graphical user interface to specify a CID and data file and validate them.

Most of the functions and classes in this module are only defined if
:py:mod:`tkinter` is installed to avoid any :py:exc:`NameError`. You can check
for their availability using :py:data:`cutplace.gui.has_tk`, for example:

>>> from cutplace import gui
>>> if gui.has_tk:
...   gui.open_gui()  # doctest: +SKIP
... else:
...   print('tkinter must be installed')
"""
# Copyright (C) 2009-2021 Thomas Aglassinger
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
import time

try:
    from tkinter import *
    from tkinter.filedialog import Open, SaveAs
    from tkinter.messagebox import showerror, showinfo

    has_tk = True
except ImportError:
    has_tk = False

from cutplace import __version__, errors, interface, validio

_PADDING = 4

_CID_ROW = 0
_DATA_ROW = 1
_VALIDATE_BUTTON_ROW = 2
_VALIDATION_REPORT_ROW = 3
_SAVE_ROW = 4

# Menu indices to enable / disable certain items.
_CHOOSE_CID_PATH_MENU_INDEX = 0
_CHOOSE_DATA_PATH_MENU_INDEX = 1
_SAVE_VALIDATION_REPORT_AS_MENU_INDEX = 2
_QUIT_MENU_INDEX = 3


if has_tk:

    class CutplaceFrame(Frame):
        """
        Tk frame to validate a CID and data file.
        """

        def __init__(self, master, cid_path=None, data_path=None, config=dict(), **keywords):
            """
            Set up a frame with widgets to validate ``id_path`` and ``data_path``.

            :param master: Tk master or root in which the frame should show up
            :param cid_path: optional preset for :guilabel:`CID` widget
            :type cid_path: str or None
            :param data_path: optional preset for :guilabel:`Data` widget
            :type data_path: str or None
            :param config: Tk configuration
            :param keywords: Tk keywords
            """
            assert has_tk
            assert master is not None

            super().__init__(master, config, **keywords)

            self._master = master

            # Define basic layout.
            self.grid(padx=_PADDING, pady=_PADDING)
            # self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(_VALIDATION_REPORT_ROW, weight=1)

            # Choose CID.
            self._cid_label = Label(self, text="CID:")
            self._cid_label.grid(row=_CID_ROW, column=0, sticky=E)
            self._cid_path_entry = Entry(self, width=55)
            self._cid_path_entry.grid(row=_CID_ROW, column=1, sticky=E + W)
            self._choose_cid_button = Button(self, command=self.choose_cid, text="Choose...")
            self._choose_cid_button.grid(row=_CID_ROW, column=2)
            self.cid_path = cid_path

            # Choose data.
            self._data_label = Label(self, text="Data:")
            self._data_label.grid(row=_DATA_ROW, column=0, sticky=E)
            self._data_path_entry = Entry(self, width=55)
            self._data_path_entry.grid(row=_DATA_ROW, column=1, sticky=E + W)
            self._choose_data_button = Button(self, command=self.choose_data, text="Choose...")
            self._choose_data_button.grid(row=_DATA_ROW, column=2)
            self.data_path = data_path

            # Validate.
            self._validate_button = Button(self, command=self.validate, text="Validate")
            self._validate_button.grid(row=_VALIDATE_BUTTON_ROW, column=0, padx=_PADDING, pady=_PADDING)

            # Validation status text.
            self._validation_status_text = StringVar()
            validation_status_label = Label(self, textvariable=self._validation_status_text)
            validation_status_label.grid(row=_VALIDATE_BUTTON_ROW, column=1)

            # Validation result.
            validation_report_frame = LabelFrame(self, text="Validation report")
            validation_report_frame.grid(row=_VALIDATION_REPORT_ROW, columnspan=3, sticky=E + N + S + W)
            validation_report_frame.grid_columnconfigure(0, weight=1)
            validation_report_frame.grid_rowconfigure(0, weight=1)
            self._validation_report_text = Text(validation_report_frame)
            self._validation_report_text.grid(column=0, row=0, sticky=E + N + S)
            _validation_report_scrollbar = Scrollbar(validation_report_frame)
            _validation_report_scrollbar.grid(column=1, row=0, sticky=N + S + W)
            _validation_report_scrollbar.config(command=self._validation_report_text.yview)
            self._validation_report_text.config(yscrollcommand=_validation_report_scrollbar.set)

            # Set up file dialogs.
            self._choose_cid_dialog = Open(
                initialfile=self.cid_path,
                title="Choose CID",
            )
            self._choose_data_dialog = Open(
                initialfile=self.data_path,
                title="Choose data",
            )
            self._save_log_as_dialog = SaveAs(
                defaultextension=".log",
                initialfile="cutplace.log",
                title="Save validation result",
            )

            menubar = Menu(master)
            master.config(menu=menubar)
            self._file_menu = Menu(menubar, tearoff=False)
            self._file_menu.add_command(command=self.choose_cid, label="Choose CID...")
            self._file_menu.add_command(command=self.choose_data, label="Choose data...")
            self._file_menu.add_command(command=self.save_validation_report_as, label="Save validation report as...")
            self._file_menu.add_command(command=self.quit, label="Quit")
            menubar.add_cascade(label="File", menu=self._file_menu)
            help_menu = Menu(menubar, tearoff=False)
            help_menu.add_command(command=self.show_about, label="About")
            menubar.add_cascade(label="Help", menu=help_menu)

            self._enable_usable_widgets()

        def _enable_usable_widgets(self):
            def state_for(possibly_empty_text):
                if (possibly_empty_text is not None) and (possibly_empty_text.rstrip() != ""):
                    result = "normal"
                else:
                    result = "disabled"
                return result

            def set_state(widget_to_set_state_for, possibly_empty_text):
                widget_to_set_state_for.config(state=state_for(possibly_empty_text))

            set_state(self._validate_button, self.cid_path)
            set_state(self._validation_report_text, self.validation_report)
            set_state(self._data_path_entry, self.cid_path)
            set_state(self._choose_data_button, self.cid_path)

            cid_path_state = state_for(self.cid_path)
            self._file_menu.entryconfig(_CHOOSE_DATA_PATH_MENU_INDEX, state=cid_path_state)
            self._file_menu.entryconfig(_SAVE_VALIDATION_REPORT_AS_MENU_INDEX, state=state_for(self.validation_report))

        def choose_cid(self):
            """
            Open a dialog to set the CID path.
            """
            cid_path = self._choose_cid_dialog.show()
            if cid_path != "":
                self.cid_path = cid_path
                self._enable_usable_widgets()

        def choose_data(self):
            """
            Open a dialog to set the data path.
            """
            data_path = self._choose_data_dialog.show()
            if data_path != "":
                self.data_path = data_path
                self._enable_usable_widgets()

        def save_validation_report_as(self):
            """
            Open a dialog to set specify where the validation results should be
            stored and write to this file.
            """
            validation_report_path = self._save_log_as_dialog.show()
            if validation_report_path != "":
                try:
                    with io.open(validation_report_path, "w", encoding="utf-8") as validation_result_file:
                        validation_result_file.write(self._validation_report_text.get(1.0, END))
                except Exception as error:
                    showerror("Cutplace error", "Cannot save validation results:\n%s" % error)

        def quit(self):
            self._master.destroy()

        def show_about(self):
            showinfo("Cutplace", "Version " + __version__)

        def clear_validation_report_text(self):
            """
            Clear the text area containing the validation results.
            """
            self._validation_report_text.configure(state="normal")
            self._validation_report_text.delete(1.0, END)
            self._validation_report_text.see(END)
            self._enable_usable_widgets()

        def _cid_path(self):
            return self._cid_path_entry.get()

        def _set_cid_path(self, value):
            self._cid_path_entry.delete(0, END)
            if value is not None:
                self._cid_path_entry.insert(0, value)

        cid_path = property(_cid_path, _set_cid_path, None, "Path of the CID to use for validation")

        def _data_path(self):
            return self._data_path_entry.get()

        def _set_data_path(self, value):
            self._data_path_entry.delete(0, END)
            if value is not None:
                self._data_path_entry.insert(0, value)

        data_path = property(_data_path, _set_data_path, None, "Path of the data to validate")

        @property
        def validation_report(self):
            return self._validation_report_text.get(0.0, END)

        def validate(self):
            """
            Validate the CID and (if specified) data file and update the
            :py:attr:`validation_result`. Show any errors unrelated to data in a
            dialog.
            """
            assert self.cid_path != ""

            def add_log_line(line):
                self._validation_report_text.config(state=NORMAL)
                try:
                    self._validation_report_text.insert(END, line + "\n")
                    self._validation_report_text.see(END)
                finally:
                    self._validation_report_text.config(state=DISABLED)

            def add_log_error_line(line_or_error):
                add_log_line("ERROR: %s" % line_or_error)

            def show_status_line(line):
                self._validation_status_text.set(line)
                self.master.update()

            assert self.cid_path != ""

            cid_name = os.path.basename(self.cid_path)
            self.clear_validation_report_text()
            add_log_line("%s: validating" % cid_name)
            self._enable_usable_widgets()
            cid = None
            try:
                cid = interface.Cid(self.cid_path)
                add_log_line("%s: ok" % cid_name)
            except errors.InterfaceError as error:
                add_log_error_line(error)
            except Exception as error:
                add_log_error_line("cannot read CID: %s" % error)

            if (cid is not None) and (self.data_path != ""):
                try:
                    data_name = os.path.basename(self.data_path)
                    add_log_line("%s: validating" % data_name)
                    validator = validio.Reader(cid, self.data_path, on_error="yield")
                    show_status_line("Validation started")
                    last_update_time = time.time()
                    for row_or_error in validator.rows():
                        now = time.time()
                        if (now - last_update_time) >= 3:
                            last_update_time = now
                            show_status_line(
                                "%d rows validated" % (validator.accepted_rows_count + validator.rejected_rows_count)
                            )
                        if isinstance(row_or_error, errors.DataError):
                            add_log_error_line(row_or_error)
                    show_status_line(
                        "%d rows validated - finished" % (validator.accepted_rows_count + validator.rejected_rows_count)
                    )
                    add_log_line(
                        "%s: %d rows accepted, %d rows rejected"
                        % (data_name, validator.accepted_rows_count, validator.rejected_rows_count)
                    )
                except Exception as error:
                    add_log_error_line("cannot validate data: %s" % error)

    def open_gui(cid_path=None, data_path=None):
        """
        Open a new window with a user interface to validate a CID and data file.

        :param cid_path: optional preset for :guilabel:`CID` widget
        :type cid_path: str or None
        :param data_path: optional preset for :guilabel:`Data` widget
        :type data_path: str or None
        """
        assert has_tk

        root = Tk()
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        # TODO: Make GUI scale on resized window.
        root.resizable(width=False, height=False)
        root.title("Cutplace")
        CutplaceFrame(root, cid_path, data_path)
        root.mainloop()
