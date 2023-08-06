import sys
import os

# Get the absolute path of the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys_path_append = os.path.join(project_root)

# Add the 'src' directory to the Python path
sys.path.append(sys_path_append)

from pydantic import BaseSettings, BaseModel
from pyconfme.settings_doc.settings_doc import with_attrs_docs   # pyright: ignore[reportMissingImports]



@with_attrs_docs
class DummyModel(BaseModel):
    #: test comment: description of member foo
    foo: str

@with_attrs_docs
class DummyRunserverSettings(BaseSettings):
    #: test comment: run server network port
    name: DummyModel


print(DummyModel.__fields__["foo"].field_info)

print(DummyRunserverSettings.__fields__)
