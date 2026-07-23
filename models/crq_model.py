from dataclasses import dataclass


@dataclass
class CRQ:

    crq: str
    sdatool: str
    descripcion: str
    portafolio: str
    fecha_instalacion: str
    certificaciones: list[str]


    def to_dict(self):

        return {

            "sdatool": self.sdatool,

            "descripcion": self.descripcion,

            "portafolio": self.portafolio,

            "fecha_instalacion":
            self.fecha_instalacion,

            "certificaciones":
            self.certificaciones

        }