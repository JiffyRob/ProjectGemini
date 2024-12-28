"""
SNEK Programming Language: Sorta like bad javascript.  Runs async with the rest of the game.
"""

import functools
import logging
import operator
import queue
import random
import time

import pyparsing as pp

UNFINISHED = "SNKconst unfinished"
DONE = "SNKconst done"
GET_VAR = "SNKconst get"
WARNING = "SNKConst warning"

pp.ParserElement.enable_packrat()
logger = logging.getLogger(__name__)


class SnekCommand:
    def __init__(self, required_context=()):
        self.context = {}
        self.value_queue = []
        for var in required_context:
            self.value_queue.append(GET_VAR)
            self.value_queue.append(var)

    def __iter__(self):
        return self

    def get_var(self, name, value):
        self.context[name] = value

    def post_warning(self, text):
        self.value_queue.append(WARNING)
        self.value_queue.append(text)

    def __next__(self):
        if self.value_queue:
            return self.value_queue.pop(0)
        return self.get_value()

    def get_value(self):
        return None


class Wait(SnekCommand):
    def __init__(self, amount=1000):
        super().__init__()
        self.time = amount
        self.start = time.time() * 1000

    def get_value(self):
        now = time.time() * 1000
        if now - self.start >= self.time:
            return 1
        return UNFINISHED


class Any:
    def __eq__(self, other):
        return True

    def __lt__(self, other):
        return False

    def __gt__(self, other):
        return False

    def __le__(self, other):
        return True

    def __ge__(self, other):
        return False

    def __repr__(self):
        return f"SNEK const ANY"


