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

Command-line options
--------------------

Consult the output of `eliot-tree --help` to see a complete list of command-line
options.

Programmatic usage
------------------

.. code-block:: python

   import json, sys
   from eliottree import tasks_from_iterable, render_tasks
   # Or `codecs.getwriter('utf-8')(sys.stdout).write` on Python 2.
   render_tasks(sys.stdout.write, tasks, colorize=True)

See :code:`help(render_tasks)` and :code:`help(tasks_from_iterable)` from a
Python REPL for more information.

Configuration
-------------

Command-line options may have custom defaults specified by way of a config file.
The config file can be passed with the `--config` argument, or will be read from
`~/.config/eliot-tree/config.json`. See `config.example.json`_ for an
example.

.. _config.example.json: https://github.com/jonathanj/eliottree/blob/master/config.example.json

Theme overrides
~~~~~~~~~~~~~~~

Theme colors can be overridden via the `theme_overrides` key in the config file.
The value of this key is itself a JSON object, each key is the name of a theme
color and each value is a JSON list. This list should contain two values:

1. A string that is a known terminal color.
2. An optional list of color attributes.

For example, to override the `root` theme color to be bold magenta, and the
`prop` theme color to be red:

.. code-block:: json

   {
     "theme_overrides": {
       "root": ["magenta", ["bold"]],
       "prop": ["red"]
     }
   }

See `_theme.py`_ for theme color names and the `termcolor`_ Python package for
available color and attribute constants.

.. _\_theme.py: https://github.com/jonathanj/eliottree/blob/master/src/eliottree/_theme.py
.. _termcolor: https://pypi.org/project/termcolor/

Contribute
----------

See <https://github.com/jonathanj/eliottree> for details.


.. |build| image:: https://travis-ci.org/jonathanj/eliottree.svg?branch=master
.. _build: https://travis-ci.org/jonathanj/eliottree

.. |coverage| image:: https://coveralls.io/repos/jonathanj/eliottree/badge.svg
.. _coverage: https://coveralls.io/r/jonathanj/eliottree
