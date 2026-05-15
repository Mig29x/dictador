#!/usr/bin/env python3
"""
DICTADOR — Remake del clásico de ZX Spectrum (DK'Tronics, 1983)
Mecánica fiel al original. Texto en español.
"""

import random
import sys
import time
import os

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    console = Console()
    USE_RICH = True
except ImportError:
    USE_RICH = False
    console = None

# ── DATOS DE FACCIONES ───────────────────────────────────────────────────────
# Formato: [nombre, pop_inicial, fuerza_inicial]
FACCIONES_INIT = [
    ("El Ejército",         7, 6),
    ("Los Campesinos",      7, 6),
    ("Los Terratenientes",  7, 6),
    ("Los Guerrilleros",    0, 6),
    ("Los Lefotanos",       7, 6),
    ("La Policía Secreta",  7, 6),
    ("Los Rusos",           7, 0),
    ("Los Americanos",      7, 0),
]

# ── DECISIONES ───────────────────────────────────────────────────────────────
# Formato: (código_17_chars, texto_es)
# Pos 0    : 'N'=disponible / '*'=usada
# Pos 1    : efecto tesoro SÍ:  10*(ord-77) miles de $
# Pos 2    : efecto costos mens: ord-77
# Pos 3-10 : efecto popularidad SÍ en 8 facciones (ord-77)
# Pos 11-16: efecto fuerza SÍ en 6 facciones (ord-77)
# Para NO: solo cambia pop[facción_peticionaria] -= (ord(código[3+gs])-77)

DECISIONES_RAW = [
    # Peticiones del Ejército (índices 0-7)
    ("NMHQJLMMMMMPKLMMM", "INTRODUCIR EL SERVICIO MILITAR OBLIGATORIO"),
    ("NMMPMJMMMMMNMLMMM", "REQUISAR TERRENOS PARA ENTRENAMIENTO MILITAR"),
    ("NCMPLNMLMLMNMNIMM", "ATACAR TODAS LAS BASES GUERRILLERAS"),
    ("NEMPLMMIMLMNMNKMM", "ATACAR BASES GUERRILLERAS EN LEFTOTO"),
    ("NMMQONMMIMMNMNMMJ", "DESTITUIR AL JEFE DE LA POLICÍA SECRETA"),
    ("NMMPMMMLMIOMMMMMM", "EXPULSAR A LOS ASESORES MILITARES RUSOS"),
    ("NMDQMLMMMMMOLLLMM", "AUMENTAR EL SUELDO DE LAS TROPAS"),
    ("NAMQLLMLLMMPLLKLM", "COMPRAR MÁS ARMAS Y MUNICIÓN"),
    # Peticiones de los Campesinos (índices 8-15)
    ("NMMLONMMMMMLMMLMM", "DETENER LA LEVA FORZADA DEL EJÉRCITO"),
    ("NMMMQIMNMMMMOLMMM", "AUMENTAR EL SALARIO MÍNIMO BÁSICO"),
    ("NMPNQOMMIMMNNNNMJ", "REDUCIR LOS PODERES DE LA POLICÍA SECRETA"),
    ("NMMMPKMKMMMMOKMMM", "EXPULSAR A LOS TRABAJADORES INMIGRANTES LEFOTANOS"),
    ("NCELQKMOLNMMNLLMM", "INSTAURAR EDUCACIÓN GRATUITA PARA TODOS"),
    ("NMMMQJMNLNMMPJMML", "LEGALIZAR LA FORMACIÓN DE SINDICATOS"),
    ("NMMLQKMNLMMMOLLMM", "LIBERAR A SU LÍDER ENCARCELADO"),
    ("NMSMPLMMMMMMMMLMM", "INICIAR UNA LOTERÍA PÚBLICA"),
    # Peticiones de los Terratenientes (índices 16-23)
    ("NMMKMPMMMMMLMMMMM", "PROHIBIR EL USO MILITAR DE SUS TIERRAS"),
    ("NMMMIQMLMLMMKONMM", "BAJAR EL SALARIO MÍNIMO BÁSICO"),
    ("NWHMMPMNMOIMMNMMM", "NACIONALIZAR EMPRESAS AMERICANAS"),
    ("NMRMMPMJMLMMNOMLM", "GRAVAR TODAS LAS IMPORTACIONES DE LEFTOTO"),
    ("NMQNNPMMIMMNMNNMK", "RECORTAR EL GASTO EN LA POLICÍA SECRETA"),
    ("NMHMMQMMMMMMMOMMM", "REDUCIR LOS IMPUESTOS SOBRE LA TIERRA"),
    ("NMMKLPMMMMMLLNNMM", "LIBERAR TROPAS PARA TRABAJAR LA TIERRA"),
    ("NACNNPMJMONMMPMKM", "CONSTRUIR UN GRAN SISTEMA DE RIEGO"),
    # Iniciativa del jugador — Complacer a grupos (índices 24-29)
    ("NMMQLLMMLMMNMMLML", "NOMBRAR AL JEFE DEL EJÉRCITO VICEPRESIDENTE"),
    ("NLILQNMOMNMMMMLMM", "CREAR CLÍNICAS GRATUITAS PARA TRABAJADORES"),
    ("NMMLKQMMLLMLLOMML", "OTORGAR PODERES REGIONALES A TERRATENIENTES"),
    ("NRMKMMMQMKNLMMLPM", "VENDER ARMAS AMERICANAS A LEFTOTO"),
    ("NYMMMLMLMKPMMMMM",  "VENDER DERECHOS MINEROS A EMPRESAS AMERICANAS"),
    ("NMWKMMMMMPJMMMMNM", "ALQUILAR A LOS RUSOS UNA BASE NAVAL"),
    # Iniciativa — Complacer a todos (índices 30-32)
    ("NMENPPMMMMMLMMLMM", "REDUCIR EL NIVEL GENERAL DE IMPUESTOS"),
    ("NEMPPPMMMMMMMMLMM", "ORGANIZAR UNA GRAN CAMPAÑA DE POPULARIDAD"),
    ("NMUPPPMMDMMONNNMD", "ELIMINAR LOS PODERES DE LA POLICÍA SECRETA"),
    # Iniciativa — Mejorar sus chances (índices 33-36)
    ("NMGJJJMMUMMLLLLMU", "AMPLIAR MUCHO LOS PODERES DE LA POLICÍA SECRETA"),
    ("NIMKLLMMLMMKMMMMl", "REFORZAR SU GUARDIA PERSONAL *"),
    ("NAMIIJMMKMMMMMMMm", "COMPRAR UN HELICÓPTERO DE ESCAPE"),
    ("NMMMMMMMMMMMMMMMM", "TRANSFERIR FONDOS A CUENTA SUIZA *"),
    # Iniciativa — Obtener dinero (índices 37-39)
    ("NMMMMMMMMMMMMMMMM", "PEDIR UN PRÉSTAMO A LOS RUSOS"),
    ("NMMMMMMMMMMMMMMMM", "SOLICITAR AYUDA EXTERIOR A LOS AMERICANOS"),
    ("NZMNNPMGMKMMMMMMM", "NACIONALIZAR EMPRESAS LEFOTANAS"),
    # Iniciativa — Fortalecer grupos (índices 40-42)
    ("NHMPMMMJMLMRMMKKL", "COMPRAR ARTILLERÍA PESADA PARA EL EJÉRCITO"),
    ("NMMmplmmlmmmrlpml", "PERMITIR LIBRE CIRCULACIÓN A LOS CAMPESINOS"),
    ("NMMllpmmlmmllrlml", "AUTORIZAR MILICIAS PRIVADAS A TERRATENIENTES"),
    # Eventos aleatorios — Noticias (índices 43-48)
    ("NMMMMMMMIMMMMMQMI", "EL PRESIDENTE PIERDE LOS ARCHIVOS DE LA P. SECRETA"),
    ("NMMMMMMMMMMLMMVMM", "LOS CUBANOS ARMAN Y ENTRENAN A GUERRILLEROS"),
    ("NMMMMMMMMMMIMMOMN", "ACCIDENTE: EL CUARTEL DEL EJÉRCITO EXPLOTA"),
    ("NMMMMMMMMMMMMJMKM", "LOS PRECIOS DEL PLÁTANO CAEN UN 98%"),
    ("NMMMMMMMMMMMMOMIM", "GRAN TERREMOTO EN LEFTOTO"),
    ("NMMMMMMMMMMMILKMM", "UNA PLAGA AZOTA A LOS CAMPESINOS"),
]