def snek_command(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        yield func(*args, **kwargs)

    return wrapper


class Lexer:
    """Holds all lexing primitives and a function to use them"""

    cache = {}

    # argument primitives
    comment = "#" + pp.rest_of_line

    number = pp.common.number
    string = pp.QuotedString("'", esc_char="\\") | pp.QuotedString('"', esc_char="\\")
    varname = pp.common.identifier | pp.Literal("NULL")
    literal = number | string | varname
    expression = pp.Forward()

    # commands and keywords
    command = varname + "(" + pp.Opt(pp.DelimitedList(expression, allow_trailing_delim=True)) + ")"
    control = pp.one_of("if switch case while", as_keyword=True)

    # expressions
    assignment = varname + "="
    expression <<= pp.Group(
        pp.infix_notation(
            pp.Group(command) | literal,
            [
                # almost all the same operators as python, with the same precedences
                # https://www.w3schools.com/python/python_operators.asp
                ("**", 2, pp.opAssoc.LEFT),
                (pp.one_of("+ - ~"), 1, pp.opAssoc.RIGHT),
                (pp.one_of("* / // %"), 2, pp.OpAssoc.LEFT),
                (pp.one_of("+ -"), 2, pp.OpAssoc.LEFT),
                (pp.one_of("<< >>"), 2, pp.OpAssoc.LEFT),
                ("&", 2, pp.OpAssoc.LEFT),
                ("^", 2, pp.OpAssoc.LEFT),
                ("|", 2, pp.OpAssoc.LEFT),
                (pp.one_of("== != > >= < <= in"), 2, pp.OpAssoc.LEFT),
                ("not in", 2, pp.OpAssoc.LEFT),
                (pp.one_of("! not"), 1, pp.opAssoc.RIGHT),
                ("and", 2, pp.opAssoc.LEFT),
                ("or", 2, pp.opAssoc.LEFT),
            ],
        )
    )

    grammar = pp.ZeroOrMore(
        pp.Group(pp.Literal("}"))
        | pp.Group(control + pp.Opt(expression) + pp.Literal("{"))
        | pp.Group(pp.Opt(assignment) + expression + pp.Literal(";").suppress())
    ).ignore(comment)

    @classmethod
    def tokenize(cls, string):
        if string in cls.cache:
            return cls.cache[string]
        result = cls.grammar.parse_string(string, parse_all=True)
        cls.cache[string] = result
        return result

    @classmethod
    def _test(cls):
        for test in (
            "a = 1; \nb = 2;",
            "a = !bool(bool(1));",
            "-1 + 3 * -4;",
            "a = bool() + 1 - 3;",
            "b(a, 1 + -1);",
            "bool(a + 45, -5 * (3 + -b) - 6);",
            "if x==0 {",
            "if x {",
            "}",
            "while 1 {",
            "_='Hi there!';",
        ):
            result = cls.tokenize(test)
            print(test)
            print(result)
            print()


class SNEKProgram:
    def __init__(self, script, start_variables=None, api=None):
        self.api = {
            "upper": snek_command(lambda arg: arg.upper()),
            "lower": snek_command(lambda arg: arg.lower()),
            "title": snek_command(lambda arg: arg.title()),
            "print": self.print,
            "format": self.format,
            "wait": Wait,
            "randint": snek_command(random.randint),
            "input": snek_command(input),
            "bool": snek_command(lambda *args: bool(*args)),
            "abs": snek_command(abs),
            "sub": snek_command(lambda a, *args: a - sum(args)),
            "div": snek_command(lambda *args: functools.reduce(operator.truediv, args)),
            "fdiv": snek_command(lambda *args: functools.reduce(operator.floordiv, args)),
            "getitem": snek_command(lambda x, y: x[y]),
            "time": snek_command(time.time() * 1000),
        }
        if api is not None:
            self.api.update(api)
        # variables go here
        self.namespace = {
            "ANY": Any(),
        }
        if start_variables is not None:
            self.namespace.update(start_variables)

        self.operators = {
            "**": pow,
            "+": lambda x, y=None: x + y if y != None else +x,
            "-": lambda x, y=None: x - y if y != None else -x,
            "~": operator.invert,
            "*": operator.mul,
            "/": operator.truediv,
            "//": operator.floordiv,
            "%": operator.mod,
            "<<": operator.lshift,
            ">>": operator.rshift,
            "&": operator.and_,
            "^": operator.xor,
            "|": operator.or_,
            "==": operator.eq,
            "!=": operator.ne,
            ">": operator.gt,
            ">=": operator.ge,
            "<": operator.lt,
            "<=": operator.le,
            "!": lambda x: not x,
            "not": lambda x: not x,
            "in": lambda x, y: x in y,
            "not in": lambda x, y: x not in y,
            # TODO: add short circuiting on logical operators
            "and": lambda x, y: x and y,
            "or": lambda x, y: x or y,
        }
        self.kwds = {
            "if": self._if,
            "switch": self._switch,
            "case": self._case,
            "while": self._while,
        }

        self.operand_evaluators = {
            int: lambda x: x,
            float: lambda x: x,
            str: lambda x: self.namespace.get(x, x),
        }
        self.script = Lexer.tokenize(script)
        self.index = 0
        self.running = True
        self.call_stack = []
        self.runner = self._run()

    def _evaluate_expression(self, expression):
        # Try to evaluate all subgroups first
        fixed = []
        for token in expression:
            if isinstance(token, pp.ParseResults):
                evaluator = self._evaluate_expression(token)
                value = next(evaluator)
                while value == UNFINISHED:
                    yield UNFINISHED
                    value = next(evaluator)
                token = value
            if isinstance(token, str) and token == "NULL":
                token = None
            if isinstance(token, str) and token in self.namespace:
                token = self.namespace[token]
            fixed.append(token)
        match fixed:
            # single term
            case [op]:
                yield op
            # function call (always grouped by itself)
            case [func_name, "(", *args, ")"]:
                callback = self.api[func_name](*args)
                while True:
                    value = next(callback)
                    if value == GET_VAR:
                        # command has requested to evaluate an expression for context
                        # ugh too many nested loops
                        expr = next(callback)
                        eval_callback = self._evaluate_expression(Lexer.tokenize(expr + ";\n"))
                        while (eval_value := next(eval_callback)) == UNFINISHED:
                            yield eval_value
                        callback.get_var(expr, eval_value)
                        continue
                    if value == WARNING:
                        # command has issued a warning
                        value = next(callback)
                        print("...")
                        print("SNEK WARNING:")
                        print(func_name, args)
                        print(value)
                        print("...")
                        continue
                    yield value
                    if value not in {UNFINISHED, GET_VAR, WARNING}:
                        break

            # unary operator (also always grouped by itself)
            case [op, arg]:
                yield self.operators[op](arg)
            # binary operator
            case [arg1, op, arg2]:
                yield self.operators[op](arg1, arg2)
            # multiple binary operators strung together
            # currently we do the leftmost operation and then recurse again
            case [arg1, op, arg2, *rest]:
                yield from self._evaluate_expression([self.operators[op](arg1, arg2), *rest])

    def _skip_to_end(self, index):
        brace_count = 1
        while brace_count:
            line = tuple(self.script[index])
            if "{" in line:
                brace_count += 1
            if "}" in line:
                brace_count -= 1
            index += 1
        return index

    def _if(self, expression):
        evaluator = self._evaluate_expression(expression)
        value = next(evaluator)
        while value == UNFINISHED:
            yield UNFINISHED
            value = next(evaluator)
        if not value:
            self.index = self._skip_to_end(self.index + 1) - 1
        else:
            self.call_stack.append(("if", value, None))
        yield

    def _switch(self, expression):
        evaluator = self._evaluate_expression(expression)
        value = next(evaluator)
        while value == UNFINISHED:
            yield UNFINISHED
            value = next(evaluator)
        self.call_stack.append(["switch", value, False])
        yield

    def _case(self, expression):
        evaluator = self._evaluate_expression(expression)
        value = next(evaluator)
        while value == UNFINISHED:
            yield UNFINISHED
            value = next(evaluator)

        owner = None
        for data in reversed(self.call_stack):
            if data[0] == "switch":
                owner = data
                break

        if owner is None:
            raise ValueError("case statement without switch", self.call_stack)

        owner_value = owner[1]
        if owner_value != value:
            self.index = self._skip_to_end(self.index + 1) - 1
        else:
            owner[-1] = True
            self.call_stack.append(("case", value, None))
        yield

    def _end_block(self):
        data = self.call_stack.pop()
        if data[0] == "while":
            self.index = data[-1]

    def _while(self, expression):
        evaluator = self._evaluate_expression(expression)
        value = next(evaluator)
        while value == UNFINISHED:
            yield UNFINISHED
            value = next(evaluator)
        if value:
            self.call_stack.append(("while", expression, self.index - 1))
        else:
            self.index = self._skip_to_end(self.index + 1) - 1
        yield

    def _count(self):
        yield

    def _run(self):
        self.index = 0
        self.running = True
        while self.running:
            line = self.script[self.index]
            match line:
                case [kwd, *args, "{"] if kwd in self.kwds:
                    evaluator = self.kwds[kwd](*args)
                    value = next(evaluator)
                    while value == UNFINISHED:
                        yield UNFINISHED
                        value = next(evaluator)
                case ["}"]:
                    self._end_block()
                case [varname, "=", expr]:
                    evaluator = self._evaluate_expression(expr)
                    value = next(evaluator)
                    while value == UNFINISHED:
                        yield value
                        value = next(evaluator)
                    self.namespace[varname] = value
                case [expr]:
                    evaluator = self._evaluate_expression(expr)
                    value = next(evaluator)
                    while value == UNFINISHED:
                        yield value
                        value = next(evaluator)
            self.index += 1
            if self.index >= len(self.script):
                self.running = False
        yield DONE

    def cycle(self):
        if self.running:
            value = next(self.runner)
            if value == DONE:
                self.running = False

    def run(self, delay=0.05):
        # just iterate through the whole thing and kill all the async
        for _ in self.runner:
            time.sleep(delay)

    def done(self):
        return not self.running

    @classmethod
    def _eval_test(cls):
        instance = cls("a = 0;")
        for test in (
            "1 + 1;",
            "-1 + 3 * -4 // (wait(0) + 1);",
            "(3 * 3 * 3 * -1);",
            "(((((0))))) + -5;",
            "2 >= 1 - 2;",
            "1 // 8 + 2;",
        ):
            print(test)
            print(
                "result:",
                list(instance._evaluate_expression(Lexer.tokenize(test)[0][0])),
            )

    def print(self, *args):
        print(f"SNEK says: {' '.join(repr(arg) for arg in args)}")
        yield 1

    def format(self, string):
        yield string.format(**self.namespace)
