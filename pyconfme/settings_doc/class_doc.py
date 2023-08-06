# Original code from https://github.com/danields761/class-doc/blob/master/class_doc.py   no license applied

import inspect
import textwrap
from typing import Dict, List, Iterator, Any
import ast

import more_itertools as mitertools

from .type_helpers import UniversalAssign
from .ast_tools import _is_advanced_ast_available, _ASTToolsExtendedAST, _ASTTools   # pyright: ignore[reportMissingImports]


_ast_tools = _ASTToolsExtendedAST if _is_advanced_ast_available() else _ASTTools


def _get_assign_targets(node: UniversalAssign) -> Iterator[str]:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Tuple):
                yield from (el.id for el in target.elts)
            else:
                yield target.id
    else:
        yield node.target.id


def extract_node_comments(lines: List[str], node: UniversalAssign) -> List[str]:
    # firstly prioritize "after assignment comment"
    res = _ast_tools.extract_definition_line_comment(lines, node)
    if res is not None:
        return [res]

    # then try to extract "right before assignment" comments
    return _ast_tools.extract_prev_node_comments(lines, node)


def extract_all_nodes_comments(lines: List[str], cls_def: ast.ClassDef) -> Dict[str, List[str]]:
    return {
        target: comments
        for node, comments in (
            (node, extract_node_comments(lines, node))
            for node in cls_def.body
            if isinstance(node, (ast.Assign, ast.AnnAssign))
        )
        if len(comments) > 0
        for target in _get_assign_targets(node)
    }


def extract_all_attr_docstrings(lines: List[str], cls_def: ast.ClassDef) -> Dict[str, List[str]]:
    return {
        target: comments
        for node, comments in (
            (node, inspect.cleandoc(next_node.value.s).split("\n"))
            for node, next_node in mitertools.windowed(cls_def.body, 2)
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            if isinstance(next_node, ast.Expr) and isinstance(next_node.value, ast.Str)
            if _ast_tools.count_neighbor_newlines(lines, node, next_node) == 0
        )
        for target in _get_assign_targets(node)
    }


def extract_docs(lines: List[str], cls_def: ast.ClassDef) -> Dict[str, List[str]]:
    """
    Extract attrs docstring and '#:' comments from class definition for hist attributes.
    Nodes comments are preferred over attr docstrings.

    TODO: cover all priority nuances

    :param lines: must be those lines from which `cls_def` has been compiled
    :param cls_def: class definition
    :return: per attribute doc lines
    """
    return {
        **extract_all_attr_docstrings(lines, cls_def),
        **extract_all_nodes_comments(lines, cls_def),
    }


def extract_docs_from_cls_obj(cls: Any):
    """
    Extract docs from class object using :py:func:`extract_docs`.

    :param cls: :py:func:`inspect.getsourcelines` must return sources of class
        definition
    :return: same as :py:func:`extract_docs`
    """
    lines, _ = inspect.getsourcelines(cls)

    # dedent the text for a inner classes declarations
    text = textwrap.dedent("".join(lines))
    lines = text.splitlines(keepends=True)

    tree = ast.parse(text).body[0]
    if not isinstance(tree, ast.ClassDef):
        raise TypeError(f'Expecting "{ast.ClassDef.__name__}", but "{cls}" is received')

    return extract_docs(lines, tree)
