# Mapa de temas: dónde mirar primero

Este archivo **no resume la ley**: dice qué normas leer para cada tipo de duda. Los números (512, 657…) son identificadores del portal de la UVigo y valen para `python3 scripts/buscar.py --ver <id>`. Los nombres sin número son ficheros de legislación (`losu`, `ebep`, `convenio-pdi-laboral-ii-2011`…).

Regla general: busca primero con `buscar.py`, y usa este mapa para comprobar que no te dejas una norma de otro nivel (ley, convenio, UVigo, Escola). Casi todo asunto de un profesor toca **al menos tres niveles**.

## Condiciones de trabajo del profesor contratado

| Duda | Leer primero | Complementar con |
|---|---|---|
| Qué figura soy y qué puedo/debo hacer (ayudante doctor, asociado, sustituto, permanente laboral) | `losu` arts. 77–88; `convenio-pdi-laboral-ii-2011` arts. 11–22 | 512 (Regulamento de profesorado, arts. 7–16, **anterior a la LOSU**); 451 (ayudante doctor), 687 (asociado), 710 (sustituto) |
| Jornada, horario, presencialidad | `convenio-…-ii-2011` art. 27; 512 art. 23 | 657 (dedicación docente), 709 (POD), 271 (reordenación de horarios), `lopdgdd` art. 88 (desconexión digital) |
| Vacaciones y días de libre disposición | `convenio-…-ii-2011` art. 36 (22 días hábiles + antigüedad) | 655 (instrución anual: **comprobar el año**), `ebep` art. 50 solo orienta, no manda para laborales |
| Permisos, licencias, baja, conciliación, lactancia | `convenio-…-ii-2011` art. 37 | `estatuto-trabajadores` art. 37, 512 art. 26, 96 (medidas de igualdad y conciliación), `ley-igualdad`, 657 (reducciones tras permisos de parto/adopción), 355 (retribución en IT) |
| Dedicación docente (horas, sexenios, reducciones) | 657 (norma anual; **ver aviso de vigencia**) y 709 (POD) | `losu` art. 75 (límites legales 120–240 h, se refiere al PDI permanente), 512 arts. 3, 22, 25 |
| Retribuciones, trienios/antigüedad, complementos | `convenio-…-ii-2011` arts. 28–33; `losu` art. 87 | `rd-1086-1989-retribuciones` (régimen de funcionarios; el convenio no menciona los sexenios: para laborales mira 657 y busca «sexenio»), 556 (trienios investigador), 633 (complementos y ayudas RRHH) |
| Incompatibilidades, segunda actividad, trabajar para empresa | `incompatibilidades` (Ley 53/1984); `convenio-…-ii-2011` art. 24; `losu` art. 79 (asociado) | 435 (servicios a tiempo parcial en empresas de la UVigo), 512 art. 30, 215 (creación de empresas), 213 (propiedad industrial) |
| Régimen disciplinario, deberes, código ético | `convenio-…-ii-2011` art. 39; `ebep` arts. 52–54 (deberes y código de conducta) y Título VII (régimen disciplinario) | 566 (Código ético), 512 art. 21, `lpac` (procedimiento) |
| Jubilación | `convenio-…-ii-2011` art. 42 y `convenio-pdi-laboral-acordo-xubilacion-2025` | `estatuto-trabajadores` |
| Comisiones de servicio, sabáticos, licencias de estudios | 512 arts. 24, 27, 28 | `convenio-…-ii-2011` art. 38 (suspensión y excedencias), 303 (cambio de campus, provisional) |
| Viajes, dietas, gastos | 328 (indemnizaciones por razón de servicio), 526 (importes), 246/244 (órdenes de comisión y gastos de viaje), 315 (agencia de viajes), 140 (congresos) | `convenio-…-ii-2011` art. 34 |
| Promoción, acreditación, quinquenios/avaliación docente | 645 (avaliación da actividade docente), 279 (plan de promoción), 646 (integración a permanente), 31–32 del 512 | `losu` arts. 85–86 |
| Contrato predoctoral (FPU, FPI, Xunta, UVigo): docencia que se puede dar, duración, derechos | `rd-103-2019-epif` arts. 4 (docencia: máx. 60 h/año y 180 h en total), 5–12; `ley-ciencia` art. 21 | `estatuto-trabajadores`; 633/680 (complementos de ayudas de RR. HH.); la convocatoria concreta de la ayuda (fuera del corpus: búscala en internet) |
| Contratación de profesorado y concursos | 658, 451, 687, 710, 530, 547/659 (prelación) | `losu`, `convenio-…-ii-2011` art. 26 (selección y tribunales), `lpac` (abstención, recusación) |

## Docencia y evaluación

