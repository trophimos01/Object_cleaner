from PySide6 import QtWidgets, QtCore, QtGui, QtMultimedia
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from shiboken6 import wrapInstance
import os

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class ObjectCleanerUI(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super().__init__(parent)
        self.setWindowTitle("Object Cleaner")
        self.setMinimumSize(360, 500)

        icon_path = r"C:\Users\ICT68\Documents\maya\2025\scripts\Object_cleaner\icons\Cleaner_Icon.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        else:
            print(f"⚠️ Icon not found at: {icon_path}")

        self.current_mode = cmds.optionVar(q="objectCleanerMode") if cmds.optionVar(exists="objectCleanerMode") else "object"
        self.stored_selection = []
        self.script_jobs = []

        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        self.apply_dark_theme()
        self.refresh_object_list()
        self.setup_scriptjobs()

    def create_widgets(self):
        self.header_label = QtWidgets.QLabel("Object Cleaner", alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self.header_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #FFFFFF;")

        self.object_tab_btn = QtWidgets.QPushButton("Object")
        self.camera_tab_btn = QtWidgets.QPushButton("Camera")

        self.object_list = QtWidgets.QListWidget()
        self.object_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

        self.search_label = QtWidgets.QLabel("Search name")
        self.search_label.setStyleSheet("color: #FFFFFF;")
        self.search_field = QtWidgets.QLineEdit()
        self.search_field.setPlaceholderText("Type to filter objects...")

        self.multi_select_btn = QtWidgets.QPushButton("Select multiple object")
        self.delete_btn = QtWidgets.QPushButton("Delete object")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")


        self.feedback_icon = QtWidgets.QLabel(alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        icon_path = r"C:\Users\ICT68\Documents\maya\2025\scripts\Object_cleaner\icons\delete_icon.png"
        if os.path.exists(icon_path):
            pixmap = QtGui.QPixmap(icon_path)
            self.feedback_icon.setPixmap(pixmap.scaled(128, 128, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
        self.feedback_icon.setVisible(False)

        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect()
        self.feedback_icon.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0) 

        self.player = QtMultimedia.QMediaPlayer()

    def create_layouts(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.header_label)

        tab_layout = QtWidgets.QHBoxLayout()
        tab_layout.addWidget(self.object_tab_btn)
        tab_layout.addWidget(self.camera_tab_btn)
        main_layout.addLayout(tab_layout)

        main_layout.addWidget(self.object_list)
        main_layout.addWidget(self.search_label)
        main_layout.addWidget(self.search_field)


        main_layout.addWidget(self.feedback_icon)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.multi_select_btn)
        button_layout.addWidget(self.delete_btn)
        main_layout.addLayout(button_layout)

        main_layout.addWidget(self.cancel_btn)

    def create_connections(self):
        self.object_tab_btn.clicked.connect(lambda: self.switch_list("object"))
        self.camera_tab_btn.clicked.connect(lambda: self.switch_list("camera"))
        self.object_list.itemSelectionChanged.connect(self.on_select)
        self.search_field.textChanged.connect(self.filter_objects)
        self.multi_select_btn.clicked.connect(self.toggle_multi_selection)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.cancel_btn.clicked.connect(self.cancel_selection)


    def setup_scriptjobs(self):
        self.cleanup_scriptjobs()
        events = ["DagObjectCreated", "Undo", "Redo", "NameChanged",
                  "SceneOpened", "NewSceneOpened", "SceneSaved"]
        for e in events:
            job_id = cmds.scriptJob(event=[e, self.refresh_if_no_filter], protected=True)
            self.script_jobs.append(job_id)

    def cleanup_scriptjobs(self):
        for job_id in self.script_jobs:
            if cmds.scriptJob(exists=job_id):
                cmds.scriptJob(kill=job_id, force=True)
        self.script_jobs.clear()

    def switch_list(self, mode):
        self.current_mode = mode
        cmds.optionVar(stringValue=("objectCleanerMode", mode))
        self.delete_btn.setText("Delete camera" if mode == "camera" else "Delete object")
        self.refresh_object_list()
        cmds.warning(f"Switched to {mode} list.")

    def refresh_object_list(self, filter_text=""):
        selected_before = [i.text() for i in self.object_list.selectedItems()]
        self.object_list.clear()

        if self.current_mode == "object":
            all_objects = cmds.ls(type="transform") or []
            cameras = [cmds.listRelatives(c, parent=True)[0] for c in cmds.ls(type="camera") if cmds.listRelatives(c, parent=True)]
            all_objects = [o for o in all_objects if o not in cameras]
        else:
            all_objects = [cmds.listRelatives(c, parent=True)[0] for c in cmds.ls(type="camera") if cmds.listRelatives(c, parent=True)]
            default_cameras = {"persp", "top", "front", "side"}
            all_objects = [c for c in all_objects if c not in default_cameras]

        if filter_text:
            all_objects = [o for o in all_objects if filter_text.lower() in o.lower()]

        self.object_list.addItems(all_objects)

        for txt in selected_before:
            items = self.object_list.findItems(txt, QtCore.Qt.MatchFlag.MatchExactly)
            for it in items:
                it.setSelected(True)

    def refresh_if_no_filter(self):
        if not self.search_field.text():
            self.refresh_object_list()

    def filter_objects(self, text):
        self.refresh_object_list(filter_text=text)

    def on_select(self):
        selected_items = [i.text() for i in self.object_list.selectedItems()]
        self.stored_selection = selected_items
        cmds.select(selected_items if selected_items else [], replace=True)

    def toggle_multi_selection(self):
        if self.object_list.selectionMode() == QtWidgets.QAbstractItemView.SelectionMode.MultiSelection:
            self.object_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
            self.stored_selection = []
            cmds.warning("Single selection mode enabled.")
        else:
            self.object_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
            cmds.warning("Multiple selection enabled.")

    def delete_selected(self):
        selected_items = [i.text() for i in self.object_list.selectedItems()]
        if not selected_items:
            cmds.warning("No object selected to delete.")
            return
        for obj in selected_items:
            if cmds.objExists(obj):
                cmds.delete(obj)

        self.stored_selection = []
        self.refresh_object_list()
        cmds.warning(f"Deleted: {', '.join(selected_items)}")

        self.feedback_icon.setVisible(True)
        self.opacity_effect.setOpacity(1)

        self.fade_animation = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(1000)
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.finished.connect(lambda: self.feedback_icon.setVisible(False))
        self.fade_animation.start()

        self.play_feedback_sound()

    def play_feedback_sound(self):
        sound_path = r"C:\Users\ICT68\Documents\maya\2025\scripts\Object_cleaner\sound button\delete_sound.mp3"
        if os.path.exists(sound_path):
            url = QtCore.QUrl.fromLocalFile(sound_path)
            content = QtMultimedia.QMediaContent(url)
            self.player.setMedia(content)
            self.player.setVolume(80)
            self.player.play()
        else:
            print(f"⚠️ Sound not found: {sound_path}")

    def cancel_selection(self):
        self.object_list.clearSelection()
        self.stored_selection = []
        cmds.select(clear=True)
        cmds.warning("Selection cleared.")

    def closeEvent(self, event):
        self.cleanup_scriptjobs()
        super().closeEvent(event)


    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog { background-color: #2e004f; }
            QLabel { color: #FFFFFF; }
            QPushButton {
                background-color: #6a00a1;
                color: #ffffff;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton:hover { background-color: #7b00bf; }
            QListWidget {
                background-color: #353535;
                color: #ffffff;
                border: 1px solid #6a00a1;
            }
            QLineEdit {
                background-color: #353535;
                color: #ffffff;
                border: 1px solid #6a00a1;
            }
            QLineEdit:focus {
                border: 1px solid #9d00d9;
            }
        """)

def run_object_cleaner():
    for w in QtWidgets.QApplication.allWidgets():
        if isinstance(w, ObjectCleanerUI):
            w.close()
    dlg = ObjectCleanerUI()
    dlg.show()
    return dlg

if __name__ == "__main__":
    run_object_cleaner()
