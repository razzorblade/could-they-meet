

# could-they-meet
Wikipedia Python parser to determine, whether two persons could meet (based on their birth and death dates)

Application requires you to have exported persons from wikipedia. Some exports are available in `data/dump_export.txt`, but if you want to run your own exports on different data splits, check wiki parser and wiki splitter below. If not, go straight to person search.

# How to run wiki parser

1. Make sure you have unzipped .xml file of wikipedia. 
2. Go to could-they-meet/src/
3. Run
```sh
> python main.py --input path/wikipedia.xml --output path/export.txt
```

You can track progress of current parsing state in console using --verbose
```sh
> python main.py --input path/wikipedia.xml --output path/export.txt --verbose
Parser started on 3.85 GiB of data.
Progress: [====                ] 20.58%
```

# How to run wiki splitter

1. Make sure you have unzipped .xml file of wikipedia. 
2. Go to could-they-meet/src/
3. Run
```sh
> python main.py --splitter SIZE --input path/wikipedia.xml --output path/dump_split.xml
```
Size must be specified in bytes. For example `python main.py --splitter 2000000000 --input path/wikipedia.xml --output path/dump_split.xml`, will export 2GB of data into file dump_export.xml. The final size may be different from requested size, because splitter is also correctly ending `<page>` so there won't be any data without corresponding ending tags.

# How to run person search
1. Make sure you have file with exported people. You can download one from `data/dump_export.txt`.
2. Go to could-they-meet/src/
3. Run

```sh
> python main.py --search --input path/dump_export.txt
Enter name of first person:  Albert Einstein
Enter name of second person: Elvis Presley
```
