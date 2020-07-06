# Introduction

## The main goal
This project access for the serial port and It is able to script control.

## Installation

```
pip install macross-serial
```

### For developers

```
git clone git@github.com:rondou/macross-serial.git
cd macross-serial
poetry install
```

## Usage

### Access for the serial port and run script.

```
macross-serial run [--repeat N] <port-name> <macro-file>
```

### Show serail port name.

```
macross-serial list-port
```

## Macro file format

```
<method>	<content>	[<timeout-second>	[progress-message]]
```

### Simple example

`script.tsv`

```tsv
wait_for_str	'system started at UTC'
send	'account\n'
send	'password\n'
wait_for_regex	r'\b(([0-9A-Fa-f]{2}:){5})\b'
send	'reboot\n'
```

### Methods

#### send

Write data to serial port

E.g.

```
send	'poweroff\n'
```

#### wait_for_str

Waiting until for find out a specific string then continue to execute next step.

E.g.

```
wait_for_str	'system started at UTC'
```

#### wait_for_regex

Waiting until for find out a regular expression pattern then continue to execute next step.

E.g.

```
wait_for_regex	r'\b(([0-9A-Fa-f]{2}:){5})\b'
```

#### wait_for_second

Wait/sleep/pause for N seconds.

E.g.

```
wait_for_second	10
```
