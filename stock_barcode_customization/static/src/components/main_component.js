import { patch } from "@web/core/utils/patch";
import { download } from "@web/core/network/download";
import { onWillStart } from "@odoo/owl";

import MainComponent from "@stock_barcode/components/main"


patch(MainComponent.prototype, {

    setup() {
        super.setup()
        onWillStart(async () => {
            this.user_is_admin = await this.orm.call("res.users", "is_base_admin", [], {})
        })
    },

    onClickExportXlsx() {

        const currentLines = this.env.model.currentState.lines

        download({
            url: "/custom-barcode/export_xlsx",
            data: {
                data: new Blob([JSON.stringify({
                    rows: currentLines.map(l => ({
                        id: l.id,
                        product_id: l.product_id.id,
                        inventory_quantity: l.inventory_quantity,
                        quantity: l.quantity,
                    }))
                })], { type: "application/json" })
            },
        });
    }
})