# ── ÁRBOL DE CONSECUENCIAS ───────────────────────────────────────────────────
# Formato: decision_idx → lista de (meses_delay, texto_evento, efectos)
# efectos: {'pop': {faccion_idx: delta}, 'fuerza': {faccion_idx: delta},
#           'tesoro': delta, 'costos': delta}
CONSECUENCIAS = {
    # 0 = Servicio militar obligatorio → deserción masiva al cabo de 3 meses
    0: [(3,
         "DESERCIÓN MASIVA EN EL EJÉRCITO CONSCRIPTO\n"
         "  Los soldados forzados huyen en masa. La moral es por los suelos.",
         {"pop": {0: -2}, "fuerza": {0: -2}})],

    # 5 = Expulsar asesores militares rusos → los rusos congelan relaciones
    5: [(1,
         "LOS RUSOS CONGELAN SUS RELACIONES CON RITIMBA\n"
         "  Moscú retira a su embajador y suspende los acuerdos comerciales.",
         {"pop": {6: -3}, "tesoro": -150})],

    # 7 = Comprar más armas → el ejército exige más presupuesto para mantenimiento
    7: [(2,
         "EL EJÉRCITO EXIGE PRESUPUESTO PARA MANTENER EL ARMAMENTO\n"
         "  El nuevo equipo requiere técnicos y repuestos costosos.",
         {"pop": {0: 1}, "costos": 15})],

    # 13 = Legalizar sindicatos → huelga general a los 4 meses
    13: [(4,
          "LOS SINDICATOS CONVOCAN UNA HUELGA GENERAL\n"
          "  El país se paraliza. Los trabajadores exigen más derechos.",
          {"pop": {1: 2, 2: -2}, "tesoro": -250})],

    # 18 = Nacionalizar banca americana → sanciones económicas de EEUU
    18: [(2,
          "EEUU IMPONE SANCIONES ECONÓMICAS A RITIMBA\n"
          "  Washington congela activos y prohíbe inversiones en el país.",
          {"pop": {7: -3, 6: 1}, "tesoro": -400})],

    # 27 = Poderes regionales a terratenientes → abusan del poder
    27: [(3,
          "LOS TERRATENIENTES ABUSAN DE SUS PODERES REGIONALES\n"
          "  Imponen tributos ilegales a los campesinos de sus provincias.",
          {"pop": {1: -2, 2: 1}})],

    # 29 = Alquilar base naval a rusos → EEUU amenaza cortar ayuda
    29: [(1,
          "EEUU AMENAZA CON CORTAR TODA LA AYUDA A RITIMBA\n"
          "  El Departamento de Estado exige el cierre inmediato de la base rusa.",
          {"pop": {7: -4}, "tesoro": -100})],

    # 32 = Cortar poderes policía completamente → colapso policial
    32: [(2,
          "COLAPSO DE LA POLICÍA SECRETA: CIENTOS DE PRESOS LIBERADOS\n"
          "  Sin estructura, la policía se desintegra. La oposición festeja.",
          {"pop": {1: 3, 0: -1}, "fuerza": {5: -3}})],

    # 33 = Ampliar mucho poderes policía → escándalo de torturas
    33: [(2,
          "ESCÁNDALO INTERNACIONAL: TORTURAS EN CÁRCELES RITIMBANAS\n"
          "  Amnistía Internacional denuncia al gobierno ante la ONU.",
          {"pop": {1: -2, 2: -1, 7: -2}})],

    # 39 = Nacionalizar empresas lefotanas → embargo comercial
    39: [(1,
          "LEFTOTO DECLARA EMBARGO COMERCIAL TOTAL A RITIMBA\n"
          "  Las exportaciones de plátano quedan bloqueadas en la frontera.",
          {"pop": {4: -2}, "fuerza": {4: 2}, "costos": 20})],

    # 41 = Comprar artillería pesada → maniobras intimidatorias en la frontera
    41: [(1,
          "EL EJÉRCITO REALIZA MANIOBRAS CERCA DE LA FRONTERA CON LEFTOTO\n"
          "  La tensión sube. Los lefotanos refuerzan sus posiciones.",
          {"pop": {0: 1, 4: -2}, "fuerza": {4: 1}})],

    # 42 = Libre circulación campesinos → éxodo campo-ciudad
    41: [(3,
          "ÉXODO MASIVO DEL CAMPO A LA CIUDAD\n"
          "  Miles de campesinos abandonan las tierras. La producción agrícola cae.",
          {"pop": {1: 1, 2: -2}, "tesoro": -200})],

    # 97 idx en DECISIONES_RAW = milicias patronales (idx 42)
    42: [(2,
          "MILICIAS PATRONALES ATACAN A TRABAJADORES EN HUELGA\n"
          "  Varios heridos. La comunidad internacional condena la represión.",
          {"pop": {1: -3, 2: 2, 0: -1}})],

    # 31 = Reducir impuestos → inversión extranjera llega (positivo!)
    30: [(4,
          "INVERSIÓN EXTRANJERA LLEGA A RITIMBA ATRAÍDA POR LOS BAJOS IMPUESTOS\n"
          "  Varias empresas abren plantas en el país. El tesoro se beneficia.",
          {"tesoro": 450, "pop": {2: 1}})],
}

