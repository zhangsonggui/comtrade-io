#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from comtrade_io.model.type import AnalogChannelFlag, AnalogChannelType

AC_VOLTAGE_SUFFIXES = [
    "Ua",
    "Ub",
    "Uc",
    "3U0",
    "3Uo",
    "3UO",
    "UL",
    "Uab",
    "Ubc",
    "Uca",
    "Uac",
    "Uba",
    "Ucb",
]
AC_CURRENT_SUFFIXES = ["Ia", "Ib", "Ic", "3I0", "3Io", "3IO"]
ALL_AC_SUFFIXES = set(AC_VOLTAGE_SUFFIXES + AC_CURRENT_SUFFIXES)
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
DEVICE_MODELS = [
    "PSIU",
    "WDLK",
    "RCS",
    "CSC",
    "PCS",
    "PSL",
    "WXH",
    "PRS",
    "NSR",
    "BP",
    "ISA",
    "CZX",
    "WMH",
    "WCH",
]
SPLIT_KEYWORDS = ["充电保护", "保护", "断路器"]
MEASURE_KEYWORDS = ["电压", "电流", "功率", "频率"]
UNUSED_RESULT = "未使用通道"
PARTIAL_RESULT = "识别部分"
CORRECT_RESULT = "正确"

RE_AC_SUFFIX = re.compile(
    r"(?<![a-zA-Z0-9])(U[abcABC]|3[Uu][0oO]|[Ii][abcABC]|3[Ii][0oO]|UL|U[abcABC][abcABC])$"
)
RE_VOLTAGE_LEVEL = re.compile(r"(\d{2,3})\s*k[vV]")


