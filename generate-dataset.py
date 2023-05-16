#!/bin/python

import os
import re
import time
import json
import bz2
import html
from bs4 import BeautifulSoup

def main(dump, output, allowed, verbose):
    print("\nLoading...")
    start_time = time.perf_counter()
    titles = set()
    articles = []
    with open(allowed, "r") as f:
        for line in f:
            line = line.strip()
            titles.add(line)

    print("Starting...")
    with open(output, "w") as output_file:
        first_article = True
        total_size = os.path.getsize(dump)
        current_position = 0
        output_file.write("[")

        try:
            with bz2.open(dump, 'rt') as f:
                line = f.readline()
                while line:
                    if line.startswith("    <title>"):
                        title = line.split("<title>")[1].split("</title>")[0]
                        print(f"[{(f.tell()/total_size)*100:.2f}%] ", end="")

                        if title not in titles:
                            print(f"\033[31m{title}\033[0m")
                            line = f.readline()
                            continue
                        while not line.startswith("      <text"):
                            line = f.readline()

                        if '#REDIRECT' in line:
                            print(f"\033[33m{title}\033[0m")
                            line = f.readline()
                            continue

                        article = ""
                        line = f.readline()
                        while not line.endswith("</text>\n"):
                            article += line
                            line = f.readline()

                        article, size = format_article(article, title)

                        if size < 2000:
                            print(f"\033[34m{title}\033[0m")
                            line = f.readline()
                            continue
                        print(f"\033[32m{title}\033[0m")

                        if not first_article:
                            output_file.write(",")
                        else:
                            first_article = False

                        json.dump(article, output_file, indent=None)

                    line = f.readline()

        except KeyboardInterrupt:
            pass

        finally:
            output_file.write("]")
            print("\nDataset generated.")

def format_article(article, title):
    article = translate_convertions(article)
    article = re.sub("{{(vr|IPA|angbr| )+\|(.*?)}}", r'"\2"', article)
    article = re.sub("{{(vr|IPA|angbr| )+\|/\[\[.*?\|(.*?)\]\]/}}", r'"\2"', article)
    article = re.sub("{{lang(\||\-).*?\|(.*?)}}", r"\2", article)
    article = re.sub("{{Lang-.*?\|(.*?)}}", r"\1", article)
    article = re.sub("''{{transl\|.*?\|(.*?)}}''", r'"\1"', article)
    article = re.sub("{{'(s)?}}", r"'\1", article)
    article = article.replace(" (", "(")
    article = clean_parenthesis(article)
    article = re.sub("\n.*?&lt;(math|code|su(b|p))&gt.*", "", article)
    article = re.sub("&lt;ref(&gt;)?.*?(&lt;)?/ref(&gt;)?", "", article)
    article = html.unescape(article)
    article = BeautifulSoup(article, "html.parser").get_text()
    article = re.sub("\{\{.*(\'\'\'.*?\'\'\').*\}\}", r"\1", article)
    article = re.sub("^(?=.*\'\'\').*\n", "", article)
    article = article.replace("\'\'\'", "")
    article = re.sub("(\n|^)(\*|\_|\{|\}|\||!|&|#|@|;|:|\.| |,|\?|%|\/|\\\\|\[?\[?(File|Image|Category):).*", "", article)
    article = re.sub("\n.*?\[http.*", "", article)
    article = re.sub("\[\[([^\||\]\]]*?)\]\]", r"\1", article)
    article = re.sub("\[\[.*?\|(.*?)\]\]", r"\1", article)
    article = re.sub("\[(.*?)\]", r"\1", article)
    article = re.sub("[ ]+(\.|:|;|,)", r"\1", article)

    article = article.replace("—", "-")
    article = article.replace("–", "-")
    article = article.replace("−", "-")
    article = article.replace("‐", "-")
    article = article.replace("―", "-")
    article = article.replace("’", "'")
    article = article.replace("ʼ", "'")
    article = article.replace("“", "\"")
    article = article.replace("”", "\"")
    article = article.replace("″", "\"")
    article = article.replace("ʻ", "\'")
    article = article.replace("ʻ", "\'")
    article = article.replace("′", "\'")
    article = article.replace("‘", "\'")
    article = article.replace("ˈ", "\'")
    article = article.replace(" ", " ")
    article = article.replace("±", "+/-")
    article = article.replace("а", "a")
    article = article.replace("с", "c")
    article = article.replace("ο", "o")
    article = article.replace("∼", "~")
    article = article.replace("≈", "~")
    article = article.replace("½", "1/2")
    article = article.replace("⅓", "1/3")
    article = article.replace("…", "...")
    article = article.replace("․", ".")
    article = article.replace("∗", "*")

    article = re.sub("\.\.\. ([a-z])", r"\1", article)
    article = re.sub("\.{4,}", "...", article)
    article = re.sub(r'\n.*?([^\x00-\x7F\u0080-\u00FF\u0100-\u017F\u0180-\u024F\u0250-\u02AF\u0300-\u036FΔωστλβμ£€ηδρπαθε]).*', '', article)
    article = article.replace(" [...] ", " ")
    article = article.replace("\'\'\'\'", "")
    article = article.replace("''", "\"")
    article = article.replace('""', '"')
    article = article.replace(',"', '"')
    article = article.replace(". ...", ".")

    article = re.sub("([a-z])\.\"( *[A-Z])", r'\1".\2', article)
    article = re.sub("(.) ,", r"\1,", article)
    article = re.sub("\n.*(:|;|!|\?|,|[A-Za-z0-9]) *(?=\n|$)", "", article)
    article = re.sub("\n[a-z].*", "", article)
    article = re.sub("\n.*((?<!=)=(?!=)|\||\[|\]).*", "", article)
    article = re.sub(" +(\n|$)", r"\1", article)
    article = remove_odd(article)
    article = f"==Definition==\n{article}"
    article = re.sub("[ ]{2,}", " ", article)
    article = re.sub("\n{2,}", "\n", article)
    article = re.sub("\n={2,}[^=]+={2,}\n.{0,300}(?=\n={2,})", "", article, flags=re.DOTALL)
    article = re.sub("(?i)\n={2,}[^\n]*?(link|further reading|sources|references|notes|citations|see also)[^\n]*?={2,}\n.*?(?=\n==|\n?$)", "", article, flags=re.DOTALL)
    article = re.sub("(={2,} ?.* ?={2,}\n+)+(={2,} ?.* ?={2,}\n+|[\n ]*$)", r"\2", article)
    article = re.sub("\n?={2,} ?(.*?) ?={2,}\n", fr'\n\n##### {title}, \1\n', article)
    article = re.sub(r"^\n+#####", "\n\n#####", article)
    article = re.sub(r"\n*$", "", article)

    sections = re.split(f'\n\n##### ([^\n]+)\n', article)
    sections.pop(0)
    result = [{'title': sections[i], 'content': sections[i+1]} for i in range(0, len(sections), 2)]
    return result, len(article)

