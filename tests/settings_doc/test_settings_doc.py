import pytest

from pydantic import BaseSettings, BaseModel
from hypothesis import given, strategies as st

from pyconfme.settings_doc.settings_doc import with_attrs_docs


@with_attrs_docs
class DummyModel(BaseModel):
    #: test comment: description of member foo
    foo: str


@with_attrs_docs
class DummyRunserverSettings(BaseSettings):
    #: test comment: run server network port
    port: int = 1234


@with_attrs_docs
class DummySettings(BaseSettings):
    #: test comment: multiline description of the 
    #: runserver class member 
    runserver: DummyRunserverSettings = DummyRunserverSettings()


def test_commented_base_model():
    assert DummyModel.__fields__['foo'] is not None
    assert DummyModel.__fields__['foo'].field_info is not None
    assert DummyModel.__fields__['foo'].field_info.description == 'test comment: description of member foo'


def test_commented_settings_model():
    assert DummySettings.__fields__['runserver'].field_info.description == 'test comment: multiline description of the\nrunserver class member'
    assert DummyRunserverSettings.__fields__['port'].field_info.description == 'test comment: run server network port'
