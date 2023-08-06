# import ast
# import more_itertools as mitertools
# import itertools
# import string
# import tokenize
# from typing import List, Optional, Iterator

# from .type_helpers import UniversalAssign




# Adapted from original code from https://github.com/danields761/class-doc/blob/master/class_doc.py   no license applied

from typing import List, Iterator, Optional
import ast
import tokenize
import string
import itertools


# This function checks whether the ast.ClassDef class has either the
# 'end_lineno' or 'end_col_offset' attribute and returns True if at least one of
# them is present, otherwise False. The purpose of this function seems to be to
# verify if advanced AST features are available in the current version of the
# Python interpreter.
def _is_advanced_ast_available() -> bool:
    # Check if either 'end_lineno' or 'end_col_offset' attribute exists in ast.ClassDef
    return hasattr(ast.ClassDef, "end_lineno") or hasattr(ast.ClassDef, "end_col_offset")




class ASTToolsBase:
    """
    Base class defining a set of routines for extracting comments from Python's Abstract Syntax Tree (AST).
    """

    @classmethod
    def _tokens_peekable_iter(cls, lines: List[str]) -> Iterator[tokenize.TokenInfo]:
        """
        Returns an iterator that generates tokens from the Python code using the `tokenize` module.

        :param lines: List of strings representing the lines of Python code.
        :return: An iterator that generates tokens from the Python code.
        """
        lines_iter = iter(lines)
        return iter(tokenize.generate_tokens(lambda: next(lines_iter)))

    @classmethod
    def _get_first_lineno(cls, node: ast.AST) -> int:
        """
        Returns the starting line number of an AST node.

        If the node is a string expression, it accounts for the number of newline characters in the string.

        :param node: The AST node.
        :return: The starting line number of the node.
        """
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
            return node.lineno - node.value.s.count("\n")
        return node.lineno

    @classmethod
    def _take_until_node(cls, tokens: Iterator[tokenize.TokenInfo], node: ast.AST) -> Iterator[tokenize.TokenInfo]:
        """
        Yields tokens from an iterator until the specified node's starting position is reached.

        :param tokens: Iterator of tokens.
        :param node: The AST node to reach.
        :return: Iterator yielding tokens until the specified node's starting position.
        """
        for token in tokens:
            yield token
            if token.start[0] >= cls._get_first_lineno(node) and token.start[1] >= node.col_offset:
                break

    @classmethod
    def extract_definition_line_comment(cls, lines: List[str], node: ast.AST) -> Optional[str]:
        """
        Extracts a comment associated with the node's definition.

        It searches for a comment starting with "#:" between the node's definition and the previous node.

        :param lines: List of strings representing the lines of Python code.
        :param node: The AST node whose comment to extract.
        :return: The comment associated with the node's definition, or None if not found.
        """
        end_lineno = node.end_lineno - 1
        end_col_offset = node.end_col_offset - 1
        node_line = lines[end_lineno]
        comment_marker_pos = node_line.find("#:", end_col_offset)
        if comment_marker_pos == -1:
            return None
        return node_line[comment_marker_pos + 2 :].strip()

    @classmethod
    def extract_prev_node_comments(cls, lines: List[str], node: ast.AST) -> List[str]:
        """
        Extracts comments that appear above the given node.

        It searches for comments starting with "#:" before the node's definition.

        :param lines: List of strings representing the lines of Python code.
        :param node: The AST node whose preceding comments to extract.
        :return: A list of comments appearing above the given node.
        """
        leading_whitespaces = "".join(itertools.takewhile(lambda char: char in set(string.whitespace), lines[node.lineno - 1]))
        comment_line_start = leading_whitespaces + "#:"
        return list(
            line[len(comment_line_start) :].strip()
            for line in itertools.takewhile(
                lambda line: line.startswith(comment_line_start),
                reversed(lines[: node.lineno - 1]),
            )
        )[::-1]

