HCC Swanson Tool1 Prototype 12/9/2012

The following are some general guidlines for the usage of Tool1 of the black
mamba system.  Tool1 is a tool designed to provided a graphical representation 
of a root file.  It allows a user to view the branches contained within a file
relative to one another in the file layout.

The tool allows for the saving of the graphics to an output image or
interactive display.  It also allows for the filtering of which branches to
display from a given tree.

To use this tool it is necessary to have both matplotlib and pyRoot installed
and prepared for usage.

The following is the uasage for the tool

-------------------------------------------------
Usage: HCCTool1.py [options]

Options:
  -h, --help            show this help message and exit
  -f FILE, --file=FILE  ROOT file to graph
  -t TREENAME, --tree=TREENAME
                        Tree to parse
  -d, --display         Show interactive matplotlib display
  -o OUTPUT, --output_file=OUTPUT
                        The name of the output file
  -l, --list_trees      List the available trees in file
  -r BRANCHREGEX, --branch_regex=BRANCHREGEX
                        Regular expression to filter out branches


-------------------------------------------------

Here is a quick rundown of the all the options required and not:

-f File name.  This is required and is the root file which is going to be
parsed.

-t Required if not a listing of trees in file.  This is the tree which will be
parsed and displayed on the file layout graph.

-l This option will cause the program to simply print out a list of trees
contained in the file.

-d Display the interactive matplotlib gui of the file layout graph

-o Name of the output file.  This will overide the default name which is
simply the name of the root file with .png appended to it.

-r Branch Regular expression. Display only branches with names that match the
given regular expression.  The regular expression can be any valid python
regular expression.  For more information on regular expressions visit:
http://docs.python.org/2/library/re.html

-------------------------------------------------

The graph has the following layout:
    When no filter is applied every branch is supplied with a different color.
At the current moment no legend is available but should be availabe in the
future.  When a filter is applied all branches will be colored black.  In the
graphics each MB within the file is contained on a sperate line along the
yaxis.  Along the x axis is the blocks in the file layed out by KB within the
MB.  

Improvements in perfomance and graphics will be made on this prototype during
the second semester. 