def clean_parenthesis(string):
    cleaned = []
    nest = 0
    paren_map = {'{': '}', '(': ')'}
    for char in string:
        if char in paren_map:
            nest += 1
        elif char in paren_map.values() and nest > 0:
            nest -= 1
        elif nest == 0:
            cleaned.append(char)
    return ''.join(cleaned)

def remove_odd(input_string: str) -> str:
    lines = input_string.split('\n')
    output_lines = []
    for line in lines:
        quotes = 0
        parens = 0
        for char in line:
            if char == '"':
                quotes += 1
            elif char == "(":
                parens += 1
            elif char == ")":
                parens += 1
        if quotes % 2 == 0 and parens % 2 == 0:
            output_lines.append(line)
    return '\n'.join(output_lines)

def translate_convertions(string):
    value = "([0-9\.,\- /\+x\*×±(by)(to)(and)]+)"
    multiplier = "(y|z|a|f|p|n|µ|m|c|d|da|h|k|M|G|T|P|E|Z|Y|L|S|e6|(U|u)\.?(S|s)\.?)"
    unit = "(in|inche?s?|ft|feet|foot|mi|miles?|yd|yards?|lbs?|gal|floz|oz|oilbbl|carat|°?C|°?F|atm|$|€|£|ha|acres?|t|tonnes?|PS|T|J|W|o|B|iB|D|m|meters?|metres?|min|minutes?|s|sec|seconds?|p?h|hours?|d|days?|g|gf|A|K|mol|cd|L|l|liters?|e?V|J|W|Pa|bar|n|N|psi|AU|ly|lbf|pc|cal|hp|knot|(M|m)ach|cc)"
    pattern = re.compile(f"{{{{((c|C)onvert|cvt) *\| *{value} *\| *((sq)?{multiplier}?{unit}([0-9]*|²?|³?)((/|p|\.)(sq)?{multiplier}?{unit}([0-9]*|²?|³?))?) *(\|.*?}}}}|}}}})")
    converted = re.sub(r"({{((c|C)onvert|cvt) *\|.*?)\|(by|to|and|or|x|×|\-|\+/\-|±|\*)\|(.*?}})", r"\2 \3 \4", string)
#    converted = re.sub(r"({{((c|C)onvert|cvt).*?)(\-change|\(-\))(.*?}})", r"\1\3", converted)
    converted = re.sub(pattern, r"\3 \4", converted)
    converted = re.sub(r"(\n|^).*?{{((c|C)onvert|cvt).*?}}.*", "", converted)
    return converted

# For debugging the regex
#    oldarticle = article
#    diff(article, oldarticle)
def diff(string1, string2):
    differ = Differ()
#    diff = list(differ.compare(string2.split(" "), string1.split(" ")))
    diff = list(differ.compare(string2.splitlines(), string1.splitlines()))
    for line in diff:
#        if line[0] == ' ':
#            print(line[2:])
        if line[0] == '+':
            print(f"\033[92m{line[2:]}\033[0m")
        elif line[0] == '-':
            print(f"\033[91m{line[2:]}\033[0m")

if __name__ == "__main__":
    dump = "wikipedia.bz2"
    output = "dataset.json"
    allowed = "titles.txt"
    verbose = True
    main(dump, output, allowed, verbose)
