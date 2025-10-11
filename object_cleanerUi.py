import maya.cmds as cmds

def object_cleaner_ui():
    window_name = "objectCleanerUI"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)


    window = cmds.window(window_name, title="Object Cleaner", sizeable=True)
    main_col = cmds.columnLayout(adjustableColumn=True, rowSpacing=8)

    cmds.text(label="Object Cleaner", align='center', height=25)


    cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnAlign2=("center", "center"), columnAttach2=("both", "both"))
    cmds.button('objectTabBtn', label="Object", command=lambda x: switch_list('object'))
    cmds.button('cameraTabBtn', label="Camera", command=lambda x: switch_list('camera'))
    cmds.setParent(main_col)


    object_list = cmds.textScrollList('objectList', height=260, allowMultiSelection=False,
                                      selectCommand=lambda: on_select(object_list))


    cmds.text(label='Search name', align='left')
    search_field = cmds.textField('searchField', placeholderText="Type to filter objects...")
    cmds.textField(search_field, edit=True, changeCommand=lambda x: filter_objects(object_list, x))

    cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnAlign2=("center", "center"), columnAttach2=("both", "both"))
    cmds.button(label="Select multiple object", command=lambda x: toggle_multi_selection(object_list))
    cmds.button('deleteBtn', label="Delete object", command=lambda x: delete_selected(object_list))
    cmds.setParent(main_col)

    cmds.separator(height=10, style='none')
    cmds.rowLayout(numberOfColumns=1, adjustableColumn=1, columnAlign=(1, "center"))
    cmds.button(label="Cancel", height=35, width=120, command=lambda x: cancel_selection(object_list))
    cmds.setParent(main_col)

    cmds.separator(height=8, style='none')


    cmds.optionVar(stringValue=("objectCleanerMode", "object"))
    refresh_object_list(object_list)

    events = [
        "DagObjectCreated", "Undo", "Redo", "NameChanged",
        "SceneOpened", "NewSceneOpened", "SceneSaved"
    ]
    for e in events:
        cmds.scriptJob(event=[e, lambda: refresh_if_no_filter(object_list)],
                       protected=True, parent=window)

    cmds.showWindow(window)
    cmds.window(window_name, edit=True, widthHeight=(320, 480)) 



def current_mode():
    if cmds.optionVar(exists="objectCleanerMode"):
        return cmds.optionVar(q="objectCleanerMode")
    return "object"


def switch_list(mode):
    cmds.optionVar(stringValue=("objectCleanerMode", mode))
    label = "Delete camera" if mode == "camera" else "Delete object"
    if cmds.button('deleteBtn', exists=True):
        cmds.button('deleteBtn', edit=True, label=label)
    refresh_object_list('objectList')
    cmds.warning(f"Switched to {mode} list.")


def refresh_object_list(object_list, filter_text=""):
    if not cmds.textScrollList(object_list, exists=True):
        return

    selected_before = cmds.textScrollList(object_list, query=True, selectItem=True) or []
    cmds.textScrollList(object_list, edit=True, removeAll=True)

    mode = current_mode()

    if mode == "object":
        all_objects = cmds.ls(type="transform") or []
        cameras = [cmds.listRelatives(c, parent=True)[0] for c in cmds.ls(type="camera") if cmds.listRelatives(c, parent=True)]
        all_objects = [obj for obj in all_objects if obj not in cameras]
    else:
        all_objects = [
            cmds.listRelatives(c, parent=True)[0]
            for c in cmds.ls(type="camera")
            if cmds.listRelatives(c, parent=True)
        ]

        default_cameras = {"persp", "top", "front", "side"}
        all_objects = [cam for cam in all_objects if cam not in default_cameras]

    if filter_text:
        all_objects = [obj for obj in all_objects if filter_text.lower() in obj.lower()]

    cmds.textScrollList(object_list, edit=True, append=all_objects)

    for item in selected_before:
        if cmds.objExists(item):
            cmds.textScrollList(object_list, edit=True, selectItem=item)


def refresh_if_no_filter(object_list):
    if not cmds.textField('searchField', exists=True):
        return
    text = cmds.textField('searchField', query=True, text=True)
    if not text:
        refresh_object_list(object_list)


def filter_objects(object_list, text):
    refresh_object_list(object_list, filter_text=text)


def _get_stored_selection():
    if not cmds.optionVar(exists="objectCleanerSelection"):
        return []
    data = cmds.optionVar(q="objectCleanerSelection")
    if isinstance(data, (list, tuple)):
        return list(data)
    if isinstance(data, str) and data:
        return data.split(",")
    return []


def _set_stored_selection(items):
    if cmds.optionVar(exists="objectCleanerSelection"):
        cmds.optionVar(remove="objectCleanerSelection")
    cmds.optionVar(stringValue=("objectCleanerSelection", ",".join(items) if items else ""))


def on_select(object_list):
    if not cmds.textScrollList(object_list, exists=True):
        return

    allow_multi = cmds.textScrollList(object_list, query=True, allowMultiSelection=True)
    clicked = cmds.textScrollList(object_list, query=True, selectItem=True)

    if not clicked:
        return

    if allow_multi:
        last_clicked = clicked[-1]
        current_selected = _get_stored_selection()

        if last_clicked in current_selected:
            current_selected.remove(last_clicked)
        else:
            current_selected.append(last_clicked)

        _set_stored_selection(current_selected)

        cmds.textScrollList(object_list, edit=True, deselectAll=True)
        for item in current_selected:
            cmds.textScrollList(object_list, edit=True, selectItem=item)

        cmds.select(current_selected, replace=True)
    else:
        _set_stored_selection([])
        cmds.select(clicked, replace=True)


def toggle_multi_selection(object_list):
    current_state = cmds.textScrollList(object_list, query=True, allowMultiSelection=True)
    new_state = not current_state
    cmds.textScrollList(object_list, edit=True, allowMultiSelection=new_state)
    _set_stored_selection([])

    if new_state:
        cmds.warning("Multiple selection enabled.")
    else:
        cmds.warning("Single selection mode enabled.")


def delete_selected(object_list):
    selected = cmds.textScrollList(object_list, query=True, selectItem=True)
    if not selected:
        cmds.warning("No object selected to delete.")
        return

    for obj in selected:
        if cmds.objExists(obj):
            cmds.delete(obj)

    cmds.select(clear=True)
    refresh_object_list(object_list)
    cmds.warning(f"Deleted: {', '.join(selected)}")


def cancel_selection(object_list):
    cmds.textScrollList(object_list, edit=True, deselectAll=True)
    cmds.select(clear=True)
    _set_stored_selection([])
    cmds.warning("Selection cleared.")


object_cleaner_ui()
