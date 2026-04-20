{
    'name': 'AI Demo',
    'version': '19.0.1.0.0',
    'summary': 'Demo addon showcasing Odoo 19 AI capabilities for Sales, Leads & Activities',
    'description': """
        Demonstrates Odoo 19 AI features:
        - Pre-visit reports on CRM Leads (open invoices, late payments, backorders, communication, logistics)
        - AI-generated sale offers based on sale history and messages
        - Suggested and planned activities (including from voice transcriptions)
    """,
    'author': 'Demo',
    'category': 'Technical',
    'depends': ['ai', 'crm', 'sale', 'stock', 'account'],
    'data': [
        'data/ai_tools_leads.xml',
        'data/ai_tools_sales.xml',
        'data/ai_tools_activities.xml',
        'data/ai_topics.xml',
        'data/ai_agent.xml',
        'data/ai_composer.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