class _ASTTools(ASTToolsBase):
    """
    Defines set of routines for such `ast` implementations, where no information
    about node end position is tracked.
    """

    @classmethod
    def count_neighbor_newlines(cls, lines: List[str], first: ast.AST, second: ast.AST) -> int:
        """
        Count logical newlines between two nodes.

        :param lines: List of strings representing the lines of Python code.
        :param first: The first AST node.
        :param second: The second AST node.
        :return: The number of logical newlines between the two nodes.
        """
        return second.lineno - first.end_lineno - 1


class _ASTToolsExtendedAST(ASTToolsBase):
    """
    Defines set of routines for advanced `ast` implementation.
    """

    @classmethod
    def count_neighbor_newlines(cls, lines: List[str], first: ast.AST, second: ast.AST) -> int:
        """
        Count logical newlines between two nodes using their line numbers and end line numbers.

        :param lines: List of strings representing the lines of Python code.
        :param first: The first AST node.
        :param second: The second AST node.
        :return: The number of logical newlines between the two nodes.
        """
        return second.lineno - first.end_lineno - 1



# class _ASTTools:
#     """
#     Defines set of routines for such `ast` implementations, where no information
#     about node end position is tracked.
#     """

#     # _tokens_peekable_iter method takes a list of lines and returns an iterator
#     # that generates tokens from the Python code using the `tokenize` module.
#     @classmethod
#     def _tokens_peekable_iter(cls, lines: List[str]) -> mitertools.peekable:
#         lines_iter = iter(lines)
#         return mitertools.peekable(tokenize.generate_tokens(lambda: next(lines_iter)))

#     # _get_first_lineno method takes an AST node and returns its starting line number.
#     # If the node is a string expression, it also accounts for the number of newline
#     # characters in the string.
#     @classmethod
#     def _get_first_lineno(cls, node: ast.AST) -> int:
#         if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
#             return node.lineno - node.value.s.count("\n")
#         return node.lineno

#     # _take_until_node method takes an iterator of tokens and an AST node,
#     # and yields tokens until the specified node's starting position is reached.
#     @classmethod
#     def _take_until_node(cls, tokens: Iterator[tokenize.TokenInfo], node: ast.AST) -> Iterator[tokenize.TokenInfo]:
#         for tok in tokens:
#             yield tok
#             if tok.start[0] >= cls._get_first_lineno(node) and tok.start[1] >= node.col_offset:
#                 break

#     # count_neighbor_newlines method counts logical newlines between two AST nodes.
#     # It considers that each node can consist of multiple lines, so simply taking the
#     # difference in line numbers won't give the correct result.
#     @classmethod
#     def count_neighbor_newlines(cls, lines: List[str], first: ast.AST, second: ast.AST) -> int:
#         """
#         Count only logical newlines between two nodes, e.g. any node may consist of
#         multiple lines, so you can't just take difference of `lineno` attribute, this
#         value will be pointless

#         :return: number of logical newlines (result will be 0 if second node is placed
#             right after first)
#         """
#         tokens_iter = cls._tokens_peekable_iter(lines)
#         mitertools.consume(cls._take_until_node(tokens_iter, first))
#         return (cls._get_first_lineno(second) - cls._get_first_lineno(first)) - sum(
#             1 for tok in cls._take_until_node(tokens_iter, second) if tok.type == tokenize.NEWLINE
#         )

#     # extract_definition_line_comment method extracts a comment associated with the node's definition.
#     # It searches for a comment starting with "#:" between the node's definition and the previous node.
#     @classmethod
#     def extract_definition_line_comment(cls, lines: List[str], node: UniversalAssign) -> Optional[str]:
#         def valid_comment_or_none(comment):
#             if comment.startswith("#:"):
#                 return comment[2:].strip()
#             return None

#         # will fetch all tokens until closing bracket of appropriate type occurs
#         #  recursively calls himself when new opening bracket detected
#         matching_brackets = {"{": "}", "[": "]", "(": ")"}

