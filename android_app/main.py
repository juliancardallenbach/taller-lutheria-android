# -*- coding: utf-8 -*-
"""
Sistema de Gestion de Taller de Lutheria - version Android (Kivy)
Reutiliza la misma logica de datos, PDF y WhatsApp que la version de
escritorio, con una interfaz reconstruida para pantalla tactil.
"""

import os
import json
import sqlite3
from datetime import datetime

from kivy.app import App
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.graphics import Color, Rectangle
from kivy.properties import ListProperty
from kivy.lang import Builder

from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib import colors
from reportlab.lib.units import mm


# ---------------------------------------------------------------------------
# UTILIDADES (identicas a la version de escritorio)
# ---------------------------------------------------------------------------

def formatear_miles(numero_str):
    limpio = "".join(ch for ch in str(numero_str) if ch.isdigit())
    if limpio == "":
        return ""
    valor = int(limpio)
    return "{:,}".format(valor).replace(",", ".")


def a_entero(texto_formateado):
    limpio = "".join(ch for ch in str(texto_formateado) if ch.isdigit())
    return int(limpio) if limpio else 0


def envolver_texto(texto, ancho_max):
    resultado = []
    for parrafo in str(texto).split("\n"):
        palabras = parrafo.split(" ")
        linea_actual = ""
        for palabra in palabras:
            candidata = (linea_actual + " " + palabra).strip()
            if len(candidata) <= ancho_max:
                linea_actual = candidata
            else:
                if linea_actual:
                    resultado.append(linea_actual)
                linea_actual = palabra
        resultado.append(linea_actual)
    return resultado if resultado else [""]


# ---------------------------------------------------------------------------
# RUTAS Y CONFIGURACION (usa el almacenamiento privado de la app en Android)
# ---------------------------------------------------------------------------

def carpeta_datos():
    return App.get_running_app().user_data_dir


def ruta_db():
    return os.path.join(carpeta_datos(), "taller_lutheria.db")


def ruta_config():
    return os.path.join(carpeta_datos(), "config.json")


CONFIG_DEFAULT = {
    "tipos_instrumento": ["Guitarra", "Bajo", "Ukelele", "Violin", "Charango", "SIN ETIQUETA"],
    "marcas": ["Fender", "Gibson", "Yamaha", "Ibanez", "Squier", "SIN ETIQUETA"],
    "modelos": ["Stratocaster", "Les Paul", "SG", "Jazz Bass", "SIN ETIQUETA"],
    "mensaje_whatsapp": (
        "Hola {cliente}! \U0001F44B Te pasamos la ficha de ingreso de tu "
        "{instrumento} en el taller.\n\n"
        "\U0001F4CB Ficha N: {numero}\n"
        "\U0001F6E0 Trabajo: {trabajo}\n"
        "\U0001F4B0 Total: $ {total}\n"
        "\U0001F4B5 Sena: $ {sena}\n"
        "\U0001F4CC Saldo pendiente: $ {resta}\n\n"
        "{firma}"
    ),
    "firma_luthier": "Jose Luis Cardozo - Maestro Luthier \U0001F3B8",
}


def cargar_config():
    ruta = ruta_config()
    if not os.path.exists(ruta):
        guardar_config(CONFIG_DEFAULT)
        return dict(CONFIG_DEFAULT)
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        for clave, valor in CONFIG_DEFAULT.items():
            if clave not in data:
                data[clave] = valor
        return data
    except Exception:
        return dict(CONFIG_DEFAULT)


