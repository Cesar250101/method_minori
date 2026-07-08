# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Install / Update the module
```bash
# From the Odoo root
./odoo-bin -u method_minori -d <database>
```

### Run Odoo with this module loaded
```bash
./odoo-bin --addons-path=addons,extra-addons -d <database>
```

### Run a single test
```bash
./odoo-bin -u method_minori -d <database> --test-enable --stop-after-init
```

## Architecture

This is an Odoo 16.0 custom module (single-company retail/minorista localization) developed by Method ERP. It depends on `l10n_cl_dte_point_of_sale` (Chilean SII/DTE electronic billing), `report_xlsx`, `stock`, `purchase`, and `sale`.

### Core domain: Brands (`method_minori.marcas`)

Defined in [models/models.py](models/models.py). The central model. Each brand has a responsible user (`user_id`), a commission percentage (`comision_marca`), and an `es_propia` flag to distinguish own-brand from third-party. The `product.template` is extended to add `marca_id` — when changed via UI, the `_onchange_marca_id` method auto-creates the matching POS category if absent. `calcular_costo()` on both `product.template` and `product.product` recalculates `standard_price` from `list_price / 1.19 * (1 - comision_marca/100)`.

### Commission report flow

1. **Wizard** (`method_minori.wizard_comision_marca` in [models/wizard_comision_marcas.py](models/wizard_comision_marcas.py)): transient model with `marca_id`, `periodo_id`, and `pos_id` fields. Triggers `imprimir_pdf` or `imprimir_excel`.
2. **Period model** (`method_minori.periodos` in [models/comision_marca.py](models/comision_marca.py)): stores date ranges used as filter for raw SQL queries.
3. **Excel report** (`report.method_minori.report_comision_excel` in [models/wizard_comision_marcas.py](models/wizard_comision_marcas.py)): inherits `report.report_xlsx.abstract`, generates the XLSX directly via `xlsxwriter`. Columns start at col 3 (D). Footer summarizes: total bruto → IVA (÷1.19) → neto → comisión → venta neta → factura bruta.
4. **`_comision_mes()`** (in [models/comision_marca.py](models/comision_marca.py)): executes raw SQL joining `pos_order`, `pos_order_line`, `method_minori_marcas`, filtered by brand, POS config, and date range. The `ReporteComisionMarcas` class inherits the wizard to add this method.

### SQL view-based reports (`_auto = False`)

All defined in [report/stock_report.py](report/stock_report.py) and [report/reporte_marcas.py](report/reporte_marcas.py). Each uses `tools.drop_view_if_exists` + `CREATE OR REPLACE VIEW` in `init()`:

| Model | Purpose |
|---|---|
| `method_minori.ventas_report_marcas` | UNION of POS orders + `account_move` lines, per brand |
| `method_minori.report_marcas_propias` | Same UNION but with `es_propia` flag and `sale_order` instead of `account_move` |
| `method_minori.ventas_dia_report` | Daily sales summary grouped by `es_propia`, UNION POS + `sale_order` |
| `method_minori.notas_credito_report` | POS credit notes (`sii_code = 61`) |
| `method_minori.stock_report` | Current stock per product filtered to internal locations, joined to brand |

### POS order report extension

[report/pos_order_report.py](report/pos_order_report.py) inherits `report.pos.order` and overrides `_select`, `_from`, `_group_by`, `_having` to add `marca_id`, `es_propia`, `tipodocto`, and `nrodocumento` columns.

### Key relationships

- `product.template.marca_id` → `method_minori.marcas`  
- `method_minori.marcas.user_id` → `res.users` (brand responsible/commission owner)  
- `method_minori.wizard_comision_marca` uses raw SQL via `self._cr.execute` — date parameters are injected as formatted strings (not ORM).

### Wizard `__init__.py` issue

The current [models/\_\_init\_\_.py](models/__init__.py) imports `wizard_comision_marcas` and `comision_marca` directly from `models/` folder — but those files live in `models/`. The root [\_\_init\_\_.py](__init__.py) imports `models`, `controllers`, and `report`. The `wizard/` directory has an empty `__init__.py` and is not imported from the root — all wizard logic lives in `models/`.
