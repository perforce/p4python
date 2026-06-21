from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import (
    Any,
    ClassVar,
    Final,
    Literal,
    NoReturn,
    TypedDict,
    overload,
    type_check_only,
)

import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

import P4API

class P4Exception(Exception):
    value: str
    errors: list[str] | None
    warnings: list[str] | None
    def __init__(self, value: str | tuple[str, list[str], list[str]]) -> None: ...

class Spec(dict[str, str | list[str]]):
    def __init__(self, fieldmap: Mapping[str, str] | None = None) -> None: ...
    def __getattr__(self, attr: str) -> str | list[str]: ...
    def __setattr__(self, attr: str, value: str | list[str]) -> None: ...
    def __setitem__(self, key: str, value: str | list[str]) -> None: ...
    def permitted_fields(self) -> Mapping[str, str] | None: ...

class Integration:
    how: str
    file: str
    srev: int
    erev: int
    def __init__(self, how: str, file: str, srev: int, erev: int) -> None: ...

class Revision:
    depotFile: DepotFile
    integrations: list[Integration]
    rev: int | None
    change: int | None
    action: Literal["add", "edit", "delete", "branch", "integrate"] | None
    type: str | None
    time: datetime | None
    user: str | None
    client: str | None
    desc: str | None
    digest: str | None
    fileSize: str | None
    def __init__(self, depotFile: DepotFile) -> None: ...
    def integration(self, how: str, file: str, srev: int, erev: int) -> Integration: ...
    def each_integration(self) -> Iterator[Integration]: ...

class DepotFile:
    depotFile: str
    revisions: list[Revision]
    def __init__(self, name: str) -> None: ...
    def new_revision(self) -> Revision: ...
    def each_revision(self) -> Iterator[Revision]: ...
    def str_revision(self, rev: Revision, revFormat: str, changeFormat: str) -> str: ...
    def str_integration(self, integ: Integration) -> str: ...

class Resolver:
    def resolve(self, mergeInfo: P4API.P4MergeData, /) -> P4API.ResolveAction: ...
    def actionResolve(
        self, mergeInfo: P4API.P4ActionMergeData, /
    ) -> P4API.ResolveAction: ...

class OutputHandler:
    REPORT: ClassVar = 0
    HANDLED: ClassVar = 1
    CANCEL: ClassVar = 2

    def outputText(self, s: str, /) -> _HandlerResult: ...
    def outputBinary(self, b: bytes, /) -> _HandlerResult: ...
    def outputStat(self, h: Spec | dict[str, Any], /) -> _HandlerResult: ...
    def outputInfo(self, i: str, /) -> _HandlerResult: ...
    def outputMessage(self, e: P4API.P4Message, /) -> _HandlerResult: ...

_HandlerResult: TypeAlias = Literal[0, 1, 2]

class ReportHandler(OutputHandler): ...

class FilelogOutputHandler(OutputHandler):
    def outputFilelog(self, f: DepotFile) -> _HandlerResult: ...

class Progress:
    TYPE_SENDFILE: ClassVar = 1
    TYPE_RECEIVEFILE: ClassVar = 2
    TYPE_TRANSFER: ClassVar = 3
    TYPE_COMPUTATION: ClassVar = 4

    UNIT_PERCENT: ClassVar = 1
    UNIT_FILES: ClassVar = 2
    UNIT_KBYTES: ClassVar = 3
    UNIT_MBYTES: ClassVar = 4

    def init(self, type: Literal[1, 2, 3, 4, 5, 6, 7]) -> None: ...
    def setDescription(
        self, description: str, units: Literal[0, 1, 2, 3, 4, 5, 6, 7]
    ) -> None: ...
    def setTotal(self, total: int) -> None: ...
    def update(self, position: int) -> None: ...
    def done(self, fail: bool | int) -> None: ...

class TextProgress(Progress):
    TYPES: Final[list[str]]
    UNITS: Final[list[str]]

    def init(self, type: Literal[1, 2, 3, 4, 5, 6, 7]) -> None: ...
    def setDescription(
        self, description: str, units: Literal[0, 1, 2, 3, 4, 5, 6, 7]
    ) -> None: ...
    def setTotal(self, total: int) -> None: ...
    def update(self, position: int) -> None: ...
    def done(self, fail: bool | int) -> None: ...

def processFilelog(h: Mapping[str, Any]) -> DepotFile: ...

class Map(P4API.P4Map):
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, maps: list[str]) -> None: ...
    @overload
    def __init__(self, map: str) -> None: ...
    @overload
    def __init__(self, lhr: str, rhs: str) -> None: ...

    LEFT2RIGHT: ClassVar = True
    RIGHT2LEFT: ClassVar = False

    def is_empty(self) -> bool: ...
    def includes(self, path: str, left_to_right: bool = True, /) -> bool: ...
    def reverse(self) -> Map: ...
    @overload
    def insert(self, maps: list[str], /) -> None: ...
    @overload
    def insert(self, lhr: str, rhs: str | None = None, /) -> None: ...

