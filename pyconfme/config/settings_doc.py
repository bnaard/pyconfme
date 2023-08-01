# from https://github.com/danields761/pydantic-settings

from typing import Callable, Optional, Type, TypeVar, Union, overload

from class_doc import extract_docs_from_cls_obj

# from pydantic_settings.types import AnyPydanticModel, is_pydantic_dataclass

from dataclasses import Field
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from attr import dataclass
from pydantic import BaseModel
from typing_extensions import Protocol, runtime_checkable

Json = Union[float, int, str, 'JsonDict', 'JsonList']
JsonDict = Dict[str, Json]
JsonList = List[Json]


@runtime_checkable
class DataclassProtocol(Protocol):
    __dataclass_fields__: ClassVar[Dict[str, Field]]


@runtime_checkable
class PydanticDataclass(DataclassProtocol, Protocol):
    __initialised__: bool
    __pydantic_model__: ClassVar[BaseModel]

    @classmethod
    def __validate__(
        cls: Type['PydanticDataclass'], value: Any
    ) -> 'PydanticDataclass':
        raise NotImplementedError

    @classmethod
    def __get_validators__(cls) -> Iterator[Callable]:
        raise NotImplementedError


AnyPydanticModel = Type[Union[BaseModel, PydanticDataclass]]
AnyModelType = Type[Union[BaseModel, DataclassProtocol]]


def is_pydantic_dataclass(cls: Type) -> bool:
    return isinstance(cls, PydanticDataclass)


JsonLocation = Sequence[Union[str, int]]
"""
Sequence of indexes or keys, represents a path to reach the value inside some
:py:obj:`JsonDict`.
"""


@dataclass
class TextLocation:
    """
    Describes value occurrence inside a text.
    """

    line: int
    col: int
    end_line: int
    end_col: int

    pos: int
    end_pos: int


FlatMapLocation = Tuple[str, Optional[TextLocation]]
AnySourceLocation = Union[FlatMapLocation, TextLocation]


SL = TypeVar('SL', contravariant=True)


class SourceValueLocationProvider(Protocol[SL]):
    """
    Describes location of a value inside the source.
    """

    def get_location(self, val_loc: JsonLocation) -> SL:
        raise NotImplementedError


AnySourceLocProvider = Union[
    SourceValueLocationProvider[FlatMapLocation],
    SourceValueLocationProvider[TextLocation],
]


def apply_attributes_docs(
    model: Type[AnyPydanticModel], *, override_existing: bool = True
) -> None:
    """
    Apply model attributes documentation in-place. Resulted docs are placed
    inside :code:`field.schema.description` for *pydantic* model field.
    :param model: any pydantic model
    :param override_existing: override existing descriptions
    """
    if is_pydantic_dataclass(model):
        apply_attributes_docs(
            model.__pydantic_model__, override_existing=override_existing
        )
        return

    docs = extract_docs_from_cls_obj(model)

    for field in model.__fields__.values():
        if field.field_info.description and not override_existing:
            continue

        try:
            field.field_info.description = '\n'.join(docs[field.name])
        except KeyError:
            pass


MC = TypeVar('MC', bound=AnyPydanticModel)
_MC = TypeVar('_MC', bound=AnyPydanticModel)


@overload
def with_attrs_docs(model_cls: Type[MC]) -> Type[MC]:
    ...


@overload
def with_attrs_docs(
    *, override_existing: bool = True
) -> Callable[[Type[MC]], Type[MC]]:
    ...


def with_attrs_docs(
    model_cls: Optional[Type[MC]] = None, *, override_existing: bool = True
) -> Union[Callable[[Type[MC]], Type[MC]], Type[MC]]:
    """
    Applies :py:func:`.apply_attributes_docs`.
    """

    def decorator(maybe_model_cls: Type[_MC]) -> Type[_MC]:
        apply_attributes_docs(
            maybe_model_cls, override_existing=override_existing
        )
        return maybe_model_cls

    if model_cls is None:
        return decorator
    return decorator(model_cls)