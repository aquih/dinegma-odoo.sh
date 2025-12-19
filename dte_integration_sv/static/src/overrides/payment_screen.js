/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    toggleCreditoFiscal() {
        this.currentOrder.set_credito_fiscal(!this.currentOrder.es_credito_fiscal);
    }
});