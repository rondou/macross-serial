Introduction
-----------

The main goal
````````````
This project access for the serial port and It is able to script control.

Installation
```````````

.. code:: sh

    pip install git+git://github.com/rondou/macross-serial.git

or

.. code:: sh

    pipenv install 'git+ssh://git@github.com/rondou/macross-serial.git#egg=macross-serial'

Usage
````````````

Show serail port name.

.. code:: sh

  macross-serial listport
  
Access for the serial port and run script.

.. code:: sh

  macross-serial run --port=<port name> --script=<script file path>
  
Script 
````````````

Simple example
............

script.tsv

.. code:: tsv

  wait_for_str  'system started at UTC'
  send  'account\n'
  send	'password\n'
  wait_for_regex    r'\b(([0-9A-Fa-f]{2}:){5})\b'

method
............

send
::::::::::::

send	'ls -l\n'
