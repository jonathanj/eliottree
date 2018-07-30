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
    u"action_type": u"app:action:nest",
    u"task_level": [1, 1]}

action_task_end = {
    u"timestamp": 1425356802,
    u"action_status": u"succeeded",
    u"task_uuid": u"f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    u"action_type": u"app:action",
    u"task_level": [2]}

action_task_end_failed = {
    u"timestamp": 1425356804,
    u"action_status": u"failed",
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

list_action_task = {
    u"timestamp": 1425356800,
    u"action_status": u"started",
    u"task_uuid": u"f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    u"action_type": u"app:action",
    u"task_level": [1],
    u"some_data": [u"a", u"b"]}

multiline_action_task = {
    u"timestamp": 1425356800,
    u"action_status": u"started",
    u"task_uuid": u"f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    u"action_type": u"app:action",
    u"task_level": [1],
    u"message": u"this is a\nmany line message"}

janky_action_task = {
    u"timestamp": '1425356800\x1b(0',
    u"action_status": u"started",
    u"task_uuid": u"f3a32bb3-ea6b-457c-\x1b(0aa99-08a3d0491ab4",
    u"action_type": u"A\x1b(0",
    u"task_level": [1],
    u"mes\nsage": u"hello\x1b(0world",
    u"\x1b(0": {u"\x1b(0": "nope"}}

janky_message_task = {
    u"task_uuid": u"cdeb220d-7605-4d5f-\x1b(08341-1a170222e308",
    u"er\x1bror": False,
    u"timestamp": 1425356700,
    u"mes\nsage": u"Main loop\x1b(0terminated.",
    u"message_type": u"M\x1b(0",
    u"task_level": [1]}

missing_uuid_task = {
    u"error": False,
    u"timestamp": 1425356700,
    u"message": u"Main loop terminated.",
    u"message_type": u"twisted:log",
    u"action_type": u"nope",
    u"task_level": [1]}
