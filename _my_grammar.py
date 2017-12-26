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


class KeystrokeRule(CompoundRule):
    spec = "[<mod1>] [<mod2>] <raw_keystroke>"
    extras = [
        RuleRef(name="raw_keystroke", rule=_KeystrokeRule()),
        RuleRef(name="mod1", rule=_ModifierRule(name="m1")),
        RuleRef(name="mod2", rule=_ModifierRule(name="m2")),
    ]

    def value(self, node):
        root = node.children[0].children[0]
        mod1 = root.children[0].value()
        mod2 = root.children[1].value()
        stroke = root.children[2].value()
        mod = ""
        if mod1:
            mod += mod1
        if mod2:
            mod += mod2
        if mod:
            stroke = "{}-{}".format(mod, stroke)
        stroke = Key(stroke)
        return stroke


class MyRepeatRule(CompoundRule):
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


my_repeat_rule = MyRepeatRule(name="my_repeat_rule")


class RepeatableKeystrokeRule(CompoundRule):
    spec = "<keystroke> [<times>]"
    extras = [
        RuleRef(name="keystroke", rule=KeystrokeRule()),
        RuleRef(name="times", rule=my_repeat_rule)
    ]

    def value(self, node):
        root = node.children[0].children[0]
        stroke = root.children[0].value()
        times = root.children[1].value()
        if times:
            return stroke * times
        else:
            return stroke


class _KeystrokeShortcut(MappingRule):
    mapping = {
        # shortcuts for vim style motion
        "drop": Key("c-d"),
        "sky": Key("c-u"),
        "scroll up": Key("c-y"),
        "scroll down": Key("c-e"),
    }


class KeystrokeShortcut(CompoundRule):
    spec = "<keystroke> [<times>]"
    extras = [
        RuleRef(name="keystroke", rule=_KeystrokeShortcut()),
        RuleRef(name="times", rule=my_repeat_rule)
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


my_vocabulary_mapping = {
    "py deaf": "def ",
    "for loop": "for ",
}

alternatives = []
alternatives.append(RuleRef(rule=RepeatableKeystrokeRule()))
alternatives.append(my_format_rule)
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


class _EmacsKeyRule(MappingRule):
    exported = False
    mapping = {
        "window": "a-m,w",
        "save buffer": "a-m,f,s",
        "highlight": "a-m,v",
        "quit": "c-g",
        "altex": "a-x",
        "easy": "a-m,o,m"  #evil-easymotion
    }


class EmacsKeyRule(CompoundRule):
    spec = "<emacs_keys>"
    extras = [RuleRef(name="emacs_keys", rule=_EmacsKeyRule())]

    def value(self, node):
        root = node.children[0].children[0]
        keys = root.children[0].value()
        return Key(keys)

    def _process_recognition(self, node, extras):
        self.value(node).execute()


class _EmacsCommandRule(MappingRule):
    exported = False
    mapping = {
        "find file": "helm-find-files",
        "recent file": "helm-recentf",
        "swiper": "helm-swoop",
        #"not much": "notmuch",
        "rej save": "copy-to-register",
        "rej pop": "insert-register",
        "buffer list": "helm-mini",
        "avy char": "evil-avy-goto-char-in-line",
        "avy word": "evil-avy-goto-word-or-subword-1",
    }


class EmacsCommandRule(CompoundRule):
    spec = "<emacs_command>"
    extras = [RuleRef(name="emacs_command", rule=_EmacsCommandRule())]

    def value(self, node):
        root = node.children[0].children[0]
        command = root.children[0].value()
        # avoid using helm-M-x because it requires delay before entering
        return Key("a-colon") + Text(
            "(call-interactively '{})".format(command)) + Key("enter")

    def _process_recognition(self, node, extras):
        self.value(node).execute()


class MyVocabulary(MappingRule):
    exported = True
    mapping = {k: Text(v) for k, v in my_vocabulary_mapping.items()}


prefixes = []
prefixes.append(RuleRef(rule=MyVocabulary()))
prefixes.append(RuleRef(rule=EmacsCommandRule()))
prefixes.append(RuleRef(rule=EmacsKeyRule()))
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
        "snore": Mimic("go to sleep"),
        #"natlink reload": Mimic("force natlink to reload all grammars"),
    }


grammar = Grammar("Generic edit")
grammar.add_rule(repeat_rule)  # Add the top-level rule.
grammar.add_rule(MyLiteralRule(name="literal_rule"))  # Add the top-level rule.
grammar.add_rule(MyMimicRule())
grammar.add_rule(KeystrokeShortcut())
grammar.add_rule(MyPrefixRule())
grammar.load()  # Load the grammar.


# Unload function which will be called at unload time.
def unload():
    global grammar
    if grammar:
        grammar.unload()
    grammar = None
