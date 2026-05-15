# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Ejecutar el juego

```bash
uv venv .venv --python 3.12   # solo si no existe
uv pip install rich
.venv/bin/python3 dictador.py
```

Dentro del juego: `s`=sí, `n`=no, `q`=salir en cualquier momento.

## Verificar sin ejecutar el loop interactivo

```bash
.venv/bin/python3 -c "
exec(compile(open('dictador.py').read().replace('\nif __name__', '\n#if __name__'), 'dictador.py', 'exec'))
juego = Juego()
# probar lógica aquí
"
```

## Arquitectura

Todo el juego vive en `dictador.py`. No hay módulos externos propios.

### Datos (nivel de módulo)

| Constante | Descripción |
|---|---|
| `FACCIONES_INIT` | 8 facciones con popularidad y fuerza inicial |
| `DECISIONES_RAW` | 49 tuplas `(código_17_chars, texto_es)` |
| `CONSECUENCIAS` | Dict `idx_decisión → [(delay_meses, texto, efectos)]` |
| `MENUS_DECISION` | 5 categorías del menú de iniciativa del jugador |

### Encoding de decisiones (crítico para modificar datos)

Cada decisión tiene un código de 17 caracteres donde `ord(c) - 77` es el delta:
- `pos[0]`: `'N'`=disponible / `'*'`=usada
- `pos[1]`: efecto en tesoro × 10 (miles $)
- `pos[2]`: efecto en costos mensuales
- `pos[3..10]`: efecto de popularidad en las 8 facciones (SÍ)
- `pos[11..16]`: efecto de fuerza en las 6 primeras facciones (SÍ)
- `'M'` (77) = sin efecto; valores > 77 = positivo; < 77 = negativo

Para NO: solo cambia la popularidad de la facción peticionaria, con delta negado.

### Índices de facciones

```
0=Ejército  1=Campesinos  2=Terratenientes  3=Guerrilleros
4=Lefotanos  5=Policía Secreta  6=Rusos  7=Americanos
```

Solo las facciones 0-2 pueden generar complots/revolución/asesinato.
Solo las facciones 0-5 tienen fuerza militar relevante.

### Flujo por mes (`Juego.jugar`)

```
costos_mensuales → procesar_consecuencias → audiencia_aleatoria →
respuesta_jugador → detectar_complots → intento_asesinato →
chequear_guerra → mostrar_tesoro/informe → menu_decision_jugador →
chequear_revolucion → noticias_flash → siguiente mes
```

### Árbol de consecuencias

`CONSECUENCIAS` mapea el índice de una decisión a eventos futuros. Al llamar `efecto_si(idx)` se encolan en `self.pendientes` como `(mes_disparo, texto, efectos_dict)`. Al inicio de cada mes, `procesar_consecuencias()` dispara los vencidos y muestra un panel al jugador.

El dict de efectos usa claves `'pop'`, `'fuerza'` (dicts `{faccion_idx: delta}`), `'tesoro'` y `'costos'` (enteros).

### Fin de partida y puntuación

```
puntaje = sum(pop de 8 facciones) + meses×3 + fuerza_propia (si vivo) + cuenta_suiza/10
```

`record` persiste en la instancia de `Juego` entre partidas (se reinicia al salir del proceso).

### ROM original

Los archivos del ZX Spectrum están en `rom/` (no se usan en runtime). `disasm/dictador_basic.txt` contiene el BASIC del juego original decodificado línea a línea, útil como referencia para verificar mecánicas.
