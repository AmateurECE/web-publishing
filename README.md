# Web Publishing Scripts for LaTeX Files

This package provides a few Python scripts that can be used to generate
static website files using `htlatex` and Middleman. To get started, install
this package using pip:

```
python3 -m pip install --index-url=https://edtwardy.hopto.org:443/pypi --user \
    web-publishing
```

Then, add a `makefile_config.py` file, which contains configuration for the
scripts. This file allows for the following keys:

* PAGE\_DATA: This can be used to add additional page data to the yaml header
  in the ERB template files. The keys are paths of generated html files, the
  values are dicts which contain key/value pairs for data to add.
* INDEX: The path of the latex file which generates the index.html.
* BOOK\_MAIN: The latex file that imports all subfiles for the totality of the
  book.
* BOOK\_EXCLUDE: A list of files that won't be included in the book, so don't
  warn if we find they're not in the book.
* BUILD\_EXCLUDE: A list of files to exclude entirely from the makefile.

An example is given below, which I use to generate the content of one of my
websites:

```
PAGE_DATA = {
    'Professional/Resume-Style1.html': {'stylesheet': 'resume'},
    'Professional/Resume-Style2.html': {'stylesheet': 'resume'},
}

INDEX = 'Introduction.tex'

BOOK_MAIN = 'BookMain.tex'
BOOK_OUTPUT = os.path.join('pdf', 'EthanRepository.pdf')
BOOK_EXCLUDE = [
    'Professional/Resume-Style1.tex',
    'Professional/Resume-Style2.tex',
    'Professional/InterviewQuestions.tex',
    'Projects/HDMIDeviceDelegate.tex',
]

BUILD_EXCLUDE = [
    'Processes/Ripping.tex',
]
```

Finally, generate the makefile, and `make`:

```
$ wp-genmakefile
$ make
```
