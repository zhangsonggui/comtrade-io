from xml.etree.ElementTree import Element

from ...model.description import Description
from ...model.description.header import Header
from ...utils import parse_float


class DescriptionElement:

    @classmethod
    def from_xml(cls, element: Element, ns: dict) -> Description:
        station_name = element.get("station_name", "")
        rec_dev_name = element.get("rec_dev_name", "")
        return Description(
            data_model_version=parse_float(element.get("version", "1.0")),
            header=Header(station=station_name, recorder=rec_dev_name),
            xmlns_scl=element.get("xmlns:scl", "http://www.iec.ch/61850/2003/SCL"),
            xmlns_xsi=element.get(
                "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance"
            ),
            xsi_schema_location=element.get(
                "xsi:schemaLocation",
                "http://www.iec.ch/61850/2003/SCLcomtrade_mdl_v1.1.xsd",
            ),
        )
