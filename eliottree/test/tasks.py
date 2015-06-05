message_task = {
    "task_uuid": "cdeb220d-7605-4d5f-8341-1a170222e308",
    "error": False,
    "timestamp": 1425356700,
    "message": "Main loop terminated.",
    "message_type": "twisted:log",
    "action_type": "nope",
    "task_level": [1]}

action_task = {
    "timestamp": 1425356800,
    "action_status": "started",
    "task_uuid": "f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    "action_type": "app:action",
    "task_level": [1]}

nested_action_task = {
    "timestamp": 1425356900,
    "action_status": "started",
    "task_uuid": "f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    "action_type": "app:action:nested",
    "task_level": [1, 1]}

action_task_end = {
    "timestamp": 1425356800,
    "action_status": "succeeded",
    "task_uuid": "f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    "action_type": "app:action",
    "task_level": [2]}
