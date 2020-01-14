=========
eliottree
=========

|build|_ |coverage|_

Render `Eliot <https://github.com/scatterhq/eliot>`_ logs as an ASCII tree.

This output:

.. image:: https://github.com/jonathanj/eliottree/raw/master/doc/example_eliot_log.png

(or as text)

.. code-block:: bash

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

Command-line options
--------------------

Consult the output of ``eliot-tree --help`` to see a complete list of command-line
options.

Streaming
---------

It's possible to pipe data into eliot-tree, from a tailed log for example, and
have it rendered incrementally. There is a caveat though: Trees are only
rendered once an end message—a success or failure status—for the tree's root
action appears in the data.

Selecting / filtering tasks
---------------------------

By task UUID
~~~~~~~~~~~~

Entire task trees can be selected by UUID with the ``--task-uuid`` (``-u``)
command-line option.

By start / end date
~~~~~~~~~~~~~~~~~~~

Individual tasks can be selected based on their timestamp, use ``--start`` to
select tasks after an ISO8601 date-time, and ``--end`` to select tasks before an
ISO8601 date-time.

By custom query
~~~~~~~~~~~~~~~

Custom task selection can be done with the ``--select`` command-line option, the
syntax of which is `JMESPath`_, and is applied to the original Eliot JSON
structures. Any data that appears within an Eliot task structure can be queried.
Only the matching tasks (and all of their children) will be displayed, the
parents of the task structure (by ``task_uuid``) will be elided.

An important thing to note is that the query should be used as a *predicate* (it
should describe a boolean condition), not to narrow a JSON data structure, as
many of the examples on the JMESPath site illustrate. The reason for this is
that Eliot tasks are not stored as one large nested JSON structure, they are
instead many small structures that are linked together by metadata
(``task_uuid``), which is not a structure than JMESPath is ideally equipped to
query.

The ``--select`` argument can be supplied multiple times to mimic logical AND,
that is all ``--select`` predicates must pass in order for a task or node to be
selected.

.. _JMESPath: http://jmespath.org/

Examples
^^^^^^^^

Select all tasks that contain a ``uri`` key, regardless of its value:

.. code-block:: bash

   --select 'uri'

Select all Eliot action tasks of type ``http_client:request``:

.. code-block:: bash

   --select 'action_type == `"http_client:request"`'

Backquotes are used to represent raw JSON values in JMESPath, ```500``` is the
number 500, ```"500"``` is the string "500".

Select all tasks that have an ``http_status`` of 401 or 500:

.. code-block:: bash

   --select 'contains(`[401, 500]`, status)'

Select all tasks that have an ``http_status`` of 401 that were also made to a
``uri`` containing the text ``/criticalEndpoint``:

.. code-block:: bash

   --select 'http_status == `401`' \
   --select 'uri && contains(uri, `"/criticalEndpoint"`)'

Here ``--select`` is passed twice to mimic a logic AND condition, it is also
possible to use the JMESPath ``&&`` operator. There is also a test for the
existence of the ``uri`` key to guard against calling the ``contains()``
function with a null subject.

See the `JMESPath specification`_ for more information.

.. _JMESPath specification: http://jmespath.org/specification.html


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
The config file can be passed with the ``--config`` argument, or will be read from
``~/.config/eliot-tree/config.json``. See `config.example.json`_ for an
example.

Use the ``--show-default-config`` command-line option to display the default
configuration, suitable for redirecting to a file. Use the
``--show-current-config`` command-line option to display the current effective
configuration.

.. _\_cli.py: https://github.com/jonathanj/eliottree/blob/master/src/eliottree/_cli.py
.. _config.example.json: https://github.com/jonathanj/eliottree/blob/master/config.example.json

Theme overrides
~~~~~~~~~~~~~~~

Theme colors can be overridden via the ``theme_overrides`` key in the config file.
The value of this key is itself a JSON object, each key is the name of a theme
color and each value is a JSON list. This list should contain three values:

1. Foreground color, terminal color name or code; or ``null`` for the default color.
2. Background color, terminal color name or code; or ``null`` for the default color.
3. An optional array of color attribute names or codes; or ``null`` for the
   default attribute.

For example, to override the ``root`` theme color to be bold magenta, and the
``prop`` theme color to be red:

.. code-block:: json

   {
     "theme_overrides": {
       "root": ["magenta", null, ["bold"]],
       "prop_key": ["red"]
     }
   }

See `_theme.py`_ for theme color names and the `colored`_ Python package for
available color and attribute constants.

.. _\_theme.py: https://github.com/jonathanj/eliottree/blob/master/src/eliottree/_theme.py
.. _colored: https://pypi.org/project/colored/

Contribute
----------

See <https://github.com/jonathanj/eliottree> for details.


.. |build| image:: https://travis-ci.org/jonathanj/eliottree.svg?branch=master
.. _build: https://travis-ci.org/jonathanj/eliottree

.. |coverage| image:: https://coveralls.io/repos/jonathanj/eliottree/badge.svg
.. _coverage: https://coveralls.io/r/jonathanj/eliottree