Para una materia concreta empieza por su guía docente (`python3 scripts/guia.py "<materia>"`, la baja de DOCNET) y por el calendario y los exámenes de la Escola (`buscar.py "<tema>" --ambito curso`; fechas de examen, cierre de actas, plazos de avaliación global; **leer en el PDF**, son tablas). Luego la norma general:

| Duda | Leer primero | Complementar con |
|---|---|---|
| **Guía docente**: qué debe contener, quién la elabora y aprueba, plazos, publicación | 565 arts. 4–8 | `rd-1791-2010-estatuto-estudiante` arts. 7.g–h y 25.1–2 (la evaluación se ajusta a los planes docentes); la guía de la materia |
| Cambiar algo de la guía ya publicada (pesos, fechas de entregas, sistema de evaluación) | 565 art. 9 (modificación) y art. 10 (incumplimiento) | `deleg-competencias-eeae` (quién aprueba en la Escola) |
| Asistencia obligatoria, prácticas, faltas justificadas | 565 arts. 13–15 | la guía de la materia |
| Evaluación continua vs **global**; renuncia; requisitos | 565 arts. 19–21 | calendario de la Escola (plazo de solicitud de avaliación global); la guía de la materia |
| Examen oral | 565 art. 22 | — |
| Oportunidades, fin de carrera, adelanto de convocatoria | 565 arts. 23–24 | 698 (estudos de grao), 353 |
| **Fecha del examen**: quién la fija, cambiarla, coincidencias | 565 art. 25; `rd-1791-2010…` art. 25.3–4 («La programación de pruebas de evaluación no podrá alterarse, salvo […] imposibilidad sobrevenida») | `exames-aero-2026-27`, `rri-eeae`, `deleg-competencias-eeae`, 714 (calendario UVigo) |
| Estudiante que no puede ir (enfermedad, coincidencia, deportista) | 565 art. 26 | 479 (deportistas), 475 (NEAE) |
| Retraso, desarrollo y vigilancia del examen, identificación, móviles | 565 arts. 27–29 | la guía |
| **Conservar exámenes** (cuánto tiempo, quién) | 565 art. 30 | `lpac` art. 17 |
| Notas: escala, no presentado, matrícula de honor | 565 arts. 31–33 | 584 (RD 1125/2003, escala y MH) |
| Publicar notas (plazos, cómo, datos personales) | 565 art. 34 | 560 y `lopdgdd` (no publicar más datos de los necesarios) |
| **Revisión** de notas y acreditación de la revisión | 565 arts. 35–36 | `rd-1791-2010…` |
| Reclamación ante tribunal, recurso de alzada | 565 arts. 37, 44–47, 61 | `lpac` (recursos) |
| **Copiar, plagio, móviles no permitidos, fraude** | 565 arts. 39–43 | 567 (disciplinario estudiantes), `ley-convivencia-universitaria`, 566 (código ético) |
| Evaluación por compensación | 565 arts. 48–55 | — |
| Actas: cumplimentar, cerrar, plazos | 353 (Título III) | calendario de la Escola (fechas de cierre de actas) |
| Tutorías, acción tutorial | 429; `reti` (Escola) | 565 art. 16, 512 art. 3 |
| TFG / TFM | 550 (TFG UVigo), 549 (TFM UVigo) y `tfg-tfm-eeae` (Escola) | 698, `rd-822-2021-ordenacion-ensenanzas`; defensas y cierre de actas en el calendario de la Escola |
| Prácticas externas | 586 y 700 (UVigo), `practicas-eeae` (Escola) | 701 |
| Estudiantes con necesidades específicas / deportistas | 565 art. 17, 475, 479 | `rd-1791-2010…`, 651 |
| Grabar clases, materiales en Moovi, medios electrónicos | 697 (medios electrónicos), 444 (aviso: era COVID; «non terá obriga de gravar as súas clases») | `propiedad-intelectual`, `lopdgdd`, 565 art. 22 (grabación de orales) |
| POD, asignación de docencia | 709 (POD 2026/27, + corrección de errores en doc1) | 657, 512 art. 5; 714 (calendario 2026/27) |
| Docencia en inglés u otra lengua | 643 (ReDLE), 695 (convocatoria vigente), 676 (English Friendly: las guías de SP y STR lo son) | 56 (uso del gallego) |
| Reconocimiento de créditos, permanencia, simultaneidad | 681, 628 | `normativa-mobilidade-eeae` |
| Conducta del estudiante, convivencia | 567, 569 | `ley-convivencia-universitaria`, 460 |
| Máster | 672 | — |

## Doctorado (como doctorando/a o como director/a o tutor/a)

