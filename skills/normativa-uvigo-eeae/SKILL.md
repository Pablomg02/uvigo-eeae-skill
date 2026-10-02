---
name: normativa-uvigo-eeae
description: Normativa de la Universidade de Vigo, la Escola de Enxeñaría Aeronáutica e do Espazo (EEAE) y la Escola Internacional de Doutoramento, con la legislación estatal, gallega y el convenio del PDI laboral, para resolver dudas del profesorado y del estudiantado de la EEAE (también si es doctorando) y comprobar que una decisión cumple la norma, verificándola en internet. Úsala siempre que pregunte si puede, debe o le está permitido algo como docente, estudiante, investigador o doctorando, aunque no diga «normativa». Cubre exámenes y convocatorias (fechas, cambios, revisión, notas, actas, avaliación global, fraude), guías docentes, calendario, tutorías, TFG/TFM, prácticas, estudiantes con necesidades, POD y dedicación, vacaciones, permisos, contratos, tesis (plan de investigación, plazos, prórrogas, depósito, defensa, mención internacional), investigación y art. 83, incompatibilidades, datos, acoso, régimen disciplinario y viajes. Responde en español citando artículo y fuente.
---

# Normativa UVigo + EEAE + doctorado para profesorado y estudiantado

Copia local de la normativa que afecta al profesorado y al estudiantado de la EEAE y a quien hace el doctorado, con un buscador y un comprobador en directo. La razón de ser es **no responder de memoria**: la norma cambia por cursos, está en gallego, y sin artículo y fecha la respuesta no sirve para decidir. El trabajo es siempre: encontrar el texto, leerlo entero, comprobar que está vigente y aplicable, y citarlo.

Contexto del caso: la skill no guarda datos de nadie. La persona cuenta su caso en la conversación y de ahí sale todo.

- **Qué hace falta saber** (solo lo que cambia la respuesta): figura contractual (contratado, funcionario, predoctoral o asociado), si pregunta como docente, estudiante (grado o máster), doctorando o director, la titulación, la materia y el curso si hay guía o fecha de por medio, y el programa de doctorado si pregunta por él. Pregúntalo en una línea; si falta algo no decisivo, declara la suposición y sigue.
- **Las guías docentes no están en el corpus.** Cuando la respuesta dependa de una materia (pesos, mínimos, asistencia, avaliación global, fin de carreira), bájala con `python3 scripts/guia.py "<nombre o código>" [--curso 2025_26] [--grep "<texto>"]` (busca en las titulaciones de la EEAE; `--lista` enseña las materias). Cítala con URL y «consultada el <fecha>».
- **Calendario y exámenes** de la Escola (`--ambito curso`) están descargados para un curso concreto, el que diga su cabecera; para otro, ver «Trampas».
- Si es doctorando, la web de su programa (actividades formativas, seguimiento, comisión académica) se consulta en línea: localiza el programa en `eido.uvigo.gal`. Es información, no norma: si difiere del Regulamento de doutoramento de 2024 (625), manda 625.

## Flujo de trabajo

1. **Fija los hechos que cambian la respuesta**: figura contractual, si actúa como profesor, estudiante, doctorando o director, curso o fecha del asunto. Si falta uno decisivo, pregúntalo en una línea; si no, declara la suposición y sigue.
2. **Enruta** con `references/temas.md`: dice qué normas leer y de qué nivel. Casi toda duda toca varios niveles (ley, convenio, UVigo, Escola, guía docente); leer solo uno lleva a aplicar una regla que otra superior ya cambió.
3. **Busca** desde la carpeta de la skill (la que contiene este SKILL.md), con varias consultas y en ambos idiomas (avaliación/evaluación, titorías/tutorías):
   ```bash
   python3 scripts/buscar.py "revisión exámenes plazo" -n 6
   python3 scripts/buscar.py "tribunal tfg" --ambito eeae          # curso | eeae | eido | uvigo | estatal | galicia
   python3 scripts/buscar.py --ver 565 --art 35                    # artículo entero (565 = id del portal)
   python3 scripts/buscar.py --layout 709 --grep "Capacidade docente"   # tabla del PDF original, con columnas
   python3 scripts/buscar.py --lista --ambito eido                 # qué hay
   ```
