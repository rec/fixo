# fixo

## Goals.

* Light weight, semi-automatic rule-based tool to add type annotations to Python code bases.

* Apply rule-based edits, and allow the user to pick and choose which edits to accept.

* Edits are not represented as raw diffs, but as semantic changes to the Python source, which are far more likely to be stable through intermediate changes in the code.

* The rules to match code and to perform edits can easily be user code.

* Less than 1k lines of code with testing.

## Design sketch

The input to the program would be the output of some other diagnostic tool, like pyrefly or mypy, outputs that are divided into _messages_, one complete message from the diagnostic tool to the user. In pyrefly it can just be a single line of text.

A message has a _file name_, a _symbol name_, and a _line number_, a _column number_ for the _start_ and _end_ of position in the file.

For each message in the input, and for each rule that that message matches, the rule creates a proposed edit to the message's file, and then writes that edit as a line of JSON into the "edits file"

The user chooses selects which edits to use, initially by just editing the edits file, and soon with a little terminal interface that displays the proposed change in context of the Python source file.

Then the edits file is applied to the code base all at once.

## How to write it?

Four main parts need to be written:

1. Parsing the inputs into messages
2. Matching messages against rules
3. Creating an edit from a rule and a matching message
4. Performing an edit

The hard part: it must easy be for developers to create and perform edits without knowing how to parse a Python file

## As of October 1

All the fundamental classes exist and some tests of the trickiest parts of their functionality too - it mostly corresponds to the above.

Now we embark on three specific rules to apply to PyTorch

1. Add a `bool` return type annotation to methods and functions that start with `_?(is|has)_`
2. Add a `bool` type annotation to parameters that start with `(is|has)_`
3. Add a `torch.Tensor` type annotation to function (but not method) parameters named `self`
