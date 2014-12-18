import re
import copy


operator_subs = {
    '>': (r'->', r'=>'),
    '=': (r'<->', r'<=>'),
    '^': (r'&',),
}

operator_funcs = {
    '=': lambda a, b: a == b,
    '~': lambda a, b: a != b,
    '>': lambda a, b: False if a and not b else True,
    '^': lambda a, b: a and b,
    '|': lambda a, b: a or b,
    '!': lambda a: not a,
}


class ExpressionNode(object):
    parent = None

    def __str__(self):
        return self.name

    def is_operator(self):
        return False


class VariableNode(ExpressionNode):
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        if parent:
            parent.children.append(self)


class OperatorNode(ExpressionNode):
    def __init__(self, name, parent=None, children=[]):
        self.name = name
        self.parent = parent
        self.children = children
        if parent:
            parent.children.append(self)
        for child in children:
            child.parent = self

    def is_operator(self):
        return True


class BinaryOperatorNode(OperatorNode):
    pass


class UnaryOperatorNode(OperatorNode):
    def __init__(self, name, parent=None, child=None):
        super(UnaryOperatorNode, self).__init__(
            name=name,
            parent=parent,
            children=[child] if child else [])


operator_node_types = {
    '=': BinaryOperatorNode,
    '~': BinaryOperatorNode,
    '>': BinaryOperatorNode,
    '^': BinaryOperatorNode,
    '|': BinaryOperatorNode,
    '!': UnaryOperatorNode,
}


def _clean_expression(expression):

    # Replace alternative operator forms with their "real", 1 character forms
    for operator, alternatives in operator_subs.items():
        for alternative in alternatives:
            expression = re.subn(alternative, operator, expression)[0]

    # Remove whitespace
    expression = re.subn(r'\s', '', expression)[0]

    # Return it
    return expression


class ExpressionTree(object):
    def __init__(self, expression, max_vars=10):
        self.expression = _clean_expression(expression)
        self.variables = []
        self.root = None
        self.max_vars = max_vars
        self._parse()

    def add_var(self, varname):
        if varname not in self.variables:
            self.variables.append(varname)
        if len(self.variables) > self.max_vars:
            raise Exception("Number of variables cannot exceed %d" % self.max_vars)

    def _parse(self):
        expression = copy.copy(self.expression)
        node = None
        parents = []

        while expression and len(expression) > 0:

            # If it's a variable make a leaf node for it
            r_varname = re.compile(r'(?P<varname>\w+)')
            match = r_varname.match(expression)
            if match:
                varname = match.group('varname')
                self.add_var(varname)

                # If the previous node is not an operator,
                # the expression was malformed
                if node and not node.is_operator():
                    raise Exception(
                        "Var node can only follow an operator node")

                # If this is the last operand of an operator
                if node:
                    VariableNode(name=varname, parent=node)

                    # If the operator was unary,
                    # move to its highest binary parent
                    while isinstance(node, UnaryOperatorNode) and node.parent:
                        node = node.parent

                # If this is a bare expression variable.
                # Set it as our current node.
                else:
                    node = VariableNode(name=varname)

                # Reduce, continue
                expression = expression[len(varname):]
                continue

            # If it's a unary operator, make an "extendable" leaf out of it
            r_operator = re.compile(r'(?P<operator>!)')
            match = r_operator.match(expression)
            if match:
                operator = match.group('operator')
                if node and not node.is_operator():
                    raise Exception(
                        "Unary operator must be bare or follow operator node")
                node = UnaryOperatorNode(name=operator, parent=node or None)
                expression = expression[len(operator):]
                continue

            # If it's a binary operator
            r_operator = re.compile(r'(?P<operator>[=|~|>|\^|\|])')
            match = r_operator.match(expression)
            if match:
                operator = match.group('operator')
                if node is None:
                    raise Exception("Expression cannot start with a binary operator, silly buns. This ain't prefix notation.")
                node = BinaryOperatorNode(name=operator, children=[node])
                expression = expression[len(operator):]
                continue

            # If it's an open bracket
            r_open = re.compile(r'(?P<bracket>\()')
            match = r_open.match(expression)
            if match:
                bracket = match.group('bracket')
                if node:
                    parents.append(node)
                    node = None
                expression = expression[len(bracket):]
                continue

            # If it's a close bracket
            r_open = re.compile(r'(?P<bracket>\))')
            match = r_open.match(expression)
            if match:
                bracket = match.group('bracket')
                if not node:
                    raise Exception("Expression cannot start with a close-bracket.")
                if len(parents) > 0:
                    parent = parents.pop()
                    parent.children.append(node)
                    node.parent = parent
                    node = parent
                    while isinstance(node, UnaryOperatorNode) and node.parent:
                        node = node.parent
                expression = expression[len(bracket):]
                continue

            # If we encountered an unrecognized expression...
            raise Exception(
                "Unrecognized symbol in expression! \"%s\"" % expression)

        # If a binary operator was left hanging...
        if isinstance(node, BinaryOperatorNode) and len(node.children) < 2:
            raise Exception(
                "Binary operator \"%s\" did not have two operands." % node.name)

        # Save the root node
        while node.parent:
            node = node.parent
        self.root = node

    def _evaluate(self, vardict, node=None):

        # Start at the root node
        if node is None:
            node = self.root

        # If this is a variable node, return it's value
        if isinstance(node, VariableNode):
            if node.name not in vardict:
                raise Exception("No value provided for variable \"%s\"" % node.name)
            return vardict[node.name]

        # If this node is an operator, evaluate it's children first, and then operate!
        if node.is_operator():
            evaluated_children = [
                self._evaluate(vardict, child) for child in node.children]
            return operator_funcs[node.name](*evaluated_children)

    def stringify(self, node=None, brackets=False):
        if node is None:
            node = self.root

        str = ""
        if brackets:
            str += "("
        if isinstance(node, UnaryOperatorNode):
            str += node.name
            str += self.stringify(node.children[0], node.children[0].is_operator())
        elif isinstance(node, BinaryOperatorNode):
            str += self.stringify(node.children[0], node.children[0].is_operator())
            str += node.name
            str += self.stringify(node.children[1], node.children[1].is_operator())
        elif isinstance(node, VariableNode):
            str += node.name
        if brackets:
            str += ")"
        return str

    def is_tautology(self, vardict={}):
        for varname in self.variables:

            # If this var doesn't have a value yet...
            if varname not in vardict:
                _vardict = copy.copy(vardict)

                # Try it with "True"
                _vardict[varname] = True
                if not self.is_tautology(_vardict):
                    return False

                # Try it with "False"
                _vardict[varname] = False
                if not self.is_tautology(_vardict):
                    return False

                # If we were a tautology with both of those, return true
                return True

        return self._evaluate(vardict)

    def get_truth_table(self, rows=None, vardict={}):

        # The first row should be variable names
        if rows is None:
            rows = []
            row = []
            for varname in self.variables:
                row.append(varname)
            row.append(self.expression)
            rows.append(row)

        # Recursively try every combination of variable values
        complete = True
        for varname in self.variables:
            if varname not in vardict:
                complete = False
                _vardict = copy.copy(vardict)

                _vardict[varname] = True
                self.get_truth_table(rows, _vardict)

                _vardict[varname] = False
                self.get_truth_table(rows, _vardict)

                break

        # If all variables have values, evaluate the expression and add a row
        if complete:
            row = []
            for varname in self.variables:
                row.append(vardict[varname])
            row.append(self._evaluate(vardict))
            rows.append(row)

        # Return the table
        return rows