class AnalogRecognizer:
    def extract_voltage(self, channel_name: str) -> str | None:
        match = RE_VOLTAGE_LEVEL.search(channel_name or "")
        return match.group(0).strip() if match else None

    def is_unused(self, channel_name: str) -> bool:
        if not channel_name or not channel_name.strip():
            return True

        name = re.sub(r"\s+", "", channel_name)
        if re.match(r"^\d+$", name):
            return True
        if re.match(r"^线路\d+", name) and not re.search(r"[一-鿿]{2,}线", name):
            return True
        if re.match(r"^电压\d+", name):
            return True
        if re.match(r"^电流\d+", name):
            return True
        if re.match(r"^模拟量\d+", name):
            return True
        if re.match(r"^模块\d+", name):
            return True
        if re.match(r"^\d+#模拟量通道", name):
            return True
        if re.match(r"^\d+#电流", name):
            return True
        if re.match(r"^\d+[-_]\d+#", name):
            return True
        return False

    def extract_phase(self, channel_name: str) -> str:
        if not channel_name or not channel_name.strip():
            return "无相别"

        name_clean = re.sub(r"\s+", "", channel_name)
        if "零序" in name_clean or re.search(r"3[UuIi][0oO]", channel_name):
            return "N相"

        suffix = channel_name.strip().split()[-1]
        if suffix in ("Ua", "Ia"):
            return "A相"
        if suffix in ("Ub", "Ib"):
            return "B相"
        if suffix in ("Uc", "Ic"):
            return "C相"

        if "A相" in name_clean or "A_" in channel_name or name_clean.endswith("A"):
            return "A相"
        if "B相" in name_clean or "B_" in channel_name or name_clean.endswith("B"):
            return "B相"
        if "C相" in name_clean or "C_" in channel_name or name_clean.endswith("C"):
            return "C相"

        match = re.search(r"(Ua|Ub|Uc|Ia|Ib|Ic)$", channel_name)
        if match:
            return {
                "Ua": "A相",
                "Ub": "B相",
                "Uc": "C相",
                "Ia": "A相",
                "Ib": "B相",
                "Ic": "C相",
            }[match.group(1)]

        match = re.search(r"[UuIi]([abcABC])$", channel_name)
        if match:
            return {"A": "A相", "B": "B相", "C": "C相"}[match.group(1).upper()]

        return "无相别"

    def extract_monitor(self, channel_name: str) -> str | None:
        if not channel_name or not channel_name.strip():
            return None
        if re.match(r"^\d+$", channel_name.strip()) or channel_name.strip() == "None":
            return None

        name = channel_name.strip()
        stripped = self._strip_ac_suffix(self._strip_digit_dash(name))
        best_pos = len(stripped)
        best_kw = None

        for keyword in ELEMENT_KEYWORDS:
            pos = stripped.find(keyword)
            if pos != -1 and pos < best_pos:
                best_pos = pos
                best_kw = keyword

        if best_kw is None:
            match = re.search(r"[一-鿿A-Za-z]线", stripped) or re.search(
                r"线", stripped
            )
            if match:
                best_kw = "线"
                best_pos = match.start() + 1

        if best_kw is not None:
            monitor = self._extract_keyword_monitor(name, stripped, best_pos, best_kw)
        else:
            monitor = self._extract_monitor_without_keyword(stripped)

        return monitor

    def classify(
        self, channel_name: str
    ) -> tuple[AnalogChannelType, AnalogChannelFlag]:
        if not channel_name or not channel_name.strip():
            return AnalogChannelType.O, AnalogChannelFlag.CONST

        name = channel_name.strip()
        name_clean = re.sub(r"\s+", "", channel_name)
        name_upper = channel_name.upper()

        if name in ("P", "Q"):
            return AnalogChannelType.O, AnalogChannelFlag.PW
        if name == "f":
            return AnalogChannelType.O, AnalogChannelFlag.FQ
        if any(
            keyword in channel_name
            for keyword in ("直1+", "直1-", "直2+", "直2-", "直+", "直-")
        ):
            return AnalogChannelType.D, AnalogChannelFlag.CONST
        if (
            "频率" in name_clean
            and "电压" not in name_clean
            and "电流" not in name_clean
        ):
            return AnalogChannelType.O, AnalogChannelFlag.FQ
        if "高频" in name_clean:
            return AnalogChannelType.O, AnalogChannelFlag.HF
        if "功率" in name_clean:
            return AnalogChannelType.O, AnalogChannelFlag.PW
        if "阻抗" in name_clean:
            return AnalogChannelType.O, AnalogChannelFlag.ZX
        if "直流" in name_clean or "DC" in name_upper:
            if "电流" in name_clean:
                return AnalogChannelType.D, AnalogChannelFlag.DA
            return AnalogChannelType.D, AnalogChannelFlag.DV

        suffix = channel_name.strip().split()[-1]
        if suffix in AC_VOLTAGE_SUFFIXES:
            return AnalogChannelType.A, AnalogChannelFlag.TV
        if suffix in AC_CURRENT_SUFFIXES:
            return AnalogChannelType.A, AnalogChannelFlag.TA

        match = re.search(
            r"(Ua|Ub|Uc|3U0|3Uo|3UO|Ia|Ib|Ic|3I0|3Io|3IO|UL)$", channel_name
        )
        if match:
            suffix = match.group(1)
            if suffix in AC_VOLTAGE_SUFFIXES:
                return AnalogChannelType.A, AnalogChannelFlag.TV
            if suffix in AC_CURRENT_SUFFIXES:
                return AnalogChannelType.A, AnalogChannelFlag.TA

        has_voltage = "电压" in name_clean or name_clean.endswith("压")
        has_current = "电流" in name_clean or name_clean.endswith("流")
        if has_voltage and has_current:
            if name_clean.rfind("电压") > name_clean.rfind("电流"):
                return AnalogChannelType.A, AnalogChannelFlag.TV
            return AnalogChannelType.A, AnalogChannelFlag.TA
        if has_voltage:
            return AnalogChannelType.A, AnalogChannelFlag.TV
        if has_current:
            return AnalogChannelType.A, AnalogChannelFlag.TA
        if (
            re.search(r"(?<!\w)[Uu][abcABC](?!\w)", channel_name)
            or "3U" in channel_name
        ):
            return AnalogChannelType.A, AnalogChannelFlag.TV
        if (
            re.search(r"(?<!\w)[Ii][abcABC](?!\w)", channel_name)
            or "3I" in channel_name
        ):
            return AnalogChannelType.A, AnalogChannelFlag.TA

        return AnalogChannelType.O, AnalogChannelFlag.CONST

    def _strip_ac_suffix(self, channel_name: str) -> str:
        parts = channel_name.rsplit(None, 1)
        if len(parts) == 2:
            if parts[1] in ALL_AC_SUFFIXES:
                return parts[0]
            if re.match(r"^AD\d+$", parts[1]):
                return channel_name
        return RE_AC_SUFFIX.sub("", channel_name)

    def _strip_digit_dash(self, channel_name: str) -> str:
        return re.sub(r"^\d+[-_]", "", channel_name)

    def _extract_keyword_monitor(
        self, original: str, stripped: str, keyword_pos: int, keyword: str
    ) -> str | None:
        keyword_end = keyword_pos + len(keyword)
        split_pos = len(stripped)

        for model in DEVICE_MODELS:
            match = re.search(
                re.escape(model) + r"[\s\-]?[a-zA-Z0-9_]*", stripped[keyword_end:]
            )
            if match and keyword_end + match.start() < split_pos:
                split_pos = keyword_end + match.start()

        for split_keyword in SPLIT_KEYWORDS + MEASURE_KEYWORDS:
            pos = stripped.find(split_keyword, keyword_end)
            if pos != -1 and pos < split_pos:
                split_pos = pos

        monitor = stripped[:keyword_end]
        voltage_prefix = self.extract_voltage(monitor)
        if voltage_prefix and monitor.startswith(voltage_prefix):
            after_voltage = monitor[len(voltage_prefix) :].strip(" _-")
            if after_voltage:
                monitor = after_voltage

        if keyword in ("线", "线路", "母线", "母联", "母差", "分段", "高抗", "电抗器"):
            remainder = stripped[keyword_end:split_pos]
            match = re.match(r"^(\d{2,5})", remainder)
            if match:
                after_number = (
                    original[keyword_end + len(match.group(1)) :]
                    if len(original) >= keyword_end + len(match.group(1))
                    else ""
                )
                has_measure_keyword = any(
                    measure in after_number for measure in MEASURE_KEYWORDS
                )
                has_model = any(
                    re.search(
                        re.escape(model) + r"[\s\-]?[a-zA-Z0-9_]*",
                        remainder[match.end() :],
                    )
                    for model in DEVICE_MODELS
                )
                if not has_model and not has_measure_keyword:
                    monitor += match.group(1)

        for model in DEVICE_MODELS:
            monitor = re.sub(
                r"[\s\-]?" + re.escape(model) + r"[\s\-]?[a-zA-Z0-9_]*", "", monitor
            )

        monitor = monitor.strip(" _-")
        return monitor or None

    def _extract_monitor_without_keyword(self, stripped: str) -> str | None:
        voltage_level = self.extract_voltage(stripped)
        if voltage_level:
            voltage_end = stripped.find(voltage_level) + len(voltage_level)
            after_voltage = stripped[voltage_end:].strip(" _-")
            after_voltage = re.sub(
                r"(电压|电流|功率|频率|保护|信号).*$", "", after_voltage
            )
            after_voltage = re.sub(r"\d{2,5}$", "", after_voltage).strip(" _-")
            return after_voltage or voltage_level

        if "直流" in stripped:
            match = re.search(r"直流[^\s]*", stripped)
            return match.group(0) if match else stripped[:20]

        return None
