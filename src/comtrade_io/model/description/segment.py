from pydantic import BaseModel, Field


class Segment(BaseModel):
    """采样点率模型

    描述单条采样段信息，包含采样点数和结束点。
    用于定义COMTRADE文件中各采样段的采样率配置。

    字符串表示形如: "1920,1000"

    属性:
        samp: 采样点数，每个采样段的采样点数量，必须大于0
        end_point: 结束采样点数，该采样段结束时的累计采样点数，必须大于0
    """
    samp: int = Field(..., description="采样率，单位（Hz）", gt=0)
    end_point: int = Field(..., description="该段结束采样点号", gt=0)
    start_point: int | None = Field(default=None, description="该段起始采样点号")
    cycle_point_num: float | None = Field(default=None, description="该段周期采样点数")
    count: int | None = Field(default=None, description="该段采样点数")

    def __str__(self) -> str:
        """序列化为逗号分隔的字符串

        将采样点率对象转换为COMTRADE配置文件格式的字符串。

        Returns:
            str: 逗号分隔的字符串，格式为 "samp,end_point"
        """
        return f"{self.samp},{self.end_point}"
