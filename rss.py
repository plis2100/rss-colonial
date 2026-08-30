import urllib.request
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urljoin

WEB_URL = "https://www.colonial-sfl.com/notas-de-prensa"
BASE_URL = "https://www.colonial-sfl.com"
OUTPUT_FILE = Path("colonial.xml")


def descargar_notas():
    solicitud = urllib.request.Request(
        WEB_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124 Safari/537.36"
            ),
            "Accept": "text/html",
        },
    )

    with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
        contenido = respuesta.read()

    soup = BeautifulSoup(contenido, "html.parser")

    notas = []
    enlaces_encontrados = set()

    for bloque in soup.select("div.file.normal-style"):
        titulo_elemento = bloque.select_one(".file__title")
        fecha_elemento = bloque.select_one(".file__date")
        enlace_elemento = bloque.select_one(
            "a.file__download[href]"
        )

        if not titulo_elemento or not enlace_elemento:
            continue

        titulo = titulo_elemento.get_text(" ", strip=True)
        enlace = urljoin(
            BASE_URL,
            enlace_elemento.get("href", ""),
        )

        fecha = ""

        if fecha_elemento:
            fecha = fecha_elemento.get_text(" ", strip=True)

        if (
            not titulo
            or not enlace
            or enlace in enlaces_encontrados
        ):
            continue

        enlaces_encontrados.add(enlace)

        notas.append(
            {
                "titulo": titulo,
                "enlace": enlace,
                "fecha": fecha,
            }
        )

    # Conserva las cien publicaciones más recientes.
    return notas[:100]


def crear_rss(notas):
    rss = ET.Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": "http://www.w3.org/2005/Atom",
        },
    )

    canal = ET.SubElement(rss, "channel")

    ET.SubElement(canal, "title").text = (
        "Notas de prensa de Colonial SFL"
    )
    ET.SubElement(canal, "link").text = WEB_URL
    ET.SubElement(canal, "description").text = (
        "Últimas notas de prensa y resultados de Colonial SFL"
    )
    ET.SubElement(canal, "language").text = "es"
    ET.SubElement(canal, "lastBuildDate").text = format_datetime(
        datetime.now(timezone.utc)
    )

    enlace_atom = ET.SubElement(
        canal,
        "{http://www.w3.org/2005/Atom}link",
    )
    enlace_atom.set("href", WEB_URL)
    enlace_atom.set("rel", "self")
    enlace_atom.set("type", "application/rss+xml")

    for nota in notas:
        elemento = ET.SubElement(canal, "item")

        ET.SubElement(
            elemento,
            "title",
        ).text = nota["titulo"]

        ET.SubElement(
            elemento,
            "link",
        ).text = nota["enlace"]

        ET.SubElement(
            elemento,
            "description",
        ).text = (
            f"{nota['titulo']}. "
            "Nota de prensa publicada por Colonial SFL."
        )

        ET.SubElement(
            elemento,
            "category",
        ).text = "Notas de prensa"

        identificador = ET.SubElement(elemento, "guid")
        identificador.set("isPermaLink", "true")
        identificador.text = nota["enlace"]

        enlace_sin_consulta = nota["enlace"].split("?")[0].lower()

        if enlace_sin_consulta.endswith(".pdf"):
            adjunto = ET.SubElement(elemento, "enclosure")
            adjunto.set("url", nota["enlace"])
            adjunto.set("type", "application/pdf")
            adjunto.set("length", "0")

        if nota["fecha"]:
            try:
                fecha_publicacion = datetime.strptime(
                    nota["fecha"],
                    "%d/%m/%Y",
                ).replace(tzinfo=timezone.utc)

                ET.SubElement(
                    elemento,
                    "pubDate",
                ).text = format_datetime(fecha_publicacion)
            except ValueError:
                pass

    ET.indent(rss, space="  ")

    ET.ElementTree(rss).write(
        OUTPUT_FILE,
        encoding="utf-8",
        xml_declaration=True,
    )


def main():
    notas = descargar_notas()

    if not notas:
        raise RuntimeError(
            "No se encontraron notas de prensa de Colonial"
        )

    crear_rss(notas)

    print(
        f"RSS creada correctamente con "
        f"{len(notas)} notas de prensa"
    )


if __name__ == "__main__":
    main()
