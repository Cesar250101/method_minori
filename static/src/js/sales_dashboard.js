/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { Component, onWillStart, onMounted, onPatched, onWillUnmount, useRef, useState } from "@odoo/owl";

export class DashboardTable extends Component {}

DashboardTable.template = "method_minori.SalesDashboard.Table";

export class MinoriSalesDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.productChartRef = useRef("productChart");
        this.customerChartRef = useRef("customerChart");
        this.posChartRef = useRef("posChart");
        this._charts = {};
        this.state = useState({
            loading: true,
            brands: [],
            selectedBrandId: false,
            dateFrom: "",
            dateTo: "",
            currency: "$",
            summary: {},
            products: [],
            customers: [],
            sellers: [],
            pos_branches: [],
        });

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadData();
        });

        onMounted(() => this.renderCharts());
        onPatched(() => this.renderCharts());
        onWillUnmount(() => this.destroyCharts());
    }

    async loadData() {
        this.state.loading = true;
        const data = await this.orm.call("method_minori.marcas", "get_sales_dashboard_data", [], {
            brand_id: this.state.selectedBrandId || false,
            date_from: this.state.dateFrom || false,
            date_to: this.state.dateTo || false,
        });
        this.state.brands = data.brands;
        this.state.selectedBrandId = data.selected_brand_id;
        this.state.dateFrom = data.date_from;
        this.state.dateTo = data.date_to;
        this.state.currency = data.currency;
        this.state.summary = data.summary;
        this.state.products = data.products;
        this.state.customers = data.customers;
        this.state.sellers = data.sellers;
        this.state.pos_branches = data.pos_branches || [];
        this.state.loading = false;
    }

    async onBrandChange(ev) {
        this.state.selectedBrandId = Number(ev.target.value) || false;
        await this.loadData();
    }

    onDateFromChange(ev) {
        this.state.dateFrom = ev.target.value;
    }

    onDateToChange(ev) {
        this.state.dateTo = ev.target.value;
    }

    async onApplyFilters() {
        await this.loadData();
    }

    openVentasReport() {
        const domain = [["marca_id", "=", this.state.selectedBrandId]];
        if (this.state.dateFrom) {
            domain.push(["date_order", ">=", this.state.dateFrom]);
        }
        if (this.state.dateTo) {
            domain.push(["date_order", "<=", `${this.state.dateTo} 23:59:59`]);
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Ventas por Marca",
            res_model: "method_minori.ventas_report_marcas",
            views: [[false, "pivot"], [false, "graph"], [false, "tree"]],
            domain,
            context: {
                search_default_group_by_product: 1,
                search_default_group_by_customer: 1,
            },
        });
    }

    // -- Charts -------------------------------------------------------------

    get chartPalette() {
        return [
            "#2563eb", "#7c3aed", "#0ea5e9", "#10b981", "#f59e0b",
            "#ef4444", "#ec4899", "#14b8a6", "#6366f1", "#84cc16",
        ];
    }

    destroyCharts() {
        for (const key of Object.keys(this._charts)) {
            if (this._charts[key]) {
                this._charts[key].destroy();
                this._charts[key] = null;
            }
        }
    }

    renderCharts() {
        if (this.state.loading || typeof Chart === "undefined") {
            return;
        }
        this.destroyCharts();
        this._renderBarChart(this.productChartRef.el, this.state.products);
        this._renderDoughnutChart(this.customerChartRef.el, this.state.customers);
        this._renderPosChart(this.posChartRef.el, this.state.pos_branches);
    }

    _topRows(rows, limit = 7) {
        return (rows || []).slice(0, limit);
    }

    _renderBarChart(canvas, rows) {
        if (!canvas) {
            return;
        }
        const data = this._topRows(rows);
        this._charts.product = new Chart(canvas, {
            type: "bar",
            data: {
                labels: data.map((r) => r.name),
                datasets: [
                    {
                        label: "Venta Bruta",
                        data: data.map((r) => r.amount_total),
                        backgroundColor: this.chartPalette[0],
                        borderRadius: 6,
                        maxBarThickness: 32,
                    },
                ],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => this.formatMoney(ctx.parsed.x),
                        },
                    },
                },
                scales: {
                    x: {
                        ticks: { callback: (v) => this.formatNumber(v, 0) },
                        grid: { color: "#eef1f5" },
                    },
                    y: { grid: { display: false } },
                },
            },
        });
    }

    _renderDoughnutChart(canvas, rows) {
        if (!canvas) {
            return;
        }
        const data = this._topRows(rows);
        this._charts.customer = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: data.map((r) => r.name),
                datasets: [
                    {
                        data: data.map((r) => r.amount_total),
                        backgroundColor: this.chartPalette,
                        borderColor: "#ffffff",
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "60%",
                plugins: {
                    legend: {
                        position: "right",
                        labels: { boxWidth: 12, padding: 12 },
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.label}: ${this.formatMoney(ctx.parsed)}`,
                        },
                    },
                },
            },
        });
    }

    _renderPosChart(canvas, rows) {
        if (!canvas) {
            return;
        }
        const data = this._topRows(rows, 10);
        this._charts.pos = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: data.map((r) => r.name),
                datasets: [
                    {
                        data: data.map((r) => r.amount_total),
                        backgroundColor: this.chartPalette,
                        borderColor: "#ffffff",
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "60%",
                plugins: {
                    legend: {
                        position: "right",
                        labels: { boxWidth: 12, padding: 12 },
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.label}: ${this.formatMoney(ctx.parsed)}`,
                        },
                    },
                },
            },
        });
    }

    formatMoney(value) {
        return `${this.state.currency} ${this.formatNumber(value, 0)}`;
    }

    formatNumber(value, decimals = 2) {
        return Number(value || 0).toLocaleString(undefined, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
        });
    }
}

MinoriSalesDashboard.template = "method_minori.SalesDashboard";
MinoriSalesDashboard.components = { DashboardTable };

registry.category("actions").add("method_minori_sales_dashboard", MinoriSalesDashboard);