4. **Lee el artículo entero** con `--ver`, y los vecinos: las excepciones están en el apartado siguiente («salvo», «sen prexuízo»), en transitorias o en el artículo al que remite. Citar un fragmento truncado es la forma más fácil de equivocarse.
5. **Comprueba vigencia**: en local (marcas del buscador, "Trampas", `references/huecos.md`) y en directo con las normas que vas a citar: `python3 scripts/comprobar.py 565 625 losu exames-aero`. Dice si el portal la anuló o hay otra que la modifica, si el BOE cambió el texto o si la Escola, la EIDO o DOCNET cambiaron el PDF. Si marca ✗, lee la versión en línea y avisa. Si el entorno no tiene red (en la app de Claude depende de la configuración), comprueba la ficha `url_portal` o la `fuente` con la herramienta web; si tampoco puedes, dilo. En consultas sin consecuencias puedes omitirlo.
6. **Resuelve conflictos** con `references/jerarquia.md` (rango → fecha → competencia → especialidad; también qué aplica a contratados, funcionarios y predoctorales). Si no está claro cuál prevalece, dilo.

## Formato de respuesta

En español y directo. Las citas, literales en su idioma original, sin traducir cifras ni plazos.

```
**Respuesta corta:** Sí / No / Depende de X — una frase.

**Fundamento**
- <Norma>, <rango y fecha>, art. X.Y: «cita literal breve». [enlace]
- (una línea por norma, de mayor a menor rango)

**Condiciones y excepciones:** plazos, requisitos, quién autoriza.

**Qué no he podido verificar:** (solo si aplica) hueco del corpus, norma de otro curso, tabla, documento escaneado, suposición, comprobación en directo no hecha.

**Siguiente paso:** a quién preguntar o qué trámite hacer.
```

- **Separa norma de interpretación**: «el art. 30 obliga a custodiar los tres últimos cursos cerrados» es un hecho; «por tanto puedes destruir los de 2021/22» es interpretación (y falla si hay una reclamación pendiente) y se marca.
- **Sin cita no hay afirmación jurídica.** Si no está en el corpus ni en una fuente oficial en línea, dilo; el conocimiento general se etiqueta como tal.
- **Cifras y plazos se leen, no se recuerdan.** Si salen de una tabla, usa `--layout` o abre el PDF original.
- Enlaza la fuente (`url_portal` o `fuente`, que imprime `--ver`). En respuestas con consecuencias (sanción, plazo que caduca, contrato, dinero), recomienda confirmar con la unidad competente y da la fecha `descargado` del corpus.

Si describe algo que piensa hacer («¿puedo cambiar la fecha del examen?»), responde como lista de requisitos: quién es competente, qué requisitos y plazos fija cada norma, qué pasa si no se cumple y los pasos para hacerlo bien.

## Consultar en internet

Úsalo para lo que el corpus no puede tener al día: plazos y convocatorias de cada curso (depósito de tesis, ayudas, premios), acuerdos de la comisión académica del programa, avisos de la EIDO o de la Escola, guías de otras materias, normas que `comprobar.py` marca como cambiadas o leyes que no están en el corpus.

Fuentes oficiales: `secretaria.uvigo.gal/uv/web/normativa/public/show/<id>`, `eido.uvigo.gal`, la web de su programa de doctorado (enlazada desde `eido.uvigo.gal`), `secretaria.uvigo.gal/docnet-nuevo/guia_docent/` (guías docentes), `aero.uvigo.es`, `boe.es/buscar/act.php?id=<id_boe>`, `xunta.gal/dog`, `sede.uvigo.gal`. `WebFetch` para páginas, `curl` + `pdftotext` para PDF, `WebSearch` solo para localizar la página oficial. `www.uvigo.gal` da 403: busca lo mismo en las otras. Cita lo de internet con URL y «consultado el <fecha>»; sindicatos, foros o blogs son pista, nunca fundamento.

