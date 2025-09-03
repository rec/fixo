# fixo goals

Light weight, semi-automatic rule-based editing of Python code bases,

Apply rule-based edits to Python code bases, and allow the user to pick and choose which edits to accept.

Edits are not represented as raw diffs, but as semantic changes to the Python source, which are far more likely to be stable through intermediate changes in the code.

The rules to match code and to perform edits can easily be user code.

Less than 1k lines of code with testing.

## Design sketch


The input to the program would be the output of some other diagnostic tool, like pyrefly or mypy, outputs that are divided into _messages_, one complete message from the diagnostic tool to the user. In pyrefly it can just be a single line of text. 

A message has a _file name_, a _line number_ and perhaps a _column number_.

For each message in the input, and for each rule that that message matches, the rule creates a proposed edit to the message's file, and then writes that edit as a line of JSON into the "edits file"

The user chooses selects which edits to use, initially by just editing the edits file, and soon with a little terminal interface that displays the proposed change in context of the Python source file.

Then the edits file is applied to the code base all at once.

## How to write it?

The four main parts that need to be written are:

1. Parsing the inputs into messages
2. Matching messages against rules
3. Creating an edit from a rule and a matching message
4. Performing an edit

Parts 1 and 2 routine and won't be further discussed. But it must be easy for developers to create and perform edits without knowing how to parse a Python file.

Both 3 and 4 rely on existing code from the [PyTorch linters](https://github.com/pytorch/pytorch/tree/main/tools/linter/adapters/_linter) which divides code into named `Block`s, where each `Block` represents either a `class`, or a function `def` definition, or a whole file - a Python scope, in other words.


