import copy
from typing import Dict, Any, List, Set, TypeVar, cast

#: :obj:`int` :
#: Maximum depth to which dictionaries are merged
MAX_RECURSION_DEPTH: int = 8


def dict_deep_update(
    target: Dict[object, object], source: Dict[object, object], recursion_depth: int = 0
):
    """Simple function to deep-update target dictionary with source.
    Non-changeable update strategy: overwrite.
    For each key, value in source: if key doesn't exist in target, deep-copy it from
    source to target. Otherwise, if value is a list, target[key] is extended with
    source[key]. If value is a set, target[key] is updated with value. If value is a dictionary,
    recursively deep-update it.
    Adapted from original code Copyright Ferry Boender, released under the MIT license.
    Source: https://www.electricmonk.nl/log/2017/05/07/merging-two-python-dictionaries-by-deep-updating/

    Args:
        target: Dictionary that gets updated.
        source: Dictionary, whose values are updated to target.
        recursion_depth: internal parameter parameter limiting the level of MAX_RECURSION_DEPTH
    Raises:
        ValueError: if either target or source is None-type
        RecursionError: if MAX_RECURSION_DEPTH is exceeded while traversing source

    Examples:
    >>> t = {'name': 'Ferry', 'hobbies': ['programming', 'sci-fi']}
    >>> dict_deep_update(t, {'hobbies': ['gaming']})
    >>> print(t)
    {'name': 'Ferry', 'hobbies': ['programming', 'sci-fi', 'gaming']}
    """
    recursion_depth = recursion_depth if recursion_depth >= 0 else 0
    if recursion_depth > MAX_RECURSION_DEPTH:
        raise RecursionError(
            f"Exceeded maximum recursion depth == {MAX_RECURSION_DEPTH}. Reduce depth"
            " of source dictionary."
        )
    if target is None:
        raise ValueError("Target dictionary is None.")
    if source is None:
        raise ValueError("Source dictionary is None.")
    if source == {}:
        target.clear()
    else:
        for source_key, source_value in source.items():
            if isinstance(source_value, List):
                if not source_key in target:
                    target[source_key] = copy.deepcopy(source_value)
                elif isinstance(target[source_key], List):
                    cast(List[object], target[source_key]).extend(source_value)
                else:
                    target[source_key] = copy.deepcopy(source_value)
            elif isinstance(source_value, Dict):
                if not source_key in target:
                    target[source_key] = copy.deepcopy(source_value)
                elif isinstance(target[source_key], Dict):
                    dict_deep_update(
                        cast(Dict[object, object], target[source_key]),
                        source_value,
                        recursion_depth=recursion_depth + 1,
                    )
                else:
                    target[source_key] = copy.deepcopy(source_value)
            elif isinstance(source_value, Set):
                if not source_key in target:
                    target[source_key] = source_value.copy()
                elif isinstance(target[source_key], Set):
                    cast(Set[object], target[source_key]).update(source_value.copy())
                else:
                    target[source_key] = copy.deepcopy(source_value)
            elif source_value is None:
                target[source_key] = None
            else:
                target[source_key] = copy.copy(source_value)