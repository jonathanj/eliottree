=========
eliottree
=========

|build|_ |coverage|_

Render `Eliot <https://github.com/scatterhq/eliot>`_ logs as an ASCII tree.

This output:

.. image:: https://github.com/jonathanj/eliottree/raw/18.1.0/doc/example_eliot_log.png

(or as text)

.. code-block::

   $ eliot-tree eliot.log
   f3a32bb3-ea6b-457c-aa99-08a3d0491ab4
   └── app:soap:client:request/1 ⇒ started 2015-03-03 04:28:56 ⧖ 1.238s
       ├── dump: /home/user/dump_files/20150303/1425356936.28_Client_req.xml
       ├── soapAction: a_soap_action
       ├── uri: http://example.org/soap
       ├── app:soap:client:success/2/1 ⇒ started 2015-03-03 04:28:57 ⧖ 0.000s
       │   └── app:soap:client:success/2/2 ⇒ succeeded 2015-03-03 04:28:57
       │       └── dump: /home/user/dump_files/20150303/1425356937.52_Client_res.xml
       └── app:soap:client:request/3 ⇒ succeeded 2015-03-03 04:28:57
           └── status: 200

    89a56df5-d808-4a7c-8526-e603aae2e2f2
    └── app:soap:service:request/1 ⇒ started 2015-03-03 04:31:08 ⧖ 3.482s
        ├── dump: /home/user/dump_files/20150303/1425357068.03_Service_req.xml
        ├── soapAction: method
        ├── uri: /endpoints/soap/method
        ├── app:soap:service:success/2/1 ⇒ started 2015-03-03 04:31:11 ⧖ 0.001s
        │   └── app:soap:service:success/2/2 ⇒ succeeded 2015-03-03 04:31:11
        │       └── dump: /home/user/dump_files/20150303/1425357071.51_Service_res.xml
        └── app:soap:service:request/3 ⇒ succeeded 2015-03-03 04:31:11
            └── status: 200

was generated from:

.. code-block:: javascript

   {"dump": "/home/user/dump_files/20150303/1425356936.28_Client_req.xml", "timestamp": 1425356936.278875, "uri": "http://example.org/soap", "action_status": "started", "task_uuid": "f3a32bb3-ea6b-457c-aa99-08a3d0491ab4", "action_type": "app:soap:client:request", "soapAction": "a_soap_action", "task_level": [1]}
   {"timestamp": 1425356937.516579, "task_uuid": "f3a32bb3-ea6b-457c-aa99-08a3d0491ab4", "action_type": "app:soap:client:success", "action_status": "started", "task_level": [2, 1]}
   {"task_uuid": "f3a32bb3-ea6b-457c-aa99-08a3d0491ab4", "action_type": "app:soap:client:success", "dump": "/home/user/dump_files/20150303/1425356937.52_Client_res.xml", "timestamp": 1425356937.517077, "action_status": "succeeded", "task_level": [2, 2]}
   {"status": 200, "task_uuid": "f3a32bb3-ea6b-457c-aa99-08a3d0491ab4", "task_level": [3], "action_type": "app:soap:client:request", "timestamp": 1425356937.517161, "action_status": "succeeded"}
   {"dump": "/home/user/dump_files/20150303/1425357068.03_Service_req.xml", "timestamp": 1425357068.032091, "uri": "/endpoints/soap/method", "action_status": "started", "task_uuid": "89a56df5-d808-4a7c-8526-e603aae2e2f2", "action_type": "app:soap:service:request", "soapAction": "method", "task_level": [1]}
   {"timestamp": 1425357071.51233, "task_uuid": "89a56df5-d808-4a7c-8526-e603aae2e2f2", "action_type": "app:soap:service:success", "action_status": "started", "task_level": [2, 1]}
   {"task_uuid": "89a56df5-d808-4a7c-8526-e603aae2e2f2", "action_type": "app:soap:service:success", "dump": "/home/user/dump_files/20150303/1425357071.51_Service_res.xml", "timestamp": 1425357071.513453, "action_status": "succeeded", "task_level": [2, 2]}
   {"status": 200, "task_uuid": "89a56df5-d808-4a7c-8526-e603aae2e2f2", "task_level": [3], "action_type": "app:soap:service:request", "timestamp": 1425357071.513992, "action_status": "succeeded"}

Streaming
---------

It's possible to pipe data into eliot-tree, from a tailed log for example, and
have it rendered incrementally. There is a caveat though: Trees are only
rendered once an end message—a success or failure status—for the tree's root
action appears in the data.

Usage from Python
-----------------

.. code-block:: python

   import json, sys
   from eliottree import tasks_from_iterable, render_tasks
   # Or `codecs.getwriter('utf-8')(sys.stdout).write` on Python 2.
   render_tasks(sys.stdout.write, tasks, colorize=True)

See :code:`help(render_tasks)` and :code:`help(tasks_from_iterable)` from a
Python REPL for more information.

Usage from the command-line
---------------------------

.. code-block::

   $ eliot-tree
   usage: eliot-tree [-h] [-u UUID] [-i KEY] [--raw]
                     [--color {always,auto,never}] [--no-colorize] [-l LENGTH]
                     [--select QUERY] [--start START] [--end END]
                     [FILE [FILE ...]]

   Display an Eliot log as a tree of tasks.

   positional arguments:
     FILE                  Files to process. Omit to read from stdin.

   optional arguments:
     -h, --help            show this help message and exit
     -u UUID, --task-uuid UUID
                           Select a specific task by UUID
     -i KEY, --ignore-task-key KEY
                           Ignore a task key, use multiple times to ignore
                           multiple keys. Defaults to ignoring most Eliot
                           standard keys.
     --raw                 Do not format some task values (such as UTC
                           timestamps) as human-readable
     --color {always,auto,never}
                           Color the output. Defaults based on whether the output
                           is a TTY.
     -l LENGTH, --field-limit LENGTH
                           Limit the length of field values to LENGTH or a
                           newline, whichever comes first. Use a length of 0 to
                           output the complete value.
     --select QUERY        Select tasks to be displayed based on a jmespath
                           query, can be specified multiple times to mimic
                           logical AND. If any child task is selected the entire
                           top-level task is selected. See <http://jmespath.org/>
     --start START         Select tasks whose timestamp occurs after (or on) an
                           ISO8601 date.
     --end END             Select tasks whose timestamp occurs before an ISO8601
                           date.

Contribute
----------

See <https://github.com/jonathanj/eliottree> for details.


.. |build| image:: https://travis-ci.org/jonathanj/eliottree.svg?branch=master
.. _build: https://travis-ci.org/jonathanj/eliottree

.. |coverage| image:: https://coveralls.io/repos/jonathanj/eliottree/badge.svg
.. _coverage: https://coveralls.io/r/jonathanj/eliottree
