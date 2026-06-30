from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .channel import ChannelBaseModel
from ..description import ReferenceBaseModel
from ..type import Contact


class StatusChangeRecord(BaseModel):
    """数字量通道变位记录

    记录某一采样点处的状态信息，用于描述数字量通道在初始时刻及每次变位时刻的状态。

    属性:
        sample_point: 采样点号（1-based）
        timestamp: 该采样点对应的绝对时间戳
        state: 该采样点处的状态值（0/1）
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    sample_point: int = Field(..., description="采样点号（1-based）")
    timestamp: datetime | None = Field(default=None, description="采样点绝对时间戳")
    state: int = Field(..., description="采样点状态值（0/1）")

    def __iter__(self):
        return iter((self.sample_point, self.timestamp, self.state))

    def __repr__(self) -> str:
        return (
            f"StatusChangeRecord(sample_point={self.sample_point}, "
            f"timestamp={self.timestamp}, state={self.state})"
        )

    def to_dict(self) -> dict:
        return {
            "sample_point": self.sample_point,
            "timestamp": self.timestamp,
            "state": self.state,
        }


class Status(ChannelBaseModel, ReferenceBaseModel):
    """数字量通道类

    表示COMTRADE配置文件中的数字量（状态量）通道信息。

    属性:
        index: 通道索引（模拟通道是An，数字通道是Dn，统一用index表示）
        name: 通道标识（ch_id）
        phase: 通道相别标识（ph）
        equip: 被监视的电路元件（ccbm）
        reference: IEC61850参引
        contact: 状态通道正常状态，默认为常开
        data: 通道数据，一维数组
    """

    model_config = ConfigDict(extra="allow")
    contact: Contact = Field(
        default=Contact.NormallyOpen, description="状态通道正常状态"
    )
    equipment_no: str | None = Field(
        default=None, description="保护/断路器/刀闸序号，如Relay_#1、Breaker_#1"
    )
    change_records: list[StatusChangeRecord] | None = Field(
        default=None,
        description="变位记录列表，含0时刻初始状态及每次变位时刻的采样点号、时间戳、状态",
    )

    def __str__(self) -> str:
        """序列化为逗号分隔的字符串

        将数字量通道对象转换为COMTRADE配置文件格式的字符串。

        返回:
            str: 逗号分隔的通道信息字符串
        """
        attrs = [
            f"{self.index}",
            f"{self.name}",
            f"{self.phase.value}",
            f"{self.equip if self.equip else ''}",
            f"{self.contact.value}",
        ]
        return ",".join(attrs)

    def to_dmf(self):
        """将数字量通道对象转换为DMF格式字符串

        返回:
            str: DMF格式的XML字符串
        """
        attrs = [
            f'idx_cfg="{self.index}"',
            f'idx_org="{self.idx_org}"',
            f'type="{self.type.value if self.type else ""}"',
            f'flag="{self.flag.value if self.flag else ""}"',
            f'contact="{self.contact.name}"',
            f'srcRef="{self.reference if self.reference else ""}"',
        ]
        return f"\t<scl:StatusChannel {' '.join(attrs)} />"

    def to_inf(self):
        """将数字量通道对象转换为INF格式字符串

        返回:
            str: INF格式的字符串
        """
        attrs = [
            f"[Public Status_Channel_#{self.index}]",
            f"Channel_ID={self.name}",
            f"Phase_ID={self.phase.value}",
            f"Monitored_Component={self.reference}",
            f"Normal_State={self.contact.value}",
        ]
        return "\n".join(attrs)

    def to_inf_parameter(self) -> str:
        """将数字量通道对象转换为参数段CHNL_INFO格式字符串

        返回:
            str: 参数段CHNL_INFO格式字符串
        """
        type_name = self.type.name if self.type else ""
        flag_name = self.flag.name if self.flag else ""
        obj_val = self.equipment_no if self.equipment_no is not None else ""

        return f"{self.index}, {self.idx_org}, {self.name}, {type_name}, {flag_name}, {obj_val}"
