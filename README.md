# SI-084 · Caso COOPAC Santa Rosa

**Akhtar Oviedo Ahmed Hasan · 2022074261**  
Auditoría de Sistemas · Examen práctico de Unidad I · UPT

## Entrega

- [Informe completo](INFORME.md).
- [Entrega etiquetada](https://github.com/Aakhtar004/si084-caso-coopac/tree/examen-u1).
- [Evidencias](evidencias/) y [capturas](evidencias/capturas/).
- PDF: `output/pdf/SI084-EXPRAC-U1-AkhtarOviedoAhmedHasan.pdf`.

Resultado: **0 de 7 reglas cumplen**. Se priorizan R5 y R7. Corte: 31/12/2025; ejecución efectiva: 07/10/2026.

## Reproducción

En Git Bash, desde este directorio, con Docker disponible:

```bash
bash scripts/auditoria.sh P0
for p in P1 P2 P3 P4 P5 P6 P7 P8; do bash scripts/auditoria.sh "$p"; done
bash scripts/auditoria.sh P9
sha256sum -c evidencias/SHA256SUMS.txt
bash scripts/auditoria.sh P10
```

P7 requiere una base `restauracion` que todavía no exista. Reproduzca en una copia independiente: las salidas de Docker contienen tiempos variables y una nueva ejecución cambiaría los hashes de la entrega.

Opcionalmente, `python scripts/panel.py` abre `http://127.0.0.1:8765/`; sus botones ejecutan los mismos comandos reales. Se utilizó para capturas complementarias porque la conexión de automatización del escritorio no estuvo disponible. No se presentan como capturas de terminal nativa. El examen no incluye una aplicación web con formularios.

La configuración, `bd/`, `datos/`, `politica/` y `respaldos/` se conservan como material del caso. Las debilidades se documentan, no se corrigen en el objeto auditado. Las credenciales incluidas son las del laboratorio suministrado.

## Integridad y publicación

`evidencias/SHA256SUMS.txt` sella los TXT de los procedimientos y se excluye a sí mismo para evitar una referencia circular. `evidencias/SHA256_ADICIONALES.sha256` cubre los registros y capturas previos a la publicación. La etiqueta `examen-u1` fija la entrega. Las verificaciones posteriores de GitHub se conservan localmente en `entrega/verificacion/`, fuera del contenido ya sellado.

La carga al aula virtual requiere la URL de la tarea y una sesión autorizada disponible. Publicar en GitHub no equivale a entregar en el aula.
