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
    exported=False
    mapping={
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

        # special characters
        "space": "space",
        "slap": "enter",
        "bang": "bang", # !
        "atta": "at", # @
        "hash": "hash", # #
        "(dollar|doll)": "dollar", # $
        "percent": "percent",
        "caret": "caret",
        "ampers": "and",
        "star": "star",
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
        "(bar|pipe)": "bar",
        "colon": "colon",
        "semicolon": "semicolon",
        "(single quote|apostrophe)": "squote",
        "quote": "dquote",
        "comma": "comma",
        "dot": "dot",
        "slash": "slash",
        "langle": "langle",
        "rangle": "rangle",
        "question": "question",
        "(equal|equals)": "equal",

        # letters
        "(alpha|alef)": "a",
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
    exported=False
    mapping={
        "troll": "c",
        "alter": "a",
        "super": "w",
        "shift": "s",
    }

class KeystrokeRule(CompoundRule):
    spec = "[<mod1>] [<mod2>] <keystroke> [<n> times]"
    extras = [RuleRef(name="keystroke", rule=_KeystrokeRule()),
              RuleRef(name="mod1", rule=_ModifierRule(name="m1")),
              RuleRef(name="mod2", rule=_ModifierRule(name="m2")),
              IntegerRef("n",1,100)]
    defaults = {"n":1}

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
        ret = stroke
        if times:
            times = times[0]
            for _ in range(times-1):
                ret = ret + stroke
        return ret


class EmacsCommandRule(MappingRule):
    exported=False
    mapping = {
        "quit": Key("c-g"),
        "drop": Key("c-d"),
        "(gopa|go up|gope)": Key("c-u"),
        "altex": Key("a-x"),
        # TODO replace with M-x command
        "find file": Key("a-m , f , f"),
        "buffer list": Key("a-m , b , b"),
        "save buffer": Key("a-m , f , s"),
        "highlight": Key("a-m , v"),
        "avy word": Key("a-m , j, w"),
        # TODO evil-easymotion, macro, "todo"
    }


# TODO better keywords (eg say, studley)
# TODO allow (some) nesting
# TODO combine dictation with python (and other) vocabulary
class FormatRule(CompoundRule):
    spec = ('[upper | natural] ( proper | camel | rel-path | abs-path | score | sentence | '
            'scope-resolve | jumble | dotword | dashword | natword | snakeword | brooding-narrative) [<dictation>]')
    extras = [Dictation(name='dictation')]

    #def value(self, node):
    def _process_recognition(self, node, extras):
        words = node.words()

        uppercase = words[0] == 'upper'
        lowercase = words[0] != 'natural'

        if lowercase:
            words = [word.lower() for word in words]
        if uppercase:
            words = [word.upper() for word in words]

        words = [word.split('\\', 1)[0].replace('-', '') for word in words]
        if words[0].lower() in ('upper', 'natural'):
            del words[0]

        function = getattr(aenea.format, 'format_%s' % words[0].lower())
        formatted = function(words[1:])

        #return Text(formatted)
        Text(formatted).execute()

format_rule = FormatRule(name="format_rule")

alternatives = []
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
grammar.add_rule(format_rule)  # Add the top-level rule.
grammar.load()  # Load the grammar.

# Unload function which will be called at unload time.
def unload():
    global grammar
    if grammar:
        grammar.unload()
    grammar = None