def guardar_config(data):
    with open(ruta_config(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def conectar_db():
    conn = sqlite3.connect(ruta_db())
    conn.execute(
        "CREATE TABLE IF NOT EXISTS fichas ("
        "numero INTEGER PRIMARY KEY AUTOINCREMENT, "
        "fecha TEXT, cliente TEXT, celular TEXT, domicilio TEXT, "
        "tipo TEXT, marca TEXT, modelo TEXT, trabajo TEXT, "
        "funda INTEGER, cuerdas INTEGER, "
        "total INTEGER, sena INTEGER, resta INTEGER, "
        "estado TEXT, drive TEXT, pagado INTEGER DEFAULT 0"
        ")"
    )
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# WHATSAPP (Intent nativo de Android; fallback navegador en desktop)
# ---------------------------------------------------------------------------

def abrir_whatsapp(numero, mensaje):
    from urllib.parse import quote
    texto = quote(mensaje)
    if platform == "android":
        try:
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            intent = Intent(Intent.ACTION_VIEW)
            intent.setData(Uri.parse("whatsapp://send?phone={0}&text={1}".format(numero, texto)))
            PythonActivity.mActivity.startActivity(intent)
            return
        except Exception:
            pass
    import webbrowser
    webbrowser.open("https://wa.me/{0}?text={1}".format(numero, texto))


# ---------------------------------------------------------------------------
# PDF (mismo diseño compacto que la version de escritorio)
# ---------------------------------------------------------------------------

def generar_pdf_ficha(ruta_pdf, datos, numero_formateado, firma):
    color_marca = colors.HexColor("#2f3e46")
    color_acento = colors.HexColor("#84a98c")
    color_fondo_caja = colors.HexColor("#f2f4f3")
    color_texto = colors.HexColor("#1b1f1f")

    ancho = 105 * mm
    alto = 190 * mm
    margen = 8 * mm

    c = pdf_canvas.Canvas(ruta_pdf, pagesize=(ancho, alto))

    alto_franja = 22 * mm
    c.setFillColor(color_marca)
    c.rect(0, alto - alto_franja, ancho, alto_franja, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(ancho / 2, alto - 11 * mm, "TALLER DE LUTHERIA")
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(ancho / 2, alto - 17 * mm,
                         "Ficha N {0}   -   {1}".format(numero_formateado, datos["fecha"]))

    y = alto - alto_franja - 8 * mm

    def caja(titulo, lineas, alto_caja, y_actual):
        c.setFillColor(color_fondo_caja)
        c.roundRect(margen, y_actual - alto_caja, ancho - 2 * margen, alto_caja, 3, stroke=0, fill=1)
        c.setFillColor(color_acento)
        c.rect(margen, y_actual - alto_caja, 2.2, alto_caja, stroke=0, fill=1)
        c.setFillColor(color_marca)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(margen + 5, y_actual - 9, titulo.upper())
        c.setFillColor(color_texto)
        c.setFont("Helvetica", 9)
        y_linea = y_actual - 19
        for linea in lineas:
            for sub in envolver_texto(linea, 46):
                c.drawString(margen + 5, y_linea, sub)
                y_linea -= 11.5
        return y_actual - alto_caja - 5

    instrumento = " ".join(x for x in (datos["tipo"], datos["marca"], datos["modelo"]) if x) or "-"
    extras = []
    if datos["funda"]:
        extras.append("Funda")
    if datos["cuerdas"]:
        extras.append("Cuerdas")

    y = caja("Cliente", [
        datos["cliente"], "Cel: {0}".format(datos["celular"] or "-"),
        "Dom: {0}".format(datos["domicilio"] or "-"),
    ], 42, y)

    y = caja("Instrumento", [
        instrumento, "Incluye: {0}".format(", ".join(extras) if extras else "Nada"),
    ], 32, y)

    lineas_trabajo = envolver_texto(datos["trabajo"] or "-", 46)
    alto_trabajo = 16 + max(1, len(lineas_trabajo)) * 11.5
    y = caja("Trabajo a realizar", [datos["trabajo"] or "-"], alto_trabajo, y)

    alto_montos = 46
    c.setFillColor(color_marca)
    c.roundRect(margen, y - alto_montos, ancho - 2 * margen, alto_montos, 3, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 9)
    c.drawString(margen + 6, y - 12, "Total")
    c.drawRightString(ancho - margen - 6, y - 12, "$ {0}".format(formatear_miles(datos["total"])))
    c.drawString(margen + 6, y - 23, "Seña")
    c.drawRightString(ancho - margen - 6, y - 23, "$ {0}".format(formatear_miles(datos["sena"])))
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(margen + 6, y - 36, "Saldo pendiente")
    c.drawRightString(ancho - margen - 6, y - 36, "$ {0}".format(formatear_miles(datos["resta"])))
    y -= alto_montos + 6

    c.setFillColor(color_acento)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margen, y, "Estado: {0}".format(datos["estado"]))
    y -= 12

    if datos["drive"]:
        c.setFillColor(color_texto)
        c.setFont("Helvetica", 7.5)
        for sub in envolver_texto("Drive: {0}".format(datos["drive"]), 55):
            c.drawString(margen, y, sub)
            y -= 10

    c.setFillColor(colors.HexColor("#6b7280"))
    c.setFont("Helvetica", 6.3)
    aviso = ("Instrumentos no retirados dentro de los 90 dias quedaran a "
             "disposicion del taller (Art. 872/873 Cod. Civil).")
    y_pie = 15 * mm
    for sub in envolver_texto(aviso, 62):
        c.drawString(margen, y_pie, sub)
        y_pie -= 8

    c.setFillColor(color_marca)
    c.setFont("Helvetica-Oblique", 8.5)
    c.drawCentredString(ancho / 2, 6 * mm, firma)
    c.save()


# ---------------------------------------------------------------------------
# WIDGETS AUXILIARES
# ---------------------------------------------------------------------------

class CampoConSugerencias(BoxLayout):
    """TextInput libre + boton que abre una lista para elegir un valor."""

    def __init__(self, hint, opciones_callback, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height="44dp", spacing=4, **kwargs)
        self.opciones_callback = opciones_callback
        self.input = TextInput(hint_text=hint, multiline=False)
        self.add_widget(self.input)
        boton = Button(text="\u25BE", size_hint_x=None, width="40dp")
        boton.bind(on_release=self._abrir_lista)
        self.add_widget(boton)

    def _abrir_lista(self, _instancia):
        opciones = self.opciones_callback()
        contenido = BoxLayout(orientation="vertical")
        scroll = ScrollView()
        lista = GridLayout(cols=1, size_hint_y=None, spacing=2)
        lista.bind(minimum_height=lista.setter("height"))
        popup = Popup(title="Elegir opcion", content=contenido, size_hint=(0.8, 0.7))

        def elegir(valor):
            self.input.text = valor
            popup.dismiss()

        for opcion in opciones:
            b = Button(text=opcion, size_hint_y=None, height="40dp")
            b.bind(on_release=lambda inst, v=opcion: elegir(v))
            lista.add_widget(b)

        scroll.add_widget(lista)
        contenido.add_widget(scroll)
        cerrar = Button(text="Cancelar", size_hint_y=None, height="40dp")
        cerrar.bind(on_release=popup.dismiss)
        contenido.add_widget(cerrar)
        popup.open()

    @property
    def text(self):
        return self.input.text

    @text.setter
    def text(self, valor):
        self.input.text = valor


class FilaColor(BoxLayout):
    color_fondo = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._color = Color(*self.color_fondo)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._actualizar, size=self._actualizar, color_fondo=self._actualizar_color)

    def _actualizar(self, *_args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _actualizar_color(self, *_args):
        self._color.rgba = self.color_fondo


# ---------------------------------------------------------------------------
# PANTALLA: FORMULARIO
# ---------------------------------------------------------------------------

class PantallaFormulario(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_data = cargar_config()
        self.conn = conectar_db()
        self.ficha_actual_id = None

        raiz = BoxLayout(orientation="vertical", padding=8, spacing=6)
        scroll = ScrollView()
        self.grid = GridLayout(cols=1, size_hint_y=None, spacing=6, padding=4)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        scroll.add_widget(self.grid)
        raiz.add_widget(scroll)

        self.campo_cliente = self._agregar_input("Cliente (Señor/es)")
        self.campo_celular = self._agregar_input("Celular")
        self.campo_domicilio = self._agregar_input("Domicilio")

        self.campo_tipo = CampoConSugerencias("Tipo de instrumento", lambda: self.config_data["tipos_instrumento"])
        self.grid.add_widget(self._con_etiqueta("Tipo", self.campo_tipo))
        self.campo_marca = CampoConSugerencias("Marca", lambda: self.config_data["marcas"])
        self.grid.add_widget(self._con_etiqueta("Marca", self.campo_marca))
        self.campo_modelo = CampoConSugerencias("Modelo", lambda: self.config_data["modelos"])
        self.grid.add_widget(self._con_etiqueta("Modelo", self.campo_modelo))

        fila_check = BoxLayout(size_hint_y=None, height="40dp", spacing=10)
        self.check_funda = CheckBox()
        fila_check.add_widget(Label(text="Funda", size_hint_x=None, width="60dp"))
        fila_check.add_widget(self.check_funda)
        self.check_cuerdas = CheckBox()
        fila_check.add_widget(Label(text="Cuerdas", size_hint_x=None, width="70dp"))
        fila_check.add_widget(self.check_cuerdas)
        self.grid.add_widget(fila_check)

        self.grid.add_widget(Label(text="Trabajo a realizar", size_hint_y=None, height="24dp", halign="left"))
        self.campo_trabajo = TextInput(multiline=True, size_hint_y=None, height="90dp")
        self.grid.add_widget(self.campo_trabajo)

        self.campo_total = TextInput(hint_text="Total ($)", multiline=False, size_hint_y=None, height="44dp")
        self.campo_total.bind(text=self._on_total_cambiado)
        self.grid.add_widget(self._con_etiqueta("Total ($)", self.campo_total))

        self.campo_sena = TextInput(hint_text="Seña ($)", multiline=False, size_hint_y=None, height="44dp")
        self.campo_sena.bind(text=self._on_sena_cambiado)
        self.grid.add_widget(self._con_etiqueta("Seña ($)", self.campo_sena))

        self.etiqueta_resta = Label(text="Restan: $ 0", size_hint_y=None, height="30dp", bold=True)
        self.grid.add_widget(self.etiqueta_resta)

        self.spinner_estado = Spinner(text="En Proceso", values=["En Proceso", "Terminado", "Entregado"],
                                       size_hint_y=None, height="44dp")
        self.grid.add_widget(self._con_etiqueta("Estado", self.spinner_estado))

        self.campo_drive = self._agregar_input("Link de Google Drive")

        self.boton_pagado = ToggleButton(text="PAGADO", size_hint_y=None, height="44dp")
        self.boton_pagado.bind(state=self._on_pagado_cambiado)
        self.grid.add_widget(self.boton_pagado)

        fila_botones1 = BoxLayout(size_hint_y=None, height="46dp", spacing=6)
        b_guardar = Button(text="Guardar / Nueva")
        b_guardar.bind(on_release=lambda i: self._guardar())
        b_actualizar = Button(text="Actualizar")
        b_actualizar.bind(on_release=lambda i: self._actualizar())
        b_limpiar = Button(text="Limpiar")
        b_limpiar.bind(on_release=lambda i: self._limpiar())
        fila_botones1.add_widget(b_guardar)
        fila_botones1.add_widget(b_actualizar)
        fila_botones1.add_widget(b_limpiar)
        self.grid.add_widget(fila_botones1)

        fila_botones2 = BoxLayout(size_hint_y=None, height="46dp", spacing=6)
        b_pdf = Button(text="Generar PDF")
        b_pdf.bind(on_release=lambda i: self._generar_pdf())
        b_wsp = Button(text="Enviar WhatsApp")
        b_wsp.bind(on_release=lambda i: self._enviar_whatsapp())
        b_lista = Button(text="Ver Lista")
        b_lista.bind(on_release=lambda i: self._ir_a_lista())
        fila_botones2.add_widget(b_pdf)
        fila_botones2.add_widget(b_wsp)
        fila_botones2.add_widget(b_lista)
        self.grid.add_widget(fila_botones2)

        self.add_widget(raiz)
        self._limpiar()

    def _con_etiqueta(self, texto, widget):
        fila = BoxLayout(size_hint_y=None, height="44dp", spacing=6)
        fila.add_widget(Label(text=texto, size_hint_x=0.4))
        fila.add_widget(widget)
        return fila

    def _agregar_input(self, hint):
        campo = TextInput(hint_text=hint, multiline=False, size_hint_y=None, height="44dp")
        self.grid.add_widget(campo)
        return campo

    def _on_total_cambiado(self, _inst, texto):
        formateado = formatear_miles(texto)
        if formateado != texto:
            self.campo_total.text = formateado
            return
        self._recalcular_resta()

    def _on_sena_cambiado(self, _inst, texto):
        formateado = formatear_miles(texto)
        if formateado != texto:
            self.campo_sena.text = formateado
            return
        self._recalcular_resta()

    def _recalcular_resta(self):
        total = a_entero(self.campo_total.text)
        sena = a_entero(self.campo_sena.text)
        resta = max(total - sena, 0)
        self.etiqueta_resta.text = "Restan: $ {0}".format(formatear_miles(str(resta)))

    def _on_pagado_cambiado(self, _inst, estado):
        if estado == "down":
            self.boton_pagado.text = "\u2714 PAGADO"
        else:
            self.boton_pagado.text = "PAGADO"
        if self.ficha_actual_id:
            self.conn.execute("UPDATE fichas SET pagado=? WHERE numero=?",
                               (1 if estado == "down" else 0, self.ficha_actual_id))
            self.conn.commit()

    def _leer_formulario(self):
        return {
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "cliente": self.campo_cliente.text.strip(),
            "celular": self.campo_celular.text.strip(),
            "domicilio": self.campo_domicilio.text.strip(),
            "tipo": self.campo_tipo.text.strip(),
            "marca": self.campo_marca.text.strip(),
            "modelo": self.campo_modelo.text.strip(),
            "trabajo": self.campo_trabajo.text.strip(),
            "funda": 1 if self.check_funda.active else 0,
            "cuerdas": 1 if self.check_cuerdas.active else 0,
            "total": a_entero(self.campo_total.text),
            "sena": a_entero(self.campo_sena.text),
            "resta": max(a_entero(self.campo_total.text) - a_entero(self.campo_sena.text), 0),
            "estado": self.spinner_estado.text,
            "drive": self.campo_drive.text.strip(),
            "pagado": 1 if self.boton_pagado.state == "down" else 0,
        }

    def _mostrar_mensaje(self, titulo, texto):
        Popup(title=titulo, content=Label(text=texto), size_hint=(0.8, 0.4)).open()

    def _limpiar(self):
        self.ficha_actual_id = None
        self.campo_cliente.text = ""
        self.campo_celular.text = ""
        self.campo_domicilio.text = ""
        self.campo_tipo.text = ""
        self.campo_marca.text = ""
        self.campo_modelo.text = ""
        self.check_funda.active = False
        self.check_cuerdas.active = False
        self.campo_trabajo.text = ""
        self.campo_total.text = ""
        self.campo_sena.text = ""
        self.etiqueta_resta.text = "Restan: $ 0"
        self.spinner_estado.text = "En Proceso"
        self.campo_drive.text = ""
        self.boton_pagado.state = "normal"

    def _guardar(self):
        datos = self._leer_formulario()
        if not datos["cliente"]:
            self._mostrar_mensaje("Datos incompletos", "Ingrese el nombre del cliente.")
            return
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO fichas (fecha, cliente, celular, domicilio, tipo, marca, modelo, "
            "trabajo, funda, cuerdas, total, sena, resta, estado, drive, pagado) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (datos["fecha"], datos["cliente"], datos["celular"], datos["domicilio"],
             datos["tipo"], datos["marca"], datos["modelo"], datos["trabajo"],
             datos["funda"], datos["cuerdas"], datos["total"], datos["sena"],
             datos["resta"], datos["estado"], datos["drive"], datos["pagado"]),
        )
        self.conn.commit()
        self.ficha_actual_id = cur.lastrowid
        self._mostrar_mensaje("Guardado", "Ficha N. {0} guardada.".format(self.ficha_actual_id))

    def _actualizar(self):
        if not self.ficha_actual_id:
            self._mostrar_mensaje("Sin ficha", "Primero cargue una ficha desde la lista.")
            return
        datos = self._leer_formulario()
        self.conn.execute(
            "UPDATE fichas SET fecha=?, cliente=?, celular=?, domicilio=?, tipo=?, marca=?, "
            "modelo=?, trabajo=?, funda=?, cuerdas=?, total=?, sena=?, resta=?, estado=?, "
            "drive=?, pagado=? WHERE numero=?",
            (datos["fecha"], datos["cliente"], datos["celular"], datos["domicilio"],
             datos["tipo"], datos["marca"], datos["modelo"], datos["trabajo"],
             datos["funda"], datos["cuerdas"], datos["total"], datos["sena"],
             datos["resta"], datos["estado"], datos["drive"], datos["pagado"], self.ficha_actual_id),
        )
        self.conn.commit()
        self._mostrar_mensaje("Actualizado", "Ficha N. {0} actualizada.".format(self.ficha_actual_id))

    def cargar_ficha(self, numero):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM fichas WHERE numero=?", (numero,))
        fila = cur.fetchone()
        if not fila:
            return
        columnas = [d[0] for d in cur.description]
        registro = dict(zip(columnas, fila))
        self.ficha_actual_id = registro["numero"]
        self.campo_cliente.text = registro["cliente"] or ""
        self.campo_celular.text = registro["celular"] or ""
        self.campo_domicilio.text = registro["domicilio"] or ""
        self.campo_tipo.text = registro["tipo"] or ""
        self.campo_marca.text = registro["marca"] or ""
        self.campo_modelo.text = registro["modelo"] or ""
        self.check_funda.active = bool(registro["funda"])
        self.check_cuerdas.active = bool(registro["cuerdas"])
        self.campo_trabajo.text = registro["trabajo"] or ""
        self.campo_total.text = formatear_miles(str(registro["total"] or 0))
        self.campo_sena.text = formatear_miles(str(registro["sena"] or 0))
        self._recalcular_resta()
        self.spinner_estado.text = registro["estado"] or "En Proceso"
        self.campo_drive.text = registro["drive"] or ""
        self.boton_pagado.state = "down" if registro["pagado"] else "normal"

    def _generar_pdf(self):
        datos = self._leer_formulario()
        if not datos["cliente"]:
            self._mostrar_mensaje("Datos incompletos", "Ingrese el cliente antes de generar el PDF.")
            return
        carpeta = os.path.join(carpeta_datos(), "PDFs")
        os.makedirs(carpeta, exist_ok=True)
        nombre = "ficha_{0}.pdf".format(self.ficha_actual_id or "nueva")
        ruta = os.path.join(carpeta, nombre)
        numero_fmt = "{:06d}".format(self.ficha_actual_id) if self.ficha_actual_id else "Nueva"
        generar_pdf_ficha(ruta, datos, numero_fmt, self.config_data.get("firma_luthier", ""))
        self._mostrar_mensaje("PDF generado", "Guardado en:\n{0}".format(ruta))

    def _enviar_whatsapp(self):
        datos = self._leer_formulario()
        if not datos["celular"]:
            self._mostrar_mensaje("Datos incompletos", "Ingrese el celular del cliente.")
            return
        numero_limpio = "".join(ch for ch in datos["celular"] if ch.isdigit())
        if not numero_limpio.startswith("549"):
            if numero_limpio.startswith("0"):
                numero_limpio = numero_limpio[1:]
            if numero_limpio.startswith("15"):
                numero_limpio = numero_limpio[2:]
            numero_limpio = "549" + numero_limpio

        instrumento = " ".join(x for x in (datos["tipo"], datos["marca"], datos["modelo"]) if x) or "instrumento"
        numero_fmt = "{:06d}".format(self.ficha_actual_id) if self.ficha_actual_id else "Nueva"
        plantilla = self.config_data.get("mensaje_whatsapp", CONFIG_DEFAULT["mensaje_whatsapp"])
        try:
            mensaje = plantilla.format(
                cliente=datos["cliente"], instrumento=instrumento, numero=numero_fmt,
                trabajo=datos["trabajo"] or "-", estado=datos["estado"],
                total=formatear_miles(str(datos["total"])), sena=formatear_miles(str(datos["sena"])),
                resta=formatear_miles(str(datos["resta"])), firma=self.config_data.get("firma_luthier", ""),
            )
        except Exception:
            mensaje = plantilla
        if datos["drive"]:
            mensaje += "\nDrive: " + datos["drive"]

        abrir_whatsapp(numero_limpio, mensaje)

    def _ir_a_lista(self):
        self.manager.get_screen("lista").refrescar()
        self.manager.current = "lista"


# ---------------------------------------------------------------------------
# PANTALLA: LISTA / BUSCADOR
# ---------------------------------------------------------------------------

class PantallaLista(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raiz = BoxLayout(orientation="vertical", padding=8, spacing=6)

        fila_busqueda = BoxLayout(size_hint_y=None, height="44dp", spacing=6)
        self.campo_buscar = TextInput(hint_text="Buscar cliente / instrumento / trabajo", multiline=False)
        self.campo_buscar.bind(text=lambda i, t: self.refrescar())
        fila_busqueda.add_widget(self.campo_buscar)
        b_volver = Button(text="Volver", size_hint_x=None, width="90dp")
        b_volver.bind(on_release=lambda i: setattr(self.manager, "current", "formulario"))
        fila_busqueda.add_widget(b_volver)
        raiz.add_widget(fila_busqueda)

        scroll = ScrollView()
        self.lista = GridLayout(cols=1, size_hint_y=None, spacing=3)
        self.lista.bind(minimum_height=self.lista.setter("height"))
        scroll.add_widget(self.lista)
        raiz.add_widget(scroll)

        self.add_widget(raiz)

    def refrescar(self):
        self.lista.clear_widgets()
        conn = self.manager.get_screen("formulario").conn
        filtro = self.campo_buscar.text.strip()
        cur = conn.cursor()
        if filtro:
            like = "%{0}%".format(filtro)
            cur.execute(
                "SELECT numero, cliente, tipo, marca, modelo, trabajo, total, sena, estado, pagado "
                "FROM fichas WHERE cliente LIKE ? OR tipo LIKE ? OR marca LIKE ? OR modelo LIKE ? "
                "OR trabajo LIKE ? ORDER BY numero DESC", (like, like, like, like, like),
            )
        else:
            cur.execute(
                "SELECT numero, cliente, tipo, marca, modelo, trabajo, total, sena, estado, pagado "
                "FROM fichas ORDER BY numero DESC"
            )
        for fila in cur.fetchall():
            numero, cliente, tipo, marca, modelo, trabajo, total, sena, estado, pagado = fila
            instrumento = " ".join(x for x in (tipo, marca, modelo) if x)
            color = [0.75, 0.94, 0.75, 1] if pagado else [1, 1, 1, 1]
            item = FilaColor(orientation="vertical", size_hint_y=None, height="70dp",
                              padding=6, color_fondo=color)
            texto = "N {0} - {1}\n{2} | {3}\nTotal ${4}  Seña ${5}  {6}".format(
                numero, cliente, instrumento, (trabajo or "")[:40],
                formatear_miles(str(total)), formatear_miles(str(sena)), estado,
            )
            etiqueta = Label(text=texto, halign="left", valign="middle", color=[0, 0, 0, 1])
            etiqueta.bind(size=lambda i, s: setattr(i, "text_size", s))
            item.add_widget(etiqueta)
            b = Button(background_color=[0, 0, 0, 0], size_hint=(1, 1))
            item.add_widget(b)
            b.bind(on_release=lambda inst, n=numero: self._elegir(n))
            self.lista.add_widget(item)

    def _elegir(self, numero):
        self.manager.get_screen("formulario").cargar_ficha(numero)
        self.manager.current = "formulario"


# ---------------------------------------------------------------------------
# APP PRINCIPAL
# ---------------------------------------------------------------------------

class TallerApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(PantallaFormulario(name="formulario"))
        sm.add_widget(PantallaLista(name="lista"))
        return sm


if __name__ == "__main__":
    TallerApp().run()
