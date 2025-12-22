/** @odoo-module */

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    setup() {
        super.setup(...arguments);
        this.es_credito_fiscal = false;
    },


    set_credito_fiscal(es_credito_fiscal) {
        this.assert_editable()
        this.es_credito_fiscal = es_credito_fiscal;
    }
});