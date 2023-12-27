
# Adapted from original code from https://github.com/danields761/class-doc/blob/master/class_doc.py   no license applied

import itertools
import string
import tokenize
from typing import List, Optional, Union, Iterator, Any
import ast

from .type_helpers import UniversalAssign
from .config import COMMENT_MARKER  # pyright: ignore[reportMissingImports]


def _test_advanced_ast_presence() -> bool:
    """ 
    Check if advanced ast is available. 
    This is needed because `ast` module is not a part of public API and some
    attributes may be missing in some versions of Python.

    :return: True if advanced ast is available, False otherwise
    """
    return hasattr(ast.ClassDef, 'end_lineno') and hasattr(ast.ClassDef, 'end_col_offset')


def _tokens_iter(lines: List[str]) -> Iterator[tokenize.TokenInfo]:
    """
    Return iterator over tokens of given lines. This function is needed because
    `tokenize.tokenize` doesn't accept iterator over lines, only iterator over
    functions that return lines. This function is needed because we want to
    tokenize only part of the file, not the whole file, so we need to be able to
    stop tokenization at some point.

    :param lines: list of lines to tokenize
    :return: iterator over tokens
    
    """
    # We need to make sure we don't overstep the end of the file.
    # If we do, we'll get an error, so catch that.
    try:
        line_iter = iter(lines)
        return iter(tokenize.generate_tokens(lambda: next(line_iter)))
    except StopIteration:
        pass
    except tokenize.TokenError as err:
        print(f"Error: {err}")
        return None
    

def _get_first_lineno(node: ast.AST) -> int:
    """
    Return first line number of given node. This function is needed because
    `ast` module is not a part of public API and some attributes may be missing
    in some versions of Python.

    :param node: node to get line number of
    :return: first line number of given node

    """
    try:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
            # Docstrings are represented as ast.Expr nodes with a single
            # ast.Str child.
            return node.lineno - node.value.s.count('\n')  # type: ignore
        return node.lineno
    except AttributeError:
        return None
    except TypeError:
        # This happens if node is None.
        return None
    
def _take_until_node(tokens: Iterator[tokenize.TokenInfo], node: ast.AST) -> Iterator[tokenize.TokenInfo]:
    """
    Yield tokens until given node is reached. This function is needed because
    `ast` module is not a part of public API and some attributes may be missing
    in some versions of Python.
    
    :param tokens: iterator over tokens
    :param node: node to stop at
    :return: iterator over tokens until given node is reached
    """
    for token in tokens:  # type: Token
        yield token  # type: Token
        # We can't use `token.end` because it's not available in Python 3.5.
        if token.start[0] >= _get_first_lineno(node):  # type: ignore
            break

def count_neighbor_newlines(lines: List[str], first: ast.AST, second: ast.AST) -> int:
    """
    Count only logical newlines between two nodes, e.g. any node may consist of
    multiple lines, so you can't just take difference of `lineno` attribute, this
    value will be pointless

    :param lines: list of lines to count newlines in
    :param first: first node
    :param second: second node
    :return: number of logical newlines (result will be 0 if second node is placed
        right after first)
    """
    # If advanced ast is available, we can use `end_lineno` attribute to get
    if _test_advanced_ast_presence():
        return second.lineno - first.end_lineno - 1
    # If advanced ast is not available, we need to tokenize the file and count
    else:
        tokens_iter = _tokens_iter(lines)
        # Consume tokens until first node is reached
        try:
            list(_take_until_node(tokens_iter, first)) 
        except ValueError:
            # Node not found
            return None

        # The first line number of the first node
        first_first_lineno = _get_first_lineno(first)

        # The first line number of the second node
        second_first_lineno = _get_first_lineno(second)

        # The difference between the two line numbers
        offset = second_first_lineno - first_first_lineno

        # The number of newlines in the first node
        tokens = _take_until_node(tokens_iter, first)
        first_n_newlines = sum(
            1
            for token in tokens
            if token.type == tokenize.NEWLINE
        )

        # Subtract the number of newlines in the first node
        offset -= first_n_newlines


