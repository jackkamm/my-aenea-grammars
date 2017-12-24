from natlink import setMicState
import aenea
from aenea import (
    Grammar,
    MappingRule,
    Rule,
    Text,
    Key,
    Function,
    Dictation,
    Choice,
    Window,
    Config,
    Section,
    Item,
    IntegerRef,
    Alternative,
    RuleRef,
    Repetition,
    CompoundRule,
    AppContext,
)

from dragonfly.actions.keyboard import keyboard
from dragonfly.actions.typeables import typeables
if 'semicolon' not in typeables:
    typeables["semicolon"] = keyboard.get_typeable(char=';')


class _KeystrokeRule(MappingRule):
    exported = False
    mapping = {
        # motions
        "up": "up",
        "down": "down",
        "right": "right",
        "left": "left",
        "page up": "pgup",
        "page down": "pgdown",
        "home": "home",
        "end": "end",
        "scape": "escape",
        "tab": "tab",
        "scratch": "backspace",

        # shortcuts for vim style motion
        "drop": "c-d",
        "(gopa|go up|gope)": "c-u",
        "scroll up": "c-y",
        "scroll down": "c-e",

        # special characters
        "space": "space",
        "slap": "enter",
        "bang": "bang",  # !
        "atta": "at",  # @
        "hash": "hash",  # #
        "(dollar|doll)": "dollar",  # $
        "percent": "percent",
        "caret": "caret",
        "star": "asterisk",
        "lepa": "lparen",
        "repa": "rparen",
        "(minus|hyphen)": "minus",
        "underscore": "underscore",
        "plus": "plus",
        "backtick": "backtick",
        "tilde": "tilde",
        "lacket": "lbracket",
        "racket": "rbracket",
        "lace": "lbrace",
        "race": "rbrace",
        "backslash": "backslash",
        "bit and": "ampersand",
        "bit or": "bar",
        "colon": "colon",
        "semicolon": "semicolon",
        "apostrophe": "squote",
        "quote": "dquote",
        "comma": "comma",
        "dot": "dot",
        "slash": "slash",
        "langle": "langle",
        "rangle": "rangle",
        "question": "question",
        "(equal|equals)": "equal",

        # letters
        "archie": "a",
        "(bravo)": "b",
        "(charlie)": "c",
        "(delta)": "d",
        "(echo)": "e",
        "(foxtrot|fox)": "f",
        "(gang|gamma)": "g",
        "(hotel)": "h",
        "(indy)": "i",
        "(juliet|julie)": "j",
        "(kilo)": "k",
        "(lima)": "l",
        "(mike|mama)": "m",
        "(november|nova)": "n",
        "(oscar)": "o",
        "(poppa|pop|papa)": "p",
        "(quiche|queen)": "q",
        "(romeo|roma)": "r",
        "(sierra|south|sigma|sig)": "s",
        "(tango)": "t",
        "(uniform|uncle)": "u",
        "(victor)": "v",
        "(whiskey)": "w",
        "(x-ray)": "x",
        "(yankee)": "y",
        "(zulu) ": "z",

        # digits
        "zero": "0",
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
    }


class _ModifierRule(MappingRule):
    exported = False
    mapping = {
        "troll": "c",
        "alter": "a",
        "super": "w",
        "(shift|big)": "s",
    }


class KeystrokeRule(CompoundRule):
    spec = "[<mod1>] [<mod2>] <keystroke> [(twice|thrice|<n> ice)]"
    extras = [
        RuleRef(name="keystroke", rule=_KeystrokeRule()),
        RuleRef(name="mod1", rule=_ModifierRule(name="m1")),
        RuleRef(name="mod2", rule=_ModifierRule(name="m2")),
        IntegerRef("n", 1, 100)
    ]
    defaults = {"n": 1}

    def value(self, node):
        root = node.children[0].children[0]
        mod1 = root.children[0].value()
        mod2 = root.children[1].value()
        stroke = root.children[2].value()
        times = root.children[3].value()
        mod = ""
        if mod1:
            mod += mod1
        if mod2:
            mod += mod2
        if mod:
            stroke = "{}-{}".format(mod, stroke)
        stroke = Key(stroke)
        if times == "twice":
            times = 2
        elif times == "thrice":
            times = 3
        elif times:
            times = times[0]
        else:
            times = 1
        return stroke * times


class EmacsCommandRule(MappingRule):
    exported = False
    mapping = {
        "quit":
        Key("c-g"),
        "altex":
        Key("a-x"),
        # use M-: instead of M-x because helm-M-x requires delay
        "find file":
        Key("a-colon") + Text("(call-interactively 'helm-find-files)") +
        Key("enter"),
        "helm swoop":
        Key("a-colon") + Text("(call-interactively 'helm-swoop)") +
        Key("enter"),
        # TODO replace with M-x command
        "buffer list":
        Key("a-m , b , b"),
        "save buffer":
        Key("a-m , f , s"),
        "avy word":
        Key("a-m , j, w"),
        # TODO evil-easymotion, macro, "todo"
    }


class FormatMapping(MappingRule):
    exported = False
    mapping = {
        "say": aenea.format.format_natword,
        "snake": aenea.format.format_score,
        "studley": aenea.format.format_proper,
        "camel": aenea.format.format_camel,
        "jumble": aenea.format.format_jumble,
        "dotword": aenea.format.format_dotword,
        "dashword": aenea.format.format_dashword,
        "sentence": aenea.format.format_sentence,
    }


dictation = Dictation(name="dictation")


class MyFormatRule(CompoundRule):
    spec = "<format_rule> <dictation>"
    extras = [
        RuleRef(name="format_rule", rule=FormatMapping()),
        dictation,
    ]

    def value(self, node):
        root = node.children[0].children[0]
        format_rule = root.children[0].value()
        dictation = root.children[1].value()
        # TODO need to remove hyphens? see aenea-grammars/_multiedit.py
        words = dictation.format().lower().split()
        return Text(format_rule(words))


my_format_rule = RuleRef(name="my_format_rule", rule=MyFormatRule())


class MyLiteralRule(CompoundRule):
    """Rule for saying MyFormatRule literally (without interruptions by other rules)"""
    spec = "literal <my_format_rule>"
    extras = [my_format_rule]

    def _process_recognition(self, node, extras):
        extras["my_format_rule"].execute()


alternatives = []
alternatives.append(my_format_rule)
alternatives.append(RuleRef(rule=KeystrokeRule()))
alternatives.append(RuleRef(rule=EmacsCommandRule()))
single_action = Alternative(alternatives)

sequence = Repetition(single_action, min=1, max=16, name="sequence")


# TODO add repeating element
class RepeatRule(CompoundRule):
    # Here we define this rule's spoken-form and special elements.
    # TODO finish with format_rule?
    spec = "<sequence>"
    extras = [
        sequence,  # Sequence of actions defined above.
    ]

    def _process_recognition(self, node, extras):  # @UnusedVariable
        sequence = extras["sequence"]  # A sequence of actions.
        for action in sequence:
            action.execute()


repeat_rule = RepeatRule(name="repeat_rule")

grammar = Grammar("Generic edit")
grammar.add_rule(repeat_rule)  # Add the top-level rule.
grammar.add_rule(MyLiteralRule(name="literal_rule"))  # Add the top-level rule.
grammar.load()  # Load the grammar.


# Unload function which will be called at unload time.
def unload():
    global grammar
    if grammar:
        grammar.unload()
    grammar = None
