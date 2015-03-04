# eliottree

Render [Eliot](https://github.com/ClusterHQ/eliot) logs as an ASCII tree.

```shell
$ python eliottree.py < eliot.log
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
```

## Usage

```
usage: eliottree.py [-h] [-u UUID] [-i KEY] [--raw] [FILE [FILE ...]]

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
```

## Contribute

See <https://github.com/jonathanj/eliottree> for details.