def _extract_definition_line_comment_after_Python38(lines: List[str], node: UniversalAssign) -> Optional[str]:
    """
    Extract definition line comment from given node. This function is needed
    because `ast` module is not a part of public API and some attributes may be
    missing in some versions of Python.
    
    :param lines: list of lines to extract comment from
    :param node: node to extract comment from   
    :return: definition line comment of given node
    """
    start_lineno = node.lineno - 1

    # If advanced ast is available, we can use `end_lineno` attribute to get
    # the line number of the last line of the node.
    end_lineno = node.end_lineno - 1
    end_col_offset = node.end_col_offset - 1

    # If the node is a multiline node, we need to get the last line of the node
    # and the column offset of the last character of the node.
    if start_lineno == end_lineno:
        node_line = lines[start_lineno]
    else:
        node_line = lines[end_lineno]

    comment_marker_pos = node_line.find(COMMENT_MARKER, end_col_offset)
    if comment_marker_pos == -1:
        return None

    return node_line[comment_marker_pos + 2:].strip() # remove comment marker and whitespace


def _extract_definition_line_comment_before_Python38(lines: List[str], node: UniversalAssign) -> Optional[str]:
    """
    Extract definition line comment from given node. This function is needed
    because `ast` module is not a part of public API and some attributes may be
    missing in some versions of Python.

    :param lines: list of lines to extract comment from
    :param node: node to extract comment from
    :return: definition line comment of given node
    """
    def valid_comment_or_none(comment):
        if comment.startswith('#:'):
            return comment[2:].strip()
        return None

    # will fetch all tokens until closing bracket of appropriate type occurs
    #  recursively calls himself when new opening bracket detected
    matching_brackets = {'{': '}', '[': ']', '(': ')'}

    def consume_between_bracers(iterable, bracket_type: str):
        closing_bracket = matching_brackets[bracket_type]
        for op in iterable:
            if op.string == closing_bracket:
                return
            if op.string in matching_brackets:
                return consume_between_bracers(iterable, op.string)
        # should never occur because these lines are already parsed and validated
        raise ValueError(f'no closing bracket for bracket of type "{bracket_type}"')

    # find last node
    if node.value is None:
        if not isinstance(node, ast.AnnAssign) or node.annotation is None:
            return None
        last_node = node.annotation
    else:
        if isinstance(node.value, ast.Tuple) and lines[node.value.lineno - 1][node.value.col_offset - 1] != '(':
            last_node = node.value.elts[-1]
        else:
            last_node = node.value

    tokens_iter = _tokens_iter(lines)

    # skip tokens until the first token of the last node occurs
    list(_take_until_node(tokens_iter, last_node))

    # skip all except newline (for \ escaped newlines NEWLINE token isn't emitted)
    #  and comment token itself
    for tok in tokens_iter:
        if tok.type in (tokenize.COMMENT, tokenize.NEWLINE):
            list(_take_until_node(tokens_iter, tok))
            break
        if tok.type == tokenize.OP and tok.string in matching_brackets:
            consume_between_bracers(tokens_iter, tok.string)

    try:
        maybe_comment = next(tokens_iter)
    except StopIteration:
        return None

    if maybe_comment.type == tokenize.COMMENT:
        return valid_comment_or_none(maybe_comment.string)

    return None

def extract_prev_node_comments(lines: List[str], node: UniversalAssign) -> List[str]:
    leading_whitespaces = ''.join(itertools.takewhile(lambda char: char in set(string.whitespace), lines[node.lineno - 1]))
    comment_line_start = leading_whitespaces + '#:'

    return [
        line[len(comment_line_start):].strip()
        for line in itertools.takewhile(
            lambda line: line.startswith(comment_line_start),
            reversed(lines[: node.lineno - 1]),
        )
    ][::-1]

def extract_definition_line_comment(lines: List[str], node: UniversalAssign) -> Optional[str]:
    if _test_advanced_ast_presence():
        return _extract_definition_line_comment_after_Python38(lines, node)
    else:
        return _extract_definition_line_comment_before_Python38(lines, node)