## Trampas

- **La guía docente obliga.** Lo que dice la guía de la materia (pesos, mínimos, asistencia, avaliación global, fin de carreira) es lo que el profesor debe aplicar; el Regulamento de avaliación (565) obliga a cumplirla y regula cómo modificarla (art. 9). Lee ambas; si chocan, prevalece 565. Bájala siempre con `guia.py`: no respondas sobre una materia de memoria.
- **Calendarios en tablas.** El texto aplanado del calendario y de los exámenes de la Escola no sirve para saber qué cae qué día: abre el PDF original (`buscar.py --layout`) y cita fecha, hora y aula tal cual; si una fecha importa, `comprobar.py exames-aero calendario-eeae`.
- **Curso distinto del descargado.** El calendario y los exámenes locales son de un solo curso (`--lista --ambito curso`). Si preguntan por otro, bájalos de `aero.uvigo.es` (docencia → calendario académico / exames) como material en línea, cítalos con fecha de consulta y di que no son la copia local.
- **«Validada» no es «vigente hoy»**, y la dedicación docente 2026/27 y la instrución de vacaciones 2026 no están publicadas (`huecos.md`). No uses la de otro curso como actual sin decirlo.
- **Contratado ≠ funcionario ≠ predoctoral**, y las normas anteriores a la LOSU ceden ante ella: ver `jerarquia.md` antes de citar EBEP, Estatutos, Regulamento de profesorado o el convenio.
- **Documentos escaneados** (`buscar.py --lista | grep 'SIN TEXTO'`): ábrelos como imagen si puedes (si no están en `_originales/`, en su `url_documento`) y di que el texto no está verificado.
- **Escola y EIDO** publican sin marca de vigencia: el RRI de la Escola es de 2017 y los procedimientos de cotutela y de tesis con datos de la EIDO son de 2015, anteriores a 625, que prevalece. La web del programa informa pero no es norma.
- **Doctorado, régimen transitorio**: 625 rige desde el 1-oct-2024; a quien empezó antes de 2023/24 le siguen aplicando las normas de su inicio salvo tribunal, defensa y evaluación (`--ver 625`, observaciones).
- **Dos planos en las fechas de examen.** Separa modificar el calendario oficial (competencia de la dirección del centro, 565 art. 25.2) de examinarse otro día por ausencia justificada (arts. 15 y 26: la fecha la fija el profesorado responsable, antes del cierre de actas y con 48 h de antelación). Un viaje de congreso no figura entre las causas del art. 15.2; si se invoca la causa residual «calquera outra causa sobrevida», exige acreditación y, si el profesorado y el estudantado discrepan, decide la dirección del centro (art. 15.3). Al responder sobre fechas, recuerda también el derecho del art. 25.3 (que las pruebas globales no coincidan en fecha y hora).

## Mantener al día

`python3 scripts/comprobar.py --novedades` (segundos) muestra normas nuevas en el portal, la Escola y la EIDO y leyes del BOE modificadas; este script sí viaja con la skill. El mantenimiento (reconstruir el corpus, cada curso nuevo) está en `tools/` del repositorio y una copia instalada no lo incluye: `bash tools/actualizar.sh` (minutos) lo vuelve a descargar todo y regenera `data/huellas.json`; después se revisan a mano `data/curated.json` y `references/huecos.md`. Propón actualizar si `--novedades` muestra algo que afecte a la consulta o el corpus tiene meses; no lo lances sin que la persona lo pida. En la app de Claude la skill es una copia fija y `_originales/` solo lleva algunos PDF (`--layout` descarga los demás si hay red): para actualizarla, la persona ejecuta en su ordenador `tools/actualizar.sh` y `tools/empaquetar.py` y la vuelve a subir. Cada curso nuevo: cambiar `CURSO` en `tools/fetch_curso.py` y ejecutarlo.

Carpetas: `normativa/{curso,uvigo,eeae,eido,estatal,galicia}/` (Markdown con cabecera de título, fecha, fuente y estado; originales en `_originales/`), `references/` (temas, jerarquía, huecos), `scripts/`.
