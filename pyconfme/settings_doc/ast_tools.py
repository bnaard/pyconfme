
# Adapted from original code from https://github.com/danields761/class-doc/blob/master/class_doc.py   no license applied

import ast
from typing import List, Optional, Iterator

class ASTToolsBase:
    """
    Base class defining common routines for `ast` implementations.
    """

    @classmethod
    def _is_advanced_ast_available(cls) -> bool:
        """
        Check whether the advanced AST features are available in the current version of the Python interpreter.

        Returns:
            bool: True if at least one of the 'end_lineno' or 'end_col_offset' attributes exists in ast.ClassDef,
                  otherwise False.
        """
        return hasattr(ast.ClassDef, "end_lineno") or hasattr(ast.ClassDef, "end_col_offset")

    @classmethod
    def _tokens_peekable_iter(cls, lines: List[str]) -> Iterator[ast.AST]:
        """
        Create an iterator that generates tokens from the Python code using the `ast` module.

        Args:
            lines (List[str]): List of lines containing Python code.

        Returns:
            Iterator[ast.AST]: An iterator that generates AST nodes from the code.
        """
        return iter(ast.parse("".join(lines)).body)

    @classmethod
    def _get_first_lineno(cls, node: ast.AST) -> int:
        """
        Get the starting line number of the given AST node.

        Args:
            node (ast.AST): The AST node.

        Returns:
            int: The starting line number of the node.
        """
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
            return node.lineno - node.value.s.count("\n")
        return node.lineno

    @classmethod
    def _take_until_node(cls, nodes: Iterator[ast.AST], target_node: ast.AST) -> Iterator[ast.AST]:
        """
        Yield nodes until the target node's starting position is reached.

        Args:
            nodes (Iterator[ast.AST]): An iterator of AST nodes.
            target_node (ast.AST): The target AST node.

        Yields:
            Iterator[ast.AST]: The next AST node until the target node is reached.
        """
        for node in nodes:
            yield node
            if node.lineno >= cls._get_first_lineno(target_node) and node.col_offset >= target_node.col_offset:
                break

    @classmethod
    def extract_prev_node_comments(cls, lines: List[str], node: ast.AST) -> List[str]:
        """
        Extract comments that appear above the given node.

        Args:
            lines (List[str]): List of lines containing Python code.
            node (ast.AST): The AST node.

        Returns:
            List[str]: A list of comments found above the node.
        """
        line_start = lines[node.lineno - 1]
        leading_whitespaces = line_start[:node.col_offset].lstrip()
        comment_line_start = leading_whitespaces + "#:"

        return [
            line[len(comment_line_start):].strip()
            for line in reversed(lines[:node.lineno - 1])
            if line.startswith(comment_line_start)
        ][::-1]

    @classmethod
    def extract_definition_line_comment(cls, lines: List[str], node: ast.AST) -> Optional[str]:
        """
        Extract a comment associated with the node's definition.

        Args:
            lines (List[str]): List of lines containing Python code.
            node (ast.AST): The AST node.

        Returns:
            Optional[str]: The comment associated with the node's definition, or None if not found.
        """
        tokens_iter = cls._tokens_peekable_iter(lines)
        for tok in cls._take_until_node(tokens_iter, node):
            pass

        try:
            maybe_comment = next(tokens_iter)
        except StopIteration:
            return None

        if isinstance(maybe_comment, ast.Expr) and isinstance(maybe_comment.value, ast.Str):
            return maybe_comment.value.s.strip()
        return None

class ASTTools(ASTToolsBase):
    """
    Defines a set of routines for `ast` implementations where no information about node end position is tracked.
    """

    @classmethod
    def count_neighbor_newlines(cls, lines: List[str], first: ast.AST, second: ast.AST) -> int:
        """
        Count logical newlines between two AST nodes.

        Args:
            lines (List[str]): List of lines containing Python code.
            first (ast.AST): The first AST node.
            second (ast.AST): The second AST node.

        Returns:
            int: The number of logical newlines between the two nodes.
        """
        tokens_iter = cls._tokens_peekable_iter(lines)
        for tok in cls._take_until_node(tokens_iter, first):
            pass

        return (self._get_first_lineno(second) - self._get_first_lineno(first)) - sum(
            1 for tok in cls._take_until_node(tokens_iter, second) if isinstance(tok, ast.Expr) and isinstance(tok.value, ast.Str)
        )

class ASTToolsExtendedAST(ASTToolsBase):
    """
    Defines a set of routines for advanced `ast` implementation.
    """

    @classmethod
    def count_neighbor_newlines(cls, lines: List[str], first: ast.AST, second: ast.AST) -> int:
        """
        Calculate the number of logical newlines between two AST nodes using their line numbers and end line numbers.

        Args:
            lines (List[str]): List of lines containing Python code.
            first (ast.AST): The first AST node.
            second (ast.AST): The second AST node.

        Returns:
            int: The number of logical newlines between the two nodes.
        """
        return second.lineno - first.end_lineno - 1

    @classmethod
    def extract_definition_line_comment(cls, lines: List[str], node: ast.AST) -> Optional[str]:
        """
        Extract a comment associated with the node's definition by searching for a comment marker (#:) on the same line as the end of the node's definition.

        Args:
            lines (List[str]): List of lines containing Python code.
            node (ast.AST): The AST node.

        Returns:
            Optional[str]: The comment associated with the node's definition, or None if not found.
        """
        end_lineno = node.end_lineno - 1
        end_col_offset = node.end_col_offset - 1

        node_line = lines[end_lineno]
        comment_marker_pos = node_line.find("#:", end_col_offset)

        if comment_marker_pos == -1:
            return None

        return node_line[comment_marker_pos + 2:].strip()
