from __future__ import absolute_import, division, print_function, unicode_literals
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QMessageBox, QFileDialog, QGridLayout, QHBoxLayout, \
    QVBoxLayout, QGroupBox, QCheckBox, QPushButton, QAction
from PatchEdit import *
from collections import OrderedDict
import copy

class PatchGUI(QMainWindow):
    def __init__(self):
        self.app = QApplication(sys.argv)
        super(PatchGUI, self).__init__()
        self.file_dic = OrderedDict()
        self.orig_patch_obj_dic = OrderedDict()
        self.patch_obj_dic = OrderedDict()
        self.cb_dic = OrderedDict()
        self.vBox_list = []
        self.apply_button = None
        self.disable_all_button = None
        self.defaults_button = None

        self.choose_files()

    def choose_files(self):
        fn_list, file_type = QFileDialog.getOpenFileNames(caption='Open File', filter='Kobo Patch (*.patch)')
        if fn_list:
            fd = {fn: None for fn in fn_list}
            self.file_dic, error = read_patch_files(fd)
            if error:
                QMessageBox.critical(self, 'Read Error!', error)
            else:
                for (fn, patch_text) in iterDic(self.file_dic):
                    self.orig_patch_obj_dic[fn] = gen_patch_obj_list(fn, patch_text)
                self.initialize()
        else:
            self.close()

    def initialize(self):
        self.patch_obj_dic = copy.deepcopy(self.orig_patch_obj_dic)
        cont_index = 0
        vBox = QVBoxLayout(self)
        for (fn, patch_obj_list) in iterDic(self.patch_obj_dic):
            self.cb_dic[fn] = []
            gb = QGroupBox(fn)
            cb_grid = QGridLayout(self)
            # Create and add checkboxes to appropriate LabelFrame
            for (cb_index, obj) in enumerate(patch_obj_list):
                # Create checkbox variable and checkbox label for display
                cb_name = ''
                if obj.group:
                    cb_name = obj.name + '\n(' + obj.group + ')'
                else:
                    cb_name = obj.name

                # Create and add checkboxes to the LabelFrame, using the grid geometry manager
                self.cb_dic[fn].append(QCheckBox(cb_name))
                # Set initial state of checkboxes
                if 'yes' in obj.status:
                    self.cb_dic[fn][cb_index].setCheckState(Qt.Checked)
                else:
                    self.cb_dic[fn][cb_index].setCheckState(Qt.Unchecked)

                self.cb_dic[fn][cb_index].stateChanged.connect(self.toggle_check)
                self.cb_dic[fn][cb_index].setToolTip(self.patch_obj_dic[fn][cb_index].help_text)
                grid_pos = calc_grid_pos(cb_index, cols=3)

                cb_grid.addWidget(self.cb_dic[fn][cb_index], grid_pos[0], grid_pos[1])

            gb.setLayout(cb_grid)
            vBox.addWidget(gb)

            cont_index += 1

        self.apply_button = QPushButton('Apply Changes')
        self.apply_button.clicked.connect(self.app_chgs)
        self.disable_all_button = QPushButton("Disable All")
        self.disable_all_button.clicked.connect(self.disable_all_patches)
        self.defaults_button = QPushButton('Restore Settings')
        self.defaults_button.clicked.connect(self.restore_defaults)

        button_box = QHBoxLayout()
        button_box.addStretch()
        button_box.addWidget(self.apply_button)
        button_box.addWidget(self.disable_all_button)
        button_box.addWidget(self.defaults_button)
        button_box.addStretch()
        vBox.addLayout(button_box)

        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(vBox)
        self.setWindowTitle('Kobo Patch GUI')
        self.show()
        sys.exit(self.app.exec_())

    def disable_all_patches(self):
        """
        Does what it says on the tin :p
        Deselects all checkboxes and sets each objects status to 'no'
        :return:
        """
        for chk_list in self.cb_dic.values():
            for cb in chk_list:
                cb.setCheckState(Qt.Unchecked)

        for (fn, patch_obj_list) in iterDic(self.patch_obj_dic):
            for patch_obj in patch_obj_list:
                patch_obj.status = '`no`'

    def restore_defaults(self):
        """
        Restores the state of the patch objects and checkboxes back to their original state of when the file was loaded
        :return:
        """
        self.patch_obj_dic = copy.deepcopy(self.orig_patch_obj_dic)
        for (cb_list, patch_obj_list) in zip(self.cb_dic.values(), self.patch_obj_dic.values()):
            for (cb, patch_obj) in zip(cb_list, patch_obj_list):
                if 'yes' in patch_obj.status:
                     cb.setCheckState(Qt.Checked)
                else:
                     cb.setCheckState(Qt.Unchecked)

    def toggle_check(self, event):
        cb = self.sender()
        name = cb.text()
        for patch_list in self.patch_obj_dic.values():
            for obj in patch_list:
                if obj.name in name:
                    if cb.isChecked():
                        obj.status = '`yes`'
                    else:
                        obj.status = '`no`'

    def app_chgs(self, event):
        ask_confirm = QMessageBox.question(self, 'Are you sure?', 'Are you sure you wish to write the changes to the '
                                                                 'patch files?', QMessageBox.Yes | QMessageBox.No,
                                           QMessageBox.No)
        if ask_confirm == QMessageBox.Yes:
            success, error_title, error_msg = apply_changes(self.patch_obj_dic, self.file_dic)
            if not success:
                QMessageBox.critical(self, error_title, error_msg)
            else:
                QMessageBox.information(self, 'Sussess!', 'The files were successfully written.')

    def edit(self):
        pass

if __name__ == '__main__':
    pg = PatchGUI()
