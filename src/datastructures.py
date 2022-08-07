from dataclasses import dataclass
from typing import Callable, Any, Optional

from src import errors

class DLList:
    """
    A double linked list datastructure.

    Used to allow linking together code
    and editing them in convenient chunks.
    """
    #Primary properties
    @property
    def next(self):
        return self._next
    @next.setter
    def next(self, value: Optional["DLList"]):
        if self.next is not value:
            if self._next is not None:
                #Release current next node
                self._next._last = None
            self._next = value
            self._next.last = self
    @property
    def last(self):
        return self._last
    @last.setter
    def last(self, value: Optional["DLList"]):
        if self._last is not value:
            if self._last is not None:
                #Release current next node
                self._last._next = None
            self._last = value
            self._last._next = self
    #Utility
    @property
    def root(self):
        """Get root of linked list"""
        if self.last is None:
            return self
        return self.last.root()
    def append(self, block: "DLList"):
        """Recursively append to end of linked list"""
        if self.next is None:
            self.next = block
        else:
            self.next.append(block)

    def __init__(self,
                 next: Optional["DLList"]=None,
                 last: Optional["DLList"]=None):
        self._next = next
        self._last = last
    def __iter__(self)->"DLList":
        yield self
        node = self
        while node.next is not None:
            node = node.next
            yield node



class CodeBlock(DLList):
    """
    A codeblock contains a representation of
    a chunk of code that belongs in a temporary
    file.

    It also contains an error callback, capable
    of constructing an exception from another exception,
    which should be associated with the codeblock if
    things go wrong.

    It is the unit of code constructed by the primary
    logic.
    """
    @property
    def end(self):
        """Returns the char this segment ends on."""
        if self.last is None:
            return len(self.code)
        return len(self.code) + self.last.end
    @property
    def start(self):
        """Returns the starting char of this in the list"""
        if self.last is None:
            return 0
        return self.last.end
    def fetch_exception(self, trace: Any, r: errors.SourceRange)-> errors.Types:
        """Fetches the exception belonging to this region of the source"""
        if self.start <= r.start and self.end >= r.end:
            output = self.exception(trace)
            return output
        if self.next is not None:
            return self.next.fetch_exception(trace, r)
        msg = "Error encountered while preprocessing. Context Unknown"
        output = errors.UnhandledPreprocessingError(trace, msg)
        return output
    def read(self)->str:
        """Read out contents of the linked list as a singular string"""
        if self.next is None:
            return self.code
        return self.code + self.next.read()
    def __init__(self,
                 code: str,
                 exception_builder: Callable[[Any], errors.Types],
                 next: Optional["CodeBlock"] = None
                 ):

        self.code = code
        self.exception = exception_builder
        super().__init__(next)



@dataclass
class CompileStub:
    """
    A small class representing
    the information needed to
    let torchscript compile.
    """
    path: str
    name: str
    code: str
    write: Callable[[str], None]
    rcb: Callable[[str], Any]
