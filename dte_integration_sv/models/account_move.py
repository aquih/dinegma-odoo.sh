# -*- coding: utf-8 -*-
import requests
from odoo import models, fields, api
from odoo.exceptions import UserError
import uuid
from datetime import datetime
import base64
class AccountMove(models.Model):
    _inherit = "account.move"

    es_diferido = fields.Boolean(string="Es Modelo Diferido")
    es_contingencia = fields.Boolean(string="Es Tipo Contingencia", help="Tipo de Operación Contingencia para el DTE")
    tipo_contingencia = fields.Selection([('01','No disponibilidad de sistema del MH'),('02','No disponibilidad de sistema del emisor '),
                                          ('03','Falla en el suministro de servicio de Internet del Emisor'),
                                          ('04', 'Falla en el suministro de servicio de energía eléctrica del emisor que impida la transmisión de los DTE'),
                                          ('05', 'Otro (deberá digitar un máximo de 500 caracteres explicando el motivo)')
                                        ])
    motivo_contingencia = fields.Char(string="Motivo Contingencia", help="Motivo de la Contingencia para el DTE")

    syncronized_with_fesv = fields.Boolean(string="Sincronizado con FESV", readonly=True, default=False)
    json_data_fesv = fields.Json(string="Datos JSON FESV", readonly=True,store=True)
    generation_code_uuid = fields.Char(string="Código de Generación UUID", readonly=True)

    pdf_generado = fields.Char(string="PDF Generado", readonly=True,store=True)
    pdf_generado_anulacion = fields.Char(string="PDF Generado Anulacion", readonly=True,store=True)
    firma_electronica = fields.Text(sting="Firma Electrónica", readonly=True,store=True)
    firma_electronica_anulacion = fields.Text(sting="Firma ElectrónicaAnulacion", readonly=True,store=True)
    sello_recibido = fields.Char(string="Sello Recibido", readonly=True,store=True)
    sello_recibido_anulacion = fields.Char(string="Sello Recibido", readonly=True,store=True)

    tipo_anulacion = fields.Selection([('1','Error en la Información del Documento Tributario Electrónico a invalidar.'),
                                       ('2','Rescindir de la operación realizada.'),
                                       ('3','Otro')
                                       ])
    anulado = fields.Boolean(string="DTE Anulado", readonly=True, default=False)
    motivo_anulacion = fields.Char(string="Motivo Anulación", help="Motivo de la Anulación para el DTE")
    dte_reemplazo = fields.Many2one('account.move', string="DTE de Reemplazo",
                                    help="Seleccione el DTE que reemplazará este documento.",
                                    domain="[('anulado', '=', False), ('syncronized_with_fesv', '=', True)]")

    es_credito_fiscal = fields.Boolean(string="Es Crédito Fiscal", help="Indica si el DTE es un crédito fiscal.")
    motivo_error = fields.Text(string="Errores")

    def _remove_none(self, value):
        if isinstance(value, dict):
            return {k: self._remove_none(v) for k, v in value.items() if v is not None}
        if isinstance(value, list):
            return [self._remove_none(v) for v in value if v is not None]
        return value



    def _attach_fesv_pdf(self, pdf_url,anulacion=False):
        self.ensure_one()

        try:
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()
        except Exception as e:
            raise UserError(f"No se pudo descargar el PDF desde FESV: {str(e)}")

        pdf_content = response.content
        pdf_b64 = base64.b64encode(pdf_content)
        if anulacion:
            filename = f"Documento_Anulacion{self.name or self.id}.pdf"
        else:
            filename = f"Documento_{self.name or self.id}.pdf"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': pdf_b64,
            'res_model': 'account.move',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        if anulacion:
            self.message_post(
                body="PDF de Anulación DTE (FESV) adjunto.",
                attachment_ids=[attachment.id]
            )
        else:
            self.message_post(
                body="PDF de Documento DTE (FESV) adjunto.",
                attachment_ids=[attachment.id]
            )

        return attachment

    def sync_invoice_fesv(self, data):
        headers = {
            'content-type': 'application/json',
            'usuario': self.company_id.username,
            'llave': self.company_id.key,
        }
        cfg_env = self.env['ir.config_parameter']
        environment = cfg_env.sudo().get_param('dte_integration_sv.environment_bill_configuration')
        if environment == 'production':
            url = self.company_id.general_stage_url.general_prod_url
        else:
            url = self.company_id.general_stage_url
        try:
            response = requests.post(
                url=url,
                json=data,
                headers=headers
            )
            json_response = response.json()
            self.write({
                'json_data_fesv': json_response
            })
            if response.status_code in [200,201]:
                self.syncronized_with_fesv = True
                self.pdf_generado = json_response.get('pdf_path')
                self.firma_electronica = json_response.get('json').get('firmaElectronica')
                self.sello_recibido = json_response.get('json').get('selloRecibido')
                if self.pdf_generado:
                    self._attach_fesv_pdf(self.pdf_generado)
                self.message_post(body="Factura sincronizada correctamente con FESV.")
            else:
                errores = json_response.get('errores')
                mensajes_error = []
                if errores.get('descripcionMsg'):
                    mensajes_error.append(errores.get('descripcionMsg'))
                    raise UserError(f"{mensajes_error}")

                if isinstance(errores, dict):
                    for campo, mensaje in errores.items():
                        mensajes_error.append(f"{campo}: {mensaje}")

                elif isinstance(errores, list):
                    for mensaje in errores:
                        mensajes_error.append(str(mensaje))

                elif errores:
                    mensajes_error.append(str(errores))

                raise UserError(f"{mensajes_error}")
        except Exception as e:
            raise UserError(f"Error de conexión con FESV: {str(e)}")




    def prepare_documento_data(self):
        tipo_dte = False
        if self.move_type in ['out_invoice', 'in_invoice']:
            if not self.debit_origin_id:
                tipo_dte = '01'
            else:
                tipo_dte = '06'
                if not self.debit_origin_id.es_credito_fiscal:
                    raise UserError('No se puede emitir una nota de débito asociada a un documento que no es crédito fiscal.')

        if self.move_type in ['out_refund', 'in_refund']:
            tipo_dte = '05'

            if not self.reversed_entry_id.es_credito_fiscal:
                raise UserError(
                    'No se puede emitir una nota de crédito asociada a un documento que no es crédito fiscal.')

        if self.es_credito_fiscal and tipo_dte not in ["05","06"]:
            tipo_dte = '03'

        generation_code_uuid = str(uuid.uuid4()).upper()
        self.generation_code_uuid = generation_code_uuid
        company_code = f"{self.company_id.cod_company}{self.journal_id.cod_punto_venta}"
        numero_secuencial = self.journal_id.secuencia_pdv_id.next_by_id()
        document = {
            'tipo_dte': tipo_dte,
            'establecimiento':  self.company_id.cod_establecimiento,
            'condicion_pago': 1, #TODO aca es 1 para contado, 2 para credoto y 3 para otro ,
            'actividad_economica': self.partner_id.actividad_economica_id.code if self.partner_id.actividad_economica_id else '',
            'uuid': generation_code_uuid,
            'numero_control': f"DTE-{tipo_dte}-{company_code}-{numero_secuencial}",
            'fecha_emision': (self.invoice_date or fields.Date.today()).strftime('%Y-%m-%d'),
            'hora_emision': datetime.now().strftime('%H:%M:%S'),
            'punto_venta': self.journal_id.cod_punto_venta,
            'descuento_no_sujeto':None,
            'descuento_exentas':None,
            'descuento_gravadas':None,
            'porcentaje_descuento':None,
            'renta_retenida':None,
            'retener_iva':None,
            'numero_pago_electronico':None,
            'tipo_contingencia': int(self.tipo_contingencia) if self.tipo_contingencia else None,
            'motivo_contingencia': self.motivo_contingencia,
            'documentos_relacionados': self.prepare_documento_relacionado(),
            'receptor': self.prepare_receptor_data(),
            # 'otros_documentos': None,
            'venta_tercero': None,
            'items': self.prepare_items_data(),
            'pagos': self.prepare_payments_data(),
            # 'extension': self.prepare_extension_data(),
            # 'aprendice': self.prepare_apendice_data(),
        }

        return document


    def prepare_documento_relacionado(self):
        documento_relacionado = []
        if self.move_type in ['out_refund','in_refund'] or self.debit_origin_id:
            generation_code_uuid = None
            tipo_documento = "03"
            fecha_emision = None
            if self.debit_origin_id:
                generation_code_uuid = self.debit_origin_id.generation_code_uuid
                fecha_emision = self.debit_origin_id.invoice_date.strftime('%Y-%m-%d') if self.debit_origin_id.invoice_date else None

            elif self.reversed_entry_id:
                generation_code_uuid = self.reversed_entry_id.generation_code_uuid
                fecha_emision = self.reversed_entry_id.invoice_date.strftime('%Y-%m-%d') if self.reversed_entry_id.invoice_date else None

            documento_relacionado.append({
                'tipo_documento': tipo_documento,
                'tipo_generacion': 2,
                'numero_documento': generation_code_uuid,
                'fecha_emision': fecha_emision,
             })
            return documento_relacionado

        return None



    def prepare_receptor_data(self):
        if self.move_type in ['out_invoice','in_invoice'] and not self.debit_origin_id and not self.es_credito_fiscal:
            receptor = {
                'nombre': self.partner_id.name,
                'correo': self.partner_id.email
            }
        else:
            receptor = {
                'nombre': self.partner_id.name,
                'correo': self.partner_id.email,
                'numero_documento': self.partner_id.x_studio_no_de_documento,
                'nrc': self.partner_id.nrc if self.partner_id.nrc else None,
                'codigo_actividad': self.partner_id.actividad_economica_id.code or None,
                'direccion': {
                    'departamento': self.partner_id.departamento or None,
                    'municipio': self.partner_id.municipio_id.code or None,
                    'complemento': self.partner_id.street or None,
                },

            }

        return receptor


    def tipo_de_venta(self, tax):
        if tax.amount and tax.amount > 0:
                return "gravada"
        nombre = tax.name.lower()

        if "iva" in nombre:
            return "no_gravada"

        return "no_sujeta"


    def prepare_items_data(self):
        items = []
        for idx, line in enumerate(self.invoice_line_ids, start=1):
            tipo_item = ''
            unidad_medida = None
            if line.product_id.type == 'consu':
                tipo_item = 1
            elif line.product_id.type == 'service':
                tipo_item = 2
                unidad_medida = 99
            elif line.product_id.type == 'combo':
                break

            price_unit = line.price_unit
            tributos = None
            category_tax = self.tipo_de_venta(line.tax_ids[0]) if line.tax_ids else ''

            if self.move_type in ['out_invoice','in_invoice'] and not self.debit_origin_id and category_tax == 'gravada' and not self.es_credito_fiscal:
                price_unit = line.price_total
            else:
                if self.es_credito_fiscal:
                    price_unit = line.price_subtotal
                tributos = []
                tax = line.tax_ids[0] if line.tax_ids else None
                if tax:
                    tributos.append({
                        'codigo': tax.cod_tributo,
                        'monto': price_unit * (tax.amount / 100),
                    })

            if price_unit > 0:
                if self.move_type in ['out_invoice', 'in_invoice'] and not self.debit_origin_id:
                    data = {
                        'tipo': tipo_item,
                        'cantidad': line.quantity,
                        'unidad_medida': unidad_medida if unidad_medida else line.product_uom_id.dte_uom_code,
                        'descripcion': line.name or line.product_id.name or 'Sin descripción',
                        'precio_unitario': price_unit / line.quantity,
                        'tributos': tributos,
                    }
                    items.append(data)
                else:
                    if self.debit_origin_id:
                        generation_code_uuid = self.debit_origin_id.generation_code_uuid
                    else:
                        generation_code_uuid = self.reversed_entry_id.generation_code_uuid
                    items.append({
                        'tipo': tipo_item,
                        'cantidad': line.quantity,
                        'unidad_medida': unidad_medida if unidad_medida else line.product_uom_id.dte_uom_code,
                        'descripcion': line.name or line.product_id.name or 'Sin descripción',
                        'precio_unitario': price_unit,
                        'tributos': tributos,
                        'numero_documento': generation_code_uuid,
                    })
        return items


    def prepare_payments_data(self):
        pagos = []
        payments = self.payment_ids
        if not payments:
            payments = self.mapped('pos_order_ids').mapped('payment_ids')
        for payment in payments:
            pagos.append({
                'tipo': payment.payment_method_id.cod_forma_pago,
                'monto': payment.amount,
            })

        return pagos



    def prepare_sync_data(self):
        self.ensure_one()
        prepare_data = {
            'documento': self.prepare_documento_data(),

        }
        prepare_data = self._remove_none(prepare_data)
        if not self.es_diferido:
            self.sync_invoice_fesv(prepare_data)



    def prepare_invalidate_dte_data(self):
        if not self.tipo_anulacion:
            raise UserError("Debe seleccionar un tipo de anulación para invalidar el DTE.")

        if self.tipo_anulacion and self.tipo_anulacion != '2':
            if not self.dte_reemplazo:
                raise UserError("Debe seleccionar un archivo para reemplazar el DTE a invalidar.")

        invalidacion = {
            'establecimiento': self.company_id.cod_establecimiento,
            'uuid': self.generation_code_uuid,
            'tipo_anulacion': int(self.tipo_anulacion),
            'motivo': self.motivo_anulacion or '',
            'nuevo_documento': self.dte_reemplazo.generation_code_uuid or None,
            'responsable': {
                'nombre': self.company_id.name,
                'tipo_documento': self.company_id.tipo_documento or "36",
                'numero_documento': self.company_id.vat,
            },
            'solicitante': {
                'nombre': self.partner_id.name,
                'tipo_documento':self.partner_id.tipo_documento or "36",
                'numero_documento': self.partner_id.x_studio_no_de_documento,
                'correo': self.partner_id.email,
            }
        }

        data = {
            'invalidacion': invalidacion
        }

        data = self._remove_none(data)

        return data


    def invalidate_dte(self):
        headers = {
            'content-type': 'application/json',
            'usuario': self.company_id.username,
            'llave': self.company_id.key,
        }
        cfg_env = self.env['ir.config_parameter']
        environment = cfg_env.sudo().get_param('dte_integration_sv.environment_bill_configuration')
        if environment == 'production':
            url = self.company_id.invalidation_prod_url
        else:
            url = self.company_id.invalidation_stage_url

        data_invalidation = self.prepare_invalidate_dte_data()

        try:
            response = requests.post(
                url=url,
                json=data_invalidation,
                headers=headers
            )
            json_response = response.json()
            if response.status_code in [200,201]:
                self.anulado = True
                self.pdf_generado_anulacion = json_response.get('pdf_path')
                self.firma_electronica_anulacion = json_response.get('json').get('firmaElectronica')
                self.sello_recibido_anulacion = json_response.get('respuesta_dgi').get('selloRecibido')

                if self.pdf_generado_anulacion:
                    self._attach_fesv_pdf(self.pdf_generado_anulacion, anulacion=True)
                self.message_post(body="DTE invalidado correctamente en FESV.")
            else:
                errores = json_response.get('errores')
                mensajes_error = []
                if errores.get('descripcionMsg'):
                    mensajes_error.append(errores.get('descripcionMsg'))
                    raise UserError(f"{mensajes_error}")

                if isinstance(errores, dict):
                    for campo, mensaje in errores.items():
                        mensajes_error.append(f"{campo}: {mensaje}")

                elif isinstance(errores, list):
                    for mensaje in errores:
                        mensajes_error.append(str(mensaje))

                elif errores:
                    mensajes_error.append(str(errores))

                raise UserError(f"{mensajes_error}")
        except Exception as e:
            raise UserError(f"Error de conexión con FESV: {str(e)}")


