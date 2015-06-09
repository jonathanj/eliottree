=========
eliottree
=========

|build|_ |coverage|_

Render `Eliot <https://github.com/ClusterHQ/eliot>`_ logs as an ASCII tree.

This output:

.. code-block::

   $ eliot-tree < eliot.log
   f3a32bb3-ea6b-457c-aa99-08a3d0491ab4
       +-- app:soap:client:request@1/started
           |-- dump: /home/user/dump_files/20150303/1425356936.28_Client_req.xml
           |-- soapAction: a_soap_action
           |-- timestamp: 2015-03-03 06:28:56.278875
           `-- uri: http://example.org/soap
       +-- app:soap:client:success@2,1/started
           `-- timestamp: 2015-03-03 06:28:57.516579
           +-- app:soap:client:success@2,2/succeeded
               |-- dump: /home/user/dump_files/20150303/1425356937.52_Client_res.xml
               `-- timestamp: 2015-03-03 06:28:57.517077
       +-- app:soap:client:request@3/succeeded
           |-- status: 200
           `-- timestamp: 2015-03-03 06:28:57.517161

   89a56df5-d808-4a7c-8526-e603aae2e2f2
       +-- app:soap:service:request@1/started
           |-- dump: /home/user/dump_files/20150303/1425357068.03_Service_req.xml
           |-- soapAction: method
           |-- timestamp: 2015-03-03 06:31:08.032091
           `-- uri: /endpoints/soap/method
       +-- app:soap:service:success@2,1/started
           `-- timestamp: 2015-03-03 06:31:11.512330
           +-- app:soap:service:success@2,2/succeeded
               |-- dump: /home/user/dump_files/20150303/1425357071.51_Service_res.xml
               `-- timestamp: 2015-03-03 06:31:11.513453
       +-- app:soap:service:request@3/succeeded
           |-- status: 200
           `-- timestamp: 2015-03-03 06:31:11.513992

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

Usage
-----

.. code-block::

   usage: eliot-tree [-h] [-u UUID] [-i KEY] [--raw] [-l LENGTH] [--select QUERY]
                     [FILE [FILE ...]]

   Display an Eliot log as a tree of tasks.

   positional arguments:
     FILE                  Files to process

   optional arguments:
     -h, --help            show this help message and exit
     -u UUID, --task-uuid UUID
                           Select a specific task by UUID
     -i KEY, --ignore-task-key KEY
                           Ignore a task key, use multiple times to ignore
                           multiple keys. Defaults to ignoring most Eliot
                           standard keys.
     --raw                 Do not format some task values (such as timestamps) as
                           human-readable
     -l LENGTH, --field-limit LENGTH
                           Limit the length of field values to LENGTH or a
                           newline, whichever comes first. Use a length of 0 to
                           output the complete value.
     --select QUERY        Select tasks to be displayed based on a jmespath
                           query, can be specified multiple times to mimic
                           logical AND. If any child task is selected the entire
                           top-level task is selected. See <http://jmespath.org/>

Contribute
----------

See <https://github.com/jonathanj/eliottree> for details.


.. |build| image:: https://travis-ci.org/jonathanj/eliottree.svg?branch=16-refactor-into-library
.. _build: https://travis-ci.org/jonathanj/eliottree

.. |coverage| image:: https://coveralls.io/repos/jonathanj/eliottree/badge.svg
.. _coverage: https://coveralls.io/r/jonathanj/eliottree