class P4(P4API.P4Adapter):
    # See https://help.perforce.com/helix-core/apis/p4python/current/Content/P4Python/python.p4.html
    # for documented public API.  Most documented attributes are inherited from P4API, and are annotated there instead.

    RAISE_ALL: ClassVar = 2
    RAISE_ERROR: ClassVar = 1
    RAISE_ERRORS: ClassVar = 1
    RAISE_NONE: ClassVar = 0

    EV_USAGE: ClassVar = 0x01
    EV_UNKNOWN: ClassVar = 0x02
    EV_CONTEXT: ClassVar = 0x03
    EV_ILLEGAL: ClassVar = 0x04
    EV_NOTYET: ClassVar = 0x05
    EV_PROTECT: ClassVar = 0x06

    EV_EMPTY: ClassVar = 0x11

    EV_FAULT: ClassVar = 0x21
    EV_CLIENT: ClassVar = 0x22
    EV_ADMIN: ClassVar = 0x23
    EV_CONFIG: ClassVar = 0x24
    EV_UPGRADE: ClassVar = 0x25
    EV_COMM: ClassVar = 0x26
    EV_TOOBIG: ClassVar = 0x27

    E_EMPTY: ClassVar = 0
    E_INFO: ClassVar = 1
    E_WARN: ClassVar = 2
    E_FAILED: ClassVar = 3
    E_FATAL: ClassVar = 4

    specfields: Final[dict[str, tuple[str, str]]]

    @classmethod
    def identify(cls) -> str: ...
    def __getattr__(self, name: str) -> Any: ...
    def __init__(self, **kwargs: Any) -> None: ...
    def is_ignored(self, path: str | Path) -> bool: ...
    def log_messages(self) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]: ...
    @contextmanager
    def while_tagged(self, t: bool) -> Iterator[None]: ...
    @contextmanager
    def at_exception_level(self, e: Literal[0, 1, 2]) -> Iterator[None]: ...
    @contextmanager
    def using_handler(self, c: OutputHandler) -> Iterator[None]: ...
    @contextmanager
    def saved_context(self, **kargs: Any) -> Iterator[None]: ...
    @contextmanager
    def temp_client(self, prefix: str, template: str) -> Iterator[str]: ...
    def run(self, /, *args: Any, **kargs: Any) -> _P4Result: ...

    # Command methods that have explicit implementations with additional processing
    def run_submit(
        self,
        *args: Any | Spec | dict[str, str | list[str]],
        progress: Progress | None = None,
        **kargs: Any,
    ) -> _P4Result: ...
    def run_shelve(
        self,
        *args: Any | Spec | dict[str, str | list[str]],
        **kargs: Any,
    ) -> _P4Result: ...
    @overload
    def delete_shelve(
        self,
        changelist_number: int | str,
        /,
        *args: str,
        **kargs,
    ) -> list[str]: ...
    @overload
    def delete_shelve(self, *args: Any, **kargs: Any) -> list[str]: ...
    def run_login(self, *args: Any, **kargs: Any) -> _P4Result: ...
    def run_password(
        self, oldpass: str, newpass: str, *args: Any, **kargs: Any
    ) -> list[str]: ...
    def run_filelog(self, *args: Any, **kwargs: Any) -> list[DepotFile | str]: ...
    def run_print(self, *args: Any, **kargs) -> list[str | bytes]: ...
    def run_resolve(
        self,
        *args: Any,
        resolver: Resolver | None = None,
        **kargs: Any,
    ) -> _P4Result: ...
    def run_tickets(self) -> list[TicketInfo]: ...
    def run_init(self, *args: Any, **kargs: Any) -> NoReturn: ...
    def run_clone(self, *args: Any, **kargs: Any) -> NoReturn: ...

_P4Result: TypeAlias = list[dict[str, Any] | Spec | str]

@type_check_only
class TicketInfo(TypedDict):
    Host: str
    User: str
    Ticket: str

class PyKeepAlive:
    def __init__(self) -> None: ...
    def isAlive(self) -> Literal[0, 1] | bool: ...

def init(
    user: str | None = None,
    client: str | None = None,
    directory: str | None = None,
    port: str | None = None,
    casesensitive: bool | None = None,
    unicode: bool | None = None,
    **kwargs: Any,
) -> P4: ...
def clone(
    user: str | None = None,
    client: str | None = None,
    directory: str | None = None,
    depth: int | None = None,
    verbose: bool | None = None,
    port: str | None = None,
    remote: str | None = None,
    file: str | None = None,
    noarchive: bool | None = None,
    progress: Progress | None = None,
    **kwargs: Any,
) -> P4: ...