# Menús de iniciativa del jugador: (texto, rango de índices 0-based en DECISIONES_RAW)
MENUS_DECISION = [
    ("COMPLACER A UN GRUPO",        (24, 30)),
    ("COMPLACER A TODOS LOS GRUPOS", (30, 33)),
    ("MEJORAR SUS POSIBILIDADES",    (33, 37)),
    ("OBTENER DINERO",               (37, 40)),
    ("FORTALECER UN GRUPO",          (40, 43)),
]

# ── HELPERS DE SALIDA ────────────────────────────────────────────────────────

def limpiar():
    os.system("clear")

def pausa(seg=1.5):
    time.sleep(seg)

def imprimir(texto="", **kwargs):
    if USE_RICH:
        console.print(texto, **kwargs)
    else:
        print(texto)

def panel(titulo, contenido, color="white"):
    if USE_RICH:
        console.print(Panel(contenido, title=titulo, border_style=color))
    else:
        print(f"\n=== {titulo} ===")
        print(contenido)
        print("=" * 40)

def barra(valor, maximo=9, ancho=9, color_si="green", color_no="red"):
    lleno = min(int(valor), maximo)
    if USE_RICH:
        t = Text()
        t.append("█" * lleno, style=color_si)
        t.append("░" * (maximo - lleno), style=color_no)
        return t
    return "█" * lleno + "░" * (maximo - lleno)

class SalirJuego(Exception):
    pass

def pedir_tecla(prompt="Presione una tecla...", opciones=None):
    """Lee una tecla del usuario. 'q' sale del juego en cualquier momento."""
    if USE_RICH:
        imprimir(f"\n[bold yellow]{prompt}[/bold yellow] [dim](q=salir)[/dim] ", end="")
    else:
        print(f"\n{prompt} (q=salir) ", end="", flush=True)
    while True:
        try:
            import tty, termios
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except KeyboardInterrupt:
            print()
            raise SalirJuego()
        except Exception:
            try:
                ch = input().strip().lower()
            except (KeyboardInterrupt, EOFError):
                print()
                raise SalirJuego()
            if not ch:
                ch = " "
            else:
                ch = ch[0]
        print()
        if ch == "q":
            raise SalirJuego()
        if ch == "\x03":  # Ctrl+C raw mode
            raise SalirJuego()
        if opciones is None or ch in opciones:
            return ch

# ── LÓGICA DEL JUEGO ─────────────────────────────────────────────────────────

