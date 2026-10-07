# Informe de auditoría · Core financiero de la COOPAC Santa Rosa

**UNIVERSIDAD PRIVADA DE TACNA · FACULTAD DE INGENIERÍA**  
**Escuela Profesional de Ingeniería de Sistemas**  
**SI-084 · Auditoría de Sistemas · Examen práctico de Unidad I**

| | |
|---|---|
| **Apellidos y nombres** | Akhtar Oviedo Ahmed Hasan |
| **Código de estudiante** | 2022074261 |
| **Docente** | Dr. Oscar Juan Jimenez Flores |
| **URL del repositorio** | https://github.com/Aakhtar004/si084-caso-coopac/tree/examen-u1 |
| **Fecha de ejecución e informe** | 07/10/2026 |
| **Corte auditado** | 31/12/2025 |
| **Lugar** | Tacna, Perú |

**Objetivo.** Determinar si el servidor de base de datos del core financiero cumple las siete reglas de la política aprobada por el Consejo de Administración.

**Conclusión.** El servidor **no cumple: 0 reglas cumplen y 7 incumplen**. Los resultados proceden de la ejecución real de P1–P7 en PostgreSQL 16 sobre Docker. Se restauró el último respaldo en una base independiente llamada `restauracion`, sin modificar la configuración ni los datos del caso. La fecha de ejecución no modifica el corte histórico de la evaluación.

## 1. Resultados de los procedimientos

| Regla | Resultado, con cifras | ¿Cumple? | Archivo de evidencia |
|---|---|---|---|
| R1 | `sr_bd` publica `0.0.0.0:55432 → 5432/tcp` y `[::]:55432 → 5432/tcp`: todas las interfaces IPv4 e IPv6, no solo el propio servidor. | No | [P1_puertos.txt](evidencias/P1_puertos.txt) |
| R2 | La contraseña administrativa figura en texto plano en `docker-compose.yml`, **línea 10**. Tiene **10 caracteres**, 2 menos que el mínimo de 12. No se reproduce la contraseña en este informe. | No | [P2_credenciales.txt](evidencias/P2_credenciales.txt) |
| R3 | **1 cuenta adicional**, `app_core`, tiene `Superuser` además de `postgres`: **2 superusuarios** en total entre los 4 roles listados. | No | [P3_roles.txt](evidencias/P3_roles.txt) |
| R4 | **16 cuentas activas** pertenecen a **10 personas distintas cesadas**; el cese más antiguo es **18/12/2015** (`u059`). Hay **22 cuentas activas sin documento**, de las cuales **4 tienen perfil ADMIN**: `backup`, `backup_3`, `consulta01_3` y `temporal`. | No | [P4_cesados.txt](evidencias/P4_cesados.txt) · [P4_genericas.txt](evidencias/P4_genericas.txt) · [P8_validacion.txt](evidencias/P8_validacion.txt) |
| R5 | **23 desembolsos** superiores a su umbral fueron registrados y aprobados por el mismo usuario, por **S/ 709,370.47**, con **21 usuarios distintos**. | No | [P5_segregacion.txt](evidencias/P5_segregacion.txt) |
| R6 | `log_connections = off` y `log_statement = none`, en lugar de `on` y `mod`. Ambos parámetros se desactivan explícitamente en `docker-compose.yml`, **línea 11**. | No | [P6_registro.txt](evidencias/P6_registro.txt) · [P6_ejecucion.log](evidencias/P6_ejecucion.log) |
| R7 | Hay **3 archivos SQL** de respaldo. El último es **14/11/2025**, **47 días** antes del corte. La restauración terminó sin errores y recuperó **2 tablas**, `empleados` y `usuarios`; falta **`desembolsos`**, presente en el core. El script la excluye y el registro consigna fallos por falta de espacio desde el 15/11/2025. No se aportó evidencia de pruebas trimestrales previas; la prueba actual no acredita ese cumplimiento histórico. | No | [P7_respaldos.txt](evidencias/P7_respaldos.txt) · [P7_restauracion.txt](evidencias/P7_restauracion.txt) · [P7_ejecucion.log](evidencias/P7_ejecucion.log) · [P8_validacion.txt](evidencias/P8_validacion.txt) |

**Condición SQL de P5**, aplicada idénticamente al resumen y al detalle:

```sql
monto > umbral_aprobacion AND usuario_registra = usuario_aprueba
```

Se usa `>` porque R5 exige que el monto **supere** el umbral; no corresponde incluir operaciones iguales al umbral. El total es el importe de operaciones observadas, no una pérdida económica demostrada.

**Priorización.** Se seleccionan R5 por la exposición directa de fondos sin aprobación independiente y R7 por la imposibilidad de recuperar íntegramente el core con los respaldos entregados. Las otras cinco reglas también incumplen y deben ser atendidas por el Jefe de Sistemas.

## 2. Hallazgo 1

