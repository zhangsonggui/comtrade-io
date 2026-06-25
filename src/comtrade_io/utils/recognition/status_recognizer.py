"""数字量通道识别模块：根据通道名称自动识别通道类型和标志"""

import re
from typing import Tuple

from pydantic import BaseModel, Field

from ...model.type import DigitalChannelFlag, DigitalChannelType


class StatusChannelInfo(BaseModel):
    """数字量通道识别结果"""

    voltage_level: str | None = Field(default=None, description="电压等级")
    monitored_component: str | None = Field(default=None, description="监视元件")
    protection_model: str | None = Field(default=None, description="保护型号")
    channel_type: DigitalChannelType | None = Field(
        default=None, description="通道类型"
    )
    channel_flag: DigitalChannelFlag | None = Field(
        default=None, description="通道标识"
    )
    recognition_status: str = Field(default="", description="识别状态")


class StatusRecognizer:
    """数字量通道识别器：根据通道名称识别数字量通道属性"""

    ELEMENT_KEYWORDS = [
        "变压器",
        "电抗器",
        "母差",
        "母线",
        "母联",
        "分段",
        "线路",
        "主变",
        "高抗",
    ]
    TRAILING_DIGIT_OK = {"线路", "线", "母差", "母线", "母联", "分段", "高抗", "电抗器"}
    MODEL_PATTERN = re.compile(
        r"(?:PSIU|WDLK|RCS|CSC|PCS|PSL|WXH|PRS|NSR|BP|ISA|CZX|WMH|WCH)[\s-]?[a-zA-Z0-9_]*",
        re.I,
    )
    SPLIT_KW = re.compile(r"(?:充电保护|保护|断路器)")
    VOLTAGE_PATTERN = re.compile(r"(\d{2,3})\s*kV", re.I)
    SIGNAL_SUFFIXES = [
        r"A相开关量",
        r"B相开关量",
        r"C相开关量",
        r"A相分位",
        r"B相分位",
        r"C相分位",
        r"A相$",
        r"B相$",
        r"C相$",
    ]

    def is_unused(self, name: str) -> bool:
        if not name or not name.strip():
            return True
        if re.match(r"^(?:\d+|开关量\d+|\d+-\d+#.*|开入\d+)$", name):
            return True
        return bool(re.search(r"一般开关量|开关量通道|备用开关量|未命名开关量", name))

    def extract_voltage(self, name: str) -> str | None:
        m = self.VOLTAGE_PATTERN.search(name)
        return m.group(0).upper() if m else None

    def extract_model(self, name: str) -> str | None:
        models = self.MODEL_PATTERN.findall(name)
        models = [m for m in models if len(m) >= 3]
        return models[0] if models else None

    def extract_monitor(self, name: str) -> str | None:
        if not name:
            return None
        if re.match(r"^(?:\d+|开关量\d+|\d+-\d+#.*|开入\d+)$", name):
            return None
        if re.search(r"一般开关量|开关量通道|备用开关量|未命名开关量", name):
            return None

        elem_pos, elem_len, elem_text = None, 0, ""
        for ek in sorted(self.ELEMENT_KEYWORDS, key=len, reverse=True):
            pos = name.find(ek)
            if pos != -1 and (elem_pos is None or pos < elem_pos):
                elem_pos, elem_len, elem_text = pos, len(ek), ek

        if elem_pos is None:
            pos = name.find("线")
            if (
                pos != -1
                and pos > 0
                and any("一" <= c <= "鿿" for c in name[max(0, pos - 3) : pos])
            ):
                elem_pos, elem_len, elem_text = pos, 1, "线"

        min_split = (elem_pos + elem_len) if elem_pos is not None else 0
        split_at = len(name)
        for m in self.MODEL_PATTERN.finditer(name):
            if m.start() >= min_split and m.start() < split_at:
                split_at = m.start()
        for m in self.SPLIT_KW.finditer(name):
            if m.start() >= min_split and m.start() < split_at:
                split_at = m.start()

        prefix = name[:split_at].strip()
        if elem_pos is not None:
            ek_text = name[elem_pos : elem_pos + elem_len]
            idx = prefix.find(ek_text)
            if idx != -1:
                prefix = prefix[: idx + elem_len]
                if any(k in elem_text for k in self.TRAILING_DIGIT_OK):
                    after_elem = name[elem_pos + elem_len : split_at]
                    md = re.match(r"(\d{3,5})", after_elem)
                    if md:
                        after_digits = name[elem_pos + elem_len + md.end() :]
                        if not (
                            self.MODEL_PATTERN.search(after_digits)
                            or self.SPLIT_KW.search(after_digits)
                        ):
                            prefix += md.group()

        if split_at == len(name):
            for sfx in self.SIGNAL_SUFFIXES + [r"开关量\d*$"]:
                prefix = re.sub(sfx, "", prefix)

        m_kv = re.search(r"\d+\s*kV", prefix, re.I)
        if (
            m_kv
            and m_kv.start() > 0
            and re.search(r"[A-Za-z#_]", prefix[: m_kv.start()])
        ):
            prefix = prefix[m_kv.start() :]

        prefix = re.sub(
            r"(?:RCS|CSC|PCS|PSL|WXH|PRS|NSR|BP[\s-]?[a-zA-Z0-9_]*|ISA|CZX|PSIU|WDLK|WMH|WCH)",
            "",
            prefix,
            flags=re.I,
        )
        prefix = re.sub(r"[_]+", "", prefix).strip()
        for sfx in self.SIGNAL_SUFFIXES:
            prefix = re.sub(sfx, "", prefix)

        m_kv_strip = self.VOLTAGE_PATTERN.match(prefix)
        if m_kv_strip:
            after = prefix[m_kv_strip.end() :].strip(" _-")
            if after:
                prefix = after

        return prefix.strip() or None

    def classify(self, name: str) -> Tuple[DigitalChannelType, DigitalChannelFlag]:
        if not name:
            return DigitalChannelType.Other, DigitalChannelFlag.GENERAL

        if re.match(r"^\d+$", name):
            return DigitalChannelType.Other, DigitalChannelFlag.GENERAL
        if re.search(r"一般开关量|开关量通道|备用开关量|未命名开关量", name):
            return DigitalChannelType.Other, DigitalChannelFlag.GENERAL
        if re.match(r"^开关量\d+", name):
            return DigitalChannelType.Other, DigitalChannelFlag.GENERAL
        if re.match(r"^\d+-\d+#", name):
            return DigitalChannelType.Other, DigitalChannelFlag.GENERAL
        if re.match(r"^开入\d+", name):
            return DigitalChannelType.Other, DigitalChannelFlag.GENERAL
        if re.search(r"收远跳|远传开出", name):
            return DigitalChannelType.Other, DigitalChannelFlag.GENERAL

        if re.search(r"告警|异常|断线|报警|故障|失压", name):
            if re.search(r"通道|通信", name):
                return DigitalChannelType.Device_Alarm, DigitalChannelFlag.CHNL_FAULT
            if re.search(r"CT|TA\b|电流", name):
                return DigitalChannelType.Device_Alarm, DigitalChannelFlag.TA_Break
            if re.search(r"PT|TV\b|电压|压变", name):
                return DigitalChannelType.Device_Alarm, DigitalChannelFlag.TV_Break
            return DigitalChannelType.Device_Alarm, DigitalChannelFlag.WARN_GENERAL

        m_close = re.search(r"(?:^|\s|,)(合[A-C])\s*(?:$|\s|,)", name)
        if m_close:
            ph = m_close.group(1)[1]
            _map = {
                "A": DigitalChannelFlag.Jump_A_Close,
                "B": DigitalChannelFlag.Jump_B_Close,
                "C": DigitalChannelFlag.Jump_C_Close,
            }
            return DigitalChannelType.Breaker_Pos, _map[ph]

        bps = re.search(r"(A相|B相|C相)开关量", name)
        if bps:
            ph = bps.group(1)[0]
            _map = {
                "A": DigitalChannelFlag.Jump_A_Close,
                "B": DigitalChannelFlag.Jump_B_Close,
                "C": DigitalChannelFlag.Jump_C_Close,
            }
            return DigitalChannelType.Breaker_Pos, _map[ph]

        op = re.search(r"(A相|B相|C相)分位", name)
        if op:
            ph = op.group(1)[0]
            _map = {
                "A": DigitalChannelFlag.Jump_A_Break,
                "B": DigitalChannelFlag.Jump_B_Break,
                "C": DigitalChannelFlag.Jump_C_Break,
            }
            return DigitalChannelType.Breaker_Pos, _map[ph]

        hp = re.search(r"保护|跳闸|重合闸|永跳|发信|收信|三跳|出口|动作", name)
        sj = re.search(r"(?:^|\s|,)([ABC]跳)\s*(?:$|\s|,)", name)
        hr = re.search(r"远动|远跳|远传|远信|远方", name)
        hm = re.search(r"失灵|不一致|启动", name)
        hd = re.search(r"母差|母线.*动|差动", name)

        if hp or sj or hr or hm or hd:
            if re.search(r"重合闸", name):
                return DigitalChannelType.Relay_Act, DigitalChannelFlag.Close_Break
            if re.search(r"永跳|闭锁重合", name):
                return DigitalChannelType.Relay_Act, DigitalChannelFlag.Jump_For_Keeps
            if re.search(r"三跳|三相.*跳|不一致", name):
                return DigitalChannelType.Relay_Act, DigitalChannelFlag.Jump_ABC
            if re.search(r"发信", name):
                return DigitalChannelType.Relay_Act, DigitalChannelFlag.Send
            if re.search(r"收信", name):
                return DigitalChannelType.Relay_Act, DigitalChannelFlag.Recv
            if sj:
                ph = sj.group(1)[0]
                _map = {
                    "A": DigitalChannelFlag.Jump_A,
                    "B": DigitalChannelFlag.Jump_B,
                    "C": DigitalChannelFlag.Jump_C,
                }
                return DigitalChannelType.Relay_Act, _map[ph]
            if re.search(r"跳A|A相.*跳|跳闸.*A", name):
                return DigitalChannelType.Relay_Act, DigitalChannelFlag.Jump_A
            if re.search(r"跳B|B相.*跳|跳闸.*B", name):
                return DigitalChannelType.Relay_Act, DigitalChannelFlag.Jump_B
            if re.search(r"跳C|C相.*跳|跳闸.*C", name):
                return DigitalChannelType.Relay_Act, DigitalChannelFlag.Jump_C
            if re.search(r"远动|远跳|远传|远信|远方", name):
                return DigitalChannelType.Relay_Act, DigitalChannelFlag.TR
            if re.search(r"跳闸|失灵|启动|动作|出口|差动|母差", name):
                return DigitalChannelType.Relay_Act, DigitalChannelFlag.TR
            return DigitalChannelType.Relay_Act, DigitalChannelFlag.TR

        ib = bool(
            re.search(r"断路器|开关位置", name)
            or re.search(r"合位|跳位|合闸位置|跳闸位置|合闸状态|分位", name)
            or re.search(r"(?:断路器|开关|线路|母线|主变|变压器).*位", name)
            or re.search(r"A相开关量|B相开关量|C相开关量", name)
        )
        if ib:
            if re.search(r"高压侧", name):
                flag = (
                    DigitalChannelFlag.Jump_Break_HIGH
                    if re.search(r"跳|分", name)
                    else DigitalChannelFlag.Jump_Close_HIGH
                )
                return DigitalChannelType.Breaker_Pos, flag
            if re.search(r"中压侧", name):
                flag = (
                    DigitalChannelFlag.Jump_Break_MEDIUM
                    if re.search(r"跳|分", name)
                    else DigitalChannelFlag.Jump_Close_MEDIUM
                )
                return DigitalChannelType.Breaker_Pos, flag
            if re.search(r"低压侧", name):
                flag = (
                    DigitalChannelFlag.Jump_Break_LOW
                    if re.search(r"跳|分", name)
                    else DigitalChannelFlag.Jump_Close_LOW
                )
                return DigitalChannelType.Breaker_Pos, flag
            ia = re.search(r"A相|A\s*相", name)
            ib_ = re.search(r"B相|B\s*相", name)
            ic = re.search(r"C相|C\s*相", name)
            ho = re.search(r"跳位|跳闸|分位", name)
            if ia:
                return DigitalChannelType.Breaker_Pos, (
                    DigitalChannelFlag.Jump_A_Break
                    if ho
                    else DigitalChannelFlag.Jump_A_Close
                )
            if ib_:
                return DigitalChannelType.Breaker_Pos, (
                    DigitalChannelFlag.Jump_B_Break
                    if ho
                    else DigitalChannelFlag.Jump_B_Close
                )
            if ic:
                return DigitalChannelType.Breaker_Pos, (
                    DigitalChannelFlag.Jump_C_Break
                    if ho
                    else DigitalChannelFlag.Jump_C_Close
                )
            if ho:
                return DigitalChannelType.Breaker_Pos, DigitalChannelFlag.Jump_Break
            if re.search(r"合位|合闸", name):
                return DigitalChannelType.Breaker_Pos, DigitalChannelFlag.Jump_Close
            if re.search(r"全位置|位置", name):
                return DigitalChannelType.Breaker_Pos, DigitalChannelFlag.Jump_Close
            return DigitalChannelType.Breaker_Pos, DigitalChannelFlag.Jump_Close

        if re.search(r"一般开入|开关量|开入|类开入", name):
            return DigitalChannelType.Switch_Pos, DigitalChannelFlag.GENERAL

        return DigitalChannelType.Other, DigitalChannelFlag.GENERAL

    def identify(self, name: str) -> StatusChannelInfo:
        voltage = self.extract_voltage(name)
        monitor = self.extract_monitor(name)
        model = self.extract_model(name)
        ch_type, ch_flag = self.classify(name)

        identified = sum(
            1 for v in (voltage, monitor, model, ch_type, ch_flag) if v is not None
        )
        if identified >= 5:
            status = "正确"
        elif identified >= 2:
            status = "识别部分"
        else:
            status = "识别错误"

        return StatusChannelInfo(
            voltage_level=voltage,
            monitored_component=monitor,
            protection_model=model,
            channel_type=ch_type,
            channel_flag=ch_flag,
            recognition_status=status,
        )