| Duda | Leer primero | Complementar con |
|---|---|---|
| Plazos: duración, prórrogas, bajas, tiempo parcial | 625 arts. 24–29 | `rd-99-2011-doctorado` art. 3 |
| Plan de investigación, documento de actividades, evaluación anual, compromiso de supervisión | 625 arts. 31–33 | `rd-99-2011-doctorado` art. 11; web del programa del doctorando (seguimiento) |
| Actividades formativas obligatorias del programa | web del programa del doctorando (actividades formativas; en línea) | 625 art. 32 (plan de formación), `convocatoria-reconocimiento-actividades` (escaneado) |
| Dirección y tutoría: quién puede dirigir, codirección, cambio de director | 625 arts. 9–10, 7–8 (experiencia investigadora acreditada) | `rd-99-2011-doctorado` art. 12; `eido-codigo-boas-practicas` |
| Conflictos con la dirección o con el programa | 625 art. 34 | `eido-codigo-boas-practicas`, 423 (Valedor/a) |
| Tesis: formato, compendio de artículos, depósito, informes externos | 625 arts. 35–36, 41–42 | `eido-normas-de-estilo-tese`, `eido-guia-solicitude-deposito-tese`, `rd-99-2011-doctorado` art. 14 |
| Tribunal, defensa y calificación, cum laude | 625 arts. 38–40 | `eido-protocolo-defensa-tese`, `instrucion-gastos-tribunais-teses` (escaneado), `rd-99-2011-doctorado` art. 14 |
| Mención internacional, cotutela, doctorado industrial | 625 arts. 43–45 | `procedemento-cotutela` (2015), `rd-99-2011-doctorado` art. 15 |
| Tesis con datos personales o confidenciales, patentes | 625 art. 37 | `procedemento-teses-proteccion-datos` (2015), `lopdgdd`, 213 (propiedad industrial) |
| Derechos y deberes del doctorando, actividades formativas | 625 arts. 30, 48–49 | `rd-1791-2010-estatuto-estudiante`; si hay contrato predoctoral, `rd-103-2019-epif` |
| Firma de publicaciones, ética | 433 (firma científica), `eido-codigo-boas-practicas` | 458, 497 |
| Órganos: EIDO, comisión académica del programa | 41 (RRI de la EIDO), 625 arts. 3–6 | — |

Lo que cambia cada curso y no está en el corpus (plazos de depósito, calendario de matrícula, convocatorias de premios y ayudas, avisos y acuerdos de la comisión académica) está en la web de la EIDO y en la web del programa de la persona (la lista de programas está en `eido.uvigo.gal`). La web del programa no es norma aprobada: si difiere de 625, manda 625: ver «Consultar en internet» en `SKILL.md`.

## Investigación y transferencia

| Duda | Leer primero | Complementar con |
|---|---|---|
| Contratar personal investigador / con cargo a proyectos | 684, 530 | 619 (recursos liberados) |
| Contratos con empresas (art. 83) | 621 | 147, 213, 215 |
| Propiedad intelectual / industrial | 213 | `propiedad-intelectual` (autoría de materiales docentes, obras en colaboración) |
| Ética de la investigación | 458 (CETIC), 497 (seres humanos y medio ambiente) | `eido-codigo-boas-practicas` |
| Firma científica | 433 | — |
| Protección de datos | 560 (repositorio de normativa de datos de la UVigo), 118 (RGPD) | `lopdgdd` |

## Gobierno, órganos y procedimiento

| Duda | Leer primero | Complementar con |
|---|---|---|
| Qué puede decidir la Escola vs la Universidad | `rri-eeae`, `deleg-competencias-eeae` | Estatutos 267 (arts. 16, 38), 616 (delegación de competencias) |
| Convocatorias, actas, quórum, voto en órganos colegiados | `rri-eeae` (Título II) | `lrjsp` arts. sobre órganos colegiados |
| Recursos, plazos, notificaciones, abstención | `lpac`, `lrjsp` | 267 disposición adicional única (qué agota la vía administrativa), 565 art. 61 (alzada en evaluación) |
| Acoso, igualdad, no discriminación | 673 (protocolo acoso sexual), 94, 96, 715 | `ley-igualdad`, `convenio-pdi-laboral-acta-paritaria-2025-02-07` |
| Denuncias, canal interno | 656 | `ley-informantes` |
| Correo corporativo, medios electrónicos | 595, 62 | `lpac` |

## Cómo usar este mapa

1. Identifica el/los temas de la pregunta.
2. Lee **la norma de mayor rango** de la fila primero y luego baja de nivel (ver `jerarquia.md`).
3. Si la fila remite a una norma anual (POD, dedicación, calendario, vacaciones) comprueba **para qué curso/año es** y si hay hueco en `huecos.md`.
4. Si el tema no está en el mapa, usa `buscar.py` con varios términos (gallego y castellano) o `buscar.py --lista --ambito <ámbito>` para ver qué hay.
