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

my_mapping = {}

movementMap = {
    "(up|oop)": "up",
    "(down|doon)": "down",
    "right": "right",
    "left": "left",
    "(page up|page oop)": "pgup",
    "(page down|page doon)": "pgdown",
    "home": "home",
    "end": "end",
    "ace": "space",
    "(enter|return|slap)": "enter",
    "escape": "escape",
    "tab": "tab",
    "backspace": "backspace",
}
my_mapping.update(movementMap)

numberMap = {
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
my_mapping.update(numberMap)

letterMap = {
    "(alpha|alef)": "a",
    "(bravo)": "b",
    "(charlie)": "c",
    "(delta|del)": "d",
    "(echo|east)": "e",
    "(foxtrot|fox)": "f",
    "(gang|gamma)": "g",
    "(hotel)": "h",
    "(indy)": "i",
    "(juliet|jon)": "j",
    "(kilo|kappa)": "k",
    "(lima|lam|lamda)": "l",
    "(mike|moo)": "m",
    "(november|north)": "n",
    "(oscar)": "o",
    "(poppa|pop)": "p",
    "(quiche|queen)": "q",
    "(romeo|roman)": "r",
    "(sierra|south|sigma|sig)": "s",
    "(tango)": "t",
    "(uniform|umm|you|yunee)": "u",
    "(victor)": "v",
    "(whiskey|west)": "w",
    "(x-ray)": "x",
    "(yankee|why)": "y",
    "(zulu|zed|zeta) ": "z",
}

# generate uppercase versions of every letter
upperLetterMap = {}
for letter in letterMap:
    upperLetterMap["(sky|big) " + letter] = letterMap[letter].upper()
letterMap.update(upperLetterMap)
my_mapping.update(letterMap)

specialCharMap = {
    "bang": "bang", # !
    "at sign": "at", # @
    "hash": "hash", # #
    "(dollar|doll)": "dollar", # $
    "percent": "percent",
    "caret": "caret",
    "ampers": "and",
    "star": "star",
    "left paren": "lparen",
    "right paren": "rparen",
    "(minus|hyphen)": "minus",
    "underscore": "underscore",
    "plus": "plus",
    "backtick": "backtick",
    "tilde": "tilde",
    "left bracket": "lbracket",
    "right bracket": "rbracket",
    "backslash": "backslash",
    "(bar|pipe)": "bar",
    "colon": "colon",
    "semicolon": "semicolon",
    "(single quote|apostrophe)": "squote",
    "quote": "quote",
    "comma": "comma",
    "dot": "dot",
    "slash": "slash",
    "langle": "langle",
    "rangle": "rangle",
    "question": "question",
    "(equal|equals)": "equals"
}
my_mapping.update(specialCharMap)

winMap = {}
for k, v in my_mapping.items():
    winMap["win " + k] = "w-" + v

altMap = {}
for k, v in my_mapping.items():
    altMap["alter " + k] = "a-" + v

controlMap = {}
for k, v in my_mapping.items():
    controlMap["troll " + k] = "c-" + v


my_mapping.update(controlMap)
my_mapping.update(altMap)
my_mapping.update(winMap)


my_mapping = {k: Key(v) for k,v in my_mapping.items()}
class KeystrokeRule(MappingRule):
    export=False
    mapping = my_mapping

alternatives = []
alternatives.append(RuleRef(rule=KeystrokeRule()))
single_action = Alternative(alternatives)

sequence = Repetition(single_action, min=1, max=16, name="sequence")
class KeystrokeSequenceRule(CompoundRule):
    # Here we define this rule's spoken-form and special elements.
    spec = "<sequence>"
    extras = [
        sequence,  # Sequence of actions defined above.
    ]

    def _process_recognition(self, node, extras):  # @UnusedVariable
        sequence = extras["sequence"]  # A sequence of actions.
        for action in sequence:
            action.execute()

key_sequence_rule = KeystrokeSequenceRule(name="key_sequence_rule")


class FormatRule(CompoundRule):
    spec = ('[upper | natural] ( proper | camel | rel-path | abs-path | score | sentence | '
            'scope-resolve | jumble | dotword | dashword | natword | snakeword | brooding-narrative) [<dictation>]')
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

#format_rule = FormatRule(name="format_rule")
format_rule = RuleRef(name='format_rule', rule=FormatRule(name='i'))

class LiteralRule(CompoundRule):
    spec = "<format_rule>"
    extras = [format_rule]

    def _process_recognition(self, node, extras):
        extras['format_rule'].execute(extras)
literal_rule = LiteralRule()

grammar = Grammar("Generic edit")
grammar.add_rule(key_sequence_rule)  # Add the top-level rule.
grammar.add_rule(literal_rule)  # Add the top-level rule.
grammar.load()  # Load the grammar.

# Unload function which will be called at unload time.
def unload():
    global grammar
    if grammar:
        grammar.unload()
    grammar = None