| Elemento | Contenido |
|---|---|
| Título | Desembolsos por S/ 709,370.47 aprobados por sus propios registradores pese a superar el umbral. |
| Condición | P5 identificó **23 desembolsos**, por **S/ 709,370.47**, registrados y aprobados por **21 usuarios distintos**. El mayor es `D00680`, del **17/08/2025**, por **S/ 161,160.52**, registrado por `u001`. El resumen y las 23 operaciones constan en `evidencias/P5_segregacion.txt`; su ejecución real, en `evidencias/P5_ejecucion.log`. |
| Criterio | **R5** de `politica/POLITICA-DE-SEGURIDAD.md`: un desembolso que supera el umbral no puede aprobarlo quien lo registró. Control de referencia de la política: **NTP-ISO/IEC 27001:2022, A.5.3 · Segregación de funciones**. |
| Causa | En `bd/01_core.sql`, **líneas 20–27**, la tabla almacena monto, umbral y ambos usuarios, pero no define una restricción que impida la autoaprobación sobre el umbral. La **línea 31** carga directamente los datos mediante `COPY`; las 23 operaciones efectivamente cargadas demuestran que esta ruta admite el incumplimiento. El paquete no contiene código de aplicación que permita atribuir una causa adicional a su flujo de aprobación. Fuente complementaria: `evidencias/P8_ejecucion.log`. |
| Efecto | **S/ 709,370.47 en 23 operaciones** quedaron sin la independencia de aprobación exigida, lo que permite errores o desembolsos indebidos sin una segunda revisión y expone a pérdidas y cuestionamientos sobre las autorizaciones. La evidencia demuestra exposición al riesgo, no fraude ni pérdida efectiva por ese monto. |
| Recomendación | El **Jefe de Sistemas y el responsable de Créditos**, en **48 horas desde la recepción del informe**, deben impedir nuevas autoaprobaciones sobre el umbral y disponer un aprobador distinto. En **10 días calendario**, Sistemas debe implementar y probar una validación en la aplicación y una restricción equivalente en la base, incluyendo valores nulos y casos iguales, inferiores y superiores al umbral. Créditos debe revisar independientemente las **23 operaciones**, conservar el sustento y resolver las excepciones en **15 días calendario**; Auditoría Interna verificará el cierre. |

## 3. Hallazgo 2

| Elemento | Contenido |
|---|---|
| Título | Respaldos con 47 días de antigüedad y sin la tabla de desembolsos impiden recuperar íntegramente el core. |
| Condición | De los **3 respaldos SQL**, el más reciente es `core_2025-11-14.sql`, **47 días anterior al 31/12/2025**. Se creó `restauracion`, se importó ese archivo y se listaron las tablas: solo se recuperaron **`empleados` y `usuarios`**; falta **`desembolsos`**. El core contiene **4,812 desembolsos**, por **S/ 45,124,350.88**, cuya tabla no se recupera con ese respaldo. Evidencias: `evidencias/P7_respaldos.txt`, `evidencias/P7_restauracion.txt`, `evidencias/P7_ejecucion.log` y `evidencias/P8_validacion.txt`. |
| Criterio | **R7** de `politica/POLITICA-DE-SEGURIDAD.md`: respaldo diario completo, incluida la tabla de desembolsos, y prueba trimestral de restauración. Control de referencia de la política: **NTP-ISO/IEC 27001:2022, A.8.13 · Respaldo de la información**. |
| Causa | `respaldos/respaldo.sh`, **líneas 3–4**, documenta la decisión del Jefe de Sistemas de excluir la tabla por su duración y ejecuta `pg_dump` con **`--exclude-table=desembolsos`**. Además, `respaldos/respaldo.log` registra **47 fallos diarios**, del **15/11/2025 al 31/12/2025**, con `No space left on device`: la falta de espacio impidió nuevos respaldos satisfactorios en ese intervalo. Son dos causas distintas: exclusión deliberada de información y agotamiento del almacenamiento. |
| Efecto | Ante una pérdida del core, el último respaldo entregado no permite recuperar la tabla que contiene **4,812 desembolsos por S/ 45,124,350.88**; tampoco asegura recuperar actualizaciones de las otras tablas durante los **47 días** posteriores al último respaldo. Esto compromete continuidad operativa, conciliaciones y trazabilidad. Los importes representan registros expuestos a pérdida de información, no una pérdida monetaria comprobada; no se cuantifica un tiempo de recuperación porque no existe medición suficiente. |
| Recomendación | El **Jefe de Sistemas y el administrador de base de datos**, en **24 horas desde la recepción del informe**, deben ampliar o liberar capacidad mediante una retención aprobada, retirar la exclusión y generar un respaldo completo. En **48 horas**, deben restaurarlo en un entorno aislado y conciliar las **3 tablas**, sus recuentos y los totales de desembolsos. En **7 días calendario**, implementar alertas de espacio, resultado y antigüedad del respaldo, revisión diaria y copias separadas del servidor. El Jefe de Sistemas programará pruebas **trimestrales** con acta y evidencia; Auditoría Interna verificará la primera prueba y el cierre. |

## 4. Trazabilidad de la ejecución

- Los TXT de P1–P7 contienen las salidas exigidas; `P8_validacion.txt` respalda los agregados adicionales.
- `scripts/auditoria.sh` conserva los comandos. En la restauración se añadió `ON_ERROR_STOP=1` para detectar fallos y se separaron las tres órdenes que el examen presenta en una sola línea.
- Las capturas `00_preparacion.png` a `08_validacion_causas.png`, en `evidencias/capturas/`, corresponden a un panel local del navegador que ejecutó Git Bash. **No son capturas de una terminal nativa** ni sustituyen los TXT exigidos. Los registros `P*_ejecucion.log` conservan comandos, salida, fecha y código de retorno.
- `evidencias/SHA256SUMS.txt` permite verificar los TXT mediante `sha256sum -c evidencias/SHA256SUMS.txt` desde la raíz del repositorio.
- Los controles se citan conforme a la política del caso; esta evaluación no constituye una certificación.
