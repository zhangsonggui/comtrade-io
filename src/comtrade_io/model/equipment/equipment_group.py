from pydantic import BaseModel, Field

from ..description import Description
from ..channel import Analog, Status
from .bus import Bus
from .line import Line
from .transformer import Transformer

class EquipmentGroup(BaseModel):
    description: Description = Field(default_factory=Description, description="描述文件")
    buses: list[Bus] | None = Field(default_factory=list, description="母线")
    lines: list[Line] | None = Field(default_factory=list, description="线路")
    transformers: list[Transformer] | None = Field(
        default_factory=list, description="变压器"
    )
    analogs: dict[int, Analog] | None = Field(
        default_factory=dict, description="模拟通道"
    )
    statuses: dict[int, Status] | None = Field(
        default_factory=dict, description="状态量通道"
    )
