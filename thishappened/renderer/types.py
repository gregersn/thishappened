
from typing import Any, Dict, List, Literal, TypedDict, Union


class RawTextData(TypedDict):
    element: Literal['raw_text']
    children: str
    escape: bool


class HeadingData(TypedDict):
    element: Literal['heading']
    children: List['MDElement']
    level: int


class BlankLineData(TypedDict):
    element: Literal['blank_line']


class LineBreakData(TypedDict):
    element: Literal['line_break']
    soft: bool


class ParagraphData(TypedDict):
    element: Literal['paragraph']
    children: List['MDElement']


class DocumentData(TypedDict):
    element: Literal['document']
    link_ref_defs: Dict[Any, Any]
    children: List['MDElement']


class ListData(TypedDict):
    element: Literal['list']
    children: List['MDElement']
    ordered: bool
    start: int
    bullet: str


class ListItemData(TypedDict):
    element: Literal['list_item']
    children: List['MDElement']


class EmphasisData(TypedDict):
    element: Literal['emphasis']
    children: List['MDElement']


class StrongEmphasisData(TypedDict):
    element: Literal['strong_emphasis']
    children: List['MDElement']


class CodeSpanData(TypedDict):
    element: Literal['code_span']


MDElement = Union[RawTextData, HeadingData,
                  BlankLineData, EmphasisData, StrongEmphasisData,
                  ListItemData, ListData, ParagraphData, LineBreakData]