#         def consume_between_bracers(iterable, bracket_type: str):
#             closing_bracket = matching_brackets[bracket_type]
#             for op in iterable:
#                 if op.string == closing_bracket:
#                     return
#                 if op.string in matching_brackets:
#                     return consume_between_bracers(iterable, op.string)
#             # should never occurs because this lines already parsed and validated
#             raise ValueError(f'no closing bracket for bracket of type "{bracket_type}"')

#         # find last node
#         if node.value is None:
#             if not isinstance(node, ast.AnnAssign) or node.annotation is None:
#                 return None
#             last_node = node.annotation
#         else:
#             if isinstance(node.value, ast.Tuple) and lines[node.value.lineno - 1][node.value.col_offset - 1] != "(":
#                 last_node = node.value.elts[-1]
#             else:
#                 last_node = node.value

#         tokens_iter = cls._tokens_peekable_iter(lines)

#         # skip tokens until first token of last node occurred
#         tokens_iter.prepend(mitertools.last(cls._take_until_node(tokens_iter, last_node)))

#         # skip all except newline (for \ escaped newlines NEWLINE token isn't emitted)
#         #  and comment token itself
#         for tok in tokens_iter:
#             if tok.type in (tokenize.COMMENT, tokenize.NEWLINE):
#                 tokens_iter.prepend(tok)
#                 break
#             if tok.type == tokenize.OP and tok.string in matching_brackets:
#                 consume_between_bracers(tokens_iter, tok.string)

#         try:
#             maybe_comment = next(tokens_iter)
#         except StopIteration:
#             return None

#         if maybe_comment.type == tokenize.COMMENT:
#             return valid_comment_or_none(maybe_comment.string)

#         return None

#     # extract_prev_node_comments method extracts comments that appear above the given node.
#     # It searches for comments starting with "#:" before the node's definition.
#     @classmethod
#     def extract_prev_node_comments(cls, lines: List[str], node: UniversalAssign) -> List[str]:
#         leading_whitespaces = "".join(itertools.takewhile(lambda char: char in set(string.whitespace), lines[node.lineno - 1]))
#         comment_line_start = leading_whitespaces + "#:"

#         return list(
#             line[len(comment_line_start) :].strip()
#             for line in itertools.takewhile(
#                 lambda line: line.startswith(comment_line_start),
#                 reversed(lines[: node.lineno - 1]),
#             )
#         )[::-1]


# class _ASTToolsExtendedAST:
#     """
#     Defines set of routines for advanced `ast` implementation.
#     """

#     # extract_prev_node_comments method is assigned to the same method from the _ASTTools class,
#     # effectively making it available in the _ASTToolsExtendedAST class as well.
#     extract_prev_node_comments = _ASTTools.extract_prev_node_comments

#     # count_neighbor_newlines method calculates the number of logical newlines between two AST nodes
#     # using their line numbers and end line numbers. It assumes that the nodes' end line number points
#     # to the last line of the node's definition.
#     @classmethod
#     def count_neighbor_newlines(cls, lines: List[str], first: ast.AST, second: ast.AST) -> int:
#         return second.lineno - first.end_lineno - 1

#     # extract_definition_line_comment method extracts a comment associated with the node's definition
#     # by searching for a comment marker (#:) on the same line as the end of the node's definition.
#     @classmethod
#     def extract_definition_line_comment(cls, lines: List[str], node: UniversalAssign) -> Optional[str]:
#         # Get the line number and column offset of the end of the node's definition.
#         end_lineno = node.end_lineno - 1 
#         end_col_offset = node.end_col_offset - 1

#         # Get the line containing the end of the node's definition.
#         node_line = lines[end_lineno]

#         # Find the position of the comment marker (#:) starting from the end of the node's definition.
#         comment_marker_pos = node_line.find("#:", end_col_offset)

#         # If no comment marker is found, return None (indicating no comment is associated with the node).
#         if comment_marker_pos == -1:
#             return None

#         # Extract the comment text starting from the comment marker and strip any leading/trailing whitespace.
#         return node_line[comment_marker_pos + 2 :].strip()

