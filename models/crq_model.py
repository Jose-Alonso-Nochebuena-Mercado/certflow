from dataclasses import dataclass


@dataclass
class CRQ:

    crq: str
    sdatool: str
    descripcion: str
    objetivo_cambio: str
    channel: str
    portafolio: str
    fecha_instalacion: str
    certificaciones: list[str]


    def to_dict(self):

        return {

            "sdatool": self.sdatool,

            "descripcion": self.descripcion,

            "objetivo_cambio": self.objetivo_cambio,

            "channel": self.channel,

            "portafolio": self.portafolio,

            "fecha_instalacion":
            self.fecha_instalacion,

            "certificaciones":
            self.certificaciones

        }