class Juego:
    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.facciones = [
            {"nombre": n, "pop": p, "fuerza": f, "estado": ":", "aliada": 0}
            for n, p, f in FACCIONES_INIT
        ]
        self.decisiones = list(DECISIONES_RAW)   # copia mutable
        self.usadas = [False] * 49

        self.tesoro = 1000      # bk (miles de $)
        self.costos = 60        # mpy (miles/mes)
        self.fuerza_propia = 4  # st
        self.cuenta_suiza = 0   # sw
        self.vivo = True        # d
        self.escapado = False   # esc
        self.mes = 0            # mth
        self.record = 0         # hst — persiste entre partidas
        self.control_pos = 0    # pc: mes en que puede pedir informe policial otra vez
        self.pendientes = []    # [(mes_disparo, texto, efectos)]

    def efecto_si(self, idx):
        """Aplica efectos de decir SÍ a la decisión idx."""
        code = self.decisiones[idx][0]
        # Tesoro
        cst = 10 * (ord(code[1]) - 77) if len(code) > 1 else 0
        # Costos mensuales
        mcst = (ord(code[2]) - 77) if len(code) > 2 else 0

        self.tesoro += cst
        self.costos = max(0, self.costos - mcst)

        # Popularidad de 8 facciones
        for i in range(8):
            pos = 3 + i
            if pos < len(code) and code[pos] != 'M':
                delta = ord(code[pos]) - 77
                self.facciones[i]["pop"] = max(0, min(9, self.facciones[i]["pop"] + delta))

        # Fuerza de 6 facciones
        for i in range(6):
            pos = 11 + i
            if pos < len(code) and code[pos] != 'M':
                delta = ord(code[pos]) - 77
                self.facciones[i]["fuerza"] = max(0, min(9, self.facciones[i]["fuerza"] + delta))

        self.usadas[idx] = True
        self._programar_consecuencias(idx)

    def _programar_consecuencias(self, idx):
        """Encola las consecuencias futuras de haber dicho SÍ a idx."""
        for delay, texto, efectos in CONSECUENCIAS.get(idx, []):
            self.pendientes.append((self.mes + delay, texto, efectos))

    def _aplicar_efectos(self, efectos):
        """Aplica un dict de efectos al estado del juego."""
        for i, delta in efectos.get("pop", {}).items():
            self.facciones[i]["pop"] = max(0, min(9, self.facciones[i]["pop"] + delta))
        for i, delta in efectos.get("fuerza", {}).items():
            self.facciones[i]["fuerza"] = max(0, min(9, self.facciones[i]["fuerza"] + delta))
        self.tesoro += efectos.get("tesoro", 0)
        self.costos = max(0, self.costos + efectos.get("costos", 0))

    def procesar_consecuencias(self):
        """Dispara los eventos que corresponden al mes actual."""
        disparadas = [p for p in self.pendientes if p[0] <= self.mes]
        self.pendientes = [p for p in self.pendientes if p[0] > self.mes]
        for _, texto, efectos in disparadas:
            limpiar()
            panel("!! CONSECUENCIA DE SU DECISIÓN !!", "", "red")
            imprimir(f"\n  [bold]{texto}[/bold]\n")
            self._aplicar_efectos(efectos)
            cambios = []
            for i, d in efectos.get("pop", {}).items():
                cambios.append(f"  Pop. {self.facciones[i]['nombre']}: {'+'if d>0 else ''}{d}")
            for i, d in efectos.get("fuerza", {}).items():
                cambios.append(f"  Fuerza {self.facciones[i]['nombre']}: {'+'if d>0 else ''}{d}")
            if efectos.get("tesoro"):
                d = efectos["tesoro"]
                cambios.append(f"  Tesoro: {'+'if d>0 else ''}${abs(d)},000")
            if efectos.get("costos"):
                d = efectos["costos"]
                cambios.append(f"  Costos mensuales: {'suben' if d>0 else 'bajan'} ${abs(d)},000/mes")
            for c in cambios:
                imprimir(c)
            pausa(2.5)

    def efecto_no(self, idx, gs):
        """Aplica efecto de decir NO a la facción gs (0-indexed)."""
        code = self.decisiones[idx][0]
        pos = 3 + gs
        if pos < len(code):
            delta = ord(code[pos]) - 77
            f = self.facciones[gs]
            f["pop"] = max(0, min(9, f["pop"] - delta))

    def mostrar_efectos_si(self, idx):
        """Muestra al jugador qué efectaría decir SÍ."""
        code = self.decisiones[idx][0]
        lineas = []
        for i in range(8):
            pos = 3 + i
            if pos < len(code) and code[pos] != 'M':
                d = ord(code[pos]) - 77
                signo = "+" if d > 0 else ""
                lineas.append(f"  Pop. {self.facciones[i]['nombre']}: {signo}{d}")
        for i in range(6):
            pos = 11 + i
            if pos < len(code) and code[pos] != 'M':
                d = ord(code[pos]) - 77
                signo = "+" if d > 0 else ""
                lineas.append(f"  Fuerza {self.facciones[i]['nombre']}: {signo}{d}")
        cst = 10 * (ord(code[1]) - 77) if len(code) > 1 else 0
        mcst = (ord(code[2]) - 77) if len(code) > 2 else 0
        if cst:
            signo = "+" if cst > 0 else ""
            lineas.append(f"  Tesoro: {signo}${abs(cst)},000")
        if mcst:
            lineas.append(f"  Costos mensuales: {'bajan' if mcst > 0 else 'suben'} ${abs(mcst)},000/mes")
        return "\n".join(lineas) if lineas else "  Sin efecto económico directo."

    def detectar_complots(self, umbral_bajo, umbral_rev):
        """Actualiza el estado de complot de las primeras 3 facciones."""
        for i in range(3):
            self.facciones[i]["estado"] = ":"
            self.facciones[i]["aliada"] = 0

        for i in range(3):
            if self.facciones[i]["pop"] > umbral_bajo:
                continue
            # Busca aliado para revolución
            for j in range(6):
                if i == j:
                    continue
                if self.facciones[j]["pop"] > umbral_bajo:
                    continue
                if (self.facciones[j]["fuerza"] + self.facciones[i]["fuerza"]) >= umbral_rev:
                    self.facciones[i]["estado"] = "R"
                    self.facciones[i]["aliada"] = j
                    break
            else:
                self.facciones[i]["estado"] = "A"  # solo asesinato

    def intento_asesinato(self):
        """Retorna True si muere, False si sobrevive."""
        candidatos = [i for i in range(3) if self.facciones[i]["estado"] == "A"]
        if not candidatos:
            return False

        r = random.choice(candidatos)
        limpiar()
        panel(
            "¡¡ INTENTO DE ASESINATO !!",
            f"Por parte de... [bold]{self.facciones[r]['nombre']}[/bold]",
            "red"
        )
        pausa(2)

        todos_en_contra = all(self.facciones[i]["estado"] == "A" for i in range(3))
        policia = self.facciones[5]
        salvado = policia["pop"] > 2 or policia["fuerza"] > 2 or (not todos_en_contra and random.randint(0, 1))

        if todos_en_contra or not salvado:
            imprimir("\n[bold red]¡¡ HA MUERTO !! [/bold red]\n")
            pausa(2)
            return True

        panel("INTENTO FALLIDO", "La Policía Secreta lo protegió.", "green")
        pausa(1.5)
        return False

    def chequear_guerra(self, umbral_bajo):
        """Retorna 'muerto', 'escapado' o None."""
        leftotan = self.facciones[4]
        if leftotan["pop"] > umbral_bajo:
            return None
        if leftotan["fuerza"] <= umbral_bajo:
            return None
        if random.randint(0, 2):  # 2/3 de posibilidades de acción real
            # Solo amenaza
            limpiar()
            panel(
                "AMENAZA DE GUERRA CON LEFTOTO",
                "Su popularidad en Ritimba [bold green]SUBE[/bold green] ante la amenaza extranjera.",
                "yellow"
            )
            for i in [0, 1, 2, 5]:
                self.facciones[i]["pop"] = min(9, self.facciones[i]["pop"] + 1)
            pausa(2)
            return None

        # Invasión real
        limpiar()
        panel("¡¡ LEFTOTO INVADE RITIMBA !!", "", "red")

        fuerza_ritimba = sum(
            self.facciones[i]["fuerza"]
            for i in [0, 1, 2, 5]
            if self.facciones[i]["pop"] > umbral_bajo
        ) + self.fuerza_propia

        fuerza_leftoto = sum(
            self.facciones[i]["fuerza"]
            for i in range(6)
            if self.facciones[i]["pop"] <= umbral_bajo
        )

        imprimir(f"  Fuerza de Ritimba: [green]{fuerza_ritimba}[/green]")
        imprimir(f"  Fuerza de Leftoto: [red]{fuerza_leftoto}[/red]")
        pausa(2)

        if fuerza_leftoto + random.randint(-1, 1) < fuerza_ritimba:
            panel("LEFTOTANOS DERROTADOS", "¡Victoria de Ritimba!", "green")
            self.facciones[4]["fuerza"] = 0
            pausa(1.5)
            return None

        # Derrota
        limpiar()
        panel("¡¡ VICTORIA LEFOTANA !!", "", "red")
        tiene_helicoptero = self.usadas[35]

        if tiene_helicoptero and random.randint(0, 2):
            panel("¡ESCAPA EN HELICÓPTERO!", "Logra huir en el último momento.", "yellow")
            pausa(1.5)
            return "escapado"

        if tiene_helicoptero and not random.randint(0, 2):
            imprimir("[red]El motor del helicóptero falla...[/red]")
            pausa(1)

        imprimir("[red]Es juzgado como ENEMIGO DEL PUEBLO... y ejecutado.[/red]")
        pausa(2)
        return "muerto"

    def chequear_revolucion(self, umbral_bajo, umbral_rev):
        """Retorna 'muerto', 'escapado' o None."""
        revolucionarios = [i for i in range(3) if self.facciones[i]["estado"] == "R"]
        if not revolucionarios:
            return None

        r = random.choice(revolucionarios)
        aliado_idx = self.facciones[r]["aliada"]

        limpiar()
        panel("¡¡ REVOLUCIÓN !!", "", "red")
        pausa(1.5)

        imprimir(f"\n  [bold]{self.facciones[r]['nombre']}[/bold] se ha aliado con")
        imprimir(f"  [bold]{self.facciones[aliado_idx]['nombre']}[/bold]")
        fuerza_rev = self.facciones[r]["fuerza"] + self.facciones[aliado_idx]["fuerza"]
        imprimir(f"  Fuerza combinada: [red]{fuerza_rev}[/red]")
        pausa(2)

        imprimir("\n[bold]¿Intenta escapar? (s/n)[/bold]")
        resp = pedir_tecla(opciones=["s", "n"])

        if resp == "s":
            tiene_helicoptero = self.usadas[35]
            if tiene_helicoptero:
                if random.randint(0, 2):
                    panel("¡ESCAPA EN HELICÓPTERO!", "", "yellow")
                    pausa(1.5)
                    return "escapado"
                imprimir("[red]El helicóptero no arranca...[/red]")
                pausa(1)

            # Intentar cruzar las montañas a Leftoto
            guerrilleros_fuerza = self.facciones[3]["fuerza"]
            if guerrilleros_fuerza > 0 and random.randint(0, guerrilleros_fuerza // 3):
                imprimir("[red]Los guerrilleros lo capturan en las montañas.[/red]")
                pausa(1.5)
                return "muerto"
            panel("¡ESCAPA A LEFTOTO!", "Los guerrilleros no lo atraparon.", "yellow")
            pausa(1.5)
            return "escapado"

        # Intentar resistir
        imprimir("\n[bold]¿A quién pide ayuda? (número de facción)[/bold]")
        leales = [(i, f) for i, f in enumerate(self.facciones[:6])
                  if f["pop"] > umbral_bajo and i not in (r, aliado_idx)]

        if not leales:
            imprimir("[red]Está completamente solo.[/red]")
            aliado_fuerza = 0
            aliado_nombre = "nadie"
        else:
            for i, f in leales:
                imprimir(f"  {i+1}. {f['nombre']} (fuerza: {f['fuerza']})")
            resp2 = pedir_tecla(opciones=[str(i+1) for i, _ in leales])
            idx_ayuda = int(resp2) - 1
            aliado_fuerza = self.facciones[idx_ayuda]["fuerza"]
            aliado_nombre = self.facciones[idx_ayuda]["nombre"]
            # El aliado gana fuerza después
            self.facciones[idx_ayuda]["fuerza"] = 9

        fuerza_defensa = self.fuerza_propia + aliado_fuerza
        imprimir(f"\n  Su fuerza total: [green]{fuerza_defensa}[/green]  vs  Revolucionarios: [red]{fuerza_rev}[/red]")
        pausa(1.5)

        if fuerza_rev <= fuerza_defensa + random.randint(-1, 1):
            panel("¡REVOLUCIÓN APLASTADA!", "", "green")
            # Resetear popularidad de los traidores
            self.facciones[r]["pop"] = 0
            self.facciones[r]["fuerza"] = 0
            self.facciones[aliado_idx]["pop"] = 0
            self.facciones[aliado_idx]["fuerza"] = 0
            self.control_pos = self.mes + 2
            pausa(1.5)
            return None

        limpiar()
        imprimir("[bold red]Ha sido derrocado y ejecutado.[/bold red]")
        pausa(2)
        return "muerto"

    def noticias_flash(self):
        """Evento aleatorio: aplica una noticia de las últimas 6 decisiones."""
        if random.randint(0, 2):  # 2/3 de no hacer nada
            return
        disponibles = [i for i in range(43, 49) if not self.usadas[i]]
        if not disponibles:
            return
        idx = random.choice(disponibles)
        _, texto = self.decisiones[idx]

        limpiar()
        panel("!! NOTICIAS DE ÚLTIMA HORA !!", "", "yellow")
        pausa(0.5)
        imprimir(f"\n  [bold]{texto}[/bold]\n")
        pausa(1.5)
        self.efecto_si(idx)

    def mostrar_tesoro(self):
        limpiar()
        panel("INFORME DEL TESORO", "", "blue")
        signo = "tiene" if self.tesoro >= 0 else "[red]DEBE[/red]"
        imprimir(f"  El TESORO {signo} [bold]${abs(int(self.tesoro))},000[/bold]")
        imprimir(f"  Gastos mensuales: [yellow]${self.costos},000[/yellow]")
        if self.cuenta_suiza > 0:
            imprimir(f"  [Cuenta suiza: ${self.cuenta_suiza},000]")
        pausa(1.5)

    def mostrar_informe_policial(self):
        if self.tesoro <= 0 or self.facciones[5]["pop"] <= 2 or self.facciones[5]["fuerza"] <= 2:
            imprimir("[red]INFORME NO DISPONIBLE[/red]")
            if self.tesoro <= 0:
                imprimir("  No tiene fondos para pagarlo.")
            if self.facciones[5]["pop"] <= 2:
                imprimir(f"  Su popularidad con la P. Secreta es muy baja: {self.facciones[5]['pop']}")
            pausa(1.5)
            return

        imprimir("\n[bold]¿Solicitar informe de la Policía Secreta? (cuesta $1,000) (s/n)[/bold]")
        resp = pedir_tecla(opciones=["s", "n"])
        if resp != "s":
            return

        self.tesoro -= 1
        limpiar()
        panel(f"INFORME DE LA POLICÍA SECRETA — MES {self.mes}", "", "cyan")

        if USE_RICH:
            tabla = Table(box=box.SIMPLE)
            tabla.add_column("Facción", style="cyan", width=22)
            tabla.add_column("Popularidad", justify="left", width=12)
            tabla.add_column("Fuerza", justify="left", width=10)
            tabla.add_column("Estado", justify="center", width=8)

            for i, f in enumerate(self.facciones):
                pop_bar = barra(f["pop"])
                if i < 6:
                    fuerza_bar = barra(f["fuerza"], color_si="blue")
                else:
                    fuerza_bar = Text("—")
                estado = ""
                if f["estado"] == "A":
                    estado = Text("¡COMPLOT!", style="bold red")
                elif f["estado"] == "R":
                    estado = Text("¡REVOLUC!", style="bold magenta")
                tabla.add_row(f["nombre"], pop_bar, fuerza_bar, estado)

            console.print(tabla)
        else:
            for i, f in enumerate(self.facciones):
                bar = "█" * f["pop"] + "░" * (9 - f["pop"])
                estado = ""
                if f["estado"] == "A":
                    estado = " [COMPLOT]"
                elif f["estado"] == "R":
                    estado = " [REVOLUC]"
                print(f"  {f['nombre']:<22} Pop: {bar} Fuerza: {f['fuerza']}{estado}")

        imprimir(f"\n  Su fuerza personal: [bold]{self.fuerza_propia}[/bold]")
        pedir_tecla("Continuar...")

    def quiebra(self):
        """Penalidades por estar en quiebra."""
        limpiar()
        panel("¡EL TESORO ESTÁ EN QUIEBRA!", "", "red")
        imprimir("  Popularidad con el Ejército y la P. Secreta: [red]BAJA[/red]")
        imprimir("  Fuerza de la Policía Secreta: [red]BAJA[/red]")
        imprimir("  Su fuerza personal: [red]BAJA[/red]")

        for i in [0, 5]:
            self.facciones[i]["pop"] = max(0, self.facciones[i]["pop"] - 1)
        self.facciones[5]["fuerza"] = max(0, self.facciones[5]["fuerza"] - 1)
        self.fuerza_propia = max(0, self.fuerza_propia - 1)
        pausa(2)

    def peticion_aleatoria(self):
        """Elige una decisión no usada de los primeros 24 (facciones 0-2)."""
        disponibles = [i for i in range(24) if not self.usadas[i]]
        if not disponibles:
            # Resetear
            for i in range(24):
                self.usadas[i] = False
            disponibles = list(range(24))
        return random.choice(disponibles)

    def pantalla_titulo(self):
        limpiar()
        if USE_RICH:
            console.print(Panel(
                Text("DICTADOR\n\nla República Bananera de Ritimba lo necesita", justify="center"),
                title="ZX Spectrum — DK'Tronics 1983 · Remake en Python",
                border_style="bold yellow",
                padding=(1, 4),
            ))
            imprimir("\n  Devised and Written by [italic]Don Priestley[/italic]")
            imprimir("  Remake en español por [italic]viudos del Spectrum[/italic]\n")
        else:
            print("\n" + "=" * 40)
            print("          D I C T A D O R")
            print("   la República Bananera de Ritimba")
            print("=" * 40)
            print("  DK'Tronics 1983 — Remake en Python\n")

        if self.record > 0:
            imprimir(f"  Mejor puntuación: [bold yellow]{self.record}[/bold yellow]\n")
        pedir_tecla("Presione cualquier tecla para convertirse en DICTADOR...")

    def bienvenida(self):
        limpiar()
        panel("BIENVENIDO AL CARGO", "", "green")
        if self.record <= 0:
            imprimir("  En su primer intento, seguramente lo hará [bold]¡MEJOR![/bold]")
        else:
            imprimir(f"  El mejor DICTADOR tuvo una puntuación de [bold]{self.record}[/bold]")
            imprimir(f"  Intente superar [bold]{self.record + 1}[/bold]")
        imprimir("\n  Empiece pidiendo un INFORME DEL TESORO")
        imprimir("  y un INFORME POLICIAL. (GRATIS)")
        pausa(2)

    def menu_decision_jugador(self):
        """Permite al jugador tomar decisiones por iniciativa propia."""
        limpiar()
        panel("DECISIÓN PRESIDENCIAL", "Trate de...", "magenta")
        for i, (texto, _) in enumerate(MENUS_DECISION, 1):
            imprimir(f"  {i}. {texto}")
        imprimir("  6. NO TOMAR NINGUNA DECISIÓN")

        resp = pedir_tecla(opciones=["1", "2", "3", "4", "5", "6"])
        if resp == "6":
            return

        opcion = int(resp) - 1
        _, (inicio, fin) = MENUS_DECISION[opcion]
        disponibles = [(i, self.decisiones[i][1]) for i in range(inicio, fin) if not self.usadas[i]]

        if not disponibles:
            imprimir("[red]Todas las opciones de esta sección ya fueron usadas.[/red]")
            pausa(1.5)
            return

        limpiar()
        for n, (i, texto) in enumerate(disponibles, 1):
            imprimir(f"  {n}. {texto}")

        opciones_validas = [str(n) for n in range(1, len(disponibles) + 1)]
        resp2 = pedir_tecla(opciones=opciones_validas + ["0"])
        if resp2 == "0":
            return

        idx = disponibles[int(resp2) - 1][0]

        # Decisiones especiales
        if idx == 36:  # Cuenta suiza
            self._hacer_transferencia_suiza()
            return
        if idx == 37:  # Préstamo rusos
            self._pedir_ayuda_exterior(0)
            return
        if idx == 38:  # Ayuda americanos
            self._pedir_ayuda_exterior(1)
            return
        if idx == 34:  # Guardia personal
            self.fuerza_propia = min(9, self.fuerza_propia + 2)

        # Mostrar efectos e info de costo
        limpiar()
        imprimir(f"\n  [bold]{self.decisiones[idx][1]}[/bold]\n")
        efectos = self.mostrar_efectos_si(idx)
        imprimir(efectos)

        code = self.decisiones[idx][0]
        cst = 10 * (ord(code[1]) - 77) if len(code) > 1 else 0
        puede_pagar = (self.tesoro + cst) > 0 or cst >= 0

        if not puede_pagar:
            imprimir(f"\n[red]El TESORO no tiene fondos para esta decisión (costaría ${abs(cst)},000)[/red]")
            pausa(1.5)
            return

        imprimir("\n[bold]¿Proceder? (s/n)[/bold]")
        resp3 = pedir_tecla(opciones=["s", "n"])
        if resp3 == "s":
            self.efecto_si(idx)
            self.mostrar_tesoro()

    def _hacer_transferencia_suiza(self):
        limpiar()
        panel("TRANSFERENCIA A CUENTA SUIZA", "", "yellow")
        x = int(self.tesoro // 2)
        if x < 1:
            imprimir("[red]No hay fondos para transferir.[/red]")
            pausa(1.5)
            return
        self.cuenta_suiza += x
        self.tesoro -= x
        imprimir(f"  El tesoro tenía [bold]${int(self.tesoro + x)},000[/bold]")
        imprimir(f"  [bold green]Se transfirieron ${x},000[/bold green] a Suiza.")
        self.usadas[36] = True
        pausa(2)

    def _pedir_ayuda_exterior(self, quien):
        """quien=0: Rusos, quien=1: Americanos"""
        idx = 37 + quien
        if self.usadas[idx]:
            imprimir("[red]Ya solicitó esta ayuda antes y fue denegada.[/red]")
            pausa(1.5)
            return

        limpiar()
        nombre = "LOS RUSOS" if quien == 0 else "LOS AMERICANOS"
        panel(f"SOLICITUD DE AYUDA EXTERIOR — {nombre}", "", "cyan")
        imprimir("  Procesando solicitud...")
        pausa(2)

        faccion_idx = 6 + quien
        if self.mes < random.randint(2, 5):
            imprimir("[red]Es demasiado pronto para pedir ayuda.[/red]")
        elif self.facciones[faccion_idx]["pop"] <= 2:
            msg = "¡NIET!" if quien == 0 else '"¡No way!"'
            imprimir(f"  {msg}")
        else:
            monto = self.facciones[faccion_idx]["pop"] * 30 + random.randint(0, 200)
            imprimir(f"  [green]Le conceden ${monto},000 dólares.[/green]")
            self.tesoro += monto
            self.usadas[idx] = True

        pausa(2)

    def pantalla_fin(self):
        limpiar()
        x = sum(f["pop"] for f in self.facciones)
        x += self.mes * 3
        if self.vivo and not self.escapado:
            x += self.fuerza_propia
        x += int(self.cuenta_suiza / 10)

        if USE_RICH:
            tabla = Table(title="SU PUNTUACIÓN COMO PRESIDENTE", box=box.ROUNDED)
            tabla.add_column("Concepto", style="cyan")
            tabla.add_column("Puntos", justify="right", style="yellow")
            pop_total = sum(f["pop"] for f in self.facciones)
            tabla.add_row("Popularidad total", str(pop_total))
            tabla.add_row(f"Meses en el cargo ({self.mes} × 3)", str(self.mes * 3))
            if self.vivo and not self.escapado:
                tabla.add_row("Por seguir con vida", str(self.fuerza_propia))
            tabla.add_row(f"Por [italic]robarle al pueblo[/italic] (${self.cuenta_suiza},000 / 10,000)", str(int(self.cuenta_suiza / 10)))
            tabla.add_section()
            tabla.add_row("[bold]TOTAL[/bold]", f"[bold]{x}[/bold]")
            console.print(tabla)
        else:
            print("\n=== SU PUNTUACIÓN COMO PRESIDENTE ===")
            print(f"  Popularidad total:    {sum(f['pop'] for f in self.facciones)}")
            print(f"  Meses en el cargo:    {self.mes * 3}")
            if self.vivo and not self.escapado:
                print(f"  Por seguir vivo:      {self.fuerza_propia}")
            print(f"  Por la cuenta suiza:  {int(self.cuenta_suiza / 10)}")
            print(f"  TOTAL: {x}")

        if x > self.record:
            self.record = x
            imprimir(f"\n[bold yellow]¡¡ NUEVO RÉCORD: {x} !! [/bold yellow]\n")
        else:
            imprimir(f"\n  [ Mejor puntuación hasta ahora: {self.record} ]\n")

        pedir_tecla("Presione cualquier tecla para jugar de nuevo...")

    def jugar(self):
        """Bucle principal del juego."""
        self.pantalla_titulo()
        self.bienvenida()
        self.mostrar_tesoro()
        self.mostrar_informe_policial()

        umbral_bajo = random.randint(2, 4)
        umbral_rev = random.randint(10, 12)

        while True:
            self.mes += 1
            umbral_bajo = random.randint(2, 4)
            umbral_rev = random.randint(10, 12)

            # Costos mensuales
            if self.tesoro > 0:
                self.tesoro -= self.costos
            if self.tesoro < 0:
                self.quiebra()

            # Consecuencias de decisiones anteriores
            self.procesar_consecuencias()

            # Mostrar mes
            limpiar()
            panel(f"MES {self.mes}", "Ritimba espera sus decisiones...", "cyan")
            pausa(0.8)

            # Petición de audiencia aleatoria
            idx = self.peticion_aleatoria()
            gs = idx // 8  # facción peticionaria (0=Ejército, 1=Campesinos, 2=Terratenientes)
            nombre_faccion = self.facciones[gs]["nombre"]
            texto_decision = self.decisiones[idx][1]

            limpiar()
            panel(
                f"AUDIENCIA — {nombre_faccion.upper()}",
                f"Una petición de {nombre_faccion}",
                "yellow"
            )
            imprimir(f"\n  ¿Accederá Su Excelencia a:\n")
            imprimir(f"  [bold]{texto_decision}[/bold]\n")

            # Mostrar asesoramiento
            efectos = self.mostrar_efectos_si(idx)
            imprimir(f"\n[dim]  Si dice SÍ:[/dim]\n{efectos}\n")

            # Verificar si puede pagar
            code = self.decisiones[idx][0]
            cst = 10 * (ord(code[1]) - 77) if len(code) > 1 else 0
            puede_pagar = (self.tesoro + cst) > 0 or cst >= 0

            if not puede_pagar:
                imprimir(f"[red]  El TESORO no tiene fondos. Su respuesta DEBE ser NO.[/red]")
                pausa(1.5)
                resp = "n"
            else:
                imprimir(f"  [yellow]Informe del tesoro: ${int(self.tesoro)},000[/yellow]")
                resp = pedir_tecla("¿Accede? (s=sí / n=no):", opciones=["s", "n"])

            if resp == "s":
                self.efecto_si(idx)
                self.mostrar_tesoro()
            else:
                self.efecto_no(idx, gs)

            # Detectar complots
            self.detectar_complots(umbral_bajo, umbral_rev)

            # Chequear asesinato
            if self.intento_asesinato():
                self.vivo = False
                break

            # Chequear guerra
            resultado_guerra = self.chequear_guerra(umbral_bajo)
            if resultado_guerra == "muerto":
                self.vivo = False
                break
            if resultado_guerra == "escapado":
                self.escapado = True
                break

            # Mostrar estado
            self.mostrar_tesoro()
            self.mostrar_informe_policial()

            # Decisión por iniciativa del jugador
            self.menu_decision_jugador()

            # Chequear revolución
            resultado_rev = self.chequear_revolucion(umbral_bajo, umbral_rev)
            if resultado_rev == "muerto":
                self.vivo = False
                break
            if resultado_rev == "escapado":
                self.escapado = True
                break

            # Noticias flash
            self.noticias_flash()

        self.pantalla_fin()


def main():
    juego = Juego()
    try:
        while True:
            juego.reiniciar()
            try:
                juego.jugar()
            except SalirJuego:
                limpiar()
                imprimir("\n[bold yellow]¡Hasta la próxima, Dictador![/bold yellow]\n")
                break
    except (KeyboardInterrupt, SalirJuego):
        limpiar()
        imprimir("\n[bold yellow]¡Hasta la próxima, Dictador![/bold yellow]\n")


if __name__ == "__main__":
    main()
