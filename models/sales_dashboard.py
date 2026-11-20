# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


class MinoriSalesDashboard(models.Model):
    _inherit = 'method_minori.marcas'

    def _has_all_brand_access(self):
        return any(
            self.env.user.has_group(group)
            for group in (
                'base.group_system',
                'sales_team.group_sale_manager',
                'purchase.group_purchase_manager',
                'method_minori.group_proveedores_marcas',
            )
        )

    def _get_allowed_dashboard_brands(self):
        domain = [
            ('active', '=', True),
            ('company_id', 'in', [self.env.company.id, False]),
        ]
        if not self._has_all_brand_access():
            domain.append(('user_id', '=', self.env.user.id))
        return self.search(domain, order='name')

    @api.model
    def get_sales_dashboard_data(self, brand_id=False, date_from=False, date_to=False,
                                 all_brands=False):
        """Datos del dashboard de ventas por marca.

        Contrato:
          * ``brand_id`` concreto: ventas de esa marca (debe estar entre las marcas
            permitidas del usuario, si no ``AccessError``).
          * ``brand_id`` falso y ``all_brands`` falso: se usa la primera marca
            permitida (comportamiento histórico del dashboard del backend de Odoo).
          * ``all_brands=True``: consolidado de TODAS las marcas activas de la
            compañía activa (las mismas que ``brands``). Solo se permite si el
            usuario tiene acceso total (``_has_all_brand_access``); si no,
            ``AccessError``. Tiene prioridad sobre ``brand_id``.

        La forma de la respuesta es la misma en ambos modos. En el consolidado
        ``selected_brand_id`` es ``False`` y ``all_brands`` es ``True``.
        """
        if all_brands and not self._has_all_brand_access():
            raise AccessError(_('No tiene acceso a la vista consolidada de todas las marcas.'))

        allowed_brands = self._get_allowed_dashboard_brands()
        brand_values = [{'id': brand.id, 'name': brand.name} for brand in allowed_brands]

        if not allowed_brands:
            empty = {
                'brands': [],
                'selected_brand_id': False,
                'all_brands': bool(all_brands),
                'date_from': date_from,
                'date_to': date_to,
                'currency': self.env.company.currency_id.symbol or '$',
                'summary': self._empty_summary(),
                'products': [],
                'customers': [],
                'sellers': [],
                'pos_branches': [],
            }
            if all_brands:
                empty['sales_by_brand'] = []
            return empty

        if all_brands:
            selected_brands = allowed_brands
            selected_brand_id = False
        else:
            selected_brand = allowed_brands[0]
            if brand_id:
                try:
                    brand_id = int(brand_id)
                except (TypeError, ValueError):
                    raise UserError(_('Marca inválida.'))
                selected_brand = self.browse(brand_id)
                if selected_brand not in allowed_brands:
                    raise AccessError(_('No tiene acceso a la marca seleccionada.'))
            selected_brands = selected_brand
            selected_brand_id = selected_brand.id

        date_from_value, date_to_value = self._normalize_dashboard_dates(date_from, date_to)
        date_to_exclusive = date_to_value + timedelta(days=1)

        params = {
            'brand_ids': selected_brands.ids,
            'date_from': date_from_value,
            'date_to': date_to_exclusive,
            'lang': self.env.lang or 'en_US',
            'company_id': self.env.company.id,
        }

        result = {
            'brands': brand_values,
            'selected_brand_id': selected_brand_id,
            'all_brands': bool(all_brands),
            'date_from': fields.Date.to_string(date_from_value),
            'date_to': fields.Date.to_string(date_to_value),
            'currency': self.env.company.currency_id.symbol or '$',
            'summary': self._get_sales_summary(params),
            'products': self._get_sales_dimension(params, 'product'),
            'customers': self._get_sales_dimension(params, 'customer'),
            'sellers': self._get_sales_dimension(params, 'seller'),
            'pos_branches': self._get_sales_by_pos(params),
        }
        if all_brands:
            # Additive key: only present in consolidated mode, so the single-brand
            # response (and the Odoo backend dashboard that consumes it) is unchanged.
            result['sales_by_brand'] = self._get_sales_by_brand(params)
        return result

    def _normalize_dashboard_dates(self, date_from, date_to):
        today = fields.Date.context_today(self)
        start = fields.Date.from_string(date_from) if date_from else today.replace(day=1)
        end = fields.Date.from_string(date_to) if date_to else today
        if start > end:
            raise UserError(_('La fecha inicial no puede ser mayor que la fecha final.'))
        return start, end

    def _sales_cte(self):
        return """
            WITH sales AS (
                SELECT
                    pt.marca_id AS brand_id,
                    pol.product_id AS product_id,
                    po.partner_id AS customer_id,
                    po.user_id AS seller_id,
                    pol.qty AS quantity,
                    pol.price_subtotal AS amount_untaxed,
                    pol.price_subtotal_incl AS amount_total
                FROM pos_order po
                JOIN pos_order_line pol ON pol.order_id = po.id
                JOIN product_product pp ON pp.id = pol.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE pt.marca_id = ANY(%(brand_ids)s)
                    AND po.company_id = %(company_id)s
                    AND po.state IN ('paid', 'done', 'invoiced')
                    AND po.date_order >= %(date_from)s
                    AND po.date_order < %(date_to)s

                UNION ALL

                SELECT
                    pt.marca_id AS brand_id,
                    aml.product_id AS product_id,
                    am.partner_id AS customer_id,
                    am.invoice_user_id AS seller_id,
                    CASE WHEN am.move_type = 'out_refund' THEN -aml.quantity ELSE aml.quantity END AS quantity,
                    CASE WHEN am.move_type = 'out_refund' THEN -aml.price_subtotal ELSE aml.price_subtotal END AS amount_untaxed,
                    CASE WHEN am.move_type = 'out_refund' THEN -aml.price_total ELSE aml.price_total END AS amount_total
                FROM account_move am
                JOIN account_move_line aml ON aml.move_id = am.id
                JOIN product_product pp ON pp.id = aml.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE pt.marca_id = ANY(%(brand_ids)s)
                    AND am.company_id = %(company_id)s
                    AND am.state = 'posted'
                    AND am.move_type IN ('out_invoice', 'out_refund')
                    AND am.invoice_date >= %(date_from)s
                    AND am.invoice_date < %(date_to)s
                    AND COALESCE(aml.display_type, 'product') = 'product'
            )
        """

    def _get_sales_summary(self, params):
        self.env.cr.execute(
            self._sales_cte()
            + """
                SELECT
                    COALESCE(SUM(quantity), 0) AS quantity,
                    COALESCE(SUM(amount_untaxed), 0) AS amount_untaxed,
                    COALESCE(SUM(amount_total), 0) AS amount_total,
                    COUNT(*) AS lines,
                    COUNT(DISTINCT product_id) AS products,
                    COUNT(DISTINCT customer_id) AS customers,
                    COUNT(DISTINCT seller_id) AS sellers
                FROM sales
            """,
            params,
        )
        row = self.env.cr.dictfetchone() or {}
        return self._format_summary(row)

    def _get_sales_dimension(self, params, dimension):
        definitions = {
            'product': {
                'select': """
                    sales.product_id AS id,
                    COALESCE(
                        pt.name->>%(lang)s,
                        pt.name->>'es_CL',
                        pt.name->>'es_ES',
                        pt.name->>'en_US',
                        pp.default_code,
                        'Sin producto'
                    ) AS name
                """,
                'join': """
                    LEFT JOIN product_product pp ON pp.id = sales.product_id
                    LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                """,
                'group': "sales.product_id, pt.name, pp.default_code",
            },
            'customer': {
                'select': "sales.customer_id AS id, COALESCE(rp.name, 'Sin cliente') AS name",
                'join': "LEFT JOIN res_partner rp ON rp.id = sales.customer_id",
                'group': "sales.customer_id, rp.name",
            },
            'seller': {
                'select': "sales.seller_id AS id, COALESCE(rp.name, 'Sin vendedor') AS name",
                'join': """
                    LEFT JOIN res_users ru ON ru.id = sales.seller_id
                    LEFT JOIN res_partner rp ON rp.id = ru.partner_id
                """,
                'group': "sales.seller_id, rp.name",
            },
        }
        definition = definitions[dimension]
        query = self._sales_cte() + """
            SELECT
                {select},
                COALESCE(SUM(sales.quantity), 0) AS quantity,
                COALESCE(SUM(sales.amount_untaxed), 0) AS amount_untaxed,
                COALESCE(SUM(sales.amount_total), 0) AS amount_total,
                COUNT(*) AS lines
            FROM sales
            {join}
            GROUP BY {group}
            ORDER BY amount_total DESC
            LIMIT 10
        """.format(**definition)
        self.env.cr.execute(query, params)
        return [self._format_dimension_row(row) for row in self.env.cr.dictfetchall()]

    def _get_sales_by_brand(self, params):
        """Ventas por marca con la misma CTE (periodo, compañía, POS + facturas) que
        ``summary``; la suma de ``amount_total`` cuadra con ``summary.amount_total``."""
        self.env.cr.execute(
            self._sales_cte()
            + """
                SELECT
                    sales.brand_id AS brand_id,
                    mm.name AS brand_name,
                    COALESCE(SUM(sales.quantity), 0) AS quantity,
                    COALESCE(SUM(sales.amount_untaxed), 0) AS amount_untaxed,
                    COALESCE(SUM(sales.amount_total), 0) AS amount_total,
                    COUNT(*) AS lines
                FROM sales
                LEFT JOIN method_minori_marcas mm ON mm.id = sales.brand_id
                GROUP BY sales.brand_id, mm.name
                ORDER BY amount_total DESC, mm.name
            """,
            params,
        )
        return [
            {
                'brand_id': row.get('brand_id') or False,
                'brand_name': row.get('brand_name') or _('Sin marca'),
                'amount': float(row.get('amount_total') or 0.0),
                'amount_untaxed': float(row.get('amount_untaxed') or 0.0),
                'units': float(row.get('quantity') or 0.0),
                'lines': int(row.get('lines') or 0),
            }
            for row in self.env.cr.dictfetchall()
        ]

    def _get_sales_by_pos(self, params):
        self.env.cr.execute("""
            SELECT
                pc.id AS id,
                pc.name AS name,
                COALESCE(SUM(pol.qty), 0) AS quantity,
                COALESCE(SUM(pol.price_subtotal), 0) AS amount_untaxed,
                COALESCE(SUM(pol.price_subtotal_incl), 0) AS amount_total,
                COUNT(*) AS lines
            FROM pos_order po
            JOIN pos_order_line pol ON pol.order_id = po.id
            JOIN pos_session ps ON ps.id = po.session_id
            JOIN pos_config pc ON pc.id = ps.config_id
            JOIN product_product pp ON pp.id = pol.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pt.marca_id = ANY(%(brand_ids)s)
                AND po.company_id = %(company_id)s
                AND po.state IN ('paid', 'done', 'invoiced')
                AND po.date_order >= %(date_from)s
                AND po.date_order < %(date_to)s
            GROUP BY pc.id, pc.name
            ORDER BY amount_total DESC
        """, params)
        return [self._format_dimension_row(row) for row in self.env.cr.dictfetchall()]

    def _empty_summary(self):
        return {
            'quantity': 0.0,
            'amount_untaxed': 0.0,
            'amount_total': 0.0,
            'lines': 0,
            'products': 0,
            'customers': 0,
            'sellers': 0,
        }

    def _format_summary(self, row):
        summary = self._empty_summary()
        summary.update({
            'quantity': float(row.get('quantity') or 0.0),
            'amount_untaxed': float(row.get('amount_untaxed') or 0.0),
            'amount_total': float(row.get('amount_total') or 0.0),
            'lines': int(row.get('lines') or 0),
            'products': int(row.get('products') or 0),
            'customers': int(row.get('customers') or 0),
            'sellers': int(row.get('sellers') or 0),
        })
        return summary

    def _format_dimension_row(self, row):
        return {
            'id': row.get('id') or False,
            'name': row.get('name') or _('Sin dato'),
            'quantity': float(row.get('quantity') or 0.0),
            'amount_untaxed': float(row.get('amount_untaxed') or 0.0),
            'amount_total': float(row.get('amount_total') or 0.0),
            'lines': int(row.get('lines') or 0),
        }
