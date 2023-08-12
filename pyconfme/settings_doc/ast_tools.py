
# Adapted from original code from https://github.com/danields761/class-doc/blob/master/class_doc.py   no license applied


import itertools
import string
import tokenize
from typing import List, Optional, Union, Iterator, Any
import more_itertools as mitertools
import ast

from .type_helpers import UniversalAssign



# Remove log statements and unused variables
def _test_advanced_ast_presence() -> bool:
    """ 
    Check if advanced ast is available. 
    """
    return hasattr(ast.ClassDef, 'end_lineno') and hasattr(ast.ClassDef, 'end_col_offset')



def _tokens_peekable_iter(lines: List[str]) -> mitertools.peekable:
    lines_iter = iter(lines)
    return mitertools.peekable(tokenize.generate_tokens(lambda: next(lines_iter)))


def _get_first_lineno(node: ast.AST) -> int:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
        return node.lineno - node.value.s.count('\n')
    return node.lineno


def _take_until_node(
    tokens: Iterator[tokenize.TokenInfo], node: ast.AST
) -> Iterator[tokenize.TokenInfo]:
    for tok in tokens:
        yield tok
        if (
            tok.start[0] >= _get_first_lineno(node)
            and tok.start[1] >= node.col_offset
        ):
            break

def count_neighbor_newlines(
    lines: List[str], first: ast.AST, second: ast.AST
) -> int:
    """
    Count only logical newlines between two nodes, e.g. any node may consist of
    multiple lines, so you can't just take difference of `lineno` attribute, this
    value will be pointless

    :return: number of logical newlines (result will be 0 if second node is placed
        right after first)
    """
    if _test_advanced_ast_presence():
        return second.lineno - first.end_lineno - 1
    else:
        tokens_iter = _tokens_peekable_iter(lines)
        mitertools.consume(_take_until_node(tokens_iter, first))
        return (_get_first_lineno(second) - _get_first_lineno(first)) - sum(
            1
            for tok in _take_until_node(tokens_iter, second)
            if tok.type == tokenize.NEWLINE
        )


def _extract_definition_line_comment_after_Python38(
    lines: List[str], node: UniversalAssign
) -> Optional[str]:
    end_lineno = node.end_lineno - 1
    end_col_offset = node.end_col_offset - 1

    node_line = lines[end_lineno]
    comment_marker_pos = node_line.find('#:', end_col_offset)
    if comment_marker_pos == -1:
        return None

    return node_line[comment_marker_pos + 2 :].strip()



def _extract_definition_line_comment_before_Python38(
    lines: List[str], node: UniversalAssign
) -> Optional[str]:
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
        # should never occurs because this lines already parsed and validated
        raise ValueError(f'no closing bracket for bracket of type "{bracket_type}"')

    # find last node
    if node.value is None:
        if not isinstance(node, ast.AnnAssign) or node.annotation is None:
            return None
        last_node = node.annotation
    else:
        if (
            isinstance(node.value, ast.Tuple)
            and lines[node.value.lineno - 1][node.value.col_offset - 1] != '('
        ):
            last_node = node.value.elts[-1]
        else:
            last_node = node.value

    tokens_iter = _tokens_peekable_iter(lines)

    # skip tokens until first token of last node occurred
    tokens_iter.prepend(
        mitertools.last(_take_until_node(tokens_iter, last_node))
    )

    # skip all except newline (for \ escaped newlines NEWLINE token isn't emitted)
    #  and comment token itself
    for tok in tokens_iter:
        if tok.type in (tokenize.COMMENT, tokenize.NEWLINE):
            tokens_iter.prepend(tok)
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


def extract_prev_node_comments(
    lines: List[str], node: UniversalAssign
) -> List[str]:
    leading_whitespaces = ''.join(
        itertools.takewhile(
            lambda char: char in set(string.whitespace), lines[node.lineno - 1]
        )
    )
    comment_line_start = leading_whitespaces + '#:'

    return list(
        line[len(comment_line_start) :].strip()
        for line in itertools.takewhile(
            lambda line: line.startswith(comment_line_start),
            reversed(lines[: node.lineno - 1]),
        )
    )[::-1]


def extract_definition_line_comment(
    lines: List[str], node: UniversalAssign
) -> Optional[str]:
    if _test_advanced_ast_presence():
        return _extract_definition_line_comment_after_Python38(lines, node)
    else:   
        return _extract_definition_line_comment_before_Python38(lines, node)


