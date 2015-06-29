unnamed_message = {
    u"task_uuid": u"cdeb220d-7605-4d5f-8341-1a170222e308",
    u"error": False,
    u"timestamp": 1425356700,
    u"message": u"Main loop terminated.",
    u"task_level": [1]}

message_task = {
    u"task_uuid": u"cdeb220d-7605-4d5f-8341-1a170222e308",
    u"error": False,
    u"timestamp": 1425356700,
    u"message": u"Main loop terminated.",
    u"message_type": u"twisted:log",
    u"action_type": u"nope",
    u"task_level": [1]}

action_task = {
    u"timestamp": 1425356800,
    u"action_status": u"started",
    u"task_uuid": u"f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    u"action_type": u"app:action",
    u"task_level": [1]}

nested_action_task = {
    u"timestamp": 1425356900,
    u"action_status": u"started",
    u"task_uuid": u"f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    u"action_type": u"app:action:nested",
    u"task_level": [1, 1]}

action_task_end = {
    u"timestamp": 1425356800,
    u"action_status": u"succeeded",
    u"task_uuid": u"f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    u"action_type": u"app:action",
    u"task_level": [2]}

dict_action_task = {
    u"timestamp": 1425356800,
    u"action_status": u"started",
    u"task_uuid": u"f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    u"action_type": u"app:action",
    u"task_level": [1],
    u"some_data": {u"a": 42}}

multiline_action_task = {
    u"timestamp": 1425356800,
    u"action_status": u"started",
    u"task_uuid": u"f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    u"action_type": u"app:action",
    u"task_level": [1],
    u"message": u"this is a\nmany line message"}
