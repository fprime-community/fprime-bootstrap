import sys

invalid_characters = [
        "#",
        "%",
        "&",
        "{",
        "}",
        "/",
        "\\",
        "<",
        ">",
        "*",
        "?",
        " ",
        "$",
        "!",
        "'",
        '"',
        ":",
        "@",
        "+",
        "`",
        "|",
        "=",
]
for char in "{{ cookiecutter.project_name }}":
    if char in invalid_characters:
        print("[ERROR]: Invalid character in project name: {}".format(char))
        sys.exit(1)