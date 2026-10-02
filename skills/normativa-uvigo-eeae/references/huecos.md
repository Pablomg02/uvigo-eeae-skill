# Huecos conocidos y límites del corpus

Léelo antes de dar una respuesta que dependa de un curso, un año, una cifra o una norma reciente. La confianza en una respuesta jurídica depende tanto de lo que *no* está como de lo que sí está. (Estado: corpus descargado el 2026-10-01.)

## Normas que se sabe que existen y NO están en el corpus

| Falta | Qué se sabe | Qué hacer |
|---|---|---|
| **Normativa de dedicación y reconocimientos docentes 2026/2027** | El POD 2026/27 (709) la cita ("aprobada no consello de goberno do 24 de novembro [de 2025]"), pero el portal solo publica la de 2025/26 (657) y las anteriores. | Usa 657 solo como referencia de la última publicada, dilo expresamente y recomienda pedir el texto 2026/27 a la Vicerreitoría de Profesorado e Ordenación Académica. No des cifras de horas/sexenios como definitivas. |
| **Instrución de vacaciones y días de libre disposición de 2026** | Solo está la de 2025 (655). | Cita 655 como orientativa y remite al convenio (art. 36), que es la norma superior. |
| **Texto consolidado oficial del II Convenio PDI laboral** | Está el texto del DOG de 2011 y el acta de la Comisión Paritaria de 7-feb-2025 (DOG 14-mar-2025) que lo adapta, más el acuerdo sobre jubilación. El sindicato CCOO habla de una "versión consolidada de febrero de 2025" que no es un documento oficial del DOG. | Lee siempre juntos `convenio-pdi-laboral-ii-2011` y `…acta-paritaria-2025-02-07`; si hay conflicto, prevalece el acta en lo que modifique. |
| **III Convenio** | En negociación desde feb-2025 según el sindicato CCOO; la UVigo habría amenazado con negociar uno propio. No hay texto. | Advertir de que puede haber cambiado. |
| **Adaptación autonómica a la LOSU** | Ley 6/2013, Estatutos (2019) y Regulamento de profesorado (2012/13) son anteriores a la LOSU. Existe un *Anteproxecto* de nuevos Estatutos en exposición pública (no vigente). | Donde choquen con la LOSU, aplica la LOSU y avisa. |
| **RD 898/1985 (régimen del profesorado funcionario)** y normas solo de funcionarios | Se omitió porque el caso de referencia es una plaza de PDI contratado. | Si la duda afecta a un funcionario, dilo; no extrapoles. |
| **Sistema de Garantía de Calidad de la Escola, procedimientos internos, formularios** | No son normativa; están en la web del centro. | Remitir a la web del centro. |
| **Normas propias de la comisión académica de cada programa de doctorado** (criterios de admisión, de evaluación anual del plan de investigación, de autorización de defensa, requisitos de publicaciones) | No son normativa del portal ni de la EIDO; están en la web o la memoria verificada del programa. | Consúltalas en línea (web del programa en `eido.uvigo.gal`) y cítalas como tales. |
| **Convocatorias concretas** (FPU, FPI, predoctorales Xunta/UVigo, premios extraordinarios, movilidad) | Fijan condiciones propias del contrato o la ayuda; cambian cada año. | Búscalas en internet en la fuente oficial (BOE, DOG, sede) y combínalas con `rd-103-2019-epif`. |
| **Acuerdos de la Comisión Permanente de la EIDO** posteriores a sus procedimientos | La web publica procedimientos de 2015 (cotutela, tesis con datos protegidos) que el Regulamento de 2024 puede haber dejado atrás. | Prevalece 625; si la duda depende del procedimiento, confírmalo con la EIDO. |
| **Actas y acuerdos de la Xunta de Escola** posteriores a los reglamentos | No están publicados como normativa. Un reglamento puede haberse modificado sin que la web se actualice. | Avisar de que el texto es el publicado en la web del centro y de que no hay marca oficial de vigencia. |

## Limitaciones técnicas del texto

- **Tablas**: la conversión de PDF a texto aplana las tablas y puede desordenar columnas (por ejemplo la tabla de sexenios en 657). Si la respuesta depende de una cifra o una celda de una tabla, usa `buscar.py --layout <id> --grep "<título de la tabla>"` (relee el PDF original conservando las columnas) o abre el PDF original (`original_local` en la cabecera del fichero) con la herramienta de lectura de PDF.
- **Documentos escaneados**: algunos PDF (antiguos de la UVigo y dos de la EIDO: gastos de tribunales de tesis y reconocimiento de actividades) son imágenes sin texto; se listan con `buscar.py --lista | grep 'SIN TEXTO'`. Hay que abrirlos visualmente y avisar de que no han podido verificarse con texto.
- **Copias en otro idioma**: el corpus guarda solo la versión principal (casi siempre en gallego); las traducciones al castellano, inglés o portugués que publica el portal no se descargan. Si hace falta una, está en la ficha del portal (`url_portal`).
- **Legislación del BOE**: el texto es el consolidado en la fecha de descarga; `boe_actualizado` en la cabecera es la fecha de la última modificación del texto. `scripts/comprobar.py <nombre>` dice en segundos si el BOE lo ha cambiado después.
- **Estado "Validada"**: lo pone la Secretaría Xeral y puede incluir normas de cursos ya pasados. Ver `data/curated.json` para las marcas propias.

## Lo que NO es esta skill

- No sustituye a la Asesoría Xurídica, a la Vicerreitoría de Profesorado, ni a Recursos Humanos para decisiones con efectos sancionadores, contractuales o económicos.
- No interpreta jurisprudencia ni criterios de la Inspección: solo texto normativo publicado.
