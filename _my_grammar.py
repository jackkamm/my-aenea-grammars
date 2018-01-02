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
    DictListRef,
    AppContext,
)

from dragonfly.actions.keyboard import keyboard
from dragonfly.actions.typeables import typeables
if 'semicolon' not in typeables:
    typeables["semicolon"] = keyboard.get_typeable(char=';')

MULTIEDIT_TAGS = ['multiedit', 'multiedit.count']
aenea.vocabulary.inhibit_global_dynamic_vocabulary('multiedit', MULTIEDIT_TAGS)

grammar = Grammar("multiedit")


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
        "(enter|return|slap)": "enter",
        "bang": "exclamation",  # !
        "at sign": "at",  # @
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


class FormatRule(CompoundRule):
    spec = (
        '[upper | natural] ( proper | camel | rel-path | abs-path | score | sentence | '
        'scope-resolve | jumble | dotword | dashword | natword | snakeword | brooding-narrative) [<dictation>]'
    )
    extras = [Dictation(name='dictation')]

    def value(self, node):
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

        return Text(formatted)


my_format_rule = RuleRef(name="my_format_rule", rule=FormatRule())


class DynamicCountRule(CompoundRule):
    spec = '<dynamic> [<times>]'

    extras = [
        DictListRef(
            'dynamic',
            aenea.vocabulary.register_dynamic_vocabulary('multiedit.count')),
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


alternatives = [
    RuleRef(rule=KeystrokeRule()),
    my_format_rule,
    DictListRef('dynamic multiedit',
                aenea.vocabulary.register_dynamic_vocabulary('multiedit')),
    RuleRef(DynamicCountRule()),
]
single_action = Alternative(alternatives)

sequence = Repetition(single_action, min=1, max=16, name="sequence")


class MyLiteralRule(CompoundRule):
    """Rule for saying MyFormatRule literally (without interruptions by other rules)"""
    spec = "say <my_format_rule>"
    extras = [my_format_rule]

    def _process_recognition(self, node, extras):
        extras["my_format_rule"].execute()


my_literal_rule = MyLiteralRule()


class MyChainingRule(CompoundRule):
    spec = "<sequence> [say <my_format_rule>]"
    extras = [
        sequence,  # Sequence of actions defined above.
        my_format_rule
    ]

    def _process_recognition(self, node, extras):  # @UnusedVariable
        sequence = extras["sequence"]  # A sequence of actions.
        for action in sequence:
            action.execute()
        if "my_format_rule" in extras:
            extras["my_format_rule"].execute()


my_chaining_rule = MyChainingRule(name="my_chaining_rule")

grammar.add_rule(my_chaining_rule)
grammar.add_rule(my_literal_rule)


class MyMimicRule(MappingRule):
    mapping = {
        "snore":
        Mimic("go to sleep") +
        aenea.proxy_actions.ProxyNotification("Microphone off"),
    }


grammar.add_rule(MyMimicRule())
grammar.load()  # Load the grammar.


# Unload function which will be called at unload time.
def unload():
    global grammar
    aenea.vocabulary.uninhibit_global_dynamic_vocabulary(
        'multiedit', MULTIEDIT_TAGS)
    for tag in MULTIEDIT_TAGS:
        aenea.vocabulary.unregister_dynamic_vocabulary(tag)
    if grammar:
        grammar.unload()
    grammar = None
