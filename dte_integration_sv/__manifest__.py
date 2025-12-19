{
    'name': 'DTE Integration El Salvador',
    'version': '1.0',
    'summary': 'Descripción breve',
    'description': """
        Descripción más detallada, funcionalidades clave.
    """,
    'depends': ['base','account','uom','point_of_sale'],
    'author': "Ingenio Solutions",
    'website': "http://www.ingeniosolutions.com.ar",
    'category': '',
    'data': [
        # SECURITY
        'security/ir.model.access.csv',

        #DATA
        'data/ir_secuence.xml',

        # VIEWS
        'views/res_config_settings.xml',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/uom_uom.xml',
        'views/account_journal.xml',
        'views/account_move.xml',
        'views/actividad_economica.xml',
        'views/municipio_info.xml',
        'views/account_tax.xml',
        'views/pos_payment_method.xml',
    ],
        'assets': {
        'point_of_sale._assets_pos': [
            'dte_integration_sv/static/src/**/*'
        ],
    },

    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}