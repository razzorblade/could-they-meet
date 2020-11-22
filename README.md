# could-they-meet
Wikipedia Python parser to determine, whether two persons could meet (based on their birth and death dates)


# How to run

1. Clone the project. Go to could-they-meet/src folder.
2. Make sure you have unzipped .xml file of wikipedia. 
3. Run
```sh
> python main.py -dump path/to/wikipedia_dump.xml
```

You can track progress of current parsing state in console using --verbose
```sh
> python main.py -dump path/to/wikipedia_dump.xml --verbose
Parser started on 3.85 GiB of data.
Progress: [====                ] 20.58%
```
