#!/usr/bin/env bash
set -euo pipefail
export MSYS_NO_PATHCONV=1
case "${1:-}" in
P0)
docker compose version
docker images postgres:16
docker compose up -d --wait
cat politica/POLITICA-DE-SEGURIDAD.md
;;
P1) docker compose ps | tee evidencias/P1_puertos.txt ;;
P2) grep -n "PASSWORD" docker-compose.yml | tee evidencias/P2_credenciales.txt ;;
P3) docker exec sr_bd psql -U postgres -d core -c "\du" | tee evidencias/P3_roles.txt ;;
P4)
docker exec sr_bd psql -U postgres -d core -c "SELECT u.usuario, e.nombre, e.fecha_cese FROM usuarios u JOIN empleados e ON e.documento = u.documento WHERE u.estado = 'activo' AND e.fecha_cese IS NOT NULL ORDER BY e.fecha_cese" | tee evidencias/P4_cesados.txt
docker exec sr_bd psql -U postgres -d core -c "SELECT usuario, perfil FROM usuarios WHERE documento IS NULL AND estado = 'activo' ORDER BY perfil, usuario" | tee evidencias/P4_genericas.txt
;;
P5)
docker exec sr_bd psql -U postgres -d core -c "SELECT count(*) AS casos, sum(monto) AS monto_total, count(DISTINCT usuario_registra) AS usuarios FROM desembolsos WHERE monto > umbral_aprobacion AND usuario_registra = usuario_aprueba" | tee evidencias/P5_segregacion.txt
docker exec sr_bd psql -U postgres -d core -c "SELECT id, fecha, monto, usuario_registra FROM desembolsos WHERE monto > umbral_aprobacion AND usuario_registra = usuario_aprueba ORDER BY monto DESC" | tee -a evidencias/P5_segregacion.txt
;;
P6)
docker exec sr_bd psql -U postgres -d core -c "SHOW log_connections" -c "SHOW log_statement" | tee evidencias/P6_registro.txt
grep -n 'command:' docker-compose.yml
;;
P7)
ls respaldos/ | tee evidencias/P7_respaldos.txt
tail -n 5 respaldos/respaldo.log | tee -a evidencias/P7_respaldos.txt
docker exec sr_bd psql -v ON_ERROR_STOP=1 -U postgres -c "DROP DATABASE IF EXISTS restauracion"
docker exec sr_bd psql -v ON_ERROR_STOP=1 -U postgres -c "CREATE DATABASE restauracion"
docker exec -i sr_bd psql -v ON_ERROR_STOP=1 -U postgres -d restauracion < respaldos/core_2025-11-14.sql
docker exec sr_bd psql -U postgres -d restauracion -c "\dt" | tee evidencias/P7_restauracion.txt
;;
P8)
docker exec sr_bd psql -U postgres -d core -c "SELECT count(*) AS cuentas_activas_cesados, count(DISTINCT e.documento) AS personas, min(e.fecha_cese) AS cese_mas_antiguo FROM usuarios u JOIN empleados e ON e.documento=u.documento WHERE u.estado='activo' AND e.fecha_cese IS NOT NULL" -c "SELECT count(*) AS sin_documento, count(*) FILTER (WHERE perfil='ADMIN') AS administradores FROM usuarios WHERE documento IS NULL AND estado='activo'" -c "SELECT DATE '2025-12-31' - DATE '2025-11-14' AS dias_sin_respaldo" -c "SELECT count(*) AS desembolsos_core, sum(monto) AS monto_total_core FROM desembolsos" -c "\dt" | tee evidencias/P8_validacion.txt
nl -ba respaldos/respaldo.sh
nl -ba bd/01_core.sql
;;
P9) sha256sum evidencias/P*.txt > evidencias/SHA256SUMS.txt; sha256sum -c evidencias/SHA256SUMS.txt ;;
P10) docker compose down -v ;;
*) echo 'Procedimiento no permitido'; exit 1 ;;
esac
