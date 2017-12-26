from natlink import setMicState
import aenea
from aenea import (
    Grammar,
    MappingRule,
    Rule,
    Text,
    Key,
    Mimic,
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


grammar = Grammar("Generic edit")

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

        # special characters
        "space": "space",
        "slap": "enter",
        "bang": "bang",  # !
        "atta": "at",  # @
        "hash": "hash",  # #
        "dollar": "dollar",  # $
        "percent": "percent",
        "caret": "caret",
        "star": "asterisk",
        "lepa": "lparen",
        "repa": "rparen",
        "(dash|minus|hyphen)": "minus",
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
        "(sierra|sigma)": "s",
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


class RepeatCountRule(CompoundRule):
    exported = False
    spec = "(twice|thrice|<n> ice)"
    extras = [IntegerRef("n", 1, 100)]

    def value(self, node):
        root = node.children[0].children[0]
        times = root.children[0].value()
        if times == "twice":
            return 2
        elif times == "thrice":
            return 3
        else:
            return times[0]


repeat_count_rule = RepeatCountRule(name="repeat_count_rule")


class KeystrokeRule(CompoundRule):
    spec = "[<mod1>] [<mod2>] <raw_keystroke> [<times>]"
    extras = [
        RuleRef(name="raw_keystroke", rule=_KeystrokeRule()),
        RuleRef(name="mod1", rule=_ModifierRule(name="m1")),
        RuleRef(name="mod2", rule=_ModifierRule(name="m2")),
        RuleRef(name="times", rule=repeat_count_rule),
    ]

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
        if times:
            return stroke * times
        else:
            return stroke


class FormatFunctionMapping(MappingRule):
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
        RuleRef(name="format_rule", rule=FormatFunctionMapping()),
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
alternatives.append(RuleRef(rule=KeystrokeRule()))
alternatives.append(my_format_rule)
single_action = Alternative(alternatives)

sequence = Repetition(single_action, min=1, max=16, name="sequence")


class MyChainingRule(CompoundRule):
    spec = "<sequence>"
    extras = [
        sequence,  # Sequence of actions defined above.
    ]

    def _process_recognition(self, node, extras):  # @UnusedVariable
        sequence = extras["sequence"]  # A sequence of actions.
        for action in sequence:
            action.execute()


my_chaining_rule = MyChainingRule(name="my_chaining_rule")

grammar.add_rule(my_chaining_rule)
grammar.add_rule(MyLiteralRule(name="literal_rule"))

# TODO move above into separate file

class _SpacemacsKeyRule(MappingRule):
    exported = False
    mapping = {
        "quit": "c-g",
        "altex": "a-x",
        "file": "a-m,f",
        "buffer": "a-m,b",
        "search": "a-m,s",
        "window": "a-m,w",
        "highlight": "a-m,v",
        "easy": "a-m,o,m",  #personal binding for evil-easymotion
        "jump": "a-m,j",
        "jump char":
        "a-m,o,f",  #personal binding for evil-avy-goto-char-in-line
        "majit": "a-m,g",
        "help": "a-m,h",
    }


class SpacemacsKeyRule(CompoundRule):
    spec = "<emacs_keys>"
    extras = [RuleRef(name="emacs_keys", rule=_SpacemacsKeyRule())]

    def value(self, node):
        root = node.children[0].children[0]
        keys = root.children[0].value()
        return Key(keys)

    def _process_recognition(self, node, extras):
        self.value(node).execute()


my_vocabulary_mapping = {
    "py deaf": "def ",
    "for loop": "for ",
    "to do": "TODO",
    "fix me": "FIXME",
}


class MyVocabulary(MappingRule):
    exported = True
    mapping = {k: Text(v) for k, v in my_vocabulary_mapping.items()}

class _KeystrokeShortcut(MappingRule):
    mapping = {
        # shortcuts for vim style motion
        "drop": Key("c-d"),
        "sky": Key("c-u"),
        "scroll up": Key("c-y"),
        "scroll down": Key("c-e"),
        # tmux
        "tea mux": Key("c-b"),
        # qutebrowser
        "google": Key("o,g,space")
    }


class KeystrokeShortcut(CompoundRule):
    spec = "<keystroke> [<times>]"
    extras = [
        RuleRef(name="keystroke", rule=_KeystrokeShortcut()),
        RuleRef(name="times", rule=repeat_count_rule)
    ]

    def value(self, node):
        root = node.children[0].children[0]
        stroke = root.children[0].value()
        times = root.children[1].value()
        if times:
            return stroke * times
        else:
            return stroke

    def _process_recognition(self, node, extras):  # @UnusedVariable
        node.value().execute()


prefixes = []
prefixes.append(RuleRef(KeystrokeShortcut()))
prefixes.append(RuleRef(rule=MyVocabulary()))
prefixes.append(RuleRef(rule=SpacemacsKeyRule()))
prefixes = Alternative(prefixes, name="prefixes")


class MyPrefixRule(CompoundRule):
    spec = "<prefixes> [<sequence>]"
    extras = [prefixes, sequence]

    def _process_recognition(self, node, extras):  # @UnusedVariable
        prefixes = extras["prefixes"]
        prefixes.execute()
        try:
            sequence = extras["sequence"]
        except KeyError:
            pass
        else:
            for action in sequence:
                action.execute()


class MyMimicRule(MappingRule):
    mapping = {
        "snore": Mimic("go to sleep") + aenea.proxy_actions.ProxyNotification("Microphone off"),
    }



grammar.add_rule(MyMimicRule())
#grammar.add_rule(KeystrokeShortcut())
grammar.add_rule(MyPrefixRule())
grammar.load()  # Load the grammar.


# Unload function which will be called at unload time.
def unload():
    global grammar
    if grammar:
        grammar.unload()
    grammar